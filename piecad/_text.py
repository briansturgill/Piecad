from piecad import *
from fontTools.ttLib import TTFont
import fontTools
import fontPens.flattenPen as fp
from importlib import resources as impresources
from . import fonts

_font = None
_glyph_set = None
_cmap = None

def set_font(fname):
    global _font, _cmap, _glyph_set

    if fname[0] != '/' and fname[0] != '\\' and fname[0] != '.':
        font_file = impresources.files(fonts) / fname
    else:
        font_file = fname

    _font = TTFont(font_file)
    _cmap = _font.getBestCmap()
    _glyph_set = _font.getGlyphSet()

set_font("LiberationMono-Regular.ttf")

def get_glyph_polygon(c):
    glyph = _glyph_set[_cmap[ord(c)]]
    recorder = fontTools.pens.recordingPen.DecomposingRecordingPen(_glyph_set)
    pen = fp.FlattenPen(recorder)

    glyph.draw(pen)
    paths = []
    path = []
    for item in recorder.value:
        if item[0] == "moveTo":
            path.append(item[1][0])
        elif item[0] == "lineTo":
            path.append(item[1][0])
        elif item[0] == "closePath":
            if len(path) > 0:
                paths.append(path)
            path = []
        else:
            print("Unhandled item:", item[0])

    max_y = 0
    max_x = 0
    for pth in paths:
        for pt in pth:
            x = pt[0]
            y = pt[1]
            if x > max_x:
                max_x = x
            if y > max_y:
                max_y = y

    obj = polygon(paths)
    obj.max_x = max_x
    obj.max_y = max_y
    return obj

def _text_func(sz: float, tstr: str, inter_char_space=None):
    """
    Draw the ASCII printable characters in `tstr` in shapes in size `sz`.
    """
    line_pos = 0
    if inter_char_space == None:
        inter_char_space = sz/3.0
    l = []
    max_x = 0
    max_y = 0
    for c in tstr:
        poly = get_glyph_polygon(c)
        if poly.max_x > max_x:
            max_x = poly.max_x
        if poly.max_y > max_y:
            max_y = poly.max_y
        if line_pos > 0:
            line_pos += inter_char_space
        poly = poly.translate([line_pos, 0])
        line_pos += max_x
        l.append(poly)
    f = sz/max_y
    obj = union(*l).scale([f,f])
    return obj


if __name__ == "__main__":
    sz = 6
    h = sz * 3
    s = "ASsTtUuVvWwXxYyZzA"
    s = "afiklgmnijmj"
    s = "0123456789"
    s = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    s = "abcdefghijklmnopqrstuvwxyz"
    s = "!\"#$%&'()*+,-./:;<=>?@[\\]|^|_|`|{|}~"
    s = "p0123456789 !\"#$%&'()*+,-./:;<=>?@[\\]|^|_|`|{|}~"
    c = _text_func(sz, s)
    x1, y1, x2, y2 = c.bounding_box()
    w = (x2-x1) + sz*2
    c3d = union(cube([w, h, 2]), c.extrude(2).translate([sz, sz, 2]))
    view(c3d)
    save("/tmp/text.obj", c3d)
