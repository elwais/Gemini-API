import asyncio
import unittest

from gemini_webapi import GeminiClient
from gemini_webapi.types import ChatInfo


class TestRefreshChats(unittest.TestCase):
    def test_refetches_and_returns_list(self):
        client = GeminiClient("psid", "psidts")
        client._recent_chats = [ChatInfo(cid="c_1", title="Chat(c_1)", is_pinned=False, timestamp=1.0)]
        calls = []

        async def fake_fetch(recent: int = 13) -> None:
            calls.append(recent)
            client._recent_chats = [ChatInfo(cid="c_1", title="Octopus facts", is_pinned=False, timestamp=2.0)]

        client._fetch_recent_chats = fake_fetch
        chats = asyncio.run(client.refresh_chats(recent=20))
        self.assertEqual(calls, [20])
        self.assertEqual([c.title for c in chats], ["Octopus facts"])
        self.assertIs(chats, client.list_chats())


if __name__ == "__main__":
    unittest.main()
