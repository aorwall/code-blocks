from collections import namedtuple
from enum import Enum
from typing import List, Tuple

from moatless.codeblocks import CodeBlock, CodeBlockType
from moatless.codeblocks.codeblocks import PathTree, NON_CODE_BLOCKS, Span
from moatless.types import BlockPath


class BlockMarker(Enum):
    TAG = 1
    COMMENT = 2


def _create_placeholder(codeblock: CodeBlock) -> str:
    if codeblock.type not in [CodeBlockType.COMMENT, CodeBlockType.COMMENTED_OUT_CODE]:
        return codeblock.create_commented_out_block("... other code").to_string()
    return ""


def _print_content(codeblock: CodeBlock, block_marker: BlockMarker = None) -> str:
    contents = ""

    if codeblock.pre_lines:
        contents += "\n" * (codeblock.pre_lines - 1)

        if codeblock.type in [
            CodeBlockType.FUNCTION,
            CodeBlockType.CLASS,
            CodeBlockType.CONSTRUCTOR,
        ]:
            if block_marker == BlockMarker.COMMENT:
                comment = codeblock.create_comment("block_path")
                contents += (
                    f"\n{codeblock.indentation}{comment}: {codeblock.path_string()}"
                )
            elif block_marker == BlockMarker.TAG:
                contents += f"\n</block>\n{codeblock.indentation}\n<block id='{codeblock.path_string()}'>"

        for i, line in enumerate(codeblock.content_lines):
            if i == 0 and line:
                contents += "\n" + codeblock.indentation + line
            elif line:
                contents += "\n" + line
            else:
                contents += "\n"
    else:
        contents += codeblock.pre_code + codeblock.content

    return contents


def print_block(
    codeblock: CodeBlock,
    path_tree: PathTree = None,
    include_types=None,
    block_marker: BlockMarker = None,
) -> str:
    if not path_tree:
        path_tree = PathTree()
        path_tree.show = True

    content = ""
    if block_marker == BlockMarker.TAG:
        content += f"<block id='start'>\n\n"
    elif block_marker == BlockMarker.COMMENT:
        content += codeblock.create_comment_block("block_id: start").to_string() + "\n"

    content += _print(
        codeblock,
        path_tree=path_tree,
        include_types=include_types,
        block_marker=block_marker,
    )

    if block_marker == BlockMarker.TAG:
        content += "\n</block>"

    return content


def print_by_block_path(codeblock: CodeBlock, block_path: BlockPath) -> str:
    tree = PathTree()
    if block_path:
        tree.add_to_tree(block_path)
    else:
        tree.show = True
    return print_block(codeblock, path_tree=tree)


def print_by_block_paths(
    codeblock: CodeBlock,
    block_paths: List[BlockPath],
    include_references: bool = False,
    block_marker: BlockMarker = None,
) -> str:

    if include_references:
        for block_path in block_paths:
            block = codeblock.find_by_path(block_path)
            if not block:
                continue

            for reference in block.references:
                referenced_block = block.find_by_path(reference.path)

                # TODO: Check tokens max tokens
                if referenced_block and referenced_block.full_path() not in block_paths:
                    block_paths.append(referenced_block.full_path())

    tree = PathTree()
    tree.extend_tree(block_paths)
    return print_block(codeblock, path_tree=tree, block_marker=block_marker)


def _print(
    codeblock: CodeBlock,
    path_tree: PathTree,
    include_types=None,
    block_marker: BlockMarker = None,
) -> str:
    if not path_tree:
        raise ValueError("Path tree is None")

    contents = _print_content(codeblock, block_marker=block_marker)

    has_outcommented_code = False
    for child in codeblock.children:
        if path_tree.show:
            contents += _print(child, block_marker=block_marker, path_tree=path_tree)
            continue

        child_tree = path_tree.child_tree(child.identifier) if path_tree else None
        if (
            child_tree
            and child_tree.show
            and (not include_types or child.type in include_types)
        ):
            if has_outcommented_code and child.type not in [
                CodeBlockType.COMMENT,
                CodeBlockType.COMMENTED_OUT_CODE,
            ]:
                contents += child.create_commented_out_block(
                    "... other code"
                ).to_string()
            contents += _print(
                codeblock=child, path_tree=child_tree, block_marker=block_marker
            )
            has_outcommented_code = False
        elif child_tree and (not include_types or child.type in include_types):
            contents += _print(
                codeblock=child, path_tree=child_tree, block_marker=block_marker
            )
            has_outcommented_code = False
        elif child.type not in NON_CODE_BLOCKS:
            has_outcommented_code = True

    if (
        codeblock.parent
        and has_outcommented_code
        and child.type not in [CodeBlockType.COMMENT, CodeBlockType.COMMENTED_OUT_CODE]
    ):
        contents += child.create_commented_out_block("... other code").to_string()

    return contents


