"""
EditorJS content sanitization utilities.

This module provides functions for sanitizing content from EditorJS, a
block-based editor that outputs JSON. The sanitization includes removing unsafe
URLs, cleaning HTML, and extracting plain text content when needed.

EditorJS outputs a JSON structure with various content blocks such as
paragraphs, lists, images, and embeds. This module ensures that the content is
safe for display by:
1. Filtering out malicious URLs (e.g., javascript: scheme)
2. Cleaning HTML content in text blocks
3. Providing options to extract plain text versions of the content

Example:
    >>> from ems.djangoapps.core.utils.editorjs import clean_editor_js
    >>> content = {
    ...     "blocks": [
    ...         {"type": "paragraph", "data": {"text": "<p>Hello World</p>"}}
    ...     ]
    ... }
    >>> cleaned_content = clean_editor_js(content)
    >>> plain_text = clean_editor_js(content, to_string=True)
"""
import re
import warnings
from enum import Enum
from typing import (
    Any,
    Callable,
    Dict,
    List,
    Literal,
    Optional,
    Tuple,
    Union,
    overload,
)

from urllib3.util import parse_url

from django.utils.html import strip_tags


class BlockType(Enum):
    """Block types supported by EditorJS."""
    PARAGRAPH = "paragraph"
    HEADER = "header"
    LIST = "list"
    IMAGE = "image"
    EMBED = "embed"
    DELIMITER = "delimiter"
    CODE = "code"
    RAW = "raw"
    TABLE = "table"
    QUOTE = "quote"


# URL schemes that are considered unsafe and will be replaced
BLACKLISTED_URL_SCHEMES = ("javascript",)

# Regex pattern to find hyperlinks in HTML content
HYPERLINK_TAG_WITH_URL_PATTERN = (
    r"(.*?<a\s+href=\\?\")(\w+://\S+[^\\])(\\?\">)"
)

# Type definitions for EditorJS content
EditorJSContent = Dict[str, Any]
EditorJSBlock = Dict[str, Any]

# Type definition for cleaning functions
CleaningFunction = Callable[
    [List[EditorJSBlock], EditorJSBlock, List[str], bool, int], None
]


@overload
def clean_editor_js(
    content: Union[EditorJSContent, str, None],
    *,
    to_string: Literal[True]
) -> str: ...


@overload
def clean_editor_js(
    content: EditorJSContent
) -> EditorJSContent: ...


@overload
def clean_editor_js(
    content: None
) -> None: ...


def clean_editor_js(
    content: Optional[Union[EditorJSContent, str]],
    *,
    to_string: bool = False
) -> Union[EditorJSContent, str, None]:
    """
    Sanitize EditorJS JSON content by cleaning URLs and extracting text.

    This function processes each block in the EditorJS content to:
    1. Remove potentially malicious URLs
    2. Clean HTML content
    3. Optionally extract plain text versions of all blocks

    Args:
        content: EditorJS JSON content with blocks or None
        to_string: When True, returns plain text extraction instead of JSON

    Returns:
        If to_string is True, returns concatenated string of all text content.
        Otherwise, returns the cleaned JSON content with unsafe content
        removed.
        If input is None, returns None (or empty string if to_string
        is True).

    Example:
        >>> content = {
        ...     "blocks": [
        ...         {"type": "paragraph", "data": {"text": "<p>Hello</p>"}}
        ...     ]
        ... }
        >>> clean_editor_js(content, to_string=True)
        'Hello'
    """
    if content is None:
        return "" if to_string else content

    # Handle string input by returning it directly
    if isinstance(content, str):
        return content if to_string else {"blocks": []}

    # Extract blocks from content
    blocks = content.get("blocks", [])

    if not blocks or not isinstance(blocks, list):
        return "" if to_string else content

    plain_text_list: List[str] = []

    for index, block in enumerate(blocks):
        # Skip invalid blocks
        if not isinstance(block, dict):
            continue

        block_type = block.get("type", "")
        data = block.get("data", {})

        if not data or not isinstance(data, dict):
            continue

        params = [blocks, block, plain_text_list, to_string, index]
        if clean_func := ITEM_TYPE_TO_CLEAN_FUNC_MAP.get(block_type):
            clean_func(*params)
        else:
            clean_other_items(*params)

    return " ".join(plain_text_list) if to_string else content


def clean_list_item(
    blocks: List[EditorJSBlock],
    block: EditorJSBlock,
    plain_text_list: List[str],
    to_string: bool,
    index: int
) -> None:
    """
    Clean list block items by sanitizing URLs and extracting text if needed.

    Args:
        blocks: All blocks from the EditorJS content
        block: The current list block being processed
        plain_text_list: List to collect plain text output
        to_string: Whether to extract plain text
        index: Index of the current block in the blocks list
    """
    # Safely get items with fallback to empty list
    items = block.get("data", {}).get("items", [])

    if not isinstance(items, list):
        return

    for item_index, item in enumerate(items):
        if not item:
            continue

        if to_string:
            plain_text_list.append(strip_tags(item))
        else:
            new_text = clean_text_data_block(item)
            blocks[index]["data"]["items"][item_index] = new_text


