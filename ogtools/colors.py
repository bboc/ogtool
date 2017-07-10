"""Various helpers to deal with colors and fonts."""

from collections import defaultdict
from string import Template
from textwrap import dedent
import os
import codecs

def hexcolors(color):
    """Convert tuple (red, green, blue) with 16 bit components to hex string."""
    try: 
        return ''.join(['{0:#04x}'.format(c/256)[2:] for c in color]).upper()
    except TypeError:
        return '--unknown--'


def color_components(hexstring):
    """Convert hexadecimal representation of color (e.g. '36FFcd')."""
    def component(c):
        return int(c, 16) * 256
    return (component(hexstring[0:2]), component(hexstring[2:4]), component(hexstring[4:6]))  
 
HTML = Template(dedent("""
    <html>
    <head><title>Color Palette</title></head>
    <body>
    <div style="float: left; width: 48%;">
    <h1>Color Groups</h1>
    $color_groups
    <h1>Fonts by Canvas</h1>
    $fonts_by_canvas
    </div><div style="float: right; width: 48%;">
    <h1>YAML-File</h1>
    <pre>
    <strong>fonts:</strong>
    $yaml_fonts
    <strong>colors:</strong>
    $yaml_colors
    </pre>
    </div>
    </body></html>"""))

YAML = Template(dedent("""
    fonts:
    $yaml_fonts
    colors:
    $yaml_colors
"""))

COLORBOX = """<p><span style="background-color: #%(color)s">&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;</span> #%(color)s </p>\n"""
YAML_COLOR = """    x%(color)s: none"""
YAML_COLOR_HTML = """<span style="background-color: #%(color)s">&nbsp;&nbsp;&nbsp;&nbsp;- </span> c%(color)s: none"""

YAML_FONT = """    %s: none"""
YAML_FONT_HTML = """&nbsp;&nbsp;&nbsp;&nbsp;- %s: none"""
COLOR_HEADER = "<h2>%s</h2>\n"

CANVAS_FONTS_HTML = '<p><strong>%s</strong>: %s</p>'

def dump_colors_and_fonts_to_yaml_and_html(target, colors, fonts):
    """
    colors: set of tuples with RGB components as 16-bit intege
    fonts: dictionary of a set of fonts per canvas
    """
    RED = 0
    GREEN = 1
    BLUE = 2
    GRAY = 3

    color_groups = [(GRAY, 'grays'), (RED, 'reds'), (GREEN, 'greens'), (BLUE, 'blues')]

    grouped_colors = defaultdict(list) # the colors grouped by most prominent component
    
    def primary_color(color):
        """determine whether a color is either a red, a green, a blue or a gray."""
        def check(c, reference, other1, other2):
            if c[reference] > c[other1] and c[reference] >= c[other2]:
                return True
            return False
        if check(c, RED, GREEN, BLUE):
            return RED
        elif check(c, GREEN, RED, BLUE):
            return GREEN
        elif check(c, BLUE, RED, GREEN):
            return BLUE
        else:
            return GRAY

    # sort colors into groups
    for c in colors: 
        if c:
            grouped_colors[primary_color(c)].append(c)
    
    color_groups_html = []
    yaml_colors = []
    yaml_colors_html = []
    for cindex, cname in color_groups:
        color_groups_html.append(COLOR_HEADER % cname)
        for color in sorted(grouped_colors[cindex], key=hexcolors):
            color_groups_html.append(COLORBOX % dict(color=hexcolors(color)))
            yaml_colors.append(YAML_COLOR % dict(color=hexcolors(color)))
            yaml_colors_html.append(YAML_COLOR_HTML % dict(color=hexcolors(color)))

    all_fonts = set()
    fonts_by_canvas_html = []
    for canvas in sorted(fonts.keys()):
        canvas_fonts = []
        for f in sorted(fonts[canvas]):
            all_fonts.add(f)
            canvas_fonts.append(f)
        fonts_by_canvas_html.append(CANVAS_FONTS_HTML % (canvas, ', '.join(canvas_fonts)))

    yaml_fonts = []
    yaml_fonts_html = []
    for f in sorted(all_fonts):
        yaml_fonts.append(YAML_FONT % f)
        yaml_fonts_html.append(YAML_FONT_HTML % f)
    
    target_path = os.path.splitext(os.path.split(target)[1])[0]
    with codecs.open(target_path + ".html", 'w+', 'utf-8') as fp:
        fp.write(HTML.substitute(color_groups='\n'.join(color_groups_html), 
                                fonts_by_canvas='\n'.join(fonts_by_canvas_html),
                                yaml_fonts='\n'.join(yaml_fonts_html),
                                yaml_colors='\n'.join(yaml_colors_html)))
    with codecs.open(target_path + ".yaml", 'w+', 'utf-8') as fp:
        fp.write(YAML.substitute(yaml_fonts='\n'.join(yaml_fonts),
                                 yaml_colors='\n'.join(yaml_colors)))