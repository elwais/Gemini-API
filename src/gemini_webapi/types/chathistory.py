from textwrap import shorten

from pydantic import BaseModel

from .modeloutput import ModelOutput


class ChatTurn(BaseModel):
    """Represents a single turn (message) in a chat conversation.

    Parameters
    ----------
    role: `str`
        The role of the message sender, either "user" or "model".
    text: `str`
        The text content of the message.
    model_output: `ModelOutput`, optional
        The full model output if the role is "model". This contains candidates, images, and metadata.
    rid: `str`, optional
        Id of the conversation turn this message belongs to. A user prompt and the model reply
        to it share one turn and therefore one `rid`.
    parent: `list[str]`, optional
        `[cid, rid, rcid]` of the reply this turn follows, or `None` for the first turn of the
        chat. Gemini stores a chat as a tree of turns; pass the turn to
        `ChatSession.rewind()` to send a replacement for it, as editing a prompt in the web
        app does.

    """

    role: str
    text: str
    model_output: ModelOutput | None = None
    rid: str = ""
    parent: list[str] | None = None

    def __str__(self) -> str:
        return f"{self.role.upper()}: {shorten(self.text, width=100)}"

    def __repr__(self) -> str:
        return f"ChatTurn(role={self.role!r}, text={shorten(self.text, width=100)!r})"


class ChatHistory(BaseModel):
    """Represents the complete history of a chat conversation, ordered from the latest turn to the oldest.

    Parameters
    ----------
    cid: `str`
        Chat ID.
    turns: `list[ChatTurn]`
        The list of messages in the conversation.
    next_cursor: `str`, optional
        Pass to `read_chat(cursor=...)` to read the next, older page. None when this page reaches
        the first turn of the chat.

    """

    cid: str
    turns: list[ChatTurn]
    next_cursor: str | None = None

    def __str__(self) -> str:
        return f"ChatHistory(cid={self.cid!r})"

    def __repr__(self) -> str:
        return f"ChatHistory(cid={self.cid!r}, turns={self.turns!r})"
