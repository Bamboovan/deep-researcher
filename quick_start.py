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

"""Test the quick start example loading agent from YAML configuration."""

import argparse
import os
import logging
import dotenv
from datetime import datetime
from pathlib import Path
import json
import shutil
import time

from nexau.archs.config.config_loader import load_agent_config
from nexau.archs.main_sub.agent_context import GlobalStorage
from nexdr.agents.html_creator.merge_slides import build_merged_presentation
from nexdr.utils.update_citation import update_citations
from nexdr.agents.markdown_report_writer.detect_user_changes import detect_user_changes


dotenv.load_dotenv()


def process_input_files(input_files: list[str], workspace: str, global_storage: GlobalStorage) -> list[dict]:
    """
    Process input files (PDF, images, text files) and store them in global storage.
    
    Args:
        input_files: List of file paths
        workspace: Workspace directory
        global_storage: Global storage instance
        
    Returns:
        List of processed file info dictionaries
    """
    from nexdr.agents.doc_reader.file_parser import FileParser
    import asyncio
    
    parser = FileParser()
    processed = []
    
    for file_path in input_files:
        if not os.path.exists(file_path):
            logger.warning(f"Input file not found: {file_path}")
            continue
        
        try:
            # Parse the file
            success, content, suffix = asyncio.run(parser.parse(file_path))
            
            if success:
                # Save extracted content to workspace
                file_name = os.path.basename(file_path)
                content_file = os.path.join(workspace, f"{file_name}.extracted.txt")
                with open(content_file, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                # Store file info
                file_info = {
                    "original_path": file_path,
                    "file_name": file_name,
                    "suffix": suffix,
                    "content_file": content_file,
                    "content_length": len(content),
                    "status": "processed",
                }
                processed.append(file_info)
                logger.info(f"Successfully processed file: {file_path} ({len(content)} chars)")
            else:
                logger.error(f"Failed to process file: {file_path} - {content}")
                processed.append({
                    "original_path": file_path,
                    "file_name": os.path.basename(file_path),
                    "suffix": suffix,
                    "status": "failed",
                    "error": content,
                })
                
        except Exception as e:
            logger.exception(f"Error processing file {file_path}: {e}")
            processed.append({
                "original_path": file_path,
                "file_name": os.path.basename(file_path),
                "status": "error",
                "error": str(e),
            })
    
    return processed

# Create logger
logger = logging.getLogger()


def get_date():
    return datetime.now().strftime("%Y-%m-%d-%H-%M-%S")


now_date = get_date()


def setup_logger(workspace: str):
    # Set logger level
    logger.setLevel(logging.INFO)

    # Clear existing handlers to avoid duplication
    if logger.handlers:
        logger.handlers.clear()

    # Create file handler
    file_handler = logging.FileHandler(
        os.path.join(workspace, f"logs_{now_date}.log"), encoding="utf-8"
    )
    file_handler.setLevel(logging.INFO)

    # Create console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)

    # Set output format
    formatter = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] [%(filename)s:%(lineno)d] %(message)s"
    )
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    # Add to logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)


def research_agent_run(query: str, context: dict, global_storage: GlobalStorage):
    script_dir = Path(__file__).parent
    research_agent_config_path = str(
        script_dir / "configs/deep_research/deep_research.yaml"
    )
    agent = load_agent_config(
        research_agent_config_path,
        global_storage=global_storage,
    )
    agent.run(query, context=context)
    agent_id = agent.config.agent_id
    agent_name = agent.config.name
    trace_key = f"{agent_name}_{agent_id}_messages"
    deep_research_trace_history = global_storage.get(trace_key)[1:]
    return deep_research_trace_history


def markdown_report_agent_run(
    deep_research_trace_history: list[dict],
    context: dict,
    global_storage: GlobalStorage,
) -> tuple[str, str]:
    script_dir = Path(__file__).parent
    markdown_report_agent_config_path = str(
        script_dir / "configs/markdown_report_writer/report_writer.yaml"
    )
    agent = load_agent_config(
        markdown_report_agent_config_path,
        global_storage=global_storage,
    )
    message = "Please write a markdown report based on the research result."
    response = agent.run(message, history=deep_research_trace_history, context=context)
    report_content, citations = update_citations(response, global_storage)
    report_path = os.path.join(context["workspace"], "markdown_report.md")
    citation_path = os.path.join(context["workspace"], "citations.json")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report_content)
    with open(citation_path, "w", encoding="utf-8") as f:
        json.dump(citations, f, ensure_ascii=False, indent=2)
    return report_path, citation_path


