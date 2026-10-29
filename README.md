# AI Towkay Lab

A faceless content channel demonstrating practical AI workflows for small businesses.

First milestone: create one vertical sample video using fictional restaurant information, text slides and placeholder visuals.

## Phase 1: turn a brief and manual script into a draft

This is a local command-line tool, not an automated content service. It reads your
brief and script and creates a storyboard, captions and a **silent placeholder
video**. Nothing is researched, narrated, uploaded or published automatically.

### Beginner setup

1. Open a terminal in the `AI-towkay` folder.
2. Check Python and FFmpeg:

   ```bash
   python3 --version
   ffmpeg -version
   ffprobe -version
   ```

   Use Python 3.10 or newer. FFmpeg must include `libx264` and `drawtext`, with
   a sans-serif system font. On macOS, `brew install python ffmpeg` installs the
   tools if Homebrew is already installed. On Ubuntu/Debian use
   `sudo apt-get update` then
   `sudo apt-get install python3 ffmpeg fonts-dejavu-core`.
   On Windows, use WSL Ubuntu and those Ubuntu commands. No Python packages,
   accounts, API keys or `.env` file are required. In this cloud workspace,
   Python and FFmpeg are already available.

3. Run the example from the repository folder:

   ```bash
   python3 produce_draft.py --brief examples/vietnamese-brief.json --script examples/vietnamese-script.json --output output/little-lotus-v1
   ```

   In this cloud workspace, first run `export XDG_CACHE_HOME=/workspace/.cache`
   and `mkdir -p "$XDG_CACHE_HOME"` if font-cache warnings appear.

4. Open `output/little-lotus-v1/preview.mp4` in VLC or your usual video player.
   On a local computer, double-click it in the file explorer. In the cloud,
   download the file from the workspace and play it locally. It should show
   eight slides over 48 seconds, with no sound. The label on each slide says
   **FICTIONAL / SILENT PLACEHOLDER DRAFT**.

5. Read `storyboard.md` and `review.md` alongside the video. In VLC, use
   **Subtitle → Add Subtitle File** to load `captions.srt`. The same manual
   script is already displayed on the video as slide text; enabling the SRT
   may therefore repeat that text. Turn subtitles off for an uncluttered preview.

### Inputs and outputs

`examples/vietnamese-brief.json` contains the fictional restaurant, audience
problem, invented business information, source URL list, experiment notes,
claim categories and rights notes. No real customer data is included.
`examples/vietnamese-script.json` contains the manually supplied scenes:
`title`, `seconds`, `narration` text and intended `visual`.

Copy these two files and edit the copies for your next draft. Keep the total
duration between 45 and 60 seconds, with each scene between 2 and 15 seconds.
Use short titles and short narration paragraphs; text that overflows the layout
is rejected. Aim for roughly 120–150 spoken words per minute, then adjust after
recording your own narration. Timing is an editorial estimate, not speech alignment.

Each run needs a **new output folder** (`little-lotus-v2`, for example). Existing
folders are never overwritten. A failed render may leave text drafts in its folder;
read the error and rerun into a new folder after fixing the problem.

| Output | Purpose |
| --- | --- |
| `preview.mp4` | 1080×1920, 24 fps H.264/yuv420p silent draft with text and geometric placeholder visuals |
| `storyboard.md` | Timed manual script, intended shots and missing recordings |
| `captions.srt` | Exact manual script text, timed to each scene |
| `review.md` | Claim flags, rights notes, missing materials and manual review checklist |
| `brief.json`, `script.json` | Copies of the inputs used for this draft |

Validate inputs and produce text files without rendering:

```bash
python3 produce_draft.py --brief examples/vietnamese-brief.json --script examples/vietnamese-script.json --output output/lotus-text-only --dry-run
```

All modes make **zero API calls**, with estimated and actual paid API spend of
**$0**. There is no paid-provider integration to configure or spending-limit
setting in phase 1. Local computer/cloud compute costs are separate. Secrets
are not needed and must never be placed in briefs or scripts: those inputs are
copied into output files and may be committed if placed under `examples/`.

### Verification and limits

```bash
python3 -m unittest discover -s tests -v
ffmpeg -v error -i output/little-lotus-v1/preview.mp4 -f null -
```

The exporter also probes and fully decodes every rendered video, and checks its
duration against the caption timeline. Tests check caption text and timing against
the supplied script. There is **no recorded narration** yet, so synchronization
with speech has not been tested. All visuals are local generated shapes and text;
no external footage, mascot, voice, music or screen recording is included.

The example deliberately includes an unsupported two-hours-per-day savings claim
in the brief. It is flagged **UNVERIFIED** in `review.md` and is excluded from the
manual script. The tool flags declared non-fictional claims conservatively; it
does not independently verify evidence or find undeclared/paraphrased claims.
Source URLs and experiment notes are copied for review, not fetched or verified.
There are no access dates because no research is performed in this phase.

Before a real video: review every claim, run your own demonstration, record your
English narration and screen footage, supply an original mascot, document licences,
align captions to the recording, and review platform/affiliate disclosures.
Research automation, narration providers, asset assembly, thumbnails, a review
queue, performance reporting, publishing and dashboards are intentionally deferred.
For three videos per week, create three separate brief/script pairs and review
each preview manually before adding more automation.

Generated outputs are ignored by Git. Download/archive them separately; commit
source changes explicitly when ready. Environment publication is not required
to render in this current workspace, but fresh-task restoration remains unverified.

## Earlier slide-only sample

Requires Python 3.10+ and FFmpeg/ffprobe on PATH. FFmpeg needs libx264,
drawtext and an installed sans-serif font. No Python packages or API keys are required.

```bash
python3 generate_video.py
```

The result is `output/restaurant-sample.mp4`: a silent 16-second, 720×1280,
24 fps H.264 video with four text slides and abstract placeholder shapes.
All restaurant information is fictional and labelled as a demo.

Edit a copy of `examples/restaurant.json` to change the restaurant, slide titles,
body text, and accent colours. Titles and body text wrap automatically; overly
long content is rejected to keep it inside the layout.

```bash
python3 generate_video.py --story examples/restaurant.json --output output/my-video.mp4 --seconds-per-slide 5
python3 -m unittest discover -s tests -v
```

Existing videos are preserved unless `--overwrite` is supplied. Each export is
probed and fully decoded before it is copied to the output path. Generated videos
are ignored by Git; download or archive them separately. No narration, music,
stock media, or external AI service is used in this first milestone.

In the prepared cloud environment, optionally activate Python with
`source /workspace/.venvs/ai-towkay/bin/activate` and set
`export XDG_CACHE_HOME=/workspace/.cache` for writable font caches.
