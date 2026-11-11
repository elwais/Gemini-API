"""Citation parsing: web sources, attached-file sources, and the shapes in between.

FILE_FIELD is the field 43 value captured from a real reply that cited an attached flake.nix
(`[cite: 1]` on the attachment). It is copied verbatim so the test checks what Gemini sends.
"""

import copy
import unittest

from gemini_webapi.types.citation import Citation
from gemini_webapi.utils.citation import citation_numbers, extract_citations

FILE_FIELD = [[['[cite: 1]', 0],
  [[None,
    [[None,
      0,
      'flake.nix',
      None,
      [3, None, 'File attachment was not previously registered'],
      'blobstore:///contrib_service/ttl_1d/xspwz3f5hmy32ocpbhhpamztkl2srf1794438495',
      None,
      None,
      1,
      None,
      None,
      'application/octet-stream'],
     None,
     None,
     None,
     None,
     None,
     'flake.nix']]],
  ['`github:NixOS/nixpkgs/nixpkgs-unstable`', 0]]]

WEB_GROUP = [
    ["[cite: 2]", 0],
    [
        ["pad", "pad", "pad", [["favicon-url", "https://example.org/page", "Example page"]]],
    ],
]


class CitationFileTests(unittest.TestCase):
    def test_attachment_resolves_to_file_source(self):
        found = extract_citations(FILE_FIELD)
        self.assertEqual(len(found), 1)
        cite = found[0]
        self.assertEqual(cite["id"], 1)
        self.assertEqual(cite["kind"], "file")
        self.assertEqual(cite["title"], "flake.nix")
        self.assertIsNone(cite["url"])
        self.assertTrue(cite["uri"].startswith("blobstore:///contrib_service/ttl_1d/"))

    def test_citation_model_carries_file_fields(self):
        cite = Citation(**extract_citations(FILE_FIELD)[0])
        self.assertEqual(cite.kind, "file")
        self.assertEqual(cite.title, "flake.nix")
        self.assertIsNone(cite.url)
        self.assertIn("flake.nix", str(cite))


class CitationWebTests(unittest.TestCase):
    def test_web_source_unchanged(self):
        found = extract_citations([WEB_GROUP])
        self.assertEqual(found, [{
            "id": 2,
            "kind": "web",
            "title": "Example page",
            "url": "https://example.org/page",
            "favicon": "favicon-url",
            "uri": None,
        }])

    def test_default_kind_is_web(self):
        self.assertEqual(Citation(id=3, url="https://a.example").kind, "web")

    def test_mixed_web_and_file_sort_by_number(self):
        mixed = copy.deepcopy(FILE_FIELD)
        # Second group cites number 2 with a web source; the file keeps number 1.
        mixed.append(copy.deepcopy(WEB_GROUP))
        found = extract_citations(mixed)
        self.assertEqual([c["id"] for c in found], [1, 2])
        self.assertEqual([c["kind"] for c in found], ["file", "web"])


class CitationShapeTests(unittest.TestCase):
    def test_non_list_returns_empty(self):
        self.assertEqual(extract_citations(None), [])
        self.assertEqual(extract_citations("nope"), [])

    def test_entry_without_url_or_blob_is_dropped(self):
        group = [["[cite: 4]", 0], [[None, [[None, 0, "notes.txt", None]]]]]
        self.assertEqual(extract_citations([group]), [])

    def test_blob_without_name_is_dropped(self):
        entry = [None, 0, "", None, None, "blobstore:///x"]
        group = [["[cite: 5]", 0], [[None, [entry]]]]
        self.assertEqual(extract_citations([group]), [])

    def test_first_occurrence_wins(self):
        first = copy.deepcopy(FILE_FIELD)
        second = copy.deepcopy(FILE_FIELD)
        second[0][1][0][1][0][2] = "other.nix"
        found = extract_citations(first + second)
        self.assertEqual(len(found), 1)
        self.assertEqual(found[0]["title"], "flake.nix")

    def test_numbers_from_brackets_only(self):
        self.assertEqual(citation_numbers("[cite: 1, 3]"), ["1", "3"])
        self.assertEqual(citation_numbers(" [cite: 12]"), ["12"])


if __name__ == "__main__":
    unittest.main()
