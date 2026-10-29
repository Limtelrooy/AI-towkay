"""Render a scripted conversation animatic using original vector shapes and local media."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import tempfile

from PIL import Image, ImageDraw, ImageFont
from mascot import image as mascot_image, svg
from phase2_video import probe
from produce_draft import timestamp

CREAM, DARK, ORANGE = '#FFF4DF', '#262420', '#F45A1C'
MODES = {'hook', 'chat', 'fact', 'false', 'freeze', 'repair', 'lesson', 'close'}


def write(draw, value, xy, size, font, width=800, bottom=1640, colour=DARK):
    face = ImageFont.truetype(str(font), size)
    lines = []
    for paragraph in value.split('\n'):
        line = ''
        for word in paragraph.split():
            candidate = (line + ' ' + word).strip()
            if draw.textlength(candidate, font=face) > width and line:
                lines.append(line)
                line = word
            else:
                line = candidate
        lines.append(line)
    wrapped = '\n'.join(lines)
    box = draw.multiline_textbbox(xy, wrapped, font=face, spacing=12)
    if box[0] < 0 or box[2] > xy[0]+width or box[3] > bottom:
        raise ValueError(f'Text clipping: {value!r}')
    draw.multiline_text(xy, wrapped, font=face, fill=colour, spacing=12)
    return wrapped, box


def validate(story):
    if not isinstance(story, dict) or not isinstance(story.get('restaurant'), str):
        raise ValueError('Episode requires a restaurant string')
    scenes = story.get('scenes')
    if not isinstance(scenes, list) or not scenes:
        raise ValueError('Episode requires scenes')
    total = 0
    for scene in scenes:
        if not isinstance(scene, dict) or scene.get('mode') not in MODES:
            raise ValueError('Invalid scene mode')
        if type(scene.get('seconds')) is not int or not 2 <= scene['seconds'] <= 5:
            raise ValueError('Scene duration must be 2–5 seconds')
        for key in ('narration', 'progress', 'expression'):
            if not isinstance(scene.get(key), str) or not scene[key].strip():
                raise ValueError(f'Scene requires {key}')
        mascot_image(scene['expression'])
        bubbles = scene.get('bubbles')
        if not isinstance(bubbles, list) or len(bubbles) > 2:
            raise ValueError('A scene supports up to two chat bubbles')
        for bubble in bubbles:
            if not all(isinstance(bubble.get(k), str) and bubble[k].strip() for k in ('who', 'text')):
                raise ValueError('Bubble needs speaker and text')
        if scene['mode'] in ('false', 'freeze') and (len(bubbles) != 2 or 'WRONG' not in bubbles[-1]['who']):
            raise ValueError('False replies must carry an explicit WRONG label')
        if scene['mode'] == 'fact' and not scene.get('fact'):
            raise ValueError('Fact scene requires fact text')
        if scene['mode'] in ('hook', 'lesson', 'close') and not scene.get('headline'):
            raise ValueError('Host scene requires headline')
        total += scene['seconds']
    if not 25 <= total <= 35:
        raise ValueError('Episode must be 25–35 seconds')
    return total


def frame(scene, story, font, silent):
    base = Image.new('RGB', (1080,1920), CREAM)
    foreground = Image.new('RGBA', (1080,1920))
    draw, fd = ImageDraw.Draw(base), ImageDraw.Draw(foreground)
    bounds = []
    def put(d, value, xy, size, **kwargs):
        wrapped, box = write(d, value, xy, size, font, **kwargs)
        bounds.append(box)
        return wrapped
    put(draw, 'AI TOWKAY LAB', (80,100), 30)
    draw.rounded_rectangle((80,162,417,216), radius=22, fill=DARK)
    put(draw, 'Illustrative demo', (100,169), 30, colour=CREAM, width=300)
    put(draw, 'SILENT ANIMATIC' if silent else 'SUPPLIED VOICE', (500,178), 24, width=400)
    put(draw, story['restaurant'], (80,251), 27)
    put(draw, scene['progress'], (80,310), 36)
    draw.line((80,374,900,374), fill=DARK, width=3)
    host_scene = scene['mode'] in ('hook','lesson','close')
    if host_scene:
        put(fd, scene['headline'], (80,430), 84, bottom=810)
        base.paste(mascot_image(scene['expression'],1.2), (320,830), mascot_image(scene['expression'],1.2))
    else:
        for index, bubble in enumerate(scene['bubbles']):
            active = index == len(scene['bubbles'])-1 and scene['mode'] not in ('fact','freeze')
            target = fd if active else draw
            y = 425+index*270
            left = 80 if index == 0 else 126
            wrong = scene['mode'] in ('false','freeze') and index == 1
            fill = '#FFE0CB' if wrong else ('#FFFFFF' if index == 0 else '#F8C4A3')
            target.rounded_rectangle((left,y,900,y+235), radius=34, fill=fill, outline=ORANGE if wrong else DARK, width=4)
            target.polygon([(left+25,y+220),(left+25,y+258),(left+65,y+232)], fill=fill)
            put(target, bubble['who'], (left+26,y+22), 26, width=720, bottom=y+65)
            put(target, bubble['text'], (left+26,y+78), 56, width=720, bottom=y+218)
        if scene['mode'] == 'fact':
            fd.rounded_rectangle((126,705,900,945), radius=16, fill=DARK)
            put(fd, 'APPROVED FACT SHEET', (158,730), 27, colour=CREAM, width=700)
            put(fd, scene['fact'], (158,795), 54, colour=CREAM, width=700, bottom=930)
        scale = 1.0 if scene['mode']=='freeze' else .78
        robot = mascot_image(scene['expression'],scale)
        base.paste(robot, (80,1000), robot)
        if scene['mode']=='freeze':
            draw.rounded_rectangle((420,1015,900,1130), radius=8, fill=ORANGE)
            put(draw, 'MADE UP.', (445,1034), 72, width=440, bottom=1120)
            put(draw, 'NO FACT. NO ANSWER.', (430,1160), 28, width=470)
        elif scene['mode']=='repair':
            put(draw, 'HUMAN CHECK', (390,1110), 39, width=510)
        elif scene['mode']=='false':
            put(draw, 'UNSUPPORTED = WRONG', (355,1110), 32, width=550)
    # Narration captions remain readable in the silent version; no fake waveform.
    draw.rounded_rectangle((72,1400,912,1625), radius=22, fill=DARK)
    caption = put(draw, scene['narration'], (96,1422), 36, colour=CREAM, width=790, bottom=1604)
    return base, foreground, caption, bounds


def render(story, output, font, voice=None, rights=None, confirm=False):
    total = validate(story)
    if voice:
        if not rights or not rights.strip() or not confirm:
            raise ValueError('Supply --voice-rights-note and --confirm-voice-timing')
        metadata = probe(voice)
        if not any(s['codec_type']=='audio' for s in metadata['streams']):
            raise ValueError('Voice file has no audio stream')
        if abs(float(metadata['format']['duration'])-total) > .15:
            raise ValueError(f'Voice must match the {total}s timeline within 0.15s')
    # Measure every scene before creating any output.
    prepared = [frame(scene,story,font,not voice) for scene in story['scenes']]
    output.mkdir(parents=True,exist_ok=False)
    (output/'frames').mkdir()
    cues, script, timing = [], [], []
    elapsed=0
    with tempfile.TemporaryDirectory(prefix='towkay-chat-') as directory:
        root=Path(directory)
        for index,(scene,(base,fg,caption,boxes)) in enumerate(zip(story['scenes'],prepared)):
            end=elapsed+scene['seconds']
            cues.append(f'{index+1}\n{timestamp(elapsed)} --> {timestamp(end)}\n{caption}\n')
            script.append(f'[{elapsed:02d}–{end:02d}s] {scene["narration"]}')
            timing.append({'scene':index+1,'start':elapsed,'end':end,'mode':scene['mode'],'bounds':boxes})
            base.save(root/'base.png'); fg.save(root/'fg.png')
            composite=base.convert('RGBA'); composite.alpha_composite(fg)
            composite.convert('RGB').save(output/'frames'/f'{index+1:02d}.jpg')
            if scene['mode']=='freeze':
                effect='[0:v][1:v]overlay=shortest=1,format=yuv420p[v]'
            else:
                effect="[1:v]fade=t=in:st=0:d=0.18:alpha=1[f];[0:v][f]overlay=y='28*max(0,1-t/0.32)':shortest=1,format=yuv420p[v]"
            subprocess.run(['ffmpeg','-v','error','-loop','1','-framerate','24','-i','base.png',
                            '-loop','1','-framerate','24','-i','fg.png','-filter_complex',effect,'-map','[v]',
                            '-t',str(scene['seconds']),'-an','-c:v','libx264','-threads','2','-preset','fast','-crf','19',f'{index}.mp4'],cwd=root,check=True)
            elapsed=end
        (root/'clips.txt').write_text(''.join(f"file '{i}.mp4'\n" for i in range(len(prepared))))
        subprocess.run(['ffmpeg','-v','error','-f','concat','-safe','1','-i','clips.txt','-c','copy','silent.mp4'],cwd=root,check=True)
        command=['ffmpeg','-v','error','-i','silent.mp4']
        if voice:
            command+=['-i',str(voice.resolve()),'-map','0:v:0','-map','1:a:0','-c:a','aac','-b:a','160k']
        else:
            command+=['-an']
        command+=['-c:v','copy','-movflags','+faststart','final.mp4']
        subprocess.run(command,cwd=root,check=True)
        info=probe(root/'final.mp4'); stream=next(s for s in info['streams'] if s['codec_type']=='video')
        if (stream['width'],stream['height'],stream['codec_name'],int(stream['nb_frames']))!=(1080,1920,'h264',total*24):
            raise ValueError('Unexpected rendered video format/frame count')
        if abs(float(info['format']['duration'])-total)>.2:
            raise ValueError('Caption/video timeline mismatch')
        subprocess.run(['ffmpeg','-v','error','-i',str(root/'final.mp4'),'-f','null','-'],check=True)
        # Inspect actual exported video frames, not only source artwork.
        for item in timing:
            subprocess.run(['ffmpeg','-v','error','-ss',str(item['start']+1),'-i',str(root/'final.mp4'),'-frames:v','1',
                            str((output/'frames'/f'{item["scene"]:02d}.jpg').resolve()),'-y'],check=True)
        shutil.copyfile(root/'final.mp4',output/'preview.mp4')
    sheet=Image.new('RGB',(270*4,480*3),CREAM)
    for i in range(len(prepared)):
        with Image.open(output/'frames'/f'{i+1:02d}.jpg') as shot:
            sheet.paste(shot.resize((270,480),Image.Resampling.LANCZOS),((i%4)*270,(i//4)*480))
    sheet.save(output/'contact-sheet.jpg',quality=94)
    (output/'captions.srt').write_text('\n'.join(cues),encoding='utf-8')
    (output/'narration.txt').write_text('AI Towkay Lab — '+story['title']+'\n\nScripted illustrative demo. Record in English within these scene windows.\n\n'+'\n\n'.join(script)+'\n',encoding='utf-8')
    (output/'episode.json').write_text(json.dumps(story,indent=2,ensure_ascii=False),encoding='utf-8')
    (output/'validation.json').write_text(json.dumps({'seconds':total,'decoded':True,'frames':total*24,'timeline':timing,
        'audio':'supplied; timing manually confirmed, not speech-recognised' if voice else 'none: silent animatic',
        'voice_rights':rights,'voice_sha256':hashlib.sha256(voice.read_bytes()).hexdigest() if voice else None,
        'rights':'Original script, simple vector mascot and shapes. System DejaVu font. No outside footage or music.',
        'cost':'No API calls or purchases.','safe_area':'Key text inside x=72..912 and y=100..1625; review platform overlays.'},indent=2),encoding='utf-8')
    print(f'Created {output}/preview.mp4: {total}s; all scenes measured, full video decoded.')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--episode',type=Path,default=Path(__file__).parent/'examples/chatbot-episode.json')
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--font',type=Path,default=Path('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'))
    parser.add_argument('--voice',type=Path)
    parser.add_argument('--voice-rights-note')
    parser.add_argument('--confirm-voice-timing',action='store_true')
    args=parser.parse_args()
    try:
        render(json.loads(args.episode.read_text(encoding='utf-8')),args.output,args.font,args.voice,args.voice_rights_note,args.confirm_voice_timing)
    except (ValueError,OSError,subprocess.CalledProcessError) as error:
        parser.exit(1,f'Error: {error}\n')


if __name__=='__main__':
    main()