def print_definitions_by_types(
    codeblock: CodeBlock, types: List[CodeBlockType] = None
) -> str:

    if not types:
        types = [
            CodeBlockType.FUNCTION,
            CodeBlockType.CLASS,
            CodeBlockType.CONSTRUCTOR,
            CodeBlockType.MODULE,
        ]

    contents = _print_content(codeblock)

    has_outcommented_code = False
    for child in codeblock.children:
        if child.type in types:
            if has_outcommented_code and child.type not in [
                CodeBlockType.COMMENT,
                CodeBlockType.COMMENTED_OUT_CODE,
            ]:
                contents += child.create_commented_out_block(
                    "... other code"
                ).to_string()
            contents += print_definitions_by_types(codeblock=child, types=types)
            has_outcommented_code = False
        elif child.type not in NON_CODE_BLOCKS:
            has_outcommented_code = True

    if (
        codeblock.parent
        and has_outcommented_code
        and child.type not in [CodeBlockType.COMMENT, CodeBlockType.COMMENTED_OUT_CODE]
    ):
        contents += child.create_commented_out_block("... other code").to_string()

    return contents


def print_by_line_numbers(
    codeblock: CodeBlock,
    spans: List[Span],
    only_show_signatures: bool = False,
    block_marker: BlockMarker = None,
    outcomment_code_comment: str = "...",
) -> str:
    contents = _print_content(codeblock, block_marker=block_marker)

    has_outcommented_code = False
    for child in codeblock.children:
        show_all = (
            not spans
            or _is_block_within_spans(child, spans)
            or (child.is_indexed and _is_span_within_block(child, spans))
        )
        show_child = show_all

        if not show_all:
            show_child = _is_span_within_block(child, spans)
            if show_child:
                show_all = not child.get_indexed_blocks()

        if only_show_signatures:
            show_all = False
            show_child = show_child and child.is_indexed

        if show_all or show_child:
            if has_outcommented_code and child.type not in [
                CodeBlockType.COMMENT,
                CodeBlockType.COMMENTED_OUT_CODE,
            ]:
                contents += child.create_commented_out_block(
                    outcomment_code_comment
                ).to_string()

        if show_all:
            contents += print_block(
                child,
                block_marker=block_marker,
            )
            has_outcommented_code = False
        elif show_child:
            # TODO: Filter out relevant spans to provide as params
            contents += print_by_line_numbers(
                child,
                spans,
                only_show_signatures=only_show_signatures,
                block_marker=block_marker,
            )
            has_outcommented_code = False
        else:
            has_outcommented_code = True

    if has_outcommented_code and child.type not in [
        CodeBlockType.COMMENT,
        CodeBlockType.COMMENTED_OUT_CODE,
    ]:
        contents += child.create_commented_out_block(
            outcomment_code_comment
        ).to_string()

    return contents


def _is_span_within_block(codeblock: CodeBlock, spans: List[Span]) -> bool:
    for span in spans:
        if (
            span.start_line >= codeblock.start_line
            and span.end_line <= codeblock.end_line
        ):
            return True
    return False


def _is_block_within_spans(codeblock: CodeBlock, spans: List[Span]) -> bool:
    for span in spans:
        if (
            span.start_line <= codeblock.start_line
            and span.end_line >= codeblock.end_line
        ):
            return True
    return False


def _contains_block_paths(codeblock: CodeBlock, block_paths: List[List[str]]):
    return [
        block_path
        for block_path in block_paths
        if block_path[: len(codeblock.full_path())] == codeblock.full_path()
    ]


def _is_block_within_line_numbers(
    codeblock: CodeBlock, line_numbers: List[Tuple[int, int]]
) -> bool:
    for start_line, end_line in line_numbers:
        if start_line <= codeblock.start_line and end_line >= codeblock.end_line:
            return True
    return False


def print_with_blockpath_comments(
    codeblock: CodeBlock, field_name: str = "block_path"
) -> str:
    return (
        _print_with_blockpath_comments(codeblock, field_name=field_name) + "\n</block>"
    )


def _print_with_blockpath_comments(
    codeblock: CodeBlock, field_name: str = "block_path"
) -> str:
    contents = ""

    if not codeblock.parent:
        contents += f"<block id='start'>\n\n"

    if codeblock.pre_lines:
        contents += "\n" * (codeblock.pre_lines - 1)

        if codeblock.type in [
            CodeBlockType.FUNCTION,
            CodeBlockType.CLASS,
            CodeBlockType.CONSTRUCTOR,
        ]:
            contents += f"\n</block>\n{codeblock.indentation}\n<block id='{codeblock.path_string()}'>"

        for line in codeblock.content_lines:
            if line:
                contents += "\n" + codeblock.indentation + line
            else:
                contents += "\n"
    else:
        contents += codeblock.pre_code + codeblock.content

    for i, child in enumerate(codeblock.children):
        contents += _print_with_blockpath_comments(child, field_name=field_name)

    return contents
