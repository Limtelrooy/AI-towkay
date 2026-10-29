import copy
import json
from pathlib import Path
import tempfile
import unittest
import xml.etree.ElementTree as ET

from chat_episode import frame, render, validate
from mascot import svg

ROOT = Path(__file__).resolve().parents[1]


class CreativeTests(unittest.TestCase):
    def setUp(self):
        self.story=json.loads((ROOT/'examples/chatbot-episode.json').read_text())

    def test_timing_and_required_dialogue(self):
        self.assertEqual(validate(self.story),31)
        words=' '.join(s['narration'] for s in self.story['scenes'])
        self.assertTrue(words.startswith('Your chatbot can answer confidently—and still be wrong.'))
        self.assertTrue(words.endswith('Follow AI Towkay Lab for practical business AI tests.'))
        self.assertIn('Let me check with our team.',words)

    def test_wrong_reply_cannot_lose_its_warning(self):
        bad=copy.deepcopy(self.story)
        bad['scenes'][6]['bubbles'][-1]['who']='DRAFT'
        with self.assertRaisesRegex(ValueError,'WRONG'):
            validate(bad)

    def test_all_scenes_fit_and_caption_words_match(self):
        font=Path('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf')
        if not font.exists():
            self.skipTest('Install DejaVu Sans for layout test')
        for scene in self.story['scenes']:
            _,_,caption,boxes=frame(scene,self.story,font,True)
            self.assertEqual(' '.join(caption.split()),' '.join(scene['narration'].split()))
            for left,top,right,bottom in boxes:
                self.assertGreaterEqual(left,72)
                self.assertLessEqual(right,912)
                self.assertLessEqual(bottom,1625)

    def test_svg_sources_match_shapes(self):
        for expression in ('confident','shocked','thoughtful'):
            content=svg(expression)
            ET.fromstring(content)
            self.assertEqual(content,(ROOT/'assets/mascot'/f'{expression}.svg').read_text())

    def test_voice_rejected_without_rights(self):
        with tempfile.TemporaryDirectory() as directory:
            target=Path(directory)/'output'
            with self.assertRaisesRegex(ValueError,'rights'):
                render(self.story,target,Path('unused.ttf'),Path('voice.wav'))
            self.assertFalse(target.exists())
