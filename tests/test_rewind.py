"""Offline tests for editing a previous prompt (ChatSession.rewind)."""

import pytest

from gemini_webapi import GeminiClient
from gemini_webapi.types import ChatTurn


def _session(**kwargs):
    return GeminiClient("psid").start_chat(**kwargs)


def test_rewind_to_parent_reply():
    chat = _session(cid="c_1", rid="r_3", rcid="rc_3")
    chat.rewind(ChatTurn(role="user", text="second", rid="r_2", parent=["c_1", "r_1", "rc_1"]))
    assert chat.metadata[:3] == ["c_1", "r_1", "rc_1"]
    assert chat.last_output is None


def test_rewind_to_first_turn_starts_root_branch():
    chat = _session(cid="c_1", rid="r_3", rcid="rc_3")
    chat.rewind(ChatTurn(role="model", text="first reply", rid="r_1", parent=None))
    assert chat.metadata[:3] == ["c_1", "", ""]


def test_rewind_without_cid_uses_parent():
    chat = _session()
    chat.rewind(ChatTurn(role="user", text="second", rid="r_2", parent=["c_1", "r_1", "rc_1"]))
    assert chat.cid == "c_1"


def test_rewind_rejects_foreign_or_unknown_turns():
    chat = _session(cid="c_1")
    with pytest.raises(ValueError):
        chat.rewind(ChatTurn(role="user", text="x", rid="r_2", parent=["c_2", "r_1", "rc_1"]))
    with pytest.raises(ValueError):
        chat.rewind(ChatTurn(role="user", text="x"))
    with pytest.raises(ValueError):
        _session().rewind(ChatTurn(role="user", text="x", rid="r_1", parent=None))
