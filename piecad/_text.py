import math
from contextlib import ExitStack
from importlib import resources as impresources
from typing import Literal

import manifold3d as _m
from fontTools.pens.basePen import BasePen
from fontTools.ttLib import TTFont

from . import Obj2d, Obj3d, _fonts, union

_font: TTFont | None = None
_glyphs = None
_cmap: dict[int, str] | None = None

# Approximate length of the line segments curves are flattened into (font units).
_SEGMENT_LENGTH: float = 5.0


def _distance(pt1: tuple[float, float], pt2: tuple[float, float]) -> float:
    return math.hypot(pt1[0] - pt2[0], pt1[1] - pt2[1])


def _quadratic_point(
    t: float,
    pt0: tuple[float, float],
    pt1: tuple[float, float],
    pt2: tuple[float, float],
) -> tuple[float, float]:
    a = (1 - t) ** 2
    b = 2 * (1 - t) * t
    c = t**2
    return (
        a * pt0[0] + b * pt1[0] + c * pt2[0],
        a * pt0[1] + b * pt1[1] + c * pt2[1],
    )


def _cubic_point(
    t: float,
    pt0: tuple[float, float],
    pt1: tuple[float, float],
    pt2: tuple[float, float],
    pt3: tuple[float, float],
) -> tuple[float, float]:
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


def _quadratic_length(
    pt0: tuple[float, float],
    pt1: tuple[float, float],
    pt2: tuple[float, float],
    precision: int = 64,
) -> float:
    length = 0.0
    prev = pt0
    for i in range(1, precision + 1):
        pt = _quadratic_point(i / precision, pt0, pt1, pt2)
        length += _distance(prev, pt)
        prev = pt
    return length


def _cubic_length(
    pt0: tuple[float, float],
    pt1: tuple[float, float],
    pt2: tuple[float, float],
    pt3: tuple[float, float],
    precision: int = 10,
) -> float:
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


def _flatten_segments(segments) -> list[list[tuple[float, float]]]:
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
                path.append(_quadratic_point(i / steps, current, control, end))
            current = end
        elif kind == "curveTo":
            control1, control2, end = args
            length = _cubic_length(current, control1, control2, end)
            steps = max(1, int(round(length / _SEGMENT_LENGTH)))
            for i in range(1, steps + 1):
                path.append(_cubic_point(i / steps, current, control1, control2, end))
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


class _OutlinePen(BasePen):
    def __init__(self, glyphs) -> None:
        super().__init__(glyphs)
        self.skipMissingComponents = False
        self.segments: list[
            tuple[Literal["moveTo", "lineTo"], tuple[float, float]]
            | tuple[
                Literal["qCurveTo"], tuple[tuple[float, float], tuple[float, float]]
            ]
            | tuple[
                Literal["curveTo"],
                tuple[tuple[float, float], tuple[float, float], tuple[float, float]],
            ]
            | tuple[Literal["closePath"], tuple[()]]
        ] = []

    def _moveTo(self, point: tuple[float, float]) -> None:
        self.segments.append(("moveTo", point))

    def _lineTo(self, point: tuple[float, float]) -> None:
        self.segments.append(("lineTo", point))

    def _qCurveToOne(
        self, control: tuple[float, float], end: tuple[float, float]
    ) -> None:
        self.segments.append(("qCurveTo", (control, end)))

    def _curveToOne(
        self,
        control1: tuple[float, float],
        control2: tuple[float, float],
        end: tuple[float, float],
    ) -> None:
        self.segments.append(("curveTo", (control1, control2, end)))

    def _closePath(self) -> None:
        self.segments.append(("closePath", ()))

    def _endPath(self) -> None:
        self.segments.append(("closePath", ()))


def set_font(fname: str) -> None:
    global _font, _glyphs, _cmap

    if fname[0] != "/" and fname[0] != "\\" and fname[0] != ".":
        font_file = impresources.files(_fonts) / fname
    else:
        font_file = fname

    with ExitStack() as cleanup:
        font = TTFont(str(font_file))
        cleanup.callback(font.close)
        glyphs = font.getGlyphSet()
        cmap = font.getBestCmap()
        if cmap is None:
            raise ValueError(f"Font has no Unicode character map: {font_file}")
        if _font is not None:
            _font.close()
        _font, _glyphs, _cmap = font, glyphs, cmap
        cleanup.pop_all()


set_font("Roboto-Regular.ttf")


def _get_glyph_polygon(c: str) -> Obj2d:
    glyph = _glyphs[_cmap.get(ord(c), ".notdef")]
    pen = _OutlinePen(_glyphs)
    glyph.draw(pen)
    paths = _flatten_segments(pen.segments)
    ys = [pt[1] for pth in paths for pt in pth]

    obj = Obj2d(_m.CrossSection(paths, _m.FillRule.NonZero))
    obj.width = glyph.width
    obj.max_y = max(ys, default=0)
    obj.min_y = min(ys, default=0)
    return obj


def text_func(
    size: float, text: str, inter_char_space: float | None = None
) -> Obj2d | Obj3d:
    """
    Draw the unicode printable characters in `text` in shapes of size `size`.

    The default font is `Roboto-Regular.ttf`.
    Also available is `Hack-Regular.ttf` (Monospaced).

    The default value for the spacing between characters (`inter_char_space`) is `size/3.0`.
    """
    if inter_char_space is None:
        inter_char_space = size / 3.0
    glyphs = [_get_glyph_polygon(c) for c in text]

    max_y = max((g.max_y for g in glyphs), default=0)
    if max_y <= 0:
        min_y = min((g.min_y for g in glyphs if not g.is_empty()), default=0)
        max_y -= min_y
    if max_y <= 0:
        return Obj2d(_m.CrossSection())
    f = size / max_y

    gap = inter_char_space / f
    line_pos = 0
    objects = []
    for poly in glyphs:
        if line_pos > 0:
            line_pos += gap
        objects.append(poly.translate([line_pos, 0]))
        line_pos += poly.width
    return union(*objects).scale([f, f])
