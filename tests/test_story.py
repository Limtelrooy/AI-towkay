import json
from pathlib import Path
import tempfile
import unittest

from generate_video import load_story, wrap


class StoryTests(unittest.TestCase):
    def test_example_fits_layout(self):
        story = load_story(Path(__file__).resolve().parents[1] / "examples/restaurant.json")
        for slide in story["slides"]:
            wrap(slide["title"], 19, 4)
            wrap(slide["body"], 32, 6)

    def test_rejects_invalid_colour(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "story.json"
            path.write_text(json.dumps({"restaurant": "Demo", "label": "Demo", "slides": [{"title": "Hi", "body": "Hi", "accent": "red:evil"}]}))
            with self.assertRaisesRegex(ValueError, "accent"):
                load_story(path)

    def test_rejects_text_overflow(self):
        with self.assertRaisesRegex(ValueError, "shorten"):
            wrap("word " * 100, 19, 4)


if __name__ == "__main__":
    unittest.main()
