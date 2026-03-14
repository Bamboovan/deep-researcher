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

"""
Detect user modifications to markdown reports and provide feedback to the agent.
"""

import difflib
import os
from typing import Optional

from nexau.archs.main_sub.agent_context import GlobalStorage

from nexdr.agents.tool_types import create_error_tool_result, create_success_tool_result


def detect_user_changes(
    original_file: str,
    modified_file: str,
    global_storage: Optional[GlobalStorage] = None,
):
    """
    Detect and analyze user modifications to a markdown report.

    Args:
        original_file: Path to the original generated markdown file
        modified_file: Path to the user-modified markdown file
        global_storage: Global storage for state management

    Returns:
        Tool result with change analysis or error message
    """
    try:
        # Read original file
        if not os.path.exists(original_file):
            error = f"Original file not found: {original_file}"
            message = "Failed to detect user changes"
            return create_error_tool_result(error, message, "detect_user_changes")

        # Read modified file
        if not os.path.exists(modified_file):
            error = f"Modified file not found: {modified_file}"
            message = "Failed to detect user changes"
            return create_error_tool_result(error, message, "detect_user_changes")

        with open(original_file, "r", encoding="utf-8") as f:
            original_content = f.read()

        with open(modified_file, "r", encoding="utf-8") as f:
            modified_content = f.read()

        # Check if files are identical
        if original_content == modified_content:
            data = {
                "has_changes": False,
                "changes_summary": "No modifications detected",
                "changes_detail": [],
            }
            message = "No user modifications detected"
            return create_success_tool_result(data, message, "detect_user_changes")

        # Generate diff
        original_lines = original_content.splitlines(keepends=True)
        modified_lines = modified_content.splitlines(keepends=True)

        diff = list(
            difflib.unified_diff(
                original_lines,
                modified_lines,
                fromfile="original",
                tofile="modified",
                n=3,
            )
        )

        # Analyze changes
        changes_analysis = analyze_changes(diff, original_content, modified_content)

        # Store change history if global_storage is provided
        if global_storage is not None:
            change_history = global_storage.get("user_change_history", [])
            change_record = {
                "original_file": original_file,
                "modified_file": modified_file,
                "changes_summary": changes_analysis["summary"],
                "timestamp": os.path.getmtime(modified_file),
            }
            change_history.append(change_record)
            global_storage.set("user_change_history", change_history)

        data = {
            "has_changes": True,
            "changes_summary": changes_analysis["summary"],
            "changes_detail": changes_analysis["details"],
            "added_sections": changes_analysis.get("added_sections", []),
            "modified_sections": changes_analysis.get("modified_sections", []),
            "deleted_sections": changes_analysis.get("deleted_sections", []),
            "diff_preview": "".join(diff[:50]),  # First 50 lines of diff
            "intent": infer_user_intent(
                changes_analysis, original_content, modified_content
            ),  # 新增：意图分析
        }

        message = f"User modifications detected: {changes_analysis['summary']}"
        return create_success_tool_result(data, message, "detect_user_changes")

    except Exception as e:
        error = f"Error detecting user changes: {str(e)}"
        message = "Failed to detect user changes"
        return create_error_tool_result(error, message, "detect_user_changes")


def infer_user_intent(changes_analysis: dict, original: str, modified: str) -> dict:
    """
    Infer user's editing intent based on changes.

    Args:
        changes_analysis: Output from analyze_changes
        original: Original content
        modified: Modified content

    Returns:
        Dictionary with intent analysis
    """
    intent = {
        "primary_intent": "unknown",
        "confidence": "low",
        "suggestions": [],
        "focus_areas": [],
    }

    added_sections = changes_analysis.get("added_sections", [])
    modified_sections = changes_analysis.get("modified_sections", [])
    deleted_sections = changes_analysis.get("deleted_sections", [])

    # 判断用户的主要意图
    if added_sections:
        if any(
            kw in " ".join(added_sections).lower()
            for kw in ["conclusion", "总结", "展望", "future", "conclusion"]
        ):
            intent["primary_intent"] = "adding_conclusion"
            intent["confidence"] = "high"
            intent["suggestions"].append(
                "用户新增了总结/展望部分，可能需要补充完整的结论"
            )
        elif any(
            kw in " ".join(added_sections).lower()
            for kw in ["method", "方法", "实验", "experiment", " methodology"]
        ):
            intent["primary_intent"] = "adding_methodology"
            intent["confidence"] = "high"
            intent["suggestions"].append(
                "用户新增了方法/实验部分，可能需要补充技术细节"
            )
        else:
            intent["primary_intent"] = "adding_content"
            intent["confidence"] = "medium"
            intent["suggestions"].append(f"用户新增了章节：{', '.join(added_sections)}")
            intent["focus_areas"].extend(added_sections)

    if modified_sections:
        if (
            "引言" in modified_sections
            or "introduction" in " ".join(modified_sections).lower()
        ):
            intent["primary_intent"] = "refining_introduction"
            intent["confidence"] = "medium"
            intent["suggestions"].append("用户修改了引言，可能希望调整文章的基调或重点")
        else:
            intent["primary_intent"] = "refining_content"
            intent["confidence"] = "medium"
            intent["suggestions"].append(
                f"用户修改了以下部分：{', '.join(modified_sections)}"
            )
            intent["focus_areas"].extend(modified_sections)

    if deleted_sections:
        intent["primary_intent"] = "simplifying"
        intent["confidence"] = "high"
        intent["suggestions"].append(
            f"用户删除了：{', '.join(deleted_sections)}，请不要再恢复这些内容"
        )

    # 综合判断
    if len(intent["suggestions"]) > 1:
        intent["primary_intent"] = "mixed"
        intent["suggestions"].append("用户进行了多处修改，请综合理解用户的意图")

    # 生成具体的建议
    if not intent["suggestions"]:
        intent["suggestions"].append("用户进行了修改，请仔细审查变更内容")

    intent["suggestions"].append("请保留用户的所有修改，不要覆盖")
    intent["suggestions"].append("请在用户修改的基础上，完善其他未修改的部分")

    return intent


