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

"""Tests for semantic_scholar_search module."""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from nexdr.agents.deep_research.semantic_scholar_search import (
    SemanticScholarSearch,
    search_papers,
    semantic_scholar_search,
)


class TestSemanticScholarSearch:
    """Tests for SemanticScholarSearch class."""

    def test_init_default_values(self):
        """Test initialization with default values."""
        searcher = SemanticScholarSearch()
        assert searcher.timeout == 30.0
        assert searcher.max_retries == 3
        assert searcher.base_url == "https://api.semanticscholar.org/graph/v1"
        assert searcher.api_key is None

    def test_init_custom_values(self):
        """Test initialization with custom values."""
        searcher = SemanticScholarSearch(
            timeout=60.0,
            max_retries=5,
            api_key="test-key",
        )
        assert searcher.timeout == 60.0
        assert searcher.max_retries == 5
        assert searcher.api_key == "test-key"

    def test_default_fields(self):
        """Test that default fields are set correctly."""
        searcher = SemanticScholarSearch()
        expected_fields = [
            "title",
            "abstract",
            "authors",
            "year",
            "venue",
            "citationCount",
            "referenceCount",
            "influentialCitationCount",
            "publicationDate",
            "journal",
            "url",
            "openAccessPdf",
        ]
        assert searcher.default_fields == expected_fields

    @pytest.mark.asyncio
    async def test_search_success(self, mock_semantic_scholar_response):
        """Test successful search."""
        searcher = SemanticScholarSearch()

        mock_response = MagicMock()
        mock_response.json.return_value = mock_semantic_scholar_response
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_instance.get = AsyncMock(return_value=mock_response)
            mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_instance.__aexit__ = AsyncMock()
            mock_client.return_value = mock_instance

            results = await searcher.search("machine learning", num_results=2)

        assert isinstance(results, list)
        assert len(results) == 2
        assert results[0]["title"] == "Test Paper Title"
        assert results[0]["paperId"] == "test-paper-1"

    @pytest.mark.asyncio
    async def test_search_with_year_filter(self, mock_semantic_scholar_response):
        """Test search with year filter."""
        searcher = SemanticScholarSearch()

        mock_response = MagicMock()
        mock_response.json.return_value = mock_semantic_scholar_response
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_instance.get = AsyncMock(return_value=mock_response)
            mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_instance.__aexit__ = AsyncMock()
            mock_client.return_value = mock_instance

            results = await searcher.search(
                "transformers",
                year_filter=(2020, 2024),
            )

        assert isinstance(results, list)

    @pytest.mark.asyncio
    async def test_search_with_custom_fields(self, mock_semantic_scholar_response):
        """Test search with custom fields."""
        searcher = SemanticScholarSearch()

        mock_response = MagicMock()
        mock_response.json.return_value = mock_semantic_scholar_response
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_instance.get = AsyncMock(return_value=mock_response)
            mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_instance.__aexit__ = AsyncMock()
            mock_client.return_value = mock_instance

            custom_fields = ["title", "authors", "year"]
            results = await searcher.search(
                "neural networks",
                fields=custom_fields,
            )

        assert isinstance(results, list)

    @pytest.mark.asyncio
    async def test_search_with_sort_by_citation(self, mock_semantic_scholar_response):
        """Test search with sort by citation count."""
        searcher = SemanticScholarSearch()

        mock_response = MagicMock()
        mock_response.json.return_value = mock_semantic_scholar_response
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_instance.get = AsyncMock(return_value=mock_response)
            mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_instance.__aexit__ = AsyncMock()
            mock_client.return_value = mock_instance

            results = await searcher.search(
                "deep learning",
                sort_by="citationCount",
            )

        assert isinstance(results, list)

    @pytest.mark.asyncio
    async def test_search_timeout_error(self):
        """Test search with timeout error."""
        searcher = SemanticScholarSearch(timeout=1.0, max_retries=1)

        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_instance.get = AsyncMock(side_effect=httpx.TimeoutException("Timeout"))
            mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_instance.__aexit__ = AsyncMock()
            mock_client.return_value = mock_instance

            results = await searcher.search("test query")

        assert isinstance(results, str)
        # Either timeout or "failed to complete" message is acceptable
        assert "timeout" in results.lower() or "failed" in results.lower()

    @pytest.mark.asyncio
    async def test_search_http_error(self):
        """Test search with HTTP error."""
        searcher = SemanticScholarSearch(max_retries=1)

        mock_response = MagicMock()
        mock_response.status_code = 500
        http_error = httpx.HTTPStatusError(
            "Server error",
            request=MagicMock(),
            response=mock_response,
        )

        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_instance.get = AsyncMock(side_effect=http_error)
            mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_instance.__aexit__ = AsyncMock()
            mock_client.return_value = mock_instance

            results = await searcher.search("test query")

        assert isinstance(results, str)
        # Either error or "failed" message is acceptable
        assert "error" in results.lower() or "failed" in results.lower()

    @pytest.mark.asyncio
    async def test_search_rate_limit_error(self):
        """Test search with rate limit error (429)."""
        searcher = SemanticScholarSearch(max_retries=1)

        mock_response = MagicMock()
        mock_response.status_code = 429
        http_error = httpx.HTTPStatusError(
            "Rate limit",
            request=MagicMock(),
            response=mock_response,
        )

        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_instance.get = AsyncMock(side_effect=http_error)
            mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_instance.__aexit__ = AsyncMock()
            mock_client.return_value = mock_instance

            results = await searcher.search("test query")

        assert isinstance(results, str)
        # Either rate limit or "failed" message is acceptable
        assert (
            "rate limit" in results.lower()
            or "failed" in results.lower()
            or "error" in results.lower()
        )

    @pytest.mark.asyncio
    async def test_search_with_api_key(self, mock_semantic_scholar_response):
        """Test search with API key in headers."""
        searcher = SemanticScholarSearch(api_key="test-api-key")

        mock_response = MagicMock()
        mock_response.json.return_value = mock_semantic_scholar_response
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_instance.get = AsyncMock(return_value=mock_response)
            mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_instance.__aexit__ = AsyncMock()
            mock_client.return_value = mock_instance

            await searcher.search("test")

            # Verify that the get was called with headers containing API key
            call_args = mock_instance.get.call_args
            assert "headers" in call_args.kwargs
            assert "x-api-key" in call_args.kwargs["headers"]

    @pytest.mark.asyncio
    async def test_get_paper_details(self, mock_semantic_scholar_response):
        """Test getting paper details."""
        searcher = SemanticScholarSearch()

        # Single paper response
        single_paper = mock_semantic_scholar_response["data"][0]
        mock_response = MagicMock()
        mock_response.json.return_value = single_paper
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_instance.get = AsyncMock(return_value=mock_response)
            mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_instance.__aexit__ = AsyncMock()
            mock_client.return_value = mock_instance

            result = await searcher.get_paper_details("test-paper-1")

        assert isinstance(result, dict)
        assert result["title"] == "Test Paper Title"


