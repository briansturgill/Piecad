"""
## Create a 2D object from an SVG-like path.
"""

from svgpathtools import svg2paths, parse_path, Line, QuadraticBezier, CubicBezier, Arc
from piecad import _chkGE, _chkV2, Obj2d, config, polygon
import typing


def _cp(pt: tuple[float, float]) -> complex:
    return complex(pt[0], pt[1])


def _xy(cplex):
    return (cplex.real, cplex.imag)


class Path:
    _ll = []
    _list = []
    _cur_pt = (0, 0)
    _beginning_pt = None

    def __init__(self, initial_point: tuple[float, float] = (0,0), segments: int= -1):
        """
        Create an SVG-like path starting at `initial_point`. The path can contain lines, arcs, and
        quadratic and cubic bezier curves.

        The `close` method returns an `Obj2d`

        For `segments` see the documentation of [`set_default_segments`](index.html#piecad.set_default_segments).

        <iframe width="100%" height="400" src="/examples/path.html"></iframe>
        """
        if segments == -1:
            segments = config["DefaultSegments"]
        _chkGE("segments", segments, 3)
        self._inital_pt = initial_point
        self._segments = segments

    def _add(self, o: object):
        if type(o) == Line:
            self._list.append(_xy(o.start))
            self._list.append(_xy(o.end))
        else:
            self._list.append(_xy(o.start))
            for t in range(1, self._segments):
                self._list.append(_xy(o.point(t / (float(self._segments) - 1))))
            self._list.append(_xy(o.end))

    def line_to(self, end: tuple[float, float]) -> typing.Self:
        """
        Add a line from the current point to `end`.
        """
        _chkV2("end", end)
        self._add(Line(_cp(self._cur_pt), _cp(end)))
        self._cur_pt = end
        return self

    def quadratic_bezier_to(
        self, control_point: tuple[float, float], end: tuple[float, float]
    ) -> typing.Self:
        """
        Add a quadratic bezier curve from the current point to `end`, with `control_point`.
        """
        _chkV2("control_panel", control_point)
        _chkV2("end", end)
        self._add(QuadraticBezier(_cp(self._cur_pt), _cp(control_point), _cp(end)))
        self._cur_pt = end
        return self

    def cubic_bezier_to(
        self,
        control_point_1: tuple[float, float],
        control_point_2: tuple[float, float],
        end: tuple[float, float],
    ) -> typing.Self:
        """
        Add a cubic bezier curve from the current point to `end`, with control points
        `control_point_1` and `control_point_2`.
        """
        _chkV2("control_point_1", control_point_1)
        _chkV2("control_point_2", control_point_2)
        _chkV2("end", end)
        self._add(
            CubicBezier(
                _cp(self._cur_pt), _cp(control_point_1), _cp(control_point_2), _cp(end)
            )
        )
        self._cur_pt = end
        return self

    def arc_to(
        self,
        radii: tuple[float, float] | float,
        end: tuple[float, float],
        x_axis_rotation: float = 0,
        large_arc: bool = False,
        ccw: bool = False,
    ) -> typing.Self:
        """
        Add an eliptical arc from the current point to `end`, with `radii` which is the x, y tuple of the
        eliptical radius. If x and y are the same, then a single float can be specified.

        The x_axis_rotation gives degrees) of the ellipse relative to the x-axis

        Four arcs can be made between using the above parameters, to choose the one needed:

        The `ccw` flag choses a counter-clockwise or a clockwise (default) arc.

        The `large_arc` flag chooses the longest arc over the shortest (default) arc.
        """
        if type(radii) == int:
            radii = float(radii)
        if type(radii) == float:
            radii = (radii, radii)
        _chkV2("radii", radii)
        _chkV2("end", end)
        self._add(
            Arc(
                _cp(self._cur_pt),
                _cp(radii),
                x_axis_rotation,
                large_arc,
                ccw,
                _cp(end),
            )
        )
        self._cur_pt = end
        return self

    def close(self) -> Obj2d:
        """
        Returns an `Obj2d` shape of the path.
        """
        if len(self._list) > 1 and self._list[0] == self._list[-1]:
            self._list.pop()
        obj = polygon([self._list], check=False)
        return obj

