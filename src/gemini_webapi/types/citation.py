from typing import Literal

from pydantic import BaseModel


class Citation(BaseModel):
    """A web source backing one of the `[cite: N]` markers in a reply.

    Citations are not a deep research feature - an ordinary chat turn can carry them too,
    though only sometimes: most grounded answers cite nothing, so an empty list is the
    common case rather than a sign of a parsing failure. Research reports are where they
    turn up reliably. Whenever markers are present the sources are published separately,
    so without resolving them the markers are dead references - the reply text never names
    what it cites.

    A `[cite: N]` can also point at a file the prompt attached. Those carry `kind="file"`,
    the file name as `title`, and the upload's `blobstore://` reference as `uri`; they have no
    `url`, since the file is not on the web.

    Parameters
    ----------
    id: `int`
        The number used by the `[cite: N]` markers that refer to this source.
    kind: `str`
        `"web"` for a page, `"file"` for an attached file.
    title: `str`, optional
        Title of the page, or the file name for an attachment.
    url: `str`, optional
        Address of the page. None for an attachment.
    favicon: `str`, optional
        Icon for the site, when one is supplied.
    uri: `str`, optional
        Reference to the attached upload (`blobstore://...`). None for a web page.

    """

    id: int
    kind: Literal["web", "file"] = "web"
    title: str | None = None
    url: str | None = None
    favicon: str | None = None
    uri: str | None = None

    def __repr__(self) -> str:
        return f"Citation(id={self.id!r}, kind={self.kind!r}, title={self.title!r}, url={self.url!r})"

    def __str__(self) -> str:
        return f"[{self.id}] {self.title or self.url or ''}".strip()
