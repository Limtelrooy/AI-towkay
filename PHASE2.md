# Phase 2: opening-hours workflow mock-up

Phase 1 is preserved: its commands and examples still work. Phase 2 is a separate
local renderer with no network calls, paid services, account creation or publishing.

## Setup and render

From the repository folder, use Python 3.10+ and FFmpeg/ffprobe with libx264.
Install Pillow into a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-phase2.txt
python phase2_video.py --output output/phase2-opening-hours-v1
```

The prepared cloud machine already has Pillow 12.3.0. On Ubuntu/Debian install
`fonts-dejavu-core` if the default font is missing. On other systems pass
`--font /path/to/a/licensed-font.ttf`. Pillow is used to measure exact text
bounding boxes before drawing, so overflowing text fails instead of being cut off.
The default DejaVu font is a system font, not copied into this repository;
its licence is available in the distribution's DejaVu package documentation.

Use a new output directory for every run. Edit a copy of
`examples/opening-hours-phase2.json` to change the scene text, manual narration
or durations. Durations must total 25–35 seconds. The example is 30 seconds.

## Preview and deliverables

Open/download `output/phase2-opening-hours-v1/preview.mp4` and play it in VLC.
It is a silent 1080×1920, 24fps H.264 MP4. `captions.srt` matches the manual
narration text and scene timing; the narration also appears on-screen for the
silent preview. Load the SRT separately if desired; it repeats the on-screen text.
`narration.txt` is the timed read-aloud script. `story.json` preserves input data
and `validation.json` records bounds checks, full decode, duration and rights notes.

Customer messages, replies and handoff cards slide in and fade into place. The
fact-sheet and hook cards fade in. Main phrases are large; all key text stays
left of x=912 and above y=1570, reserving the right and bottom for platform
controls. These are conservative margins, not a guarantee for every platform.

## Import your own voice recording

Record the exact `narration.txt` script in English, following each scene window.
Export one aligned 30-second audio file. Use only your own voice or a voice
recording you have permission to use; do not clone another person's voice.
Keep private recordings outside Git, for example under ignored `output/`.

```bash
python phase2_video.py --output output/phase2-with-my-voice \
  --voice output/my-aligned-voice.wav \
  --voice-rights-note 'My own recording; no third-party music; no attribution needed' \
  --confirm-voice-timing
```

The importer requires an audio stream and a duration matching the scene total
within 0.15 seconds. It never trims, stretches or generates speech. You must listen
and confirm alignment; duration checks do not establish word-level synchronization.
Rights notes are operator declarations, not automatic licence verification. Supplied
audio is encoded as AAC; its SHA-256 and rights note are recorded in validation.json.
There is no audio track in the default preview because no licensed narration was supplied.

## Checks and limitations

```bash
python -m unittest discover -s tests -v
ffmpeg -v error -i output/phase2-opening-hours-v1/preview.mp4 -f null -
```

Every export checks dimensions, pixel format, frame count and total duration,
then decodes the complete video. Text boxes are measured before rendering.
This is an **illustrative workflow mock-up** using a fictional restaurant and
invented opening time. “Approved” describes the fictional fact sheet, not an
external approval or a connected knowledge base. There is no AI integration,
live chat, tool execution or tested business result. The unknown question's human
handoff is drawn on-screen; no message is sent. No mascot, third-party footage,
music or voice is included. Review any applicable AI/affiliate disclosures and
platform overlays before publication. All generated outputs stay outside Git.
