"""Resolving the `[cite: N]` markers Gemini leaves in grounded replies.

Citations are not a deep research feature - an ordinary chat turn can carry them too, if
irregularly. The layout is the same wherever they appear, so this lives outside
`research.py` and takes the container it is given rather than knowing where to look:
field 43 of a candidate's rich content block for a chat turn, of `[17][1]` or `[5]` for a
research document.
"""

import re
from typing import Any

from .parsing import get_nested_value

_CITE_MARKER_RE = re.compile(r"\[cite:\s*([\d,\s]+)\]")
_CITE_NUMBER_RE = re.compile(r"\d+")


def citation_numbers(marker: str) -> list[str]:
    """The citation numbers a marker declares, in order.

    Markers arrive as `" [cite: 1, 2, 3]"`, and the numbers are positionally zipped with
    the source entries, so any digit picked up from outside the brackets would shift every
    source onto the wrong citation. Reading the bracket contents keeps that impossible;
    a marker without brackets falls back to scanning the whole string.
    """
    if bracket := _CITE_MARKER_RE.search(marker):
        return _CITE_NUMBER_RE.findall(bracket.group(1))
    return _CITE_NUMBER_RE.findall(marker)


def extract_citations(groups: Any) -> list[dict[str, Any]]:
    """Resolve `[cite: N]` markers to the web sources backing them.

    Sources are grouped by the citation marker they belong to, each group pairing a marker
    such as `" [cite: 1, 2, 3]"` with the sources backing it, in the order the numbers
    appear. The same source recurs across groups, so the first occurrence of each number
    wins and the result is returned sorted by citation number.

    Parameters
    ----------
    groups: `Any`
        The citation groups container, read as `constants.Field.CITATIONS` of whichever
        array publishes it.

    Returns
    -------
    `list[dict[str, Any]]`
        One mapping per citation with keys `id`, `kind` (`"web"` or `"file"`), `title`, `url`,
        `favicon` and `uri`. A web source has a `url`; an attached file has its name as `title`
        and its `blobstore://` reference as `uri`, with no `url`.

    """
    if not isinstance(groups, list):
        return []

    resolved: dict[int, dict[str, Any]] = {}
    for group in groups:
        marker = get_nested_value(group, [0, 0])
        entries = _entry_list(get_nested_value(group, [1]))
        if not isinstance(marker, str) or not isinstance(entries, list):
            continue

        for number, entry in zip(citation_numbers(marker), entries, strict=False):
            citation_id = int(number)
            if citation_id in resolved:
                continue

            url = get_nested_value(entry, [3, 0, 1])
            title = get_nested_value(entry, [3, 0, 2])
            if isinstance(url, str):
                resolved[citation_id] = {
                    "id": citation_id,
                    "kind": "web",
                    "title": title if isinstance(title, str) else None,
                    "url": url,
                    "favicon": get_nested_value(entry, [3, 0, 0]),
                    "uri": None,
                }
                continue

            file_source = _file_source(citation_id, entry)
            if file_source is not None:
                resolved[citation_id] = file_source

    return [resolved[key] for key in sorted(resolved)]


def _entry_list(sources: Any) -> Any:
    """The list of sources a group publishes.

    Web sources sit directly under the group. An attachment's sources sit one level down, in a
    `[None, [...]]` pair, so the pair is unwrapped only when it has exactly that shape.
    """
    if (
        isinstance(sources, list)
        and len(sources) == 1
        and isinstance(sources[0], list)
        and len(sources[0]) == 2
        and sources[0][0] is None
        and isinstance(sources[0][1], list)
    ):
        return sources[0][1]
    return sources


_BLOB_PREFIX = "blobstore://"


def _file_source(citation_id: int, entry: Any) -> dict[str, Any] | None:
    """Resolve a `[cite: N]` that points at a file attached to the prompt.

    A web source keeps its URL at `[3][0][1]`. An attachment does not: its entry carries the
    file name at `[2]` and a `blobstore://` reference to the upload somewhere in the entry (`[5]`
    in the layout seen so far). The name is the useful part for a reader, so it becomes the
    title, and the reference is kept as `uri`, since it is not a web address.
    """
    name = get_nested_value(entry, [2])
    uri = get_nested_value(entry, [5])
    if not isinstance(uri, str) or not uri.startswith(_BLOB_PREFIX):
        uri = next(
            (v for v in (entry or []) if isinstance(v, str) and v.startswith(_BLOB_PREFIX)),
            None,
        )
    if uri is None or not isinstance(name, str) or not name:
        return None
    return {
        "id": citation_id,
        "kind": "file",
        "title": name,
        "url": None,
        "favicon": None,
        "uri": uri,
    }