def markdown_report_with_feedback_loop(
    deep_research_trace_history: list[dict],
    context: dict,
    global_storage: GlobalStorage,
    max_iterations: int = 3,
) -> tuple[str, str, int]:
    """
    Generate markdown report with interactive user feedback loop.
    
    Args:
        deep_research_trace_history: Research history from deep research agent
        context: Context dictionary with workspace info
        global_storage: Global storage for state management
        max_iterations: Maximum number of revision iterations
        
    Returns:
        Tuple of (report_path, citation_path, iterations_used)
    """
    script_dir = Path(__file__).parent
    markdown_report_agent_config_path = str(
        script_dir / "configs/markdown_report_writer/report_writer.yaml"
    )
    
    agent = load_agent_config(
        markdown_report_agent_config_path,
        global_storage=global_storage,
    )
    
    report_path = os.path.join(context["workspace"], "markdown_report.md")
    citation_path = os.path.join(context["workspace"], "citations.json")
    original_report_path = os.path.join(context["workspace"], "markdown_report.original.md")
    user_modified_path = os.path.join(context["workspace"], "markdown_report.user.md")
    
    iterations_used = 0
    current_message = "Please write a markdown report based on the research result."
    current_history = deep_research_trace_history.copy()
    
    for iteration in range(1, max_iterations + 1):
        iterations_used = iteration
        logger.info(f"=== Generating markdown report (iteration {iteration}/{max_iterations}) ===")
        
        # Generate report
        response = agent.run(current_message, history=current_history, context=context)
        report_content, citations = update_citations(response, global_storage)
        
        # Save report
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(report_content)
        with open(citation_path, "w", encoding="utf-8") as f:
            json.dump(citations, f, ensure_ascii=False, indent=2)
        
        # Save original for comparison
        shutil.copy(report_path, original_report_path)
        
        logger.info(f"Report saved to: {report_path}")
        print(f"\n{'='*60}")
        print(f"Iteration {iteration}/{max_iterations} - Report generated")
        print(f"{'='*60}")
        print(f"\nPlease review and edit the report:")
        print(f"  {report_path}")
        print(f"\nOriginal version saved to:")
        print(f"  {original_report_path}")
        print(f"\nOptions:")
        print(f"  1. Edit the report file and press Enter to continue")
        print(f"  2. Type 'done' to finish (no more changes)")
        print(f"  3. Type 'skip' to skip this iteration")
        
        # Wait for user to edit
        user_input = input("\nPress Enter after you've finished editing (or type 'done'/'skip'): ").strip().lower()
        
        if user_input == 'done':
            logger.info("User finished the feedback loop")
            break
        elif user_input == 'skip':
            logger.info("User skipped this iteration")
            continue
        
        # Check if user modified the file
        if not os.path.exists(report_path):
            logger.warning("Report file not found. Ending feedback loop.")
            break
        
        # Copy user-modified file for comparison
        shutil.copy(report_path, user_modified_path)
        
        # Detect changes
        logger.info("Detecting user changes...")
        change_result = detect_user_changes(
            original_report_path,
            user_modified_path,
            global_storage,
        )
        
        if hasattr(change_result, 'data'):
            change_data = change_result.data
        elif isinstance(change_result, dict) and 'data' in change_result:
            # Result is a dict with 'data' key
            change_data = change_result['data']
        else:
            change_data = change_result
        
        if isinstance(change_data, dict) and change_data.get('has_changes'):
            logger.info(f"Changes detected: {change_data.get('changes_summary')}")
            print(f"\n✓ Changes detected:")
            print(f"  {change_data.get('changes_summary')}")
            
            if change_data.get('added_sections'):
                print(f"  Added sections: {', '.join(change_data['added_sections'][:5])}")
            if change_data.get('modified_sections'):
                print(f"  Modified sections: {', '.join(change_data['modified_sections'][:5])}")
            if change_data.get('deleted_sections'):
                print(f"  Deleted sections: {', '.join(change_data['deleted_sections'][:5])}")
            
            # Prepare feedback for agent
            feedback_message = f"""
<user_feedback>
The user has modified the report. Here's what changed:

Summary: {change_data.get('changes_summary', 'Unknown')}

Details:
{json.dumps(change_data.get('changes_detail', []), indent=2)}

Please review these changes and continue improving the report.
Focus on:
1. Expanding on the sections the user added or modified
2. Adding more details and evidence to support the user's edits
3. Maintaining consistency with the user's changes
4. Do NOT revert or undo the user's modifications
</user_feedback>
"""
            current_message = feedback_message
            # Update history to include the generated report
            current_history.append({
                "role": "assistant",
                "content": f"[Previous report generated, saved to {report_path}]"
            })
            current_history.append({
                "role": "user",
                "content": feedback_message
            })
        else:
            logger.info("No changes detected")
            print("\n✓ No changes detected")
            print("If you want to make changes, please edit the report file and run again.")
            break
    
    return report_path, citation_path, iterations_used


def html_report_agent_run(
    deep_research_trace_history: dict, context: dict, global_storage: GlobalStorage
) -> str:
    script_dir = Path(__file__).parent
    html_report_agent_config_path = str(
        script_dir / "configs/html_creator/html_creator.yaml"
    )
    agent = load_agent_config(
        html_report_agent_config_path,
        global_storage=global_storage,
    )
    message = "Please write a html presentation based on the research result."
    response = agent.run(message, history=deep_research_trace_history, context=context)
    workspace_root = context["workspace"]
    try:
        data = json.loads(response)
        filepath = data["data"]["filepath"]
        output_path = os.path.join(workspace_root, "html_report.html")
        shutil.copy(filepath, output_path)
        return output_path
    except Exception:
        agent_id = agent.config.agent_id
        agent_name = agent.config.name
        agent_key = f"{agent_name}_{agent_id}_html_creator_data"
        html_creator_data = global_storage.get(agent_key)
        slides = html_creator_data.get("slides", {})
        slide_name = html_creator_data.get("metadata", {}).get(
            "slide_name", "Presentation"
        )
        each_page_contents = []
        for slide in slides.values():
            each_page_contents.append(slide["content"])
        merged_html_content = build_merged_presentation(
            each_page_contents, title=slide_name
        )
        merged_html_filepath = os.path.join(workspace_root, "html_report.html")
        with open(merged_html_filepath, "w", encoding="utf-8") as f:
            f.write(merged_html_content)
        return merged_html_filepath


