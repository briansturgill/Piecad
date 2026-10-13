import ctypes
import math
from importlib import resources as impresources

import freetype
import manifold3d as _m
from freetype import raw
from freetype.ft_structs import FT_Outline_Funcs, FT_Vector

from piecad import *
from . import Obj2d, _fonts

_font = None

# Approximate length of the line segments curves are flattened into (font units).
_SEGMENT_LENGTH = 5.0


def _close_font():
    global _font
    _font = None


def _distance(pt1, pt2):
    return math.hypot(pt1[0] - pt2[0], pt1[1] - pt2[1])


def _quadratic_point(t, pt0, pt1, pt2):
    a = (1 - t) ** 2
    b = 2 * (1 - t) * t
    c = t**2
    return (
        a * pt0[0] + b * pt1[0] + c * pt2[0],
        a * pt0[1] + b * pt1[1] + c * pt2[1],
    )


def _cubic_point(t, pt0, pt1, pt2, pt3):
    cx = (pt1[0] - pt0[0]) * 3
    cy = (pt1[1] - pt0[1]) * 3
    bx = (pt2[0] - pt1[0]) * 3 - cx
    by = (pt2[1] - pt1[1]) * 3 - cy
    ax = pt3[0] - pt0[0] - cx - bx
    ay = pt3[1] - pt0[1] - cy - by
    t2 = t * t
    t3 = t2 * t
    return (
        ax * t3 + bx * t2 + cx * t + pt0[0],
        ay * t3 + by * t2 + cy * t + pt0[1],
    )


def _quadratic_length(pt0, pt1, pt2, precision=64):
    length = 0.0
    prev = pt0
    for i in range(1, precision + 1):
        pt = _quadratic_point(i / precision, pt0, pt1, pt2)
        length += _distance(prev, pt)
        prev = pt
    return length


def _cubic_length(pt0, pt1, pt2, pt3, precision=10):
    length = 0.0
    step = 1.0 / precision
    points = []
    for i in range(precision + 1):
        t = i * step
        if t == 0:
            points.append(pt0)
        elif t == 1:
            points.append(pt3)
        else:
            points.append(_cubic_point(t, pt0, pt1, pt2, pt3))
    for i in range(len(points) - 1):
        length += _distance(points[i], points[i + 1])
    return length


def _outline_to_segments(outline):
    segments = []
    user = ctypes.py_object(segments)

    def move_to(to, user_obj):
        obj = user_obj.value if hasattr(user_obj, "value") else user_obj
        obj.append(("moveTo", (to.contents.x, to.contents.y)))
        return 0

    def line_to(to, user_obj):
        obj = user_obj.value if hasattr(user_obj, "value") else user_obj
        obj.append(("lineTo", (to.contents.x, to.contents.y)))
        return 0

    def conic_to(control, to, user_obj):
        obj = user_obj.value if hasattr(user_obj, "value") else user_obj
        obj.append(
            (
                "qCurveTo",
                (
                    (control.contents.x, control.contents.y),
                    (to.contents.x, to.contents.y),
                ),
            )
        )
        return 0

    def cubic_to(control1, control2, to, user_obj):
        obj = user_obj.value if hasattr(user_obj, "value") else user_obj
        obj.append(
            (
                "curveTo",
                (
                    (control1.contents.x, control1.contents.y),
                    (control2.contents.x, control2.contents.y),
                    (to.contents.x, to.contents.y),
                ),
            )
        )
        return 0

    funcs = FT_Outline_Funcs(
        move_to=ctypes.CFUNCTYPE(
            ctypes.c_int, ctypes.POINTER(FT_Vector), ctypes.py_object
        )(move_to),
        line_to=ctypes.CFUNCTYPE(
            ctypes.c_int, ctypes.POINTER(FT_Vector), ctypes.py_object
        )(line_to),
        conic_to=ctypes.CFUNCTYPE(
            ctypes.c_int,
            ctypes.POINTER(FT_Vector),
            ctypes.POINTER(FT_Vector),
            ctypes.py_object,
        )(conic_to),
        cubic_to=ctypes.CFUNCTYPE(
            ctypes.c_int,
            ctypes.POINTER(FT_Vector),
            ctypes.POINTER(FT_Vector),
            ctypes.POINTER(FT_Vector),
            ctypes.py_object,
        )(cubic_to),
        shift=0,
        delta=0,
    )
    raw.FT_Outline_Decompose(
        ctypes.byref(outline._FT_Outline), ctypes.byref(funcs), user
    )
    return segments