def clean_image_item(
    blocks: List[EditorJSBlock],
    block: EditorJSBlock,
    plain_text_list: List[str],
    to_string: bool,
    index: int
) -> None:
    """
    Clean image block by sanitizing URLs and extracting text if needed.

    Args:
        blocks: All blocks from the EditorJS content
        block: The current image block being processed
        plain_text_list: List to collect plain text output
        to_string: Whether to extract plain text
        index: Index of the current block in the blocks list
    """
    data = block.get("data", {})
    file_data = data.get("file", {})

    if not isinstance(file_data, dict):
        file_data = {}

    file_url = file_data.get("url", "")
    caption = data.get("caption", "")

    if file_url:
        if to_string:
            plain_text_list.append(strip_tags(file_url))
        else:
            file_url = clean_text_data_block(file_url)
            # Fix the typo: "ulr" should be "url"
            blocks[index]["data"]["file"]["url"] = file_url

    if caption:
        if to_string:
            plain_text_list.append(strip_tags(caption))
        else:
            caption = clean_text_data_block(caption)
            blocks[index]["data"]["caption"] = caption


def clean_embed_item(
    blocks: List[EditorJSBlock],
    block: EditorJSBlock,
    plain_text_list: List[str],
    to_string: bool,
    index: int
) -> None:
    """
    Clean embed block by sanitizing URLs and extracting text if needed.

    Args:
        blocks: All blocks from the EditorJS content
        block: The current embed block being processed
        plain_text_list: List to collect plain text output
        to_string: Whether to extract plain text
        index: Index of the current block in the blocks list
    """
    block_data = block.get("data", {})

    if not isinstance(block_data, dict):
        return

    for field in ["source", "embed", "caption"]:
        field_data = block_data.get(field)
        if not field_data:
            continue

        if to_string:
            plain_text_list.append(strip_tags(field_data))
        else:
            cleaned_data = clean_text_data_block(field_data)
            blocks[index]["data"][field] = cleaned_data


def clean_other_items(
    blocks: List[EditorJSBlock],
    block: EditorJSBlock,
    plain_text_list: List[str],
    to_string: bool,
    index: int
) -> None:
    """
    Clean text-based blocks (paragraphs, headers, etc.) by sanitizing URLs.

    This function handles all block types not specifically handled by other
    cleaning functions. Most block types (paragraph, header, quote, etc.) have
    a text field.

    Args:
        blocks: All blocks from the EditorJS content
        block: The current block being processed
        plain_text_list: List to collect plain text output
        to_string: Whether to extract plain text
        index: Index of the current block in the blocks list
    """
    block_data = block.get("data", {})

    if not isinstance(block_data, dict):
        return

    text = block_data.get("text", "")
    if not text:
        return

    if to_string:
        plain_text_list.append(strip_tags(text))
    else:
        new_text = clean_text_data_block(text)
        blocks[index]["data"]["text"] = new_text


def clean_text_data_block(text: str) -> str:
    """
    Clean URLs in text by replacing unsafe URLs with "#invalid".

    This function searches for hyperlinks in HTML text and sanitizes any URLs
    that use blacklisted schemes (like javascript:).

    Args:
        text: HTML text that may contain hyperlinks

    Returns:
        Cleaned text with unsafe URLs replaced with "#invalid"

    Note:
        By default, only the "javascript:" protocol is blacklisted.
    """
    if not text:
        return text

    # Track where we are in the original text
    end_of_match = 0
    new_text = ""

    # Find all hyperlinks in the text
    for match in re.finditer(HYPERLINK_TAG_WITH_URL_PATTERN, text):
        # Get the URL part of the match
        original_url = match.group(2).strip()

        try:
            # Parse the URL to extract its components
            url_parts = parse_url(original_url)
            new_url = url_parts.url
            url_scheme = url_parts.scheme

            # Check if the URL uses a blacklisted scheme
            if url_scheme in BLACKLISTED_URL_SCHEMES:
                warnings.warn(
                    f"An invalid url was found: {original_url} "
                    f"-- Scheme: {url_scheme} is blacklisted",
                    warnings.UserWarning,
                    stacklevel=2,
                )
                new_url = "#invalid"

            # Reconstruct the hyperlink with the processed URL
            prefix = match.group(1)  # The part before the URL
            suffix = match.group(3)  # The part after the URL
            new_text += prefix + new_url + suffix

        except Exception as e:
            # Handle any URL parsing errors
            warnings.warn(
                f"Error processing URL {original_url}: {str(e)}",
                warnings.UserWarning,
                stacklevel=2,
            )
            # Keep the original text in case of error
            new_text += match.string[match.start():match.end()]

        # Update the position in the original text
        end_of_match = match.end()

    # Add any remaining text after the last match
    if end_of_match:
        new_text += text[end_of_match:]
        return new_text

    # If no matches were found, return the original text
    return text


def validate_editor_js_content(content: Any) -> Tuple[bool, Optional[str]]:
    """
    Validate EditorJS content structure.

    Args:
        content: Content to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    if content is None:
        return True, None

    if not isinstance(content, dict):
        return False, "Content must be a dictionary"

    blocks = content.get("blocks")
    if blocks is None:
        return False, "Content must have 'blocks' key"

    if not isinstance(blocks, list):
        return False, "'blocks' must be a list"

    for i, block in enumerate(blocks):
        if not isinstance(block, dict):
            return False, f"Block {i} must be a dictionary"

        if "type" not in block:
            return False, f"Block {i} must have a 'type' key"

        if "data" not in block:
            return False, f"Block {i} must have a 'data' key"

        if not isinstance(block.get("data"), dict):
            return False, f"Block {i} 'data' must be a dictionary"

    return True, None


# Mapping of block types to their cleaning functions
# Defined after all functions to avoid circular imports
ITEM_TYPE_TO_CLEAN_FUNC_MAP: Dict[str, CleaningFunction] = {
    BlockType.LIST.value: clean_list_item,
    BlockType.IMAGE.value: clean_image_item,
    BlockType.EMBED.value: clean_embed_item,
}
