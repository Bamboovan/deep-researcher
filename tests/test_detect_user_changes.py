# Copyright (c) Nex-AGI. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Tests for detect_user_changes module."""

from nexdr.agents.markdown_report_writer.detect_user_changes import (
    analyze_change_types,
    analyze_changes,
    detect_user_changes,
    extract_markdown_sections,
    infer_user_intent,
)


class TestDetectUserChanges:
    """Tests for detect_user_changes function."""

    def test_no_changes_detected(self, temp_dir):
        """Test detection when files are identical."""
        content = "# Test Report\n\n## Section 1\n\nContent here."
        file1 = temp_dir / "original.md"
        file2 = temp_dir / "modified.md"
        file1.write_text(content, encoding="utf-8")
        file2.write_text(content, encoding="utf-8")

        result = detect_user_changes(str(file1), str(file2))

        assert result["status"] == "success"
        assert result["data"]["has_changes"] is False
        assert result["data"]["changes_summary"] == "No modifications detected"

    def test_line_additions_detected(self, temp_dir):
        """Test detection of added lines."""
        original = "# Report\n\n## Section\n\nOriginal content."
        modified = "# Report\n\n## Section\n\nOriginal content.\nNew line added."

        file1 = temp_dir / "original.md"
        file2 = temp_dir / "modified.md"
        file1.write_text(original, encoding="utf-8")
        file2.write_text(modified, encoding="utf-8")

        result = detect_user_changes(str(file1), str(file2))

        assert result["status"] == "success"
        assert result["data"]["has_changes"] is True
        assert "lines added" in result["data"]["changes_summary"]

    def test_line_deletions_detected(self, temp_dir):
        """Test detection of deleted lines."""
        original = "# Report\n\n## Section\n\nLine 1.\nLine 2.\nLine 3."
        modified = "# Report\n\n## Section\n\nLine 1.\nLine 3."

        file1 = temp_dir / "original.md"
        file2 = temp_dir / "modified.md"
        file1.write_text(original, encoding="utf-8")
        file2.write_text(modified, encoding="utf-8")

        result = detect_user_changes(str(file1), str(file2))

        assert result["status"] == "success"
        assert result["data"]["has_changes"] is True
        assert "-1 lines deleted" in result["data"]["changes_summary"]

    def test_new_section_detected(self, temp_dir):
        """Test detection of new section."""
        original = "# Report\n\n## Section 1\n\nContent."
        modified = (
            "# Report\n\n## Section 1\n\nContent.\n\n## Section 2\n\nNew section."
        )

        file1 = temp_dir / "original.md"
        file2 = temp_dir / "modified.md"
        file1.write_text(original, encoding="utf-8")
        file2.write_text(modified, encoding="utf-8")

        result = detect_user_changes(str(file1), str(file2))

        assert result["status"] == "success"
        assert result["data"]["has_changes"] is True
        assert "Section 2" in result["data"]["added_sections"]

    def test_deleted_section_detected(self, temp_dir):
        """Test detection of deleted section."""
        original = "# Report\n\n## Section 1\n\nContent.\n\n## Section 2\n\nTo delete."
        modified = "# Report\n\n## Section 1\n\nContent."

        file1 = temp_dir / "original.md"
        file2 = temp_dir / "modified.md"
        file1.write_text(original, encoding="utf-8")
        file2.write_text(modified, encoding="utf-8")

        result = detect_user_changes(str(file1), str(file2))

        assert result["status"] == "success"
        assert "Section 2" in result["data"]["deleted_sections"]

    def test_modified_section_detected(self, temp_dir):
        """Test detection of modified section."""
        original = "# Report\n\n## Section\n\nOriginal content."
        modified = "# Report\n\n## Section\n\nModified content."

        file1 = temp_dir / "original.md"
        file2 = temp_dir / "modified.md"
        file1.write_text(original, encoding="utf-8")
        file2.write_text(modified, encoding="utf-8")

        result = detect_user_changes(str(file1), str(file2))

        assert result["status"] == "success"
        assert "Section" in result["data"]["modified_sections"]

    def test_original_file_not_found(self, temp_dir):
        """Test error when original file not found."""
        non_existent = temp_dir / "non_existent.md"
        existing = temp_dir / "existing.md"
        existing.write_text("content", encoding="utf-8")

        result = detect_user_changes(str(non_existent), str(existing))

        assert result["status"] == "error"
        assert "not found" in result["data"].lower()

    def test_modified_file_not_found(self, temp_dir):
        """Test error when modified file not found."""
        existing = temp_dir / "existing.md"
        existing.write_text("content", encoding="utf-8")
        non_existent = temp_dir / "non_existent.md"

        result = detect_user_changes(str(existing), str(non_existent))

        assert result["status"] == "error"
        assert "not found" in result["data"].lower()

    def test_with_global_storage(self, temp_dir, mock_global_storage):
        """Test with global storage for change history."""
        original = "# Report\n\n## Section\n\nOriginal."
        modified = "# Report\n\n## Section\n\nModified."

        file1 = temp_dir / "original.md"
        file2 = temp_dir / "modified.md"
        file1.write_text(original, encoding="utf-8")
        file2.write_text(modified, encoding="utf-8")

        result = detect_user_changes(
            str(file1), str(file2), global_storage=mock_global_storage
        )

        assert result["status"] == "success"
        history = mock_global_storage.get("user_change_history")
        assert len(history) == 1


