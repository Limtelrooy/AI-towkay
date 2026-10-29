import copy
import json
from pathlib import Path
import tempfile
import unittest

from PIL import Image, ImageDraw
from phase2_video import render, text, validate


class PhaseTwoTests(unittest.TestCase):
    def setUp(self):
        self.story = json.loads((Path(__file__).resolve().parents[1] / 'examples/opening-hours-phase2.json').read_text())

    def test_example_is_thirty_seconds_and_contains_handoff(self):
        self.assertEqual(validate(self.story), 30)
        self.assertIn('Ask a staff member.', self.story['scenes'][4]['text'])
        self.assertEqual(' '.join(self.story['scenes'][0]['text'].split()), 'Still answering the same customer question?')
        self.assertEqual(' '.join(self.story['scenes'][-1]['text'].split()), 'Which customer question do you answer every day?')

    def test_rejects_out_of_range_timeline(self):
        bad = copy.deepcopy(self.story)
        for scene in bad['scenes']:
            scene['seconds'] = 10
        with self.assertRaisesRegex(ValueError, '25–35'):
            validate(bad)

    def test_voice_requires_rights_and_manual_timing(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / 'out'
            with self.assertRaisesRegex(ValueError, 'rights'):
                render(self.story, target, Path('unused.ttf'), Path('voice.wav'))
            self.assertFalse(target.exists())

    def test_clipping_check_rejects_large_text(self):
        font = Path('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf')
        if not font.exists():
            self.skipTest('DejaVu Sans not installed')
        with self.assertRaisesRegex(ValueError, 'safe layout'):
            text(ImageDraw.Draw(Image.new('RGB', (1080, 1920))), (80, 100), 'Overflow '*30, 66, font)
