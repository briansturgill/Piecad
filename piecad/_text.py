from piecad import *
from fontTools.ttLib import TTFont
import fontTools.ttLib
from fontTools.ttLib.removeOverlaps import removeOverlaps
import fontTools
import fontPens.flattenPen
from importlib import resources as impresources
from . import fonts

_font = None
_glyph_set = None
_cmap = None


def _close_font():
    global _font
    if _font != None:
        _font.close()
        _font = None


def set_font(fname):
    global _font, _cmap, _glyph_set

    if fname[0] != "/" and fname[0] != "\\" and fname[0] != ".":
        font_file = impresources.files(fonts) / fname
    else:
        font_file = fname

    _close_font()

    _font = TTFont(font_file)
    removeOverlaps(_font)
    _cmap = _font.getBestCmap()
    _glyph_set = _font.getGlyphSet()


set_font("Roboto-Regular.ttf")


def _get_glyph_polygon(c):
    glyph = _glyph_set[_cmap[ord(c)]]
    recorder = fontTools.pens.recordingPen.RecordingPen()
    flattener = fontPens.flattenPen.FlattenPen(recorder)
    decomposer = fontTools.pens.filterPen.DecomposingFilterPen(flattener, _glyph_set)

    glyph.draw(decomposer)
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
    for pth in paths:
        for pt in pth:
            y = pt[1]
            if y > max_y:
                max_y = y

    try:
        a = polygon
    except NameError:
        from . import polygon

    obj = polygon(paths, check=False)
    obj.width = glyph.width
    obj.max_y = max_y
    return obj


def text_func(size: float, text: str, inter_char_space=None):
    """
     Draw the unicode printable characters in `text` in shapes of size `size`.

    The default font is `Roboto-Regular.ttf`.
    Also available is `Hack-Regular.ttf` (Monospaced).

    The default value for the spacing between characters (`inter_char_space`) is `size/3.0`.

    """
    line_pos = 0
    if inter_char_space == None:
        inter_char_space = size / 3.0
    l = []
    max_y = 0
    for c in text:
        poly = _get_glyph_polygon(c)
        width = poly.width
        if poly.max_y > max_y:
            max_y = poly.max_y
        if line_pos > 0:
            line_pos += inter_char_space
        poly = poly.translate([line_pos, 0])
        line_pos += width
        l.append(poly)
    f = size / max_y
    obj = union(*l).scale([f, f])
    return obj


if __name__ == "__main__":
    size = 6
    h = size * 3
    s = "ASsTtUuVvWwXxYyZzA"
    s = "afiklgmnijmj"
    s = "0123456789"
    s = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    s = "abcdefghijklmnopqrstuvwxyz"
    s = "!\"#$%&'()*+,-./:;<=>?@[\\]|^|_|`|{|}~"
    s = "p0123456789 !\"#$%&'()*+,-./:;<=>?@[\\]|^|_|`|{|}~"
    c = text_func(size, s)
    x1, y1, x2, y2 = c.bounding_box()
    w = (x2 - x1) + size * 2
    c3d = union(cube([w, h, 2]), c.extrude(2).translate([size, size, 2]))
    view(c3d)
    save("/tmp/text.obj", c3d)
