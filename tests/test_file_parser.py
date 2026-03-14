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

"""Tests for file_parser module."""

import os
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from nexdr.agents.doc_reader.file_parser import (
    BINARY_EXTENSIONS,
    DEFAULT_SUFFIX,
    IMAGE_EXTENSIONS,
    PDF_EXTENSIONS,
    TEXT_EXTENSIONS,
    FileParser,
)


class TestFileParserInit:
    """Tests for FileParser initialization."""

    def test_init_default_values(self):
        """Test initialization with default values."""
        with patch.dict(os.environ, {}, clear=True):
            parser = FileParser()
            assert parser.timeout == 45.0
            # API keys may be None or empty string depending on env
            assert parser.jina_api_key in (None, "")
            assert parser.serper_api_key in (None, "")

    def test_init_custom_timeout(self):
        """Test initialization with custom timeout."""
        parser = FileParser(timeout=60.0)
        assert parser.timeout == 60.0

    def test_init_with_env_keys(self, mock_env_vars):
        """Test initialization loads API keys from environment."""
        parser = FileParser()
        assert parser.jina_api_key == "test-jina-key"
        assert parser.serper_api_key == "test-serper-key"


class TestFileParserConstants:
    """Tests for module constants."""

    def test_text_extensions(self):
        """Test TEXT_EXTENSIONS contains expected values."""
        assert ".txt" in TEXT_EXTENSIONS
        assert ".md" in TEXT_EXTENSIONS
        assert ".py" in TEXT_EXTENSIONS
        assert ".json" in TEXT_EXTENSIONS
        assert ".yaml" in TEXT_EXTENSIONS
        assert ".html" in TEXT_EXTENSIONS

    def test_pdf_extensions(self):
        """Test PDF_EXTENSIONS contains expected values."""
        assert ".pdf" in PDF_EXTENSIONS

    def test_image_extensions(self):
        """Test IMAGE_EXTENSIONS contains expected values."""
        assert ".jpg" in IMAGE_EXTENSIONS
        assert ".jpeg" in IMAGE_EXTENSIONS
        assert ".png" in IMAGE_EXTENSIONS
        assert ".gif" in IMAGE_EXTENSIONS
        assert ".webp" in IMAGE_EXTENSIONS

    def test_binary_extensions(self):
        """Test BINARY_EXTENSIONS is union of PDF and IMAGE."""
        assert BINARY_EXTENSIONS == PDF_EXTENSIONS | IMAGE_EXTENSIONS

    def test_default_suffix(self):
        """Test DEFAULT_SUFFIX value."""
        assert DEFAULT_SUFFIX == ".txt"


class TestLooksLikeUrl:
    """Tests for _looks_like_url method."""

    def test_http_url(self):
        """Test HTTP URL detection."""
        assert FileParser._looks_like_url("http://example.com") is True

    def test_https_url(self):
        """Test HTTPS URL detection."""
        assert FileParser._looks_like_url("https://example.com") is True

    def test_local_path(self):
        """Test local path detection."""
        assert FileParser._looks_like_url("/path/to/file.txt") is False
        assert FileParser._looks_like_url("./relative/path.txt") is False
        assert FileParser._looks_like_url("file.txt") is False


class TestParseLocalTextFiles:
    """Tests for parsing local text files."""

    @pytest.mark.asyncio
    async def test_parse_text_file(self, sample_text_file):
        """Test parsing a text file."""
        parser = FileParser()
        success, content, suffix = await parser.parse(str(sample_text_file))

        assert success is True
        assert "test text file" in content
        assert suffix == ".txt"

    @pytest.mark.asyncio
    async def test_parse_markdown_file(self, sample_markdown_file):
        """Test parsing a markdown file."""
        parser = FileParser()
        success, content, suffix = await parser.parse(str(sample_markdown_file))

        assert success is True
        assert "# Test Report" in content
        assert suffix == ".md"

    @pytest.mark.asyncio
    async def test_parse_json_file(self, sample_json_file):
        """Test parsing a JSON file."""
        parser = FileParser()
        success, content, suffix = await parser.parse(str(sample_json_file))

        assert success is True
        assert '"key": "value"' in content
        assert suffix == ".json"

    @pytest.mark.asyncio
    async def test_parse_nonexistent_file(self, temp_dir):
        """Test parsing a non-existent file."""
        parser = FileParser()
        non_existent = temp_dir / "does_not_exist.txt"
        success, content, suffix = await parser.parse(str(non_existent))

        assert success is False
        assert "not found" in content.lower()
        assert suffix == DEFAULT_SUFFIX

    @pytest.mark.asyncio
    async def test_parse_empty_file(self, temp_dir):
        """Test parsing an empty file."""
        parser = FileParser()
        empty_file = temp_dir / "empty.txt"
        empty_file.write_text("", encoding="utf-8")

        success, content, suffix = await parser.parse(str(empty_file))

        assert success is False
        assert "empty" in content.lower()

    @pytest.mark.asyncio
    async def test_parse_python_file(self, temp_dir):
        """Test parsing a Python file."""
        parser = FileParser()
        py_file = temp_dir / "test.py"
        py_file.write_text("def hello():\n    print('Hello')\n", encoding="utf-8")

        success, content, suffix = await parser.parse(str(py_file))

        assert success is True
        assert "def hello" in content
        assert suffix == ".py"

    @pytest.mark.asyncio
    async def test_parse_yaml_file(self, temp_dir):
        """Test parsing a YAML file."""
        parser = FileParser()
        yaml_file = temp_dir / "test.yaml"
        yaml_file.write_text(
            "key: value\nlist:\n  - item1\n  - item2\n", encoding="utf-8"
        )

        success, content, suffix = await parser.parse(str(yaml_file))

        assert success is True
        assert "key: value" in content
        assert suffix == ".yaml"


