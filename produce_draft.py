"""Local phase-one draft production. No network calls, AI providers or audio."""
import argparse
import json
from pathlib import Path
import subprocess

from generate_video import render, wrap


def timestamp(seconds):
    milliseconds = seconds * 1000
    hours, milliseconds = divmod(milliseconds, 3600000)
    minutes, milliseconds = divmod(milliseconds, 60000)
    seconds, milliseconds = divmod(milliseconds, 1000)
    return f"{hours:02}:{minutes:02}:{seconds:02},{milliseconds:03}"


def prepare(brief, script):
    if not isinstance(brief, dict) or not isinstance(script, dict):
        raise ValueError("Brief and script must be JSON objects")
    for key in ("restaurant", "topic", "audience_problem", "business_data", "experiment_notes", "rights_notes"):
        if not isinstance(brief.get(key), str) or not brief[key].strip():
            raise ValueError(f"Brief needs nonempty {key}")
    scenes = script.get("scenes")
    if not isinstance(scenes, list) or not 1 <= len(scenes) <= 20:
        raise ValueError("Script needs 1–20 scenes")
    slides, cues, rows = [], [], []
    elapsed = 0
    for index, scene in enumerate(scenes, 1):
        if not isinstance(scene, dict):
            raise ValueError("Each scene must be an object")
        for key in ("title", "narration", "visual"):
            if not isinstance(scene.get(key), str) or not scene[key].strip():
                raise ValueError(f"Scene {index} needs {key}")
        seconds = scene.get("seconds")
        if type(seconds) is not int or not 2 <= seconds <= 15:
            raise ValueError(f"Scene {index}: seconds must be an integer from 2–15")
        wrap(scene["title"], 19, 4)
        wrap(scene["narration"], 32, 6)
        end = elapsed + seconds
        cues.append(f"{index}\n{timestamp(elapsed)} --> {timestamp(end)}\n{wrap(scene['narration'], 42, 6)}\n")
        slides.append({"title": scene["title"], "body": scene["narration"], "seconds": seconds})
        rows.append(f"### Scene {index} · {elapsed}–{end}s\n\nTitle: {scene['title']}\n\nManual script: {scene['narration']}\n\nIntended shot: {scene['visual']}\n\nStatus: PLACEHOLDER — no recording or narration supplied.\n")
        elapsed = end
    if not 45 <= elapsed <= 60:
        raise ValueError(f"Script totals {elapsed}s; phase-one drafts must be 45–60 seconds")
    claims = brief.get("claims", [])
    if not isinstance(claims, list) or any(not isinstance(c, dict) or not isinstance(c.get("text"), str) for c in claims):
        raise ValueError("claims must be a list of objects with text")
    review = ["DRAFT ONLY — NOT APPROVED FOR PUBLICATION", "", "Cost: $0 API spend. Local compute only; no paid operations implemented.", "", "Human claim review required: no source fetching or automatic fact verification is implemented."]
    for claim in claims:
        category = claim.get("category", "unclassified")
        status = "FICTIONAL — never present as a real result" if category == "fictional" else "UNVERIFIED — check evidence and exclude unsupported assertions"
        review.append(f"- {status}: {claim['text']} [{category}]. Evidence note: {claim.get('evidence', 'missing')}")
    review.extend(["", "Manual checks remaining:", "- Check every script assertion; the tool does not detect undeclared or paraphrased claims.", "- Record narration and align captions to the actual audio. Current SRT follows manual scene timing only.", "- Supply owned/licensed recordings and an original mascot; record licences and attribution before use.", "- Check platform AI-disclosure and affiliate-disclosure requirements before publishing.", "- No source pages were accessed; URLs and notes below are user-supplied, not verified research.", "", json.dumps(brief, indent=2, ensure_ascii=False)])
    story = {"restaurant": brief["restaurant"], "label": "FICTIONAL / SILENT PLACEHOLDER DRAFT", "slides": slides}
    storyboard = "# Storyboard\n\n" + brief["topic"] + "\n\nProblem: " + brief["audience_problem"] + "\n\n" + "\n".join(rows)
    return story, "\n".join(cues), storyboard, "\n".join(review) + "\n", elapsed


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--brief", type=Path, required=True)
    parser.add_argument("--script", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True, help="New output directory; existing paths are never overwritten")
    parser.add_argument("--dry-run", action="store_true", help="Validate and write text drafts, skipping video rendering")
    args = parser.parse_args()
    try:
        brief = json.loads(args.brief.read_text(encoding="utf-8"))
        script = json.loads(args.script.read_text(encoding="utf-8"))
        story, srt, board, review, seconds = prepare(brief, script)
        args.output.mkdir(parents=True, exist_ok=False)
        for filename, content in (("storyboard.md", board), ("captions.srt", srt), ("review.md", review), ("brief.json", json.dumps(brief, indent=2)), ("script.json", json.dumps(script, indent=2))):
            (args.output / filename).write_text(content, encoding="utf-8")
        print("Estimated and actual paid API cost: $0. No external calls.")
        if not args.dry_run:
            duration = float(render(story, (args.output / "preview.mp4").resolve(), 6, full_hd=True))
            if abs(duration - seconds) > 1 / 24:
                raise ValueError("Video duration differs from caption timeline")
            print(f"Verified {duration:.1f}s 1080×1920 MP4: probed and fully decoded.")
        print(f"Draft files: {args.output}. Read review.md before any publication.")
    except (ValueError, OSError, subprocess.CalledProcessError) as error:
        parser.exit(1, f"Error: {error}\n")


if __name__ == "__main__":
    main()