def agent_run(query: str, report_format: str, output_dir: str, use_feedback_loop: bool = False, max_iterations: int = 3, input_files: list[str] = None):
    start_time = datetime.now()
    request_id = f"request_{now_date}"
    workspace = os.path.abspath(output_dir)
    os.makedirs(workspace, exist_ok=True)
    global_storage = GlobalStorage()
    global_storage.set("request_id", request_id)
    global_storage.set("workspace", workspace)
    global_storage.set("date", now_date)
    
    # Process input files if provided
    if input_files:
        logger.info(f"Processing {len(input_files)} input file(s)...")
        processed_files = process_input_files(input_files, workspace, global_storage)
        global_storage.set("input_files", processed_files)
        logger.info(f"Processed {len(processed_files)} file(s) successfully")
    
    context = {"date": now_date, "request_id": request_id, "workspace": workspace}

    deep_research_trace_history = research_agent_run(query, context, global_storage)
    
    if report_format == "markdown":
        if use_feedback_loop:
            report_path, citation_path, iterations = markdown_report_with_feedback_loop(
                deep_research_trace_history, context, global_storage, max_iterations
            )
            logger.info(f"Feedback loop completed with {iterations} iteration(s)")
        else:
            report_path, citation_path = markdown_report_agent_run(
                deep_research_trace_history, context, global_storage
            )
    elif report_format == "html":
        report_path = html_report_agent_run(
            deep_research_trace_history, context, global_storage
        )
        citation_path = None
    elif report_format == "markdown+html":
        if use_feedback_loop:
            markdown_report_path, citation_path, iterations = markdown_report_with_feedback_loop(
                deep_research_trace_history, context, global_storage, max_iterations
            )
            logger.info(f"Feedback loop completed with {iterations} iteration(s)")
        else:
            markdown_report_path, citation_path = markdown_report_agent_run(
                deep_research_trace_history, context, global_storage
            )
        html_report_path = html_report_agent_run(
            deep_research_trace_history, context, global_storage
        )
        citation_path = None
        report_path = {
            "markdown": markdown_report_path,
            "html": html_report_path,
        }
    else:
        raise ValueError(f"Invalid report format: {report_format}")
    logger.info(f"Report is saved at: {report_path}")
    final_state = {}
    final_state["report_path"] = report_path
    if citation_path:
        final_state["citation_path"] = citation_path
    if use_feedback_loop:
        final_state["iterations_used"] = iterations
    for key, value in global_storage.items():
        try:
            json.dumps(value)  # try to serialize the value
            final_state[key] = value
        except (TypeError, ValueError):
            # If error, skip
            continue
    end_time = datetime.now()
    final_state["start_time"] = start_time.isoformat()
    final_state["end_time"] = end_time.isoformat()
    final_state["used_time"] = (end_time - start_time).total_seconds()
    final_state_path = os.path.join(workspace, "final_state.json")
    with open(final_state_path, "w") as f:
        json.dump(final_state, f, indent=4, ensure_ascii=False)
    logger.info(f"Final state is saved at: {final_state_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Test the quick start example loading agent from YAML configuration.",
    )
    parser.add_argument(
        "--query",
        type=str,
        required=True,
        help="Query to test the agent",
    )
    parser.add_argument(
        "--report_format",
        type=str,
        default="markdown",
        choices=["markdown", "html", "markdown+html"],
        help="Report format: markdown, html, markdown+html",
    )
    parser.add_argument(
        "--output_dir",
        type=str,
        default=f"workspaces/workspace_{now_date}",
        help="Output directory to save the report",
    )
    parser.add_argument(
        "--use_feedback_loop",
        action="store_true",
        help="Enable interactive feedback loop for markdown reports (allows user to modify and get agent to revise)",
    )
    parser.add_argument(
        "--max_iterations",
        type=int,
        default=3,
        help="Maximum number of feedback iterations (default: 3)",
    )
    parser.add_argument(
        "--input_files",
        type=str,
        nargs="+",
        help="Input files to process (PDF, images, text files, etc.)",
    )
    args = parser.parse_args()
    os.makedirs(args.output_dir, exist_ok=True)
    setup_logger(args.output_dir)
    agent_run(
        args.query, 
        args.report_format, 
        args.output_dir,
        use_feedback_loop=args.use_feedback_loop,
        max_iterations=args.max_iterations,
        input_files=args.input_files,
    )


if __name__ == "__main__":
    main()
