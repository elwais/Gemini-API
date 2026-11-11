import asyncio
import json
import unittest
from unittest import mock

from gemini_webapi import GeminiClient
from gemini_webapi.components import chat_mixin


def user_turn(rid: str, text: str) -> list:
    # Shape of one conversation turn as read_chat parses it: [[cid, rid], parent, [[text]]].
    return [["c_1", rid], None, [[text]]]


class FakeResponse:
    def __init__(self, payload):
        self.text = json.dumps(payload)


class TestReadChatPaging(unittest.TestCase):
    def make_client(self, pages):
        """A client whose history RPC answers from `pages`, keyed by the cursor it receives."""
        client = GeminiClient("psid", "psidts")
        client._check_account_status = lambda raise_error=False: None
        sent = []

        async def fake_batch(payloads, **kwargs):
            payload = json.loads(payloads[0].payload)
            sent.append(payload)
            return FakeResponse(pages[payload[2]])

        client._batch_execute = fake_batch
        return client, sent

    def test_cursor_is_sent_and_returned(self):
        pages = {
            None: {"body": [[user_turn("r3", "third"), user_turn("r2", "second")], "T1", [], []]},
            "T1": {"body": [[user_turn("r1", "first")], None, [], []]},
        }
        # Each page's body is a JSON string in slot 2 of a part, as the batchexecute response has it.
        wire = {
            k: [[None, None, json.dumps(v["body"])]] for k, v in pages.items()
        }
        client, sent = self.make_client(wire)
        with mock.patch.object(chat_mixin, "extract_json_from_response", side_effect=lambda text: json.loads(text)):
            first = asyncio.run(client.read_chat("c_1", limit=2))
            second = asyncio.run(client.read_chat("c_1", limit=2, cursor=first.next_cursor))

        self.assertIsNone(sent[0][2])  # first page: no cursor
        self.assertEqual(sent[1][2], "T1")  # next page: the previous next_cursor
        self.assertEqual(sent[0][1], 2)  # limit still in slot 1
        self.assertEqual([t.text for t in first.turns], ["third", "second"])
        self.assertEqual(first.next_cursor, "T1")
        self.assertEqual([t.text for t in second.turns], ["first"])
        self.assertIsNone(second.next_cursor)


if __name__ == "__main__":
    unittest.main()