class TestExtractMarkdownSections:
    """Tests for extract_markdown_sections function."""

    def test_extract_single_section(self):
        """Test extracting a single section."""
        content = "# Main Title\n\n## Section 1\n\nContent of section 1."
        sections = extract_markdown_sections(content)

        assert len(sections) == 2
        assert sections[0]["title"] == "Main Title"
        assert sections[1]["title"] == "Section 1"

    def test_extract_multiple_sections(self):
        """Test extracting multiple sections."""
        content = """# Title

## Section 1
Content 1.

## Section 2
Content 2.

## Section 3
Content 3.
"""
        sections = extract_markdown_sections(content)

        assert len(sections) == 4
        titles = [s["title"] for s in sections]
        assert "Section 1" in titles
        assert "Section 2" in titles
        assert "Section 3" in titles

    def test_extract_nested_sections(self):
        """Test extracting nested sections."""
        content = """# Main

## Level 2

### Level 3

Content here.
"""
        sections = extract_markdown_sections(content)

        assert len(sections) == 3

    def test_extract_sections_with_code_blocks(self):
        """Test extracting sections containing code blocks."""
        content = """# Title

## Code Section

```python
def hello():
    print("Hello")
```

End of section.
"""
        sections = extract_markdown_sections(content)

        assert len(sections) == 2
        assert "print" in sections[1]["content"]

    def test_empty_content(self):
        """Test with empty content."""
        sections = extract_markdown_sections("")
        assert sections == []

    def test_no_headers(self):
        """Test content without headers."""
        content = "Just plain text.\nNo headers here."
        sections = extract_markdown_sections(content)
        assert sections == []


class TestAnalyzeChanges:
    """Tests for analyze_changes function."""

    def test_analyze_simple_diff(self):
        """Test analyzing a simple diff."""
        original = "Line 1\nLine 2\nLine 3"
        modified = "Line 1\nLine 2 modified\nLine 3"
        lines_original = original.splitlines(keepends=True)
        lines_modified = modified.splitlines(keepends=True)

        import difflib

        diff = list(
            difflib.unified_diff(
                lines_original, lines_modified, fromfile="original", tofile="modified"
            )
        )

        result = analyze_changes(diff, original, modified)

        assert "summary" in result
        assert "details" in result
        assert result["additions"] >= 1
        assert result["deletions"] >= 1

    def test_analyze_section_changes(self):
        """Test analyzing section-level changes."""
        original = """# Report

## Section 1
Content 1.

## Section 2
Content 2.
"""
        modified = """# Report

## Section 1
Content 1.

## Section 3
Content 3.
"""
        lines_original = original.splitlines(keepends=True)
        lines_modified = modified.splitlines(keepends=True)

        import difflib

        diff = list(
            difflib.unified_diff(
                lines_original, lines_modified, fromfile="original", tofile="modified"
            )
        )

        result = analyze_changes(diff, original, modified)

        assert "Section 2" in result["deleted_sections"]
        assert "Section 3" in result["added_sections"]


class TestAnalyzeChangeTypes:
    """Tests for analyze_change_types function."""

    def test_citation_additions(self):
        """Test detection of citation additions."""
        added = ["Some text with citation【1】", "Another citation†2"]
        deleted = []

        result = analyze_change_types(added, deleted)

        assert any("citation" in ct.lower() for ct in result)

    def test_code_additions(self):
        """Test detection of code additions."""
        added = ["    def function():", "        return True", "\tpass"]
        deleted = []

        result = analyze_change_types(added, deleted)

        assert any("code" in ct.lower() for ct in result)

    def test_table_additions(self):
        """Test detection of table row additions."""
        added = ["| Header 1 | Header 2 |", "| Cell 1 | Cell 2 |"]
        deleted = []

        result = analyze_change_types(added, deleted)

        assert any("table" in ct.lower() for ct in result)

    def test_list_additions(self):
        """Test detection of list item additions."""
        added = ["- Item 1", "* Item 2", "1. Numbered item"]
        deleted = []

        result = analyze_change_types(added, deleted)

        assert any("list" in ct.lower() for ct in result)

    def test_empty_changes(self):
        """Test with empty changes."""
        result = analyze_change_types([], [])
        assert result == []


