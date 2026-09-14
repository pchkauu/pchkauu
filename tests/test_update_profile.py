import copy
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
from urllib.error import HTTPError
import xml.etree.ElementTree as ET

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import update_profile as profile


def repository(name, **changes):
    return {
        "name": name, "owner": {"login": profile.OWNER},
        "private": False, "fork": False, "archived": False, **changes,
    }


def snapshot():
    return {
        "versions": {name: {"tag": "v1.0.0", "kind": "Tag"} for name, _ in profile.PACKAGES},
        "languages": {"Dart": 600, "Go": 200, "Python": 100, "C": 50, "Shell": 30, "HTML": 15, "CSS": 5},
        "repositories": 8,
        "updated": "2026-09-14 04:17 UTC",
    }


class ProfileTests(unittest.TestCase):
    def test_highest_numeric_stable_tag_and_matching_public_release(self):
        tags = [{"name": name} for name in (
            "v2.9.0", "v2.10.0", "v10.0.0-rc.1", "v02.11.0", "main",
        )]
        release = {"tag_name": "v2.10.0", "draft": False, "prerelease": False,
                   "published_at": "2026-09-14T00:00:00Z"}
        self.assertEqual(profile.version_info(tags, [release]), {"tag": "v2.10.0", "kind": "Release"})
        for change in ({"tag_name": "v2.9.0"}, {"draft": True}, {"prerelease": True}, {"published_at": None}):
            with self.subTest(change=change):
                self.assertEqual(profile.version_info(tags, [{**release, **change}])["kind"], "Tag")
        self.assertEqual(profile.version_info([{"name": "3.0.0+build.2"}], [])["tag"], "3.0.0+build.2")

    def test_no_stable_tag_is_not_a_version(self):
        self.assertEqual(profile.version_info([], []), {"tag": None, "kind": None})
        self.assertIsNone(profile.version_info([{"name": "v1.0.0-beta"}], [])["tag"])
        data = snapshot()
        data["versions"][profile.PACKAGES[0][0]] = {"tag": None, "kind": None}
        self.assertIn("No stable tag", profile.version_radar(data, "light"))

    def test_pagination_keeps_every_page_and_existing_query(self):
        first = [{"id": number} for number in range(100)]
        with patch.object(profile, "get_json", side_effect=[first, [{"id": 100}]]) as get:
            self.assertEqual(profile.paginate("users/pchkauu/repos?type=owner"), first + [{"id": 100}])
            self.assertEqual([call.args[0] for call in get.call_args_list], [
                "users/pchkauu/repos?type=owner&per_page=100&page=1",
                "users/pchkauu/repos?type=owner&per_page=100&page=2",
            ])
        with patch.object(profile, "get_json", return_value={"message": "unavailable"}):
            with self.assertRaises(RuntimeError):
                profile.paginate("repos/pchkauu/observatory/tags")

    def test_filters_non_public_non_original_archived_and_profile_repositories(self):
        repos = [repository("visible"), repository("fork", fork=True),
                 repository("private", private=True), repository("archive", archived=True),
                 repository(profile.OWNER), repository("foreign", owner={"login": "someone-else"})]
        missing_visibility = repository("unknown")
        del missing_visibility["private"]
        self.assertEqual(profile.eligible_repositories(repos + [missing_visibility]), [repository("visible")])

    def test_collection_adds_byte_counts_and_only_reads_eligible_repositories(self):
        repos = [repository(name) for name, _ in profile.PACKAGES]
        repos += [repository("private", private=True), repository("fork", fork=True)]

        def pages(path):
            if path.startswith("users/"):
                return repos
            if path.endswith("/tags"):
                return [{"name": "v1.0.0"}]
            return []

        with patch.object(profile, "paginate", side_effect=pages), \
                patch.object(profile, "get_json", return_value={"Dart": 100, "Go": 20}) as get:
            data = profile.collect_profile()
        self.assertEqual(data["languages"], {"Dart": 500, "Go": 100})
        self.assertEqual(data["repositories"], 5)
        self.assertEqual(get.call_count, 5)
        self.assertFalse(any("/private/" in call.args[0] or "/fork/" in call.args[0] for call in get.call_args_list))

    def test_language_breakdown_empty_data_and_valid_svg(self):
        data = snapshot()
        self.assertEqual(profile.language_breakdown(data["languages"]), [
            ("Dart", 600), ("Go", 200), ("Python", 100), ("C", 50), ("Shell", 30), ("Other", 20),
        ])
        widgets = profile.render_widgets(data)
        self.assertEqual(len(widgets), 6)
        for svg in widgets.values():
            self.assertEqual(ET.fromstring(svg).attrib["viewBox"], "0 0 640 520")
        data["languages"] = {}
        for theme in profile.THEMES:
            svg = profile.code_footprint(data, theme)
            self.assertIn("No public language data available.", svg)
            self.assertNotIn("nan", svg.lower())
            ET.fromstring(svg)

    def test_external_text_is_escaped_and_rendering_is_repeatable(self):
        data = snapshot()
        data["languages"] = {"C<&\"'><script>": 100}
        widgets = profile.render_widgets(data)
        self.assertEqual(widgets, profile.render_widgets(copy.deepcopy(data)))
        for svg in widgets.values():
            root = ET.fromstring(svg)
            self.assertEqual(root.findall(".//{http://www.w3.org/2000/svg}script"), [])
        self.assertIn("&lt;script&gt;", widgets["code-footprint-dark.svg"])

    def test_http_failure_does_not_change_existing_widgets(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            existing = output / "package-map-dark.svg"
            existing.write_text("existing snapshot", encoding="utf-8")
            with patch.object(profile, "get_json", side_effect=RuntimeError("GitHub HTTP 403")):
                with self.assertRaises(RuntimeError):
                    profile.update(output)
            repositories = [repository(name) for name, _ in profile.PACKAGES]
            with patch.object(profile, "paginate", side_effect=lambda path: repositories if path.startswith("users/") else []), \
                    patch.object(profile, "get_json", side_effect=[{"Dart": 100}, RuntimeError("GitHub HTTP 403")]):
                with self.assertRaises(RuntimeError):
                    profile.update(output)
            self.assertEqual(existing.read_text(encoding="utf-8"), "existing snapshot")
            self.assertEqual(list(output.iterdir()), [existing])
        with patch.object(profile, "urlopen", side_effect=HTTPError("https://api.github.com/", 403, "rate limit", {}, None)):
            with self.assertRaisesRegex(RuntimeError, "GitHub HTTP 403"):
                profile.get_json("users/pchkauu/repos")


if __name__ == "__main__":
    unittest.main()
