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

from typing import Optional

from nexau.archs.main_sub.agent_context import GlobalStorage

from nexdr.agents.deep_research.arxiv_search import arxiv_search_papers
from nexdr.agents.deep_research.semantic_scholar_search import semantic_scholar_search
from nexdr.agents.deep_research.web_search import web_search
from nexdr.agents.tool_types import create_error_tool_result


def search(
    query: str,
    search_source: str = "web",
    num_results: int = 10,
    web_search_type: str = "search",
    arxiv_categories: Optional[list[str]] = None,
    arxiv_sort_by: Optional[str] = "submittedDate",
    arxiv_sort_order: Optional[str] = "descending",
    semantic_scholar_fields: Optional[list[str]] = None,
    semantic_scholar_year_filter: Optional[tuple[int, int]] = None,
    semantic_scholar_sort_by: Optional[str] = "relevance",
    global_storage: Optional[GlobalStorage] = None,
):
    if search_source == "web":
        return web_search(query, web_search_type, num_results, global_storage)
    elif search_source == "arxiv":
        return arxiv_search_papers(
            query,
            arxiv_categories,
            num_results,
            arxiv_sort_by,
            arxiv_sort_order,
            global_storage,
        )
    elif search_source == "semantic_scholar":
        return semantic_scholar_search(
            query,
            num_results,
            semantic_scholar_fields,
            semantic_scholar_year_filter,
            semantic_scholar_sort_by,
            global_storage,
        )
    else:
        error = f"Invalid search source: {search_source}"
        message = "Failed to search"
        tool_result = create_error_tool_result(error, message, "search")
        return tool_result