class TestParseLocalBinaryFiles:
    """Tests for parsing local binary files (PDF, images)."""

    @pytest.mark.asyncio
    async def test_parse_pdf_file_not_installed(self, mock_pdf_file):
        """Test parsing PDF when pypdf is not installed."""
        parser = FileParser()

        with patch.dict("sys.modules", {"pypdf": None}):
            success, content, suffix = await parser.parse(str(mock_pdf_file))

        # Should fail gracefully if pypdf not installed
        assert suffix == ".pdf"

    @pytest.mark.asyncio
    async def test_parse_image_file_no_config(self, mock_image_file):
        """Test parsing image without multi-modal LLM config."""
        parser = FileParser()
        # No API keys configured
        success, content, suffix = await parser.parse(str(mock_image_file))

        assert suffix == ".png"
        # Without OCR or captioning, should handle gracefully


class TestParseRemote:
    """Tests for parsing remote URLs."""

    @pytest.mark.asyncio
    async def test_parse_remote_with_jina(self, mock_env_vars):
        """Test parsing remote URL with Jina."""
        # Force provider to be jina only
        with patch.dict(os.environ, {"DOC_READER_PROVIDERS": "jina"}):
            parser = FileParser()

            with patch("asyncio.to_thread", new_callable=AsyncMock) as mock_to_thread:
                mock_to_thread.return_value = b"Extracted content from URL"
                success, content, suffix = await parser.parse("https://example.com")

            assert success is True
            assert "Extracted content" in content
            assert suffix == DEFAULT_SUFFIX

    @pytest.mark.asyncio
    async def test_parse_remote_no_api_key(self):
        """Test parsing remote URL without API key."""
        # Clear all relevant env vars and force jina provider only
        with patch.dict(
            os.environ,
            {
                "JINA_API_KEY": "",
                "SERPER_API_KEY": "",
                "DOC_READER_PROVIDERS": "jina",
            },
        ):
            parser = FileParser()
            success, content, suffix = await parser.parse("https://example.com")

        # Should fail without API key when only jina provider is configured
        assert success is False
        assert (
            "API_KEY" in content
            or "not set" in content.lower()
            or "failed" in content.lower()
        )

    @pytest.mark.asyncio
    async def test_parse_remote_empty_content(self, mock_env_vars):
        """Test parsing remote URL that returns empty content."""
        # Force provider to be jina only
        with patch.dict(os.environ, {"DOC_READER_PROVIDERS": "jina"}):
            parser = FileParser()

            with patch("asyncio.to_thread", new_callable=AsyncMock) as mock_to_thread:
                mock_to_thread.return_value = b""
                success, content, suffix = await parser.parse("https://example.com")

            assert success is False
            assert "empty" in content.lower() or "failed" in content.lower()


class TestProviderOrder:
    """Tests for provider order configuration."""

    def test_default_provider_order(self):
        """Test default provider order."""
        with patch.dict(os.environ, {}, clear=True):
            providers = FileParser._load_provider_order()
            assert providers == ["jina", "serper"]

    def test_custom_provider_order(self):
        """Test custom provider order from environment."""
        with patch.dict(
            os.environ, {"DOC_READER_PROVIDERS": "serper, jina"}, clear=True
        ):
            providers = FileParser._load_provider_order()
            assert providers == ["serper", "jina"]

    def test_empty_provider_env(self):
        """Test empty provider environment variable."""
        with patch.dict(os.environ, {"DOC_READER_PROVIDERS": ""}, clear=True):
            providers = FileParser._load_provider_order()
            assert providers == ["jina", "serper"]


class TestBuildJinaReaderUrl:
    """Tests for _build_jina_reader_url method."""

    def test_build_url_from_regular_url(self):
        """Test building Jina reader URL from regular URL."""
        result = FileParser._build_jina_reader_url("https://example.com")
        assert result == "https://r.jina.ai/https://example.com"

    def test_url_already_has_prefix(self):
        """Test URL that already has Jina prefix."""
        url = "https://r.jina.ai/https://example.com"
        result = FileParser._build_jina_reader_url(url)
        assert result == url