class TestInferUserIntent:
    """Tests for infer_user_intent function."""

    def test_intent_adding_conclusion(self):
        """Test intent detection for adding conclusion."""
        changes_analysis = {
            "added_sections": ["Conclusion", "展望"],
            "modified_sections": [],
            "deleted_sections": [],
        }

        result = infer_user_intent(changes_analysis, "original", "modified")

        assert result["primary_intent"] == "adding_conclusion"
        assert result["confidence"] == "high"

    def test_intent_adding_methodology(self):
        """Test intent detection for adding methodology."""
        changes_analysis = {
            "added_sections": ["方法论", "Methodology"],
            "modified_sections": [],
            "deleted_sections": [],
        }

        result = infer_user_intent(changes_analysis, "original", "modified")

        assert result["primary_intent"] == "adding_methodology"

    def test_intent_refining_introduction(self):
        """Test intent detection for refining introduction."""
        changes_analysis = {
            "added_sections": [],
            "modified_sections": ["Introduction", "引言"],
            "deleted_sections": [],
        }

        result = infer_user_intent(changes_analysis, "original", "modified")

        assert result["primary_intent"] == "refining_introduction"

    def test_intent_simplifying(self):
        """Test intent detection for deleting sections."""
        changes_analysis = {
            "added_sections": [],
            "modified_sections": [],
            "deleted_sections": ["Unnecessary Section"],
        }

        result = infer_user_intent(changes_analysis, "original", "modified")

        assert result["primary_intent"] == "simplifying"
        assert result["confidence"] == "high"

    def test_intent_mixed(self):
        """Test intent detection for mixed changes."""
        changes_analysis = {
            "added_sections": ["New Section"],
            "modified_sections": ["Introduction"],
            "deleted_sections": ["Old Section"],
        }

        result = infer_user_intent(changes_analysis, "original", "modified")

        assert result["primary_intent"] == "mixed"

    def test_intent_suggestions_generated(self):
        """Test that suggestions are always generated."""
        changes_analysis = {
            "added_sections": [],
            "modified_sections": [],
            "deleted_sections": [],
        }

        result = infer_user_intent(changes_analysis, "original", "modified")

        assert len(result["suggestions"]) > 0
        assert any("保留" in s or "保留" in s for s in result["suggestions"])


class TestEdgeCases:
    """Tests for edge cases."""

    def test_unicode_content(self, temp_dir):
        """Test with unicode content."""
        original = "# 中文报告\n\n## 第一章\n\n这是中文内容。"
        modified = "# 中文报告\n\n## 第一章\n\n这是修改后的中文内容。"

        file1 = temp_dir / "original.md"
        file2 = temp_dir / "modified.md"
        file1.write_text(original, encoding="utf-8")
        file2.write_text(modified, encoding="utf-8")

        result = detect_user_changes(str(file1), str(file2))

        assert result["status"] == "success"
        assert result["data"]["has_changes"] is True

    def test_large_file(self, temp_dir):
        """Test with large file."""
        original = "# Report\n\n" + "\n".join([f"Line {i}" for i in range(1000)])
        modified = (
            "# Report\n\n"
            + "\n".join([f"Line {i}" for i in range(1000)])
            + "\nNew line"
        )

        file1 = temp_dir / "original.md"
        file2 = temp_dir / "modified.md"
        file1.write_text(original, encoding="utf-8")
        file2.write_text(modified, encoding="utf-8")

        result = detect_user_changes(str(file1), str(file2))

        assert result["status"] == "success"
        assert result["data"]["has_changes"] is True

    def test_empty_files(self, temp_dir):
        """Test with empty files."""
        file1 = temp_dir / "original.md"
        file2 = temp_dir / "modified.md"
        file1.write_text("", encoding="utf-8")
        file2.write_text("", encoding="utf-8")

        result = detect_user_changes(str(file1), str(file2))

        assert result["status"] == "success"
        assert result["data"]["has_changes"] is False
