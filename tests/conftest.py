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

"""Pytest configuration and fixtures for NexDR tests."""

import os
import tempfile
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


# ============================================================================
# Environment Setup
# ============================================================================


@pytest.fixture(autouse=True)
def reset_env():
    """Reset environment variables before each test."""
    # Store original values
    original_env = dict(os.environ)
    yield
    # Restore original values
    os.environ.clear()
    os.environ.update(original_env)


@pytest.fixture
def mock_env_vars():
    """Set up mock environment variables for testing."""
    env_vars = {
        "JINA_API_KEY": "test-jina-key",
        "SERPER_API_KEY": "test-serper-key",
        "SEMANTIC_SCHOLAR_API_KEY": "test-ss-key",
        "MULTI_MODAL_LLM_API_KEY": "test-mm-key",
        "MULTI_MODAL_LLM_BASE_URL": "https://api.test.com/v1",
        "MULTI_MODAL_LLM_MODEL": "test-model",
    }
    with patch.dict(os.environ, env_vars):
        yield env_vars


# ============================================================================
# HTTP Mock Fixtures
# ============================================================================


@pytest.fixture
def mock_httpx_client():
    """Mock httpx.AsyncClient for testing HTTP requests."""
    with patch("httpx.AsyncClient") as mock_client:
        mock_instance = AsyncMock()
        mock_client.return_value.__aenter__.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def mock_semantic_scholar_response():
    """Mock Semantic Scholar API response."""
    return {
        "data": [
            {
                "paperId": "test-paper-1",
                "title": "Test Paper Title",
                "abstract": "This is a test abstract.",
                "authors": [
                    {"authorId": "1", "name": "John Doe"},
                    {"authorId": "2", "name": "Jane Smith"},
                ],
                "year": 2023,
                "venue": "Test Conference",
                "citationCount": 100,
                "referenceCount": 20,
                "influentialCitationCount": 10,
                "publicationDate": "2023-06-15",
                "journal": None,
                "url": "https://example.com/paper/1",
                "openAccessPdf": {"url": "https://example.com/pdf/1"},
            },
            {
                "paperId": "test-paper-2",
                "title": "Another Test Paper",
                "abstract": "Another test abstract.",
                "authors": [{"authorId": "3", "name": "Alice Johnson"}],
                "year": 2022,
                "venue": "Test Journal",
                "citationCount": 50,
                "referenceCount": 15,
                "influentialCitationCount": 5,
                "publicationDate": "2022-01-20",
                "journal": "Test Journal",
                "url": "https://example.com/paper/2",
                "openAccessPdf": None,
            },
        ],
        "total": 2,
    }


@pytest.fixture
def mock_semantic_scholar_error_response():
    """Mock Semantic Scholar API error response."""
    return {"error": "Rate limit exceeded"}


# ============================================================================
# File System Fixtures
# ============================================================================


@pytest.fixture
def temp_dir():
    """Create a temporary directory for tests."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sample_markdown_file(temp_dir):
    """Create a sample markdown file for testing."""
    content = """# Test Report

## Introduction

This is the introduction section.

## Section 1

Content of section 1 with some details.

## Conclusion

This is the conclusion.
"""
    file_path = temp_dir / "test_report.md"
    file_path.write_text(content, encoding="utf-8")
    return file_path


@pytest.fixture
def sample_modified_markdown_file(temp_dir):
    """Create a modified markdown file for testing change detection."""
    content = """# Test Report

## Introduction

This is the introduction section.
This is an added line.

## Section 1

Content of section 1 with some details.

## New Section

This is a new section added by the user.

## Conclusion

This is the modified conclusion.
"""
    file_path = temp_dir / "modified_report.md"
    file_path.write_text(content, encoding="utf-8")
    return file_path


@pytest.fixture
def sample_text_file(temp_dir):
    """Create a sample text file for testing."""
    content = "This is a test text file.\nWith multiple lines.\nFor testing purposes."
    file_path = temp_dir / "test.txt"
    file_path.write_text(content, encoding="utf-8")
    return file_path


@pytest.fixture
def sample_json_file(temp_dir):
    """Create a sample JSON file for testing."""
    content = '{"key": "value", "number": 42, "list": [1, 2, 3]}'
    file_path = temp_dir / "test.json"
    file_path.write_text(content, encoding="utf-8")
    return file_path


# ============================================================================
# Global Storage Mock
# ============================================================================


@pytest.fixture
def mock_global_storage():
    """Mock GlobalStorage for testing."""
    storage = MagicMock()
    storage._data = {}

    def get_data(key, default=None):
        return storage._data.get(key, default)

    def set_data(key, value):
        storage._data[key] = value

    storage.get.side_effect = get_data
    storage.set.side_effect = set_data
    return storage


# ============================================================================
# PDF Mock Fixtures
# ============================================================================


@pytest.fixture
def mock_pdf_file(temp_dir):
    """Create a minimal mock PDF file for testing file type detection."""
    # This is a minimal valid PDF structure (just header)
    pdf_content = b"%PDF-1.4\n%test pdf content\n%%EOF"
    file_path = temp_dir / "test.pdf"
    file_path.write_bytes(pdf_content)
    return file_path


# ============================================================================
# Image Mock Fixtures
# ============================================================================


@pytest.fixture
def mock_image_file(temp_dir):
    """Create a minimal mock image file for testing file type detection."""
    # This creates a minimal valid PNG file (1x1 transparent pixel)
    import base64

    png_data = base64.b64decode(
        "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk"
        "+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
    )
    file_path = temp_dir / "test.png"
    file_path.write_bytes(png_data)
    return file_path


# ============================================================================
# Async Test Support
# ============================================================================


@pytest.fixture
def event_loop_policy():
    """Configure event loop policy for async tests."""
    import asyncio

    return asyncio.DefaultEventLoopPolicy()