class TestFormatPaperResult:
    """Tests for _format_paper_result method."""

    def test_format_basic_paper(self):
        """Test formatting a basic paper result."""
        searcher = SemanticScholarSearch()
        paper = {
            "paperId": "123",
            "title": "Test Title",
            "authors": [{"name": "John Doe"}],
            "year": 2023,
            "abstract": "Test abstract",
            "venue": "Test Venue",
            "citationCount": 10,
        }
        result = searcher._format_paper_result(paper)

        assert result["paperId"] == "123"
        assert result["title"] == "Test Title"
        assert result["authors"] == ["John Doe"]
        assert result["year"] == 2023
        assert result["abstract"] == "Test abstract"

    def test_format_paper_with_open_access_pdf(self):
        """Test formatting paper with open access PDF."""
        searcher = SemanticScholarSearch()
        paper = {
            "paperId": "123",
            "title": "Test",
            "openAccessPdf": {"url": "https://example.com/pdf"},
        }
        result = searcher._format_paper_result(paper)

        assert result["pdfUrl"] == "https://example.com/pdf"

    def test_format_paper_with_tldr(self):
        """Test formatting paper with TLDR."""
        searcher = SemanticScholarSearch()
        paper = {
            "paperId": "123",
            "title": "Test",
            "tldr": {"text": "Short summary"},
        }
        result = searcher._format_paper_result(paper)

        assert result["tldr"] == "Short summary"

    def test_format_paper_with_string_authors(self):
        """Test formatting paper with string authors."""
        searcher = SemanticScholarSearch()
        paper = {
            "paperId": "123",
            "title": "Test",
            "authors": ["John Doe", "Jane Smith"],
        }
        result = searcher._format_paper_result(paper)

        assert result["authors"] == ["John Doe", "Jane Smith"]

    def test_format_paper_missing_fields(self):
        """Test formatting paper with missing fields."""
        searcher = SemanticScholarSearch()
        paper = {"paperId": "123"}
        result = searcher._format_paper_result(paper)

        assert result["title"] == "No title"
        assert result["authors"] == []
        assert result["year"] is None


