"""Create a 2D object from an SVG-like path.
"""

from __future__ import annotations

import math
import re
import xml.etree.ElementTree as ET
from os import PathLike
from typing import Self

import ezdxf
from svgpathtools import Arc, CubicBezier, Line, QuadraticBezier, parse_path

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

    def to_svg(self, filename: str | PathLike) -> None:
        """Write SVG path geometry with even-odd fill, in SVG coordinates."""
        commands = []
        bounds = []
        for part in self._subpaths:
            here = part["start"]
            bounds.append((here[0], here[0], here[1], here[1]))
            commands.append(f"M {here[0]} {here[1]}")
            for cmd in part["commands"]:
                kind = cmd[0]
                if kind == "line":
                    end = cmd[1]
                    curve = Line(_cp(here), _cp(end))
                    commands.append(f"L {end[0]} {end[1]}")
                elif kind == "quadratic":
                    control, end = cmd[1:]
                    curve = QuadraticBezier(_cp(here), _cp(control), _cp(end))
                    commands.append(f"Q {control[0]} {control[1]} {end[0]} {end[1]}")
                elif kind == "cubic":
                    p1, p2, end = cmd[1:]
                    curve = CubicBezier(_cp(here), _cp(p1), _cp(p2), _cp(end))
                    commands.append(
                        f"C {p1[0]} {p1[1]} {p2[0]} {p2[1]} {end[0]} {end[1]}"
                    )
                else:
                    radii, end, rotation, large, ccw = cmd[1:]
                    if here != end and all(r > 0 for r in radii):
                        commands.append(
                            f"A {radii[0]} {radii[1]} {rotation} "
                            f"{int(large)} {int(ccw)} {end[0]} {end[1]}"
                        )
                        curve = Arc(_cp(here), _cp(radii), rotation, large, ccw, _cp(end))
                    else:
                        commands.append(f"L {end[0]} {end[1]}")
                        curve = Line(_cp(here), _cp(end))
                bounds.append(curve.bbox())
                here = end
            if part["closed"]:
                commands.append("Z")
        xmin = min(b[0] for b in bounds)
        xmax = max(b[1] for b in bounds)
        ymin = min(b[2] for b in bounds)
        ymax = max(b[3] for b in bounds)
        width, height = xmax - xmin, ymax - ymin
        # A zero-sized viewBox is invalid, even for an open or empty subpath.
        viewbox = f"{xmin} {ymin} {width or 1} {height or 1}"
        root = ET.Element("svg", {
            "xmlns": "http://www.w3.org/2000/svg",
            "viewBox": viewbox,
        })
        ET.SubElement(root, "path", {"fill-rule": "evenodd", "d": " ".join(commands)})
        ET.ElementTree(root).write(filename, encoding="utf-8", xml_declaration=True)

    @classmethod
    def from_svg(cls, filename: str | PathLike, segments: int = -1) -> Self:
        """Read SVG path elements; all contours use even-odd fill.

        SVG coordinates are used as-is. Transforms, CSS, non-path shapes and
        explicit nonzero fill rules are not supported. Coincident-endpoint
        SVG arcs are not supported by the path parser.
        """
        root = ET.parse(filename).getroot()
        if root.tag.split("}")[-1] != "svg":
            raise ValidationError("Expected an SVG document")
        result = cls(segments=segments)
        result._subpaths.clear()
        number = r"[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?"
        token = re.compile(rf"[MmLlHhVvCcSsQqTtAaZz]|{number}")
        move = re.compile(rf"^[Mm]\s*({number})[\s,]*({number})")
        for element in root.iter():
            tag = element.tag.split("}")[-1]
            if tag not in ("svg", "g", "path", "title", "desc", "metadata"):
                raise ValidationError(f"Unsupported SVG element: {tag}")
            unsupported = {"transform", "style", "clip-path", "mask", "display",
                           "visibility", "filter"}
            if unsupported.intersection(element.attrib):
                raise ValidationError("SVG transforms, CSS and visual effects are not supported")
            if element.get("fill-rule", "evenodd") != "evenodd":
                raise ValidationError("Only the evenodd SVG fill rule is supported")
            if tag != "path":
                continue
            data = element.get("d", "").strip()
            if not data:
                continue
            previous = 0
            for match in token.finditer(data):
                if data[previous:match.start()].strip(" \t\r\n,"):
                    raise ValidationError("Invalid SVG path data")
                previous = match.end()
            if data[previous:].strip(" \t\r\n,"):
                raise ValidationError("Invalid SVG path data")
            here = 0j
            # Each moveto starts a new independent subpath. Split off close
            # commands so the parser does not turn the implicit edge into a line.
            for chunk in re.split(r"(?=[MmZz])", data):
                chunk = chunk.strip()
                if not chunk:
                    continue
                if chunk[0] in "Zz":
                    if not result._subpaths or result._subpaths[-1]["closed"]:
                        raise ValidationError("SVG close command has no open subpath")
                    result.close()
                    here = _cp(result._cur_pt)
                    chunk = chunk[1:].strip()
                    if not chunk:
                        continue
                    if chunk[0] not in "LlHhVvCcSsQqTtAa":
                        raise ValidationError("Invalid SVG command after close")
                    chunk = f"M {here.real} {here.imag} {chunk}"
                match = move.match(chunk)
                if not match:
                    raise ValidationError("SVG subpath must begin with a moveto")
                start = complex(float(match[1]), float(match[2]))
                if chunk[0] == "m":
                    start += here
                start_xy = _point(_xy(start), "SVG start")
                result.sub_path(start_xy)
                try:
                    parsed = parse_path(chunk, current_pos=here)
                except (ValueError, AssertionError, IndexError, ZeroDivisionError) as exc:
                    raise ValidationError(f"Invalid SVG path data: {exc}") from exc
                for curve in parsed:
                    if isinstance(curve, Line):
                        result.line_to(_xy(curve.end))
                    elif isinstance(curve, QuadraticBezier):
                        result.quadratic_bezier_to(_xy(curve.control), _xy(curve.end))
                    elif isinstance(curve, CubicBezier):
                        result.cubic_bezier_to(
                            _xy(curve.control1), _xy(curve.control2), _xy(curve.end)
                        )
                    elif isinstance(curve, Arc):
                        result.arc_to(_xy(curve.radius), _xy(curve.end),
                                      curve.rotation, curve.large_arc, curve.sweep)
                here = _cp(result._cur_pt)
        if not result._subpaths:
            raise ValidationError("SVG contains no path geometry")
        return result

    def to_dxf(self, filename: str | PathLike) -> None:
        """Write each subpath as a DXF polyline, sampling curves into lines."""
        doc = ezdxf.new()
        model = doc.modelspace()
        for part, points in zip(self._subpaths, self.to_points()):
            model.add_lwpolyline(points, close=part["closed"])
        doc.saveas(filename)

    @classmethod
    def from_dxf(cls, filename: str | PathLike, segments: int = -1) -> Self:
        """Read planar DXF polylines and lines as independent subpaths.

        Curved (bulged) polyline segments and other entity types are rejected.
        """
        doc = ezdxf.readfile(filename)
        result = cls(segments=segments)
        result._subpaths.clear()
        for entity in doc.modelspace():
            kind = entity.dxftype()
            if kind == "LWPOLYLINE":
                if entity.dxf.elevation != 0 or entity.dxf.extrusion != (0, 0, 1):
                    raise ValidationError("Only XY-plane DXF polylines are supported")
                vertices = list(entity.get_points("xyb"))
                if any(vertex[2] != 0 for vertex in vertices):
                    raise ValidationError("DXF polyline bulges are not supported")
                points = [(v[0], v[1]) for v in vertices]
                closed = entity.closed
            elif kind == "POLYLINE":
                if not entity.is_2d_polyline or entity.dxf.extrusion != (0, 0, 1):
                    raise ValidationError("Only XY-plane DXF polylines are supported")
                if entity.dxf.elevation.z != 0:
                    raise ValidationError("Only XY-plane DXF polylines are supported")
                if any(v.dxf.bulge != 0 or v.dxf.location.z != 0 for v in entity.vertices):
                    raise ValidationError("DXF polyline bulges or 3D vertices are not supported")
                points = [(v.dxf.location.x, v.dxf.location.y) for v in entity.vertices]
                closed = entity.is_closed
            elif kind == "LINE":
                start, end = entity.dxf.start, entity.dxf.end
                if start.z != 0 or end.z != 0:
                    raise ValidationError("Only XY-plane DXF lines are supported")
                points = [(start.x, start.y), (end.x, end.y)]
                closed = False
            else:
                raise ValidationError(f"Unsupported DXF entity: {kind}")
            if not points:
                raise ValidationError("DXF polyline has no vertices")
            result.sub_path(points[0])
            for point in points[1:]:
                result.line_to(point)
            if closed:
                result.close()
        if not result._subpaths:
            raise ValidationError("DXF contains no path geometry")
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
