"""Render configurable text slides into a vertical MP4 using only stdlib + FFmpeg."""
import argparse
import json
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import textwrap


def load_story(path):
    story = json.loads(Path(path).read_text(encoding="utf-8"))
    for key in ("restaurant", "label"):
        if not isinstance(story.get(key), str) or not story[key].strip():
            raise ValueError(f"{key} must be a nonempty string")
    slides = story.get("slides")
    if not isinstance(slides, list) or not 1 <= len(slides) <= 20:
        raise ValueError("slides must contain 1 to 20 slides")
    for slide in slides:
        if not isinstance(slide, dict):
            raise ValueError("each slide must be an object")
        for key in ("title", "body"):
            if not isinstance(slide.get(key), str) or not slide[key].strip():
                raise ValueError(f"slide {key} must be a nonempty string")
        if not re.fullmatch(r"#[0-9A-Fa-f]{6}", slide.get("accent", "#F5B544")):
            raise ValueError("accent must be a #RRGGBB colour")
    return story


def wrap(text, width, max_lines):
    lines = []
    for paragraph in text.splitlines():
        lines.extend(textwrap.wrap(paragraph, width=width) or [""])
    if len(lines) > max_lines:
        raise ValueError(f"Text exceeds {max_lines} lines at {width} characters; shorten it")
    return "\n".join(lines)


def render(story, output, seconds, overwrite=False, full_hd=False):
    for executable in ("ffmpeg", "ffprobe"):
        if not shutil.which(executable):
            raise ValueError(f"{executable} is required on PATH")
    if output.exists() and not overwrite:
        raise ValueError(f"{output} exists; use --overwrite to replace it")
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="towkay-") as directory:
        root = Path(directory)
        for index, slide in enumerate(story["slides"]):
            duration = slide.get("seconds", seconds)
            fields = [
                (story["label"], 22, 88, "0xA6B6C8", 45, 2),
                (story["restaurant"], 30, 155, "white", 32, 2),
                (slide["title"], 54, 340, "white", 19, 4),
                (slide["body"], 30, 670, "0xD1DCE8", 32, 6),
                (f"AI TOWKAY LAB     /     {index + 1:02d}", 22, 1160, "0xA6B6C8", 45, 1),
            ]
            accent = slide.get("accent", "#F5B544").replace("#", "0x")
            filters = [
                f"drawbox=x=48:y=260:w=112:h=8:color={accent}:t=fill",
                f"drawbox=x=560:y=970:w=110:h=110:color={accent}:t=fill",
                "drawbox=x=600:y=1010:w=70:h=70:color=0x101F30:t=fill",
            ]
            for number, (text, size, y, colour, width, limit) in enumerate(fields):
                name = f"text-{index}-{number}.txt"
                (root / name).write_text(wrap(text, width, limit), encoding="utf-8")
                filters.append(f"drawtext=font=Sans:textfile={name}:expansion=none:fontsize={size}:fontcolor={colour}:x=48:y={y}:line_spacing=14")
            if full_hd:
                filters.append("scale=1080:1920")
            subprocess.run([
                "ffmpeg", "-hide_banner", "-loglevel", "error", "-f", "lavfi",
                "-i", f"color=c=0x101F30:s=720x1280:r=24:d={duration}",
                "-vf", ",".join(filters), "-an", "-c:v", "libx264", "-threads", "2",
                "-preset", "fast", "-crf", "20", "-pix_fmt", "yuv420p", f"slide-{index}.mp4"
            ], cwd=root, check=True)
        (root / "clips.txt").write_text("".join(f"file 'slide-{i}.mp4'\n" for i in range(len(story["slides"]))), encoding="utf-8")
        combined = root / "combined.mp4"
        subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-f", "concat", "-safe", "1", "-i", "clips.txt", "-c", "copy", "-movflags", "+faststart", str(combined)], cwd=root, check=True)
        info = json.loads(subprocess.check_output(["ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", str(combined)]))
        stream = info["streams"][0]
        dimensions = (1080, 1920) if full_hd else (720, 1280)
        if (stream["width"], stream["height"], stream["codec_name"]) != (*dimensions, "h264"):
            raise RuntimeError("Unexpected video format")
        subprocess.run(["ffmpeg", "-v", "error", "-i", str(combined), "-f", "null", "-"], check=True)
        shutil.copyfile(combined, output)
        return info["format"]["duration"]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--story", type=Path, default=Path(__file__).parent / "examples/restaurant.json")
    parser.add_argument("--output", type=Path, default=Path("output/restaurant-sample.mp4"))
    parser.add_argument("--seconds-per-slide", type=int, choices=range(1, 31), default=4, metavar="1-30")
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()
    try:
        duration = render(load_story(args.story), args.output.resolve(), args.seconds_per_slide, args.overwrite)
    except (ValueError, OSError, subprocess.CalledProcessError) as error:
        parser.exit(1, f"Error: {error}\n")
    print(f"Created {args.output}: 720x1280 H.264, {float(duration):.1f}s (silent)")


if __name__ == "__main__":
    main()
