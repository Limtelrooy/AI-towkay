"""Original simple vector mascot, rendered from shared editable shape definitions."""
from html import escape
from PIL import Image, ImageDraw


def shapes(expression):
    if expression not in ('confident', 'shocked', 'thoughtful'):
        raise ValueError('Unknown mascot expression')
    orange, dark, cream = '#F45A1C', '#262420', '#FFF4DF'
    result = [
        ('line', (150, 26, 150, 54), dark, 9),
        ('ellipse', (136, 4, 164, 32), orange, 0),
        ('round', (14, 103, 50, 169), orange, 12),
        ('round', (250, 103, 286, 169), orange, 12),
        ('round', (34, 50, 266, 223), orange, 40),
        ('round', (54, 74, 246, 195), dark, 30),
        ('round', (124, 212, 176, 247), dark, 10),
        ('round', (66, 237, 234, 320), orange, 28),
        ('round', (20, 252, 65, 289), dark, 14),
        ('round', (235, 252, 280, 289), dark, 14),
        ('round', (88, 308, 132, 341), dark, 10),
        ('round', (168, 308, 212, 341), dark, 10),
        ('ellipse', (134, 258, 166, 290), cream, 0),
    ]
    if expression == 'shocked':
        result += [('ellipse', (82, 94, 116, 138), cream, 0), ('ellipse', (184, 94, 218, 138), cream, 0),
                   ('ellipse', (134, 151, 166, 183), cream, 0)]
    elif expression == 'thoughtful':
        result += [('round', (82, 113, 118, 129), cream, 7), ('ellipse', (184, 101, 216, 133), cream, 0),
                   ('line', (132, 164, 168, 157), cream, 7), ('line', (81, 91, 117, 99), orange, 7)]
    else:
        result += [('round', (82, 108, 118, 136), cream, 11), ('round', (182, 108, 218, 136), cream, 11),
                   ('line', (126, 158, 145, 172), cream, 7), ('line', (145, 172, 176, 151), cream, 7)]
    return result


def image(expression, scale=1):
    canvas = Image.new('RGBA', (300, 350))
    draw = ImageDraw.Draw(canvas)
    for kind, box, colour, value in shapes(expression):
        if kind == 'round':
            draw.rounded_rectangle(box, radius=value, fill=colour)
        elif kind == 'ellipse':
            draw.ellipse(box, fill=colour)
        else:
            draw.line(box, fill=colour, width=value)
    return canvas.resize((round(300*scale), round(350*scale)), Image.Resampling.LANCZOS)


def svg(expression):
    elements = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 300 350">',
                '<title>AI Towkay Lab original simple vector robot: ' + escape(expression) + '</title>']
    for kind, (x1,y1,x2,y2), colour, value in shapes(expression):
        if kind == 'round':
            elements.append(f'<rect x="{x1}" y="{y1}" width="{x2-x1}" height="{y2-y1}" rx="{value}" fill="{colour}"/>')
        elif kind == 'ellipse':
            elements.append(f'<ellipse cx="{(x1+x2)/2}" cy="{(y1+y2)/2}" rx="{(x2-x1)/2}" ry="{(y2-y1)/2}" fill="{colour}"/>')
        else:
            elements.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{colour}" stroke-width="{value}"/>')
    return '\n'.join(elements + ['</svg>']) + '\n'
