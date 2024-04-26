import difflib
import logging
import re
from typing import Optional, List, Union

from pydantic import BaseModel

from moatless.codeblocks import CodeBlock
from moatless.codeblocks.codeblocks import BlockSpan
from moatless.coder.types import CodingTask

logger = logging.getLogger(__name__)


class CodePart(BaseModel):
    file_path: Optional[str] = None
    language: Optional[str] = None
    content: str


def create_instruction_code_block(codeblock: CodeBlock, task: CodingTask) -> str:
    if task.action == "update":
        expected_block = codeblock.find_by_path(task.block_path)
        if task.start_index is not None and task.end_index is not None:
            start_line = expected_block.children[task.start_index].start_line
            end_line = expected_block.children[task.end_index].end_line
            return codeblock.to_prompt(
                start_line=start_line,
                end_line=end_line,
                show_outcommented_code=True,
                outcomment_code_comment="... other code",
            )
        elif task.span_id:
            return codeblock.to_prompt(
                span_ids={task.span_id},
                show_outcommented_code=True,
                outcomment_code_comment="... other code",
            )
        else:
            return codeblock.to_prompt()
    else:
        span = codeblock.find_span_by_id(task.span_id)
        trimmed_block = codeblock.copy_with_trimmed_parents(add_placeholders=False)
        comment = "Write the implementation here..."
        if trimmed_block.children:
            comment_block = trimmed_block.children[0].create_comment_block(comment)
        else:
            comment_block = trimmed_block.create_comment_block(comment)
        comment_block.pre_lines = 1
        trimmed_block.children = [comment_block]
        return trimmed_block.root().to_string()


def extract_response_parts(response: str) -> List[Union[str, CodePart]]:
    """
    This function takes a string containing text and code blocks.
    It returns a list of CodePart and non-code text in the order they appear.

    The function can parse two types of code blocks:

    1) Backtick code blocks with optional file path:
    F/path/to/file
    ```LANGUAGE
    code here
    ```

    2) Square-bracketed code blocks with optional file path:
    /path/to/file
    [LANGUAGE]
    code here
    [/LANGUAGE]


    Parameters:s
    text (str): The input string containing code blocks and text

    Returns:
    list: A list containing instances of CodeBlock, FileBlock, and non-code text strings.
    """

    combined_parts = []

    # Normalize line breaks
    response = response.replace("\r\n", "\n").replace("\r", "\n")

    # Regex pattern to match code blocks
    block_pattern = re.compile(
        r"```(?P<language1>\w*)\n(?P<code1>.*?)\n```|"  # for backtick code blocks
        r"\[(?P<language2>\w+)\]\n(?P<code2>.*?)\n\[/\3\]",  # for square-bracketed code blocks
        re.DOTALL,
    )

    # Define pattern to find files mentioned with backticks
    file_pattern = re.compile(r"`([\w/]+\.\w{1,4})`")

    # Pattern to check if the filename stands alone on the last line
    standalone_file_pattern = re.compile(
        r'^(?:"|`)?(?P<filename>[\w\s\-./\\]+\.\w{1,4})(?:"|`)?$', re.IGNORECASE
    )

    last_end = 0

    for match in block_pattern.finditer(response):
        start, end = match.span()

        preceding_text = response[last_end:start].strip()
        preceding_text_lines = preceding_text.split("\n")

        file_path = None

        non_empty_lines = [line for line in preceding_text_lines if line.strip()]
        if non_empty_lines:
            last_line = non_empty_lines[-1].strip()

            filename_match = standalone_file_pattern.match(last_line)
            if filename_match:
                file_path = filename_match.group("filename")
                # Remove the standalone filename from the preceding text
                idx = preceding_text_lines.index(last_line)
                preceding_text_lines = preceding_text_lines[:idx]
                preceding_text = "\n".join(preceding_text_lines).strip()

            # If not found, then check for filenames in backticks
            if not file_path:
                all_matches = file_pattern.findall(last_line)
                if all_matches:
                    file_path = all_matches[-1]  # Taking the last match from backticks
                    if len(all_matches) > 1:
                        logging.info(
                            f"Found multiple files in preceding text: {all_matches}, will set {file_path}"
                        )

        # If there's any non-code preceding text, append it to the parts
        if preceding_text:
            combined_parts.append(preceding_text)

        if match.group("language1") or match.group("code1"):
            language = match.group("language1") or None
            content = match.group("code1").strip()
        else:
            language = match.group("language2").lower()
            content = match.group("code2").strip()

        code_block = CodePart(file_path=file_path, language=language, content=content)

        combined_parts.append(code_block)

        last_end = end

    remaining_text = response[last_end:].strip()
    if remaining_text:
        combined_parts.append(remaining_text)

    return combined_parts


def do_diff(
    file_path: str, original_content: str, updated_content: str
) -> Optional[str]:
    return "".join(
        difflib.unified_diff(
            original_content.strip().splitlines(True),
            updated_content.strip().splitlines(True),
            fromfile=file_path,
            tofile=file_path,
            lineterm="\n",
        )
    )
