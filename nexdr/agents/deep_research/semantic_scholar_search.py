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

import asyncio
import os
from typing import Any, Optional

import httpx
from nexau.archs.main_sub.agent_context import GlobalStorage
from nexdr.agents.tool_types import create_success_tool_result, create_error_tool_result
from nexdr.agents.deep_research.update_search_resources import update_search_resources


class SemanticScholarSearch:
    """Semantic Scholar API search implementation

    API Documentation: https://api.semanticscholar.org/api-docs/
    Free tier: 100 requests/day, no API key required
    """

    def __init__(
        self,
        timeout: float = 30.0,
        max_retries: int = 3,
        api_key: Optional[str] = None,
    ):
        self.api_key = api_key or os.getenv("SEMANTIC_SCHOLAR_API_KEY")
        self.base_url = "https://api.semanticscholar.org/graph/v1"
        self.timeout = timeout
        self.max_retries = max_retries

        # Default fields to retrieve for papers
        self.default_fields = [
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

    async def search(
        self,
        query: str,
        num_results: int = 10,
        fields: Optional[list[str]] = None,
        year_filter: Optional[tuple[int, int]] = None,
        sort_by: str = "relevance",
    ) -> list[dict[str, Any]] | str:
        """Search for academic papers on Semantic Scholar

        Args:
            query: Search query string
            num_results: Number of results to return
            fields: List of fields to retrieve for each paper
            year_filter: Tuple of (min_year, max_year) to filter by publication year
            sort_by: Sort order - 'relevance', 'citationCount', 'publicationDate', or 'influence'

        Returns:
            List of paper dictionaries or error message string
        """
        if fields is None:
            fields = self.default_fields

        # Build query parameters
        params = {
            "query": query,
            "limit": num_results,
            "fields": ",".join(fields),
        }

        # Add year filter if provided
        if year_filter:
            min_year, max_year = year_filter
            params["year"] = f"{min_year}-{max_year}"

        # Add sort parameter
        if sort_by in ["citationCount", "publicationDate", "influence"]:
            params["sort"] = sort_by

        for attempt in range(self.max_retries):
            try:
                headers = {}
                if self.api_key:
                    headers["x-api-key"] = self.api_key

                async with httpx.AsyncClient(
                    timeout=httpx.Timeout(
                        connect=self.timeout,
                        read=self.timeout,
                        write=self.timeout,
                        pool=self.timeout,
                    ),
                ) as client:
                    response = await client.get(
                        f"{self.base_url}/paper/search",
                        headers=headers,
                        params=params,
                    )
                    response.raise_for_status()

                    data = response.json()
                    results = data.get("data", [])

                    # Format results for consistency with other search functions
                    formatted_results = []
                    for paper in results:
                        formatted = self._format_paper_result(paper)
                        formatted_results.append(formatted)

                    return formatted_results

            except httpx.ConnectTimeout as e:
                if attempt == self.max_retries - 1:
                    return f"Connection timeout after {self.max_retries} attempts: {str(e)}"
                await asyncio.sleep(2**attempt)
                continue

            except httpx.TimeoutException as e:
                if attempt == self.max_retries - 1:
                    return (
                        f"Request timeout after {self.max_retries} attempts: {str(e)}"
                    )
                await asyncio.sleep(2**attempt)
                continue

            except httpx.HTTPStatusError as e:
                if attempt == self.max_retries - 1:
                    error_msg = f"HTTP error {e.response.status_code}: {str(e)}"
                    if e.response.status_code == 429:
                        error_msg = "Rate limit exceeded. Consider adding API key or reducing requests."
                    return error_msg
                await asyncio.sleep(2**attempt)
                continue

            except Exception as e:
                if attempt == self.max_retries - 1:
                    return f"Unexpected error: {str(e)}"
                await asyncio.sleep(2**attempt)
                continue

        return f"Failed to complete search after {self.max_retries} attempts"

    async def get_paper_details(
        self,
        paper_id: str,
        fields: Optional[list[str]] = None,
    ) -> dict[str, Any] | str:
        """Get detailed information about a specific paper

        Args:
            paper_id: Semantic Scholar paper ID or DOI
            fields: List of fields to retrieve

        Returns:
            Paper details dictionary or error message string
        """
        if fields is None:
            fields = self.default_fields + ["references", "citations", "tldr"]

        params = {"fields": ",".join(fields)}

        try:
            headers = {}
            if self.api_key:
                headers["x-api-key"] = self.api_key

            async with httpx.AsyncClient(
                timeout=httpx.Timeout(
                    connect=self.timeout,
                    read=self.timeout,
                    write=self.timeout,
                    pool=self.timeout,
                ),
            ) as client:
                response = await client.get(
                    f"{self.base_url}/paper/{paper_id}",
                    headers=headers,
                    params=params,
                )
                response.raise_for_status()

                paper = response.json()
                return self._format_paper_result(paper)

        except Exception as e:
            return f"Failed to get paper details: {str(e)}"

    async def get_citations(
        self,
        paper_id: str,
        num_results: int = 10,
    ) -> list[dict[str, Any]] | str:
        """Get papers that cite the given paper

        Args:
            paper_id: Semantic Scholar paper ID or DOI
            num_results: Number of citing papers to return

        Returns:
            List of citing papers or error message string
        """
        params = {
            "limit": num_results,
            "fields": ",".join(self.default_fields),
        }

        try:
            headers = {}
            if self.api_key:
                headers["x-api-key"] = self.api_key

            async with httpx.AsyncClient(
                timeout=httpx.Timeout(
                    connect=self.timeout,
                    read=self.timeout,
                    write=self.timeout,
                    pool=self.timeout,
                ),
            ) as client:
                response = await client.get(
                    f"{self.base_url}/paper/{paper_id}/citations",
                    headers=headers,
                    params=params,
                )
                response.raise_for_status()

                data = response.json()
                citations = data.get("data", [])

                return [self._format_paper_result(paper) for paper in citations]

        except Exception as e:
            return f"Failed to get citations: {str(e)}"

    async def get_references(
        self,
        paper_id: str,
        num_results: int = 10,
    ) -> list[dict[str, Any]] | str:
        """Get papers referenced by the given paper

        Args:
            paper_id: Semantic Scholar paper ID or DOI
            num_results: Number of referenced papers to return

        Returns:
            List of referenced papers or error message string
        """
        params = {
            "limit": num_results,
            "fields": ",".join(self.default_fields),
        }

        try:
            headers = {}
            if self.api_key:
                headers["x-api-key"] = self.api_key

            async with httpx.AsyncClient(
                timeout=httpx.Timeout(
                    connect=self.timeout,
                    read=self.timeout,
                    write=self.timeout,
                    pool=self.timeout,
                ),
            ) as client:
                response = await client.get(
                    f"{self.base_url}/paper/{paper_id}/references",
                    headers=headers,
                    params=params,
                )
                response.raise_for_status()

                data = response.json()
                references = data.get("data", [])

                return [self._format_paper_result(paper) for paper in references]

        except Exception as e:
            return f"Failed to get references: {str(e)}"

    def _format_paper_result(self, paper: dict[str, Any]) -> dict[str, Any]:
        """Format a paper result for consistency

        Args:
            paper: Raw paper data from API

        Returns:
            Formatted paper dictionary
        """
        # Extract authors
        authors = paper.get("authors", [])
        author_names = []
        for author in authors:
            if isinstance(author, dict):
                author_names.append(author.get("name", "Unknown"))
            else:
                author_names.append(str(author))

        # Handle open access PDF
        open_access_pdf = paper.get("openAccessPdf", {})
        pdf_url = None
        if isinstance(open_access_pdf, dict):
            pdf_url = open_access_pdf.get("url")

        # Build formatted result
        formatted = {
            "title": paper.get("title", "No title"),
            "authors": author_names,
            "year": paper.get("year"),
            "venue": paper.get("venue"),
            "abstract": paper.get("abstract"),
            "citationCount": paper.get("citationCount", 0),
            "referenceCount": paper.get("referenceCount", 0),
            "influentialCitationCount": paper.get("influentialCitationCount", 0),
            "publicationDate": paper.get("publicationDate"),
            "journal": paper.get("journal"),
            "url": paper.get("url"),
            "pdfUrl": pdf_url,
            "paperId": paper.get("paperId"),
            "doi": paper.get("doi"),
        }

        # Add citation snippet if available
        if "citationContext" in paper:
            formatted["citationContext"] = paper["citationContext"]

        # Add TL;DR if available
        if "tldr" in paper:
            tldr = paper["tldr"]
            if isinstance(tldr, dict):
                formatted["tldr"] = tldr.get("text", "")
            else:
                formatted["tldr"] = str(tldr)

        return formatted


def search_papers(
    query: str,
    num_results: int = 10,
    fields: Optional[list[str]] = None,
    year_filter: Optional[tuple[int, int]] = None,
    sort_by: str = "relevance",
) -> list[dict[str, Any]] | str:
    """Convenience function to search papers

    Args:
        query: Search query string
        num_results: Number of results to return
        fields: List of fields to retrieve
        year_filter: Tuple of (min_year, max_year)
        sort_by: Sort order

    Returns:
        List of paper results or error message
    """
    searcher = SemanticScholarSearch()
    return asyncio.run(
        searcher.search(
            query=query,
            num_results=num_results,
            fields=fields,
            year_filter=year_filter,
            sort_by=sort_by,
        )
    )


def semantic_scholar_search(
    query: str,
    num_results: int = 10,
    fields: Optional[list[str]] = None,
    year_filter: Optional[tuple[int, int]] = None,
    sort_by: Optional[str] = "relevance",
    global_storage: Optional[GlobalStorage] = None,
):
    """Semantic Scholar search wrapper function compatible with NexDR framework

    Args:
        query: Search query string
        num_results: Number of results to return
        fields: List of fields to retrieve for each paper
        year_filter: Tuple of (min_year, max_year) to filter by publication year
        sort_by: Sort order - 'relevance', 'citationCount', 'publicationDate', or 'influence'
        global_storage: Global storage for resource management

    Returns:
        Tool result with search results or error message
    """
    searcher = SemanticScholarSearch()
    results = asyncio.run(
        searcher.search(
            query=query,
            num_results=num_results,
            fields=fields,
            year_filter=year_filter,
            sort_by=sort_by,
        )
    )

    if isinstance(results, list):
        # Update search resources if global_storage is provided
        if global_storage is not None:
            results = update_search_resources(results, global_storage)

        data = {
            "semantic_scholar_result": results,
        }
        message = "Successfully searched Semantic Scholar"
        tool_result = create_success_tool_result(
            data, message, "semantic_scholar_search"
        )
        return tool_result
    elif isinstance(results, str):
        error = results
        message = "Failed to search Semantic Scholar"
        tool_result = create_error_tool_result(
            error, message, "semantic_scholar_search"
        )
        return tool_result
    else:
        error = "Unknown error when searching Semantic Scholar"
        message = "Failed to search Semantic Scholar"
        tool_result = create_error_tool_result(
            error, message, "semantic_scholar_search"
        )
        return tool_result


if __name__ == "__main__":
    import json
    import time

    async def main():
        searcher = SemanticScholarSearch()

        # Test 1: Basic search
        print("=" * 60)
        print("Test 1: Basic search for 'transformer attention mechanism'")
        print("=" * 60)
        start_time = time.time()

        results = await searcher.search(
            query="transformer attention mechanism",
            num_results=5,
            sort_by="citationCount",
        )

        end_time = time.time()
        print(f"Search took: {end_time - start_time:.2f} seconds")

        if isinstance(results, list):
            print(f"Found {len(results)} results\n")
            for i, paper in enumerate(results, 1):
                print(f"Paper {i}:")
                print(f"  Title: {paper['title']}")
                print(
                    f"  Authors: {', '.join(paper['authors'][:3])}{'...' if len(paper['authors']) > 3 else ''}"
                )
                print(f"  Year: {paper['year']}")
                print(f"  Venue: {paper['venue']}")
                print(f"  Citations: {paper['citationCount']}")
                if paper.get("abstract"):
                    abstract_preview = (
                        paper["abstract"][:200] + "..."
                        if len(paper["abstract"]) > 200
                        else paper["abstract"]
                    )
                    print(f"  Abstract: {abstract_preview}")
                print()
        else:
            print(f"Error: {results}")

        # Test 2: Search with year filter
        print("=" * 60)
        print("Test 2: Search with year filter (2020-2024)")
        print("=" * 60)

        results_filtered = await searcher.search(
            query="large language model",
            num_results=3,
            year_filter=(2020, 2024),
            sort_by="publicationDate",
        )

        if isinstance(results_filtered, list):
            print(f"Found {len(results_filtered)} results\n")
            for i, paper in enumerate(results_filtered, 1):
                print(f"Paper {i}:")
                print(f"  Title: {paper['title']}")
                print(f"  Year: {paper['year']}")
                print(f"  Citations: {paper['citationCount']}")
                print()
        else:
            print(f"Error: {results_filtered}")

        # Save results to file
        with open("semantic_scholar_results.json", "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        print("Results saved to semantic_scholar_results.json")

    asyncio.run(main())