def analyze_changes(diff: list[str], original: str, modified: str) -> dict:
    """
    Analyze diff and provide structured summary of changes.

    Args:
        diff: Unified diff output
        original: Original content
        modified: Modified content

    Returns:
        Dictionary with change analysis
    """
    summary_parts = []
    details = []

    # Count additions and deletions
    additions = 0
    deletions = 0

    added_lines = []
    deleted_lines = []

    for line in diff:
        if line.startswith("+") and not line.startswith("+++"):
            additions += 1
            added_lines.append(line[1:].strip())
        elif line.startswith("-") and not line.startswith("---"):
            deletions += 1
            deleted_lines.append(line[1:].strip())

    summary_parts.append(f"+{additions} lines added")
    summary_parts.append(f"-{deletions} lines deleted")

    # Detect section-level changes (markdown headers)
    original_sections = extract_markdown_sections(original)
    modified_sections = extract_markdown_sections(modified)

    original_section_titles = set(s["title"] for s in original_sections)
    modified_section_titles = set(s["title"] for s in modified_sections)

    added_sections = list(modified_section_titles - original_section_titles)
    deleted_sections = list(original_section_titles - modified_section_titles)
    modified_sections_list = []

    # Check for modified sections (same title, different content)
    for orig_sec in original_sections:
        for mod_sec in modified_sections:
            if orig_sec["title"] == mod_sec["title"]:
                if orig_sec["content"] != mod_sec["content"]:
                    modified_sections_list.append(orig_sec["title"])

    if added_sections:
        summary_parts.append(f"{len(added_sections)} new section(s)")
        details.extend([f"Added section: {s}" for s in added_sections])

    if deleted_sections:
        summary_parts.append(f"{len(deleted_sections)} removed section(s)")
        details.extend([f"Removed section: {s}" for s in deleted_sections])

    if modified_sections_list:
        summary_parts.append(f"{len(modified_sections_list)} modified section(s)")
        details.extend(
            [f"Modified section: {s}" for s in modified_sections_list[:10]]
        )  # Limit to 10

    # Analyze change types
    change_types = analyze_change_types(added_lines, deleted_lines)
    if change_types:
        details.append(f"Change types: {', '.join(change_types)}")

    return {
        "summary": "; ".join(summary_parts),
        "details": details,
        "additions": additions,
        "deletions": deletions,
        "added_sections": added_sections,
        "deleted_sections": deleted_sections,
        "modified_sections": modified_sections_list,
        "change_types": change_types,
    }


def extract_markdown_sections(content: str) -> list[dict]:
    """
    Extract sections from markdown content based on headers.

    Args:
        content: Markdown content

    Returns:
        List of section dictionaries with title and content
    """
    import re

    lines = content.split("\n")
    sections = []
    current_section = None
    current_content = []

    header_pattern = re.compile(r"^(#{1,6})\s+(.+)$")

    for line in lines:
        match = header_pattern.match(line)
        if match:
            # Save previous section
            if current_section is not None:
                sections.append(
                    {
                        "title": current_section,
                        "content": "\n".join(current_content),
                        "level": len(match.group(1)) if current_section else 0,
                    }
                )

            # Start new section
            level = len(match.group(1))
            current_section = match.group(2).strip()
            current_content = []
        else:
            if current_section is not None:
                current_content.append(line)

    # Add last section
    if current_section is not None:
        sections.append(
            {
                "title": current_section,
                "content": "\n".join(current_content),
            }
        )

    return sections


def analyze_change_types(added_lines: list[str], deleted_lines: list[str]) -> list[str]:
    """
    Analyze the types of changes made.

    Args:
        added_lines: Lines that were added
        deleted_lines: Lines that were deleted

    Returns:
        List of change type descriptions
    """
    change_types = []

    # Check for citation additions
    citation_additions = sum(1 for line in added_lines if "†" in line or "【" in line)
    if citation_additions > 0:
        change_types.append(f"{citation_additions} citation(s) added")

    # Check for code additions
    code_additions = sum(
        1 for line in added_lines if line.startswith("    ") or line.startswith("\t")
    )
    if code_additions > 0:
        change_types.append(f"{code_additions} code line(s) added")

    # Check for table modifications
    table_additions = sum(
        1 for line in added_lines if "|" in line and line.count("|") >= 2
    )
    if table_additions > 0:
        change_types.append(f"{table_additions} table row(s) added")

    # Check for list modifications
    list_additions = sum(
        1
        for line in added_lines
        if line.strip().startswith(("-", "*", "•", "1.", "2.", "3."))
    )
    if list_additions > 0:
        change_types.append(f"{list_additions} list item(s) added")

    return change_types


if __name__ == "__main__":
    # Test the module
    import tempfile

    # Create test files
    original = """# Test Report

## Introduction
This is the introduction.

## Section 1
Content of section 1.

## Conclusion
Original conclusion.
"""

    modified = """# Test Report

## Introduction
This is the introduction.
Added more context here.

## Section 1
Content of section 1.

## New Section
This is a new section added by user.

## Conclusion
Modified conclusion with updates.
"""

    with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f1:
        f1.write(original)
        original_file = f1.name

    with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f2:
        f2.write(modified)
        modified_file = f2.name

    result = detect_user_changes(original_file, modified_file)
    print("Test Result:")
    print(result)

    # Cleanup
    os.unlink(original_file)
    os.unlink(modified_file)