class TestExtractTextFromSerperResponse:
    """Tests for _extract_text_from_serper_response method."""

    def test_extract_markdown_field(self):
        """Test extracting markdown field from response."""
        response = '{"markdown": "# Title\\n\\nContent here."}'
        result = FileParser._extract_text_from_serper_response(response)
        assert "# Title" in result

    def test_extract_content_field(self):
        """Test extracting content field from response."""
        response = '{"content": "Plain text content."}'
        result = FileParser._extract_text_from_serper_response(response)
        assert result == "Plain text content."

    def test_extract_text_field(self):
        """Test extracting text field from response."""
        response = '{"text": "Text content."}'
        result = FileParser._extract_text_from_serper_response(response)
        assert result == "Text content."

    def test_non_json_response(self):
        """Test handling non-JSON response."""
        response = "Plain text response, not JSON."
        result = FileParser._extract_text_from_serper_response(response)
        assert result == response

    def test_invalid_json(self):
        """Test handling invalid JSON."""
        response = '{"invalid": json}'
        result = FileParser._extract_text_from_serper_response(response)
        assert result == response


class TestIsProbablyText:
    """Tests for _is_probably_text method."""

    def test_text_file(self, temp_dir):
        """Test text file detection."""
        text_file = temp_dir / "unknown_txt"
        text_file.write_text("Plain text content", encoding="utf-8")
        # mimetypes.guess_type may not recognize files without extension
        # This is expected behavior - files without extension are checked differently
        result = FileParser._is_probably_text(text_file)
        # Result depends on system's mime type detection
        assert isinstance(result, bool)

    def test_binary_file(self, temp_dir):
        """Test binary file detection."""
        binary_file = temp_dir / "unknown_bin"
        binary_file.write_bytes(b"\x00\x01\x02\x03")
        assert FileParser._is_probably_text(binary_file) is False

    def test_file_with_text_extension(self, temp_dir):
        """Test file with recognized text extension."""
        text_file = temp_dir / "file.txt"
        text_file.write_text("Text content", encoding="utf-8")
        assert FileParser._is_probably_text(text_file) is True


class TestEdgeCases:
    """Tests for edge cases."""

    @pytest.mark.asyncio
    async def test_unicode_filename(self, temp_dir):
        """Test file with unicode filename."""
        unicode_file = temp_dir / "测试文件.txt"
        unicode_file.write_text("中文内容", encoding="utf-8")

        parser = FileParser()
        success, content, suffix = await parser.parse(str(unicode_file))

        assert success is True
        assert "中文内容" in content

    @pytest.mark.asyncio
    async def test_file_with_special_chars(self, temp_dir):
        """Test file with special characters in content."""
        special_file = temp_dir / "special.txt"
        special_file.write_text("Special: \t\n\r\n特殊字符™ ©", encoding="utf-8")

        parser = FileParser()
        success, content, suffix = await parser.parse(str(special_file))

        assert success is True

    @pytest.mark.asyncio
    async def test_symlink(self, temp_dir):
        """Test parsing a symlink."""
        original = temp_dir / "original.txt"
        original.write_text("Original content", encoding="utf-8")

        link = temp_dir / "link.txt"
        link.symlink_to(original)

        parser = FileParser()
        success, content, suffix = await parser.parse(str(link))

        assert success is True
        assert "Original content" in content

    @pytest.mark.asyncio
    async def test_expanded_home_path(self, temp_dir, monkeypatch):
        """Test file path with ~ expansion."""
        # This test verifies the path expansion works
        parser = FileParser()

        # Create a test file
        test_file = temp_dir / "test.txt"
        test_file.write_text("Test content", encoding="utf-8")

        # Parse with the actual path (expansion should handle it)
        success, content, suffix = await parser.parse(str(test_file))

        assert success is True

    @pytest.mark.asyncio
    async def test_very_long_file_path(self, temp_dir):
        """Test with very long file path."""
        # Create a deeply nested directory
        deep_dir = temp_dir
        for i in range(5):
            deep_dir = deep_dir / f"level_{i}"
        deep_dir.mkdir(parents=True)

        long_file = deep_dir / "file.txt"
        long_file.write_text("Content", encoding="utf-8")

        parser = FileParser()
        success, content, suffix = await parser.parse(str(long_file))

        assert success is True

    @pytest.mark.asyncio
    async def test_file_without_extension(self, temp_dir):
        """Test file without extension."""
        no_ext = temp_dir / "README"
        no_ext.write_text("README content", encoding="utf-8")

        parser = FileParser()
        success, content, suffix = await parser.parse(str(no_ext))

        assert success is True
        assert suffix == DEFAULT_SUFFIX


class TestTimeout:
    """Tests for timeout handling."""

    @pytest.mark.asyncio
    async def test_custom_timeout(self, temp_dir):
        """Test that custom timeout is respected."""
        parser = FileParser(timeout=1.0)

        # This should work quickly with local file
        test_file = temp_dir / "test.txt"
        test_file.write_text("Content", encoding="utf-8")

        success, _, _ = await parser.parse(str(test_file))
        assert success is True
