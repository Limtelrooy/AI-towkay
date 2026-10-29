import copy
import json
from pathlib import Path
import unittest

from produce_draft import prepare, timestamp

ROOT = Path(__file__).resolve().parents[1]


class PipelineTests(unittest.TestCase):
    def setUp(self):
        self.brief = json.loads((ROOT / "examples/vietnamese-brief.json").read_text())
        self.script = json.loads((ROOT / "examples/vietnamese-script.json").read_text())

    def test_caption_text_and_timeline_match_manual_script(self):
        story, srt, board, review, seconds = prepare(self.brief, self.script)
        cues = srt.strip().split("\n\n")
        self.assertEqual(len(cues), len(self.script["scenes"]))
        elapsed = 0
        for scene, slide, cue in zip(self.script["scenes"], story["slides"], cues):
            lines = cue.splitlines()
            end = elapsed + scene["seconds"]
            self.assertEqual(lines[1], f"{timestamp(elapsed)} --> {timestamp(end)}")
            self.assertEqual(" ".join(" ".join(lines[2:]).split()), " ".join(scene["narration"].split()))
            self.assertEqual(slide["body"], scene["narration"])
            elapsed = end
        self.assertEqual(seconds, 48)
        self.assertIn("UNVERIFIED", review)
        self.assertIn("save two hours", review)
        self.assertIn("PLACEHOLDER", board)

    def test_rejects_invalid_timing_and_long_script(self):
        for value in (True, 0, 1.5, 16):
            script = copy.deepcopy(self.script)
            script["scenes"][0]["seconds"] = value
            with self.assertRaises(ValueError):
                prepare(self.brief, script)
        script = copy.deepcopy(self.script)
        for scene in script["scenes"]:
            scene["seconds"] = 15
        with self.assertRaisesRegex(ValueError, "45–60"):
            prepare(self.brief, script)

    def test_text_overflow_is_rejected_before_render(self):
        self.script["scenes"][0]["narration"] = "This is too much text. " * 100
        with self.assertRaisesRegex(ValueError, "shorten"):
            prepare(self.brief, self.script)