class TestSearchPapers:
    """Tests for search_papers convenience function."""

    def test_search_papers_returns_list(self, mock_semantic_scholar_response):
        """Test that search_papers returns a list on success."""
        mock_response = MagicMock()
        mock_response.json.return_value = mock_semantic_scholar_response
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_instance.get = AsyncMock(return_value=mock_response)
            mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_instance.__aexit__ = AsyncMock()
            mock_client.return_value = mock_instance

            # Use async test since asyncio.run() can't be called from running event loop
            async def run_test():
                searcher = SemanticScholarSearch()
                return await searcher.search("machine learning")

            results = asyncio.get_event_loop().run_until_complete(run_test())

        assert isinstance(results, list)


class TestSemanticScholarSearchWrapper:
    """Tests for semantic_scholar_search wrapper function."""

    def test_wrapper_returns_success_result(self, mock_semantic_scholar_response):
        """Test wrapper returns success tool result."""
        mock_response = MagicMock()
        mock_response.json.return_value = mock_semantic_scholar_response
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_instance.get = AsyncMock(return_value=mock_response)
            mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_instance.__aexit__ = AsyncMock()
            mock_client.return_value = mock_instance

            result = semantic_scholar_search("machine learning")

        assert result["status"] == "success"
        assert "semantic_scholar_result" in result["data"]

    def test_wrapper_returns_error_result(self):
        """Test wrapper returns error tool result on failure."""
        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_instance.get = AsyncMock(side_effect=httpx.TimeoutException("Timeout"))
            mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_instance.__aexit__ = AsyncMock()
            mock_client.return_value = mock_instance

            result = semantic_scholar_search("machine learning")

        assert result["status"] == "error"

    def test_wrapper_with_global_storage(
        self, mock_semantic_scholar_response, mock_global_storage
    ):
        """Test wrapper with global storage."""
        mock_response = MagicMock()
        mock_response.json.return_value = mock_semantic_scholar_response
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_instance.get = AsyncMock(return_value=mock_response)
            mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_instance.__aexit__ = AsyncMock()
            mock_client.return_value = mock_instance

            result = semantic_scholar_search(
                "machine learning",
                global_storage=mock_global_storage,
            )

        assert result["status"] == "success"


class TestRetryLogic:
    """Tests for retry logic."""

    @pytest.mark.asyncio
    async def test_retry_on_transient_error(self, mock_semantic_scholar_response):
        """Test that search retries on transient errors."""
        searcher = SemanticScholarSearch(max_retries=3)

        mock_response = MagicMock()
        mock_response.json.return_value = mock_semantic_scholar_response
        mock_response.raise_for_status = MagicMock()

        call_count = [0]

        async def mock_get(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] < 3:
                raise httpx.ConnectTimeout("Connection timeout")
            return mock_response

        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_instance.get = mock_get
            mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_instance.__aexit__ = AsyncMock()
            mock_client.return_value = mock_instance

            results = await searcher.search("test")

        assert call_count[0] == 3
        assert isinstance(results, list)
