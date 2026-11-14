"""Create a 2D object from an SVG-like path.
"""

from __future__ import annotations

import math
from typing import Self

from svgpathtools import Arc, CubicBezier, QuadraticBezier

from . import Config, Obj2d, ValidationError


def _point(value, name="point") -> tuple[float, float]:
    """Validate and normalize a finite 2D point."""
    if not isinstance(value, (tuple, list)) or len(value) != 2:
        raise ValidationError(f"{name} must be a tuple/list of two numbers")
    try:
        p = (float(value[0]), float(value[1]))
    except (TypeError, ValueError, OverflowError) as exc:
        raise ValidationError(f"{name} must contain two numbers") from exc
    if not all(math.isfinite(v) for v in p):
        raise ValidationError(f"{name} coordinates must be finite")
    return p


def _number(value, name) -> float:
    try:
        result = float(value)
    except (TypeError, ValueError, OverflowError) as exc:
        raise ValidationError(f"{name} must be a number") from exc
    if not math.isfinite(result):
        raise ValidationError(f"{name} must be finite")
    return result


def _cp(pt):
    return complex(*pt)


def _xy(value):
    return (float(value.real), float(value.imag))


class Path:
    """An ordered collection of independent, open or closed 2D subpaths.

    Each subpath retains its source curve commands. Curves are sampled only
    when converting to an Obj2d.

    Only Even/Odd fill rule is supported.
    """

    def __init__(self, initial_point: tuple[float, float] = (0, 0),
                 segments: int = -1):
        if segments == -1:
            segments = Config.get_default_segments()
        if not isinstance(segments, int) or isinstance(segments, bool) or segments < 3:
            raise ValidationError("segments must be an integer >= 3")
        self._segments = segments
        start = _point(initial_point, "initial_point")
        self._subpaths = [self._make_subpath(start)]
        self._cur_pt = start

    @staticmethod
    def _make_subpath(start):
        return {"start": start, "commands": [], "closed": False}

    def _current(self):
        item = self._subpaths[-1]
        if item["closed"]:
            raise ValidationError(
                "Current subpath is closed; call sub_path(point) before drawing"
            )
        return item

    def sub_path(self, initial_point: tuple[float, float]) -> Self:
        """Begin another independent, open subpath at initial_point."""
        start = _point(initial_point, "initial_point")
        self._subpaths.append(self._make_subpath(start))
        self._cur_pt = start
        return self

    def line_to(self, end: tuple[float, float]) -> Self:
        part = self._current()
        end = _point(end, "end")
        part["commands"].append(("line", end))
        self._cur_pt = end
        return self

    def quadratic_bezier_to(self, control_point: tuple[float, float],
                            end: tuple[float, float]) -> Self:
        part = self._current()
        control_point = _point(control_point, "control_point")
        end = _point(end, "end")
        part["commands"].append(("quadratic", control_point, end))
        self._cur_pt = end
        return self

    def cubic_bezier_to(self, control_point_1: tuple[float, float],
                        control_point_2: tuple[float, float],
                        end: tuple[float, float]) -> Self:
        part = self._current()
        p1 = _point(control_point_1, "control_point_1")
        p2 = _point(control_point_2, "control_point_2")
        end = _point(end, "end")
        part["commands"].append(("cubic", p1, p2, end))
        self._cur_pt = end
        return self

    def arc_to(self, radii: tuple[float, float] | float,
               end: tuple[float, float], x_axis_rotation: float = 0,
               large_arc: bool = False, ccw: bool = False) -> Self:
        """SVG endpoint arc; ccw is the sweep flag in the current API."""
        part = self._current()
        if isinstance(radii, (int, float)):
            r = abs(_number(radii, "radii"))
            radii = (r, r)
        else:
            radii = _point(radii, "radii")
            radii = (abs(radii[0]), abs(radii[1]))
        end = _point(end, "end")
        rotation = _number(x_axis_rotation, "x_axis_rotation")
        part["commands"].append(
            ("arc", radii, end, rotation, bool(large_arc), bool(ccw))
        )
        self._cur_pt = end
        return self

    def close(self) -> Self:
        """Close *only* the current subpath; return self for chaining.

        The closure edge is implicit, as it is for SVG's Z command.
        Calling close() twice is harmless. Starting another subpath requires
        sub_path(point).
        """
        self._subpaths[-1]["closed"] = True
        self._cur_pt = self._subpaths[-1]["start"]
        return self

    def to_commands(self) -> list[dict]:
        """Return independent copies of all original geometric commands.

        Each entry is {'start': (x,y), 'commands': [(operation, ...), ...],
        'closed': bool}. A terminal ('close',) is provided for exporters.
        """
        result = []
        for part in self._subpaths:
            cmds = list(part["commands"])
            if part["closed"]:
                cmds.append(("close",))
            result.append({
                "start": part["start"],
                "commands": cmds,
                "closed": part["closed"],
            })
        return result

    def to_points(self) -> list[list[tuple[float, float]]]:
        """Return sampled vertices for each subpath, open or closed.

        Closed contours have no repeated final start point. For *open*
        contours, an explicit final line back to start is preserved.
        A subpath with no drawable segments returns its start point.
        """
        result = []
        for part in self._subpaths:
            start = part["start"]
            points = [start]
            here = start
            for cmd in part["commands"]:
                kind = cmd[0]
                if kind == "line":
                    end = cmd[1]
                    if end != points[-1]:
                        points.append(end)
                elif kind == "quadratic":
                    end = cmd[2]
                    curve = QuadraticBezier(_cp(here), _cp(cmd[1]), _cp(end))
                    self._sample(points, curve, end)
                elif kind == "cubic":
                    end = cmd[3]
                    curve = CubicBezier(_cp(here), _cp(cmd[1]), _cp(cmd[2]), _cp(end))
                    self._sample(points, curve, end)
                elif kind == "arc":
                    radii, end, rotation, large, ccw = cmd[1:]
                    if here != end and all(r > 0 for r in radii):
                        curve = Arc(_cp(here), _cp(radii), rotation, large,
                                    ccw, _cp(end))
                        self._sample(points, curve, end)
                    elif here != end and points[-1] != end:
                        # SVG spec: zero-radius arc is a straight line.
                        points.append(end)
                else:
                    raise AssertionError(f"Unknown path command {kind!r}")
                here = end
            if part["closed"] and len(points) > 1 and points[-1] == start:
                points.pop()
            result.append(points)
        return result

    def _sample(self, points, curve, end):
        # Use the exact requested endpoint to avoid a tiny floating-point gap
        # between adjacent SVG curves.
        for i in range(1, self._segments):
            xy = (end if i == self._segments - 1 else
                  _xy(curve.point(i / (self._segments - 1))))
            if xy != points[-1]:
                points.append(xy)

    def to_obj2d(self, include_open: bool = False) -> Obj2d:
        """Convert eligible subpaths to a single filled Piecad Obj2d.

        Only closed subpaths are included by default. Set include_open=True
        to treat open paths as implicitly closed (SVG filling semantics).
        Open geometry remains unchanged in Path for SVG/DXF export.
        """
        contours = []
        for part, points in zip(self._subpaths, self.to_points()):
            if not part["closed"] and not include_open:
                continue
            # Polygon is implicitly closed by Manifold. Eliminate an explicit
            # final start point without changing the stored path commands.
            if len(points) > 1 and points[0] == points[-1]:
                points = points[:-1]
            if len(set(points)) >= 3:
                contours.append(points)
        return polygon(contours)