def _flatten_segments(segments):
    paths = []
    current = None
    first = None
    path = []

    for kind, args in segments:
        if kind == "moveTo":
            if path:
                if path[0] != path[-1]:
                    path.append(path[0])
                paths.append(path)
            current = args
            first = args
            path = [args]
        elif kind == "lineTo":
            if current is not None and args != current:
                path.append(args)
            current = args
        elif kind == "qCurveTo":
            control, end = args
            steps = max(
                1,
                int(round(_quadratic_length(current, control, end) / _SEGMENT_LENGTH)),
            )
            for i in range(1, steps + 1):
                t = i / steps
                path.append(_quadratic_point(t, current, control, end))
            current = end
        elif kind == "curveTo":
            control1, control2, end = args
            length = _cubic_length(current, control1, control2, end)
            steps = max(1, int(round(length / _SEGMENT_LENGTH)))
            for i in range(1, steps + 1):
                t = i / steps
                path.append(_cubic_point(t, current, control1, control2, end))
            current = end
        elif kind == "closePath":
            if path and first is not None and path[0] != path[-1]:
                path.append(path[0])
            if path:
                paths.append(path)
            path = []
            current = None
            first = None

    if path:
        if first is not None and path[0] != path[-1]:
            path.append(path[0])
        paths.append(path)

    return paths


def set_font(fname):
    global _font

    if fname[0] != "/" and fname[0] != "\\" and fname[0] != ".":
        font_file = impresources.files(_fonts) / fname
    else:
        font_file = fname

    _close_font()
    _font = freetype.Face(str(font_file))


set_font("Roboto-Regular.ttf")


def _get_glyph_polygon(c):
    # NO_SCALE keeps coordinates in font units.
    _font.load_char(c, freetype.FT_LOAD_NO_SCALE | freetype.FT_LOAD_NO_HINTING)
    paths = _flatten_segments(_outline_to_segments(_font.glyph.outline))

    ys = [pt[1] for pth in paths for pt in pth]

    # Non-zero fill merges the overlapping contours some fonts contain.
    obj = Obj2d(_m.CrossSection(paths, _m.FillRule.NonZero))
    obj.width = _font.glyph.advance.x
    obj.max_y = max(ys, default=0)
    obj.min_y = min(ys, default=0)
    return obj


def text_func(size: float, text: str, inter_char_space=None):
    """
     Draw the unicode printable characters in `text` in shapes of size `size`.

    The default font is `Roboto-Regular.ttf`.
    Also available is `Hack-Regular.ttf` (Monospaced).

    The default value for the spacing between characters (`inter_char_space`) is `size/3.0`.

    """
    if inter_char_space == None:
        inter_char_space = size / 3.0
    glyphs = [_get_glyph_polygon(c) for c in text]

    # The tallest glyph top sets the scale; if every glyph lies below the
    # baseline (e.g. "_"), fall back to the full vertical extent.
    max_y = max((g.max_y for g in glyphs), default=0)
    if max_y <= 0:
        min_y = min((g.min_y for g in glyphs if not g.is_empty()), default=0)
        max_y -= min_y
    if max_y <= 0:
        return Obj2d(_m.CrossSection())
    f = size / max_y

    # Glyphs are positioned in font units, so convert the spacing to them.
    gap = inter_char_space / f
    line_pos = 0
    l = []
    for poly in glyphs:
        if line_pos > 0:
            line_pos += gap
        l.append(poly.translate([line_pos, 0]))
        line_pos += poly.width
    return union(*l).scale([f, f])
