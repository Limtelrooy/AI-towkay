"""Render an illustrative workflow mock-up. Local files only; no AI integration."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import textwrap

from PIL import Image, ImageDraw, ImageFont
from produce_draft import timestamp

WIDTH, HEIGHT = 1080, 1920
BG, INK = '#101F30', '#F6F7FA'
COLOURS = {'hook': '#F5B544', 'message': '#8DB5FF', 'fact': '#76C5B1',
           'reply': '#76C5B1', 'handoff': '#F5B544', 'close': '#F5B544'}


def probe(path):
    return json.loads(subprocess.check_output([
        'ffprobe', '-v', 'error', '-show_streams', '-show_format', '-of', 'json', str(path)]))


def text(draw, xy, value, size, font_path, colour=INK, max_width=780, max_bottom=1500):
    font = ImageFont.truetype(str(font_path), size)
    box = draw.multiline_textbbox(xy, value, font=font, spacing=18)
    if box[2] - xy[0] > max_width or box[3] > max_bottom:
        raise ValueError(f'Text does not fit the safe layout: {value!r}')
    draw.multiline_text(xy, value, font=font, fill=colour, spacing=18)
    return box


def validate(story):
    if not isinstance(story, dict) or not isinstance(story.get('restaurant'), str):
        raise ValueError('restaurant must be a string')
    scenes = story.get('scenes')
    if not isinstance(scenes, list) or not scenes:
        raise ValueError('scenes must be a nonempty list')
    total = 0
    for scene in scenes:
        if not isinstance(scene, dict) or scene.get('kind') not in COLOURS:
            raise ValueError('Each scene needs a supported kind')
        if type(scene.get('seconds')) is not int or not 2 <= scene['seconds'] <= 10:
            raise ValueError('Scene seconds must be integers from 2–10')
        for field in ('label', 'text', 'narration'):
            if not isinstance(scene.get(field), str) or not scene[field].strip():
                raise ValueError(f'Scene needs {field}')
        total += scene['seconds']
    if not 25 <= total <= 35:
        raise ValueError('Total duration must be 25–35 seconds')
    return total


def render(story, output, font_path, voice=None, rights_note=None, confirm_timing=False):
    total = validate(story)
    for name in ('ffmpeg', 'ffprobe'):
        if not shutil.which(name):
            raise ValueError(f'{name} is required on PATH')
    if voice:
        if not rights_note or not rights_note.strip() or not confirm_timing:
            raise ValueError('Voice requires --voice-rights-note and --confirm-voice-timing')
        info = probe(voice)
        if not any(s['codec_type'] == 'audio' for s in info['streams']):
            raise ValueError('Supplied voice has no audio stream')
        if abs(float(info['format']['duration']) - total) > 0.15:
            raise ValueError(f'Voice must match the {total}s scene timeline within 0.15s; align it manually first')
    output.mkdir(parents=True, exist_ok=False)
    srt, narration, bounds = [], [], []
    elapsed = 0
    with tempfile.TemporaryDirectory(prefix='towkay-phase2-') as directory:
        root = Path(directory)
        for index, scene in enumerate(story['scenes']):
            end = elapsed + scene['seconds']
            cue = '\n'.join(textwrap.wrap(scene['narration'], 38))
            srt.append(f'{index+1}\n{timestamp(elapsed)} --> {timestamp(end)}\n{cue}\n')
            narration.append(f'[{elapsed:02d}–{end:02d}s]\n{scene["narration"]}\n')
            base = Image.new('RGB', (WIDTH, HEIGHT), BG)
            draw = ImageDraw.Draw(base)
            boxes = []
            boxes.append(text(draw, (80, 120), 'ILLUSTRATIVE WORKFLOW MOCK-UP', 34, font_path))
            boxes.append(text(draw, (80, 182), 'No live AI integration · No tested results', 27, font_path, '#A6B6C8'))
            boxes.append(text(draw, (80, 260), story['restaurant'], 28, font_path))
            boxes.append(text(draw, (80, 1230), cue, 34, font_path, max_bottom=1530))
            boxes.append(text(draw, (80, 1510), f'AI TOWKAY LAB   /   {index+1:02d}', 27, font_path, '#A6B6C8', max_bottom=1570))
            draw.rounded_rectangle((80, 1600, 900, 1608), radius=4, fill='#263C52')
            draw.rounded_rectangle((80, 1600, 80 + round(820*(index+1)/len(story['scenes'])), 1608), radius=4, fill=COLOURS[scene['kind']])
            base.save(root / 'base.png')
            card = Image.new('RGBA', (840, 650), (0, 0, 0, 0))
            cd = ImageDraw.Draw(card)
            cd.rounded_rectangle((0, 0, 839, 649), radius=36, fill='#20364D')
            cd.rounded_rectangle((32, 40, 120, 48), radius=4, fill=COLOURS[scene['kind']])
            boxes.append(text(cd, (32, 85), scene['label'], 26, font_path, COLOURS[scene['kind']], max_width=776, max_bottom=640))
            size = 52 if scene['kind'] == 'handoff' else 66
            card_box = text(cd, (32, 175), scene['text'], size, font_path, max_width=776, max_bottom=625)
            boxes.append(card_box)
            card.save(root / 'card.png')
            # Entering message/reply cards move into place; all cards fade in.
            motion = '440+90*max(0,1-t/0.5)' if scene['kind'] in ('message', 'reply', 'handoff') else '440'
            filters = f"[1:v]format=rgba,fade=t=in:st=0:d=0.4:alpha=1[card];[0:v][card]overlay=x=72:y='{motion}':shortest=1,format=yuv420p[v]"
            subprocess.run(['ffmpeg', '-v', 'error', '-loop', '1', '-framerate', '24', '-i', 'base.png',
                            '-loop', '1', '-framerate', '24', '-i', 'card.png', '-filter_complex', filters,
                            '-map', '[v]', '-t', str(scene['seconds']), '-an', '-c:v', 'libx264', '-threads', '2',
                            '-preset', 'fast', '-crf', '20', f'clip-{index}.mp4'], cwd=root, check=True)
            bounds.append({'scene': index+1, 'text_bounds': boxes, 'card_global_bounds_at_rest': [72,440,912,1090],
                           'max_animated_card_bottom': 1180, 'right_margin_px':168, 'bottom_reserved_px':312})
            elapsed = end
        (root / 'clips.txt').write_text(''.join(f"file 'clip-{i}.mp4'\n" for i in range(len(story['scenes']))))
        subprocess.run(['ffmpeg', '-v', 'error', '-f', 'concat', '-safe', '1', '-i', 'clips.txt',
                        '-c', 'copy', 'silent.mp4'], cwd=root, check=True)
        destination = root / 'preview.mp4'
        command = ['ffmpeg', '-v', 'error', '-i', 'silent.mp4']
        if voice:
            command += ['-i', str(voice.resolve()), '-map', '0:v:0', '-map', '1:a:0', '-c:a', 'aac', '-b:a', '160k']
        else:
            command += ['-an']
        command += ['-c:v', 'copy', '-movflags', '+faststart', str(destination)]
        subprocess.run(command, cwd=root, check=True)
        info = probe(destination)
        video = next(s for s in info['streams'] if s['codec_type'] == 'video')
        if (video['width'], video['height'], video['codec_name'], video['pix_fmt']) != (1080,1920,'h264','yuv420p'):
            raise ValueError('Unexpected video format')
        if abs(float(info['format']['duration']) - total) > 0.2 or int(video['nb_frames']) != total*24:
            raise ValueError('Video timing does not match caption timeline')
        subprocess.run(['ffmpeg', '-v', 'error', '-i', str(destination), '-f', 'null', '-'], check=True)
        shutil.copyfile(destination, output / 'preview.mp4')
    (output / 'captions.srt').write_text('\n'.join(srt), encoding='utf-8')
    (output / 'narration.txt').write_text('AI Towkay Lab — manual narration script\nRead each segment within its time window.\n\n' + '\n'.join(narration), encoding='utf-8')
    (output / 'story.json').write_text(json.dumps(story, indent=2, ensure_ascii=False), encoding='utf-8')
    report = {'duration_seconds': total, 'frames': total*24, 'fully_decoded': True, 'text_bounds_checked': True,
              'bounds': bounds, 'voice_imported': bool(voice), 'voice_rights_note': rights_note,
              'voice_sha256': hashlib.sha256(voice.read_bytes()).hexdigest() if voice else None,
              'audio_alignment': 'Manually confirmed by operator; not automatically verified' if voice else 'Not applicable: silent preview',
              'cost': 'No APIs or paid services called', 'font': str(font_path),
              'limitations': ['Illustrative mock-up only: no chatbot or AI integration.', 'No measured results or time-savings claims.',
                              'Opening time is invented; approved means approved within the fictional scenario.',
                              'Original text and generated shapes; no mascot, third-party footage or music.',
                              'Safe margins are conservative; review each platform overlay before publication.']}
    (output / 'validation.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(f'Created {output}/preview.mp4: {total}s, 1080×1920, {"supplied audio" if voice else "silent"}. Fully decoded.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--story', type=Path, default=Path(__file__).parent / 'examples/opening-hours-phase2.json')
    parser.add_argument('--output', type=Path, required=True, help='New directory; never overwrites existing outputs')
    parser.add_argument('--font', type=Path, help='Licensed TrueType/OpenType font; default: system DejaVu Sans')
    parser.add_argument('--voice', type=Path)
    parser.add_argument('--voice-rights-note', help='Ownership/licence and attribution notes; no secrets')
    parser.add_argument('--confirm-voice-timing', action='store_true', help='Confirm speech matches the supplied scene windows')
    args = parser.parse_args()
    try:
        font = args.font or Path('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf')
        if not font.is_file():
            raise ValueError('Install DejaVu Sans or supply --font /path/to/licensed-font.ttf')
        render(json.loads(args.story.read_text(encoding='utf-8')), args.output, font, args.voice, args.voice_rights_note, args.confirm_voice_timing)
    except (OSError, ValueError, subprocess.CalledProcessError) as error:
        parser.exit(1, f'Error: {error}\n')


if __name__ == '__main__':
    main()
