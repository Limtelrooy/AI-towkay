# AI Towkay Lab: the made-up answer episode

A 31-second **silent animatic** of a scripted, fictional conversation. It is not
a live AI test. No paid services, API calls, music, external footage or voices are used.
Earlier Phase 1 and Phase 2 commands remain unchanged.

## Render

Use the same Python/Pillow and FFmpeg setup described in `PHASE2.md`:

```bash
python3 -m pip install -r requirements-phase2.txt
python3 chat_episode.py --output output/chatbot-creative-v1
```

Use a new output directory for each run. The default episode is
`examples/chatbot-episode.json`. To change an episode, copy and edit this file,
then pass `--episode path/to/episode.json`. Questions, answers, approved facts,
narration, expression and timing are configured there. Each scene takes 2–5
seconds; the total must be 25–35 seconds. The closing line is split over two
shots for readability. Keep false answers labelled `WRONG`; validation rejects
false/freeze scenes without that warning.

Available scene modes: hook, chat, fact, false, freeze, repair, lesson and close.
Chat bubbles enter with a restrained 0.32-second movement and 0.18-second fade.
The freeze scene stays still with an enlarged shocked host and `MADE UP.` stamp.
New questions reset the conversation and progress label. The host is a **simple
original vector mascot**, not a premium illustrated character. Its three expressions
are confident, shocked and thoughtful. Editable SVGs are in `assets/mascot/`.
`mascot.py` contains the shared vector shape definitions used to draw those SVGs
and the rendered character. Edit that module and regenerate the SVGs when changing
the design; editing only an SVG does not change the video renderer.

```bash
python3 - <<'PY'
from pathlib import Path
from mascot import svg
for expression in ('confident', 'shocked', 'thoughtful'):
    Path(f'assets/mascot/{expression}.svg').write_text(svg(expression))
PY
```

## Outputs and review

- `preview.mp4`: 1080×1920, 24 fps H.264/yuv420p, no audio unless supplied.
- `contact-sheet.jpg`: a frame extracted from every scene in the final MP4.
- `frames/`: those frames individually, for close inspection.
- `captions.srt`: exact narration text, wrapped and timed to scene windows.
- `narration.txt`: complete English script with recording windows.
- `episode.json`, `validation.json`: input snapshot, bounds and timing report.

Open/download the MP4 and play it in VLC or another video player. Captions are
already drawn into the animatic; the SRT is also exported for editing. Loading
the SRT in a player may duplicate on-screen captions. Key text remains within
x=72..912 and above y=1625. These are conservative margins, not universal platform
overlay guarantees. Dark text on cream and cream on charcoal carry key information;
orange is an accent, not the only way an error is communicated.

## Voice recording input

No `espeak`, `espeak-ng`, `piper` or `festival` executable was found in the current
workspace. No local voice model with verified commercial usage rights was supplied.
Accordingly this deliverable is silent; no narration or waveform is fabricated.

Record the complete `narration.txt` script as one **31-second WAV/MP3** (or another
FFmpeg-readable audio file), aligned to the listed scene windows. Use your own
voice or a recording whose licence allows the intended commercial use. Leave
appropriate pauses between lines. Then run:

```bash
python3 chat_episode.py --output output/chatbot-with-voice \
  --voice output/my-aligned-voice.wav \
  --voice-rights-note 'My own original voice recording; no attribution required' \
  --confirm-voice-timing
```

The audio duration must match within 0.15 seconds. This checks the audio stream
and duration, not spoken words. Listen and confirm script/timing manually before
using the confirmation flag. No stretching, speech recognition or synthesis is
performed. The supplied recording is encoded as AAC, with rights notes and its
SHA-256 recorded in validation.json. Private recordings should remain under ignored
`output/` or outside the repository. No face or voice is cloned.

## Checks and limitations

```bash
python3 -m unittest discover -s tests -v
```

The renderer measures all text before rendering, checks exact frame count and
duration, fully decodes the exported MP4, and extracts one frame per scene. The
caption wording is the supplied narration, not evidence that a voice exists.
The restaurant, fact sheet, bad reply and human fallback are all scripted. The
pet-friendly answer is explicitly marked wrong from its first appearance, before
the freeze stamp. No actual chatbot, customer message, team handoff or measured
business result exists. Before publication, review any platform AI disclosure and
affiliate requirements and recheck overlays on the target platform.
