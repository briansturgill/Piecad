# Prompt:
# I need a python program that will take a mesh (input is vertices, faces) I need
# two lists of edges, one that needs an inner fillet and one that needs an outer fillet.

from collections import defaultdict
from typing import Sequence
from . import *
from .lin_math import Vec3
from .trigonometry import atan2


__all__ = [
    "modify_circular_edges",
    "modify_edges",
]


def face_normal(
    vertices: Sequence[Sequence[float]], face: Sequence[int]
) -> tuple[float, float, float]:
    """Return a normalized polygon normal using Newell's method."""
    if len(face) < 3:
        raise ValueError(f"A face needs at least three vertices: {face}")

    normal = (0.0, 0.0, 0.0)

    for current_index, next_index in zip(face, face[1:] + face[:1]):
        current = vertices[current_index]
        next_vertex = vertices[next_index]

        normal = (
            normal[0] + (current[1] - next_vertex[1]) * (current[2] + next_vertex[2]),
            normal[1] + (current[2] - next_vertex[2]) * (current[0] + next_vertex[0]),
            normal[2] + (current[0] - next_vertex[0]) * (current[1] + next_vertex[1]),
        )

    length = Vec3.length(normal)
    if length == 0.0:
        raise ValueError(f"Degenerate face has no normal: {face}")

    return Vec3.normalize(normal)


def classify_edges(
    vertices: Sequence[Sequence[float]],
    faces: Sequence[Sequence[int]],
) -> tuple[list[tuple[int, int]], list[tuple[int, int]]]:
    """
    Classify mesh edges as inner (concave) or outer (convex) fillet edges.

    Args:
        vertices:
            Vertex positions, e.g. [(x, y, z), ...].
        faces:
            Polygon faces represented by vertex-index loops.  Faces must use
            consistent winding, with outward-facing normals.

    Returns:
        A tuple of:
            - inner_edges: concave edges, suitable for an inner fillet
            - outer_edges: convex edges, suitable for an outer fillet

        Each edge is a sorted `(vertex_a, vertex_b)` vertex-index tuple.

    Notes:
        Boundary edges and non-manifold edges are ignored because they do not
        have exactly two adjacent faces.
    """
    angle_tolerance = 1e-6

    if not vertices or any(len(vertex) != 3 for vertex in vertices):
        raise ValueError("vertices must be an Nx3 collection")

    face_loops = [list(face) for face in faces]
    normals = [face_normal(vertices, face) for face in face_loops]

    # Maps an undirected edge to:
    # [(face_index, directed_start_vertex, directed_end_vertex), ...]
    edge_faces: dict[tuple[int, int], list[tuple[int, int, int]]] = defaultdict(list)

    for face_index, face in enumerate(face_loops):
        if len(face) < 3:
            raise ValueError(f"Face {face_index} has fewer than 3 vertices")

        for start, end in zip(face, face[1:] + face[:1]):
            if start == end:
                continue

            edge = tuple(sorted((start, end)))
            edge_faces[edge].append((face_index, start, end))

    inner_edges: list[tuple[int, int]] = []
    outer_edges: list[tuple[int, int]] = []

    for edge, adjacent_faces in edge_faces.items():
        # Ignore boundaries (one face) and non-manifold edges (more than two).
        if len(adjacent_faces) != 2:
            continue

        first_face, start, end = adjacent_faces[0]
        second_face, _, _ = adjacent_faces[1]

        edge_vector = Vec3.sub(vertices[end], vertices[start])
        edge_length = Vec3.length(edge_vector)
        if edge_length == 0.0:
            continue

        edge_direction = Vec3.normalize(edge_vector)
        first_normal = normals[first_face]
        second_normal = normals[second_face]

        signed_angle = atan2(
            Vec3.dot(edge_direction, Vec3.cross(first_normal, second_normal)),
            Vec3.dot(first_normal, second_normal),
        )

        # With outward-facing, consistently wound faces:
        # positive = convex/outer, negative = concave/inner.
        if signed_angle > angle_tolerance:
            outer_edges.append(
                (edge, edge_length, signed_angle, first_normal, second_normal)
            )
        elif signed_angle < -angle_tolerance:
            inner_edges.append(
                (edge, edge_length, signed_angle, first_normal, second_normal)
            )

    return inner_edges, outer_edges


def _circular_edge_geometry(
    obj: Obj3d,
    origin: tuple[float, float, float],
    radii: tuple[float, float],
    outward: bool,
) -> tuple[int, int, float]:
    if obj.is_empty():
        raise ValueError("could not uniquely identify the circular edge and material side")
    vertices, faces = obj.to_verts_and_faces()
    _, outer_edges = classify_edges(vertices, faces)
    cx, cy, cz = origin
    rx, ry = radii
    tolerance = 1e-6 * max(1.0, rx, ry)
    sides = set()
    rim_edges = set()

    for edge, _, _, first_normal, second_normal in outer_edges:
        points = [vertices[index] for index in edge]
        if any(
            abs(point[2] - cz) > tolerance
            or abs(math.hypot((point[0] - cx) / rx, (point[1] - cy) / ry) - 1)
            > tolerance / max(rx, ry)
            for point in points
        ):
            continue
        for horizontal, radial in (
            (first_normal, second_normal),
            (second_normal, first_normal),
        ):
            if abs(abs(horizontal[2]) - 1) > 1e-6 or abs(radial[2]) > 1e-6:
                continue
            midpoint_x = (points[0][0] + points[1][0]) / 2 - cx
            midpoint_y = (points[0][1] + points[1][1]) / 2 - cy
            radial_dot = (
                radial[0] * (midpoint_x / rx) / rx
                + radial[1] * (midpoint_y / ry) / ry
            )
            if (outward and radial_dot > 0) or (not outward and radial_dot < 0):
                sides.add(-1 if horizontal[2] > 0 else 1)
                rim_edges.add(edge)

    if len(sides) != 1:
        raise ValueError("could not uniquely identify the circular edge and material side")

    degrees = defaultdict(int)
    for start, end in rim_edges:
        degrees[start] += 1
        degrees[end] += 1
    segments = len(degrees)
    if (
        segments < 3
        or len(rim_edges) != segments
        or any(count != 2 for count in degrees.values())
    ):
        raise ValueError("circular edge must be a complete, regularly segmented rim")
    angles = sorted(
        math.atan2((vertices[i][1] - cy) / ry, (vertices[i][0] - cx) / rx)
        % (2 * math.pi)
        for i in degrees
    )
    step = 2 * math.pi / segments
    if any(
        abs((angles[(i + 1) % segments] - angles[i]) % (2 * math.pi) - step) > 1e-5
        for i in range(segments)
    ):
        raise ValueError("circular edge must be a complete, regularly segmented rim")
    return sides.pop(), segments, math.degrees(angles[0])


def modify_circular_edges(
    obj: Obj3d,
    mod_type: str,
    origin: tuple[float, float, float],
    radius: float | tuple[float, float],
    outward: bool = True,
    size: float = 4.0,
    overhang: float = 1e-5,
) -> Obj3d:
    """Cut an XY-plane circular or elliptical rim centered at origin."""
    profiles = {
        "bevel": bevel_2d,
        "chamfer": bevel_2d,
        "comma": comma_2d,
        "fillet": fillet_2d,
        "sawtooth": sawtooth_2d,
        "steeper_facets": steeper_facets_2d,
    }
    if mod_type not in profiles:
        raise ValueError(f"Unknown cutter type: {mod_type}")
    _validate_profile_dimensions(size, overhang)
    if len(origin) != 3 or not all(math.isfinite(value) for value in origin):
        raise ValueError("origin must contain three finite components")
    if not isinstance(outward, bool):
        raise TypeError("outward must be a bool")
    if isinstance(radius, tuple):
        if len(radius) != 2:
            raise ValueError("radius must be positive or a pair of positive radii")
        radii = radius
    else:
        radii = (radius, radius)
    if any(not math.isfinite(value) or value <= 0 for value in radii):
        raise ValueError("radius must be positive and finite")
    rx, ry = radii
    if outward and rx <= size + overhang:
        raise ValueError("outer radius must be greater than size plus overhang")

    side, segments, rotation = _circular_edge_geometry(obj, origin, radii, outward)
    profile = profiles[mod_type](size=size, overhang=overhang)
    profile = (
        profile.translate((size / 2, size / 2))
        .scale((-1 if outward else 1, side))
        .translate((rx, 0))
    )
    cutter = (
        profile.revolve(segments=segments)
        .rotate((0, 0, rotation))
        .scale((1, ry / rx, 1))
        .translate(origin)
    )
    return difference(obj, cutter).simplify()


def modify_edges(
    obj: Obj3d,
    mod_type: str,
    size: float,  # For fillets this is radius
    min_edge_length,
    angle_range,
    include: list[tuple[float, float, float, float, float, float]] | None,
    exclude: list[tuple[float, float, float, float, float, float]] | None,
    overhang=1e-5,
    flip_on_top=True
) -> Obj3d:
    """
    Modify the edges of an `Obj3d` object.
    This function is used internally by the `modify_edges` and `modify_edge` methods of `Obj3d`.
    """
    vertices, faces = obj.to_verts_and_faces()
    _, outer_edges = classify_edges(vertices, faces)

    to_cut = []

    for t in outer_edges:
        edge, edge_length, signed_angle, first_normal, second_normal = t
        abs_angle = abs(signed_angle)
        if (
            abs_angle < angle_range[0]
            or abs_angle > angle_range[1]
            or edge_length < min_edge_length
        ):
            continue

        v1, v2 = edge
        v1 = vertices[v1]
        v2 = vertices[v2]

        if include is not None:
            inside_include = False
            for bbox in include:
                xmin, ymin, zmin, xmax, ymax, zmax = bbox
                if (
                    xmin <= v1[0] <= xmax
                    and ymin <= v1[1] <= ymax
                    and zmin <= v1[2] <= zmax
                    and xmin <= v2[0] <= xmax
                    and ymin <= v2[1] <= ymax
                    and zmin <= v2[2] <= zmax
                ):
                    inside_include = True
                    break
            if not inside_include:
                continue

        if exclude is not None:
            inside_exclude = False
            for bbox in exclude:
                xmin, ymin, zmin, xmax, ymax, zmax = bbox
                if (
                    xmin <= v1[0] <= xmax
                    and ymin <= v1[1] <= ymax
                    and zmin <= v1[2] <= zmax
                    and xmin <= v2[0] <= xmax
                    and ymin <= v2[1] <= ymax
                    and zmin <= v2[2] <= zmax
                ):
                    inside_exclude = True
                    break
            if inside_exclude:
                continue

        cut_obj = modify_edge(
            mod_type,
            (v1,
            v2,
            first_normal,
            second_normal),
            size=size,
            overhang=overhang,
            flip_on_top=flip_on_top
        )
        to_cut.append(cut_obj)

    print(len(to_cut))
    o = difference(obj, *to_cut)
    # view(union(*to_cut))

    return o.simplify()


def modify_edge(
    mod_type: str,
    edge: tuple[tuple[float, float, float], tuple[float, float, float], tuple[float, float, float], tuple[float, float, float]],
    size: float,
    overhang=1e-5,
    flip_on_top=True
) -> Obj3d:
    """
    Modify a single edge of an object.
    This is a low-level function used internally by `modify_edges`.
    """
    o = position_cutter(
            make_cutter(mod_type, edge, size, overhang, flip_on_top),
            edge=edge,
            size=size
        )
    return o

def _orient_cutter(cutter, edge):
    start, end, first_normal, second_normal = edge
    edge_direction = Vec3.sub(end, start)
    local_z = Vec3.cross(edge_direction, Vec3.neg(first_normal))
    # The second face can lie on either side of local Z; mirror if needed.
    if Vec3.dot(local_z, second_normal) > 0:
        cutter = cutter.mirror((0, 0, 1))
    return cutter


def _fillet_cylinder(edge, size, segments=-1):
    start, end, _, _ = edge
    length = Vec3.distance(start, end)
    # Opposite the triangle's right-angle vertex, the circle is tangent to both faces.
    cylinder_cut = (
        cylinder(length, size, segments=segments, center=True)
        .rotate((0, 90, 0))
        .translate((0, size / 2, size / 2))
    )
    return _orient_cutter(cylinder_cut, edge)


def _vertical_edge(edge):
    direction = Vec3.sub(edge[1], edge[0])
    length = Vec3.length(direction)
    if length == 0:
        raise ValueError("edge endpoints must be distinct")
    return math.hypot(direction[0], direction[1]) <= length * 1e-10


def _swap_profile(edge, flip_on_top):
    first_normal, second_normal = edge[2:]
    if first_normal[2] == second_normal[2]:
        swap = tuple(first_normal) < tuple(second_normal)
    else:
        swap = first_normal[2] < second_normal[2]
    on_top = max(first_normal[2], second_normal[2]) > 1e-10 and min(
        first_normal[2], second_normal[2]
    ) >= -1e-10
    return swap != (flip_on_top and on_top)


def _validate_profile_dimensions(size, overhang):
    if not math.isfinite(size) or size <= 0:
        raise ValueError("size must be finite and positive")
    if not math.isfinite(overhang) or overhang < 0:
        raise ValueError("overhang must be finite and non-negative")


def _profile_cutter(edge, size, overhang, flip_on_top, angles, arc_steps):
    """Sweep sampled fillet-to-tangent profiles along the edge."""
    length = Vec3.distance(edge[0], edge[1])
    swap = _swap_profile(edge, flip_on_top)
    vertices = []
    for section, angle in enumerate(angles):
        x = length * (section / (len(angles) - 1) - 0.5)
        join_x = size * (1 - math.cos(angle))
        join_y = size * (1 - math.sin(angle))
        bottom_x = join_x + join_y * math.tan(angle)
        points = [(-overhang, -overhang)]
        if overhang:
            points.append((bottom_x + overhang * math.tan(angle), -overhang))
        points.append((bottom_x, 0))
        points.extend(
            (
                size * (1 - math.cos(angle * i / arc_steps)),
                size * (1 - math.sin(angle * i / arc_steps)),
            )
            for i in range(arc_steps, -1, -1)
        )
        if overhang:
            points.append((-overhang, size))
        for a, b in points:
            if swap:
                a, b = b, a
            vertices.append((x, a - size / 2, b - size / 2))

    count = len(points)
    faces = []
    end = (len(angles) - 1) * count
    for i in range(1, count - 1):
        faces.append((0, i + 1, i))
        faces.append((end, end + i, end + i + 1))
    # Keep the same world-space diagonals if the edge endpoints are reversed.
    reverse = tuple(edge[1]) < tuple(edge[0])
    for section in range(len(angles) - 1):
        for i in range(count):
            a = section * count + i
            b = section * count + (i + 1) % count
            c = b + count
            d = a + count
            if reverse:
                faces.extend(((a, b, d), (b, c, d)))
            else:
                faces.extend(((a, b, c), (a, c, d)))
    if swap:
        faces = [(a, c, b) for a, b, c in faces]
    return _orient_cutter(polyhedron(vertices, faces, check="batch"), edge)


def _cutter_profile(cutter, size, overhang):
    """Slice the 3D cutter into its local face-normal coordinates."""
    edge = ((-size, 0, 0), (size, 0, 0), (0, -1, 0), (0, 0, -1))
    shape = cutter(edge, size=size, overhang=overhang)
    return shape.transform(((0, 1, 0, 0), (0, 0, 1, 0), (1, 0, 0, 0))).slice(0)


def bevel_2d(size=2.0, overhang=1e-5):
    return _cutter_profile(bevel_3d, size, overhang)


def bevel_3d(edge, size=2.0, overhang=1e-5):
    """Build a 45-degree bevel cutter with legs of length size."""
    if not math.isfinite(size) or size <= 0:
        raise ValueError("size must be finite and positive")
    start, end, _, _ = edge
    half_length = Vec3.distance(start, end) / 2
    reach = size / 2 + overhang
    # The triangular cross-section's diagonal stays on y + z = 0 as it grows.
    vertices = [
        (-half_length, -reach, -reach),
        (-half_length, reach, -reach),
        (-half_length, -reach, reach),
        (half_length, -reach, -reach),
        (half_length, reach, -reach),
        (half_length, -reach, reach),
    ]
    faces = [
        (0, 2, 1),
        (3, 4, 5),
        (0, 1, 4),
        (0, 4, 3),
        (1, 2, 5),
        (1, 5, 4),
        (2, 0, 3),
        (2, 3, 5),
    ]
    return _orient_cutter(polyhedron(vertices, faces, check="batch"), edge)


def comma_2d(size=2.0, overhang=1e-5):
    return _cutter_profile(comma_3d, size, overhang)


def comma_3d(edge, size=2.0, overhang=1e-5, flip_on_top=True):
    """Build a printable fillet, optionally flipping it on top-facing edges.

    Top-facing means neither outward normal points down and at least one points
    up in world Z. Vertical edges use a fillet regardless of this setting.
    """
    if _vertical_edge(edge):
        return fillet_3d(edge, size, overhang)

    start, end, _, _ = edge
    length = Vec3.distance(start, end)
    cutter = bevel_3d(edge, size, overhang)
    # Include the 45-degree arc endpoint as a cylinder vertex.
    segments = ((Config.get_default_segments() + 7) // 8) * 8
    cylinder_cut = _fillet_cylinder(edge, size, segments)

    join = size * (1 - 1 / math.sqrt(2))
    extent = 3 * size + abs(overhang)
    bottom = -size - abs(overhang)
    points = [
        (join, join),
        (2 * join - bottom, bottom),
        (extent, bottom),
        (extent, extent),
        (join, extent),
    ]
    if _swap_profile(edge, flip_on_top):
        points = [(y, x) for x, y in points]
    points = [(x - size / 2, y - size / 2) for x, y in points]
    wedge = (
        polygon([points])
        .extrude(length)
        .translate((0, 0, -length / 2))
        .rotate((90, 0, 90))
    )
    return difference(cutter, cylinder_cut, _orient_cutter(wedge, edge))


def fillet_2d(size=2.0, overhang=1e-5):
    return _cutter_profile(fillet_3d, size, overhang)


def fillet_3d(edge, size=2.0, overhang=1e-5):
    """Build a fillet cutter by removing a cylinder from the bevel."""
    return difference(bevel_3d(edge, size, overhang), _fillet_cylinder(edge, size))


def sawtooth_2d(size=2.0, overhang=1e-5):
    """Return a representative section of the varying 3D sawtooth."""
    return _cutter_profile(sawtooth_3d, size, overhang)


def sawtooth_3d(edge, size=2.0, overhang=1e-5, flip_on_top=True):
    """Vary the transition from 22.5 to 45 degrees, with pitch about size."""
    _validate_profile_dimensions(size, overhang)
    if _vertical_edge(edge):
        return fillet_3d(edge, size, overhang)
    length = Vec3.distance(edge[0], edge[1])
    samples_per_tooth = 8
    steps = samples_per_tooth * max(1, math.ceil(length / size))
    angles = [
        3 * math.pi / 16
        + math.pi / 16 * math.cos(2 * math.pi * i / samples_per_tooth)
        for i in range(steps + 1)
    ]
    arc_steps = max(1, math.ceil(Config.get_default_segments() / 8))
    return _profile_cutter(edge, size, overhang, flip_on_top, angles, arc_steps)


def steeper_facets_2d(size=2.0, overhang=1e-5):
    return _cutter_profile(steeper_facets_3d, size, overhang)


def steeper_facets_3d(edge, size=2.0, overhang=1e-5, flip_on_top=True):
    """Approximate the upper fillet with two facets and a 45-degree tangent."""
    _validate_profile_dimensions(size, overhang)
    if _vertical_edge(edge):
        return fillet_3d(edge, size, overhang)
    return _profile_cutter(edge, size, overhang, flip_on_top, (math.pi / 4,) * 2, 2)


def make_cutter(mod_type, edge, size=2.0, overhang=1e-5, flip_on_top=True):
    if mod_type == "bevel" or mod_type == "chamfer":
        return bevel_3d(edge, size, overhang)
    elif mod_type == "fillet":
        return fillet_3d(edge, size, overhang)
    elif mod_type == "comma":
        return comma_3d(edge, size, overhang, flip_on_top)
    elif mod_type == "steeper_facets":
        return steeper_facets_3d(edge, size, overhang, flip_on_top)
    elif mod_type == "sawtooth":
        return sawtooth_3d(edge, size, overhang, flip_on_top)
    raise ValueError(f"Unknown cutter type: {mod_type}")


def position_cutter(cutter, edge, size=2.0):
    """Align the cutter to the edge and its adjacent faces, then translate it."""
    start, end, first_normal, second_normal = edge
    edge_vector = Vec3.sub(end, start)
    if Vec3.length(edge_vector) == 0:
        raise ValueError("edge endpoints must be distinct")
    direction = Vec3.normalize(edge_vector)
    # For perpendicular faces, the cutter origin is half the size inward from each.
    center = Vec3.sub(
        Vec3.mul(Vec3.add(start, end), (0.5, 0.5, 0.5)),
        Vec3.mul(Vec3.add(first_normal, second_normal), (size / 2,) * 3),
    )

    axis = Vec3.cross((1, 0, 0), direction)
    axis_length = Vec3.length(axis)
    if axis_length == 0:
        # Parallel or antiparallel to X: Z is a valid axis for either 0 or 180 degrees.
        axis = (0, 0, 1)
    else:
        axis = Vec3.normalize(axis)
    angle = math.atan2(axis_length, direction[0])
    cutter = quaternion_rotate(cutter, axis, math.degrees(angle))

    # Apply the same rotation to local Y using Rodrigues' formula, then roll it
    # around the edge until it points inward from the first face.
    cosine, sine = math.cos(angle), math.sin(angle)
    y_axis = (0, 1, 0)
    rotated_y = Vec3.add(
        Vec3.add(
            Vec3.mul(y_axis, (cosine,) * 3),
            Vec3.mul(Vec3.cross(axis, y_axis), (sine,) * 3),
        ),
        Vec3.mul(axis, (Vec3.dot(axis, y_axis) * (1 - cosine),) * 3),
    )
    inward = Vec3.neg(first_normal)
    roll = math.atan2(
        Vec3.dot(direction, Vec3.cross(rotated_y, inward)), Vec3.dot(rotated_y, inward)
    )
    cutter = quaternion_rotate(cutter, direction, math.degrees(roll))
    return cutter.translate(center)


def quaternion_rotate(
    obj: Obj3d, axis: tuple[float, float, float], degrees: float
) -> Obj3d:
    """Return a rotated object, leaving the original unchanged.

    Parameters:
        obj: The piecad 3D object to rotate.
        axis: Three finite direction components (x, y, z), not angles.
            The vector must be nonzero and need not be normalized. The
            rotation axis passes through the origin.
        degrees: A finite, signed rotation angle in degrees. Positive
            angles follow the right-hand rule around the axis.

    Returns:
        A new piecad 3D object.

    Raises:
        ValueError: If the angle or axis is non-finite, or the axis does
            not have exactly three components or is zero.
    """
    if not math.isfinite(degrees):
        raise ValueError("degrees must be finite")
    if len(axis) != 3 or not all(math.isfinite(component) for component in axis):
        raise ValueError("axis must contain three finite components")

    # Scale first to avoid overflow or underflow when normalizing extreme axes.
    scale = max(abs(component) for component in axis)
    if scale == 0:
        raise ValueError("axis must be nonzero")
    scaled_axis = tuple(component / scale for component in axis)
    length = math.hypot(*scaled_axis)
    # Reduce full turns before evaluating the quaternion's half-angle.
    half_angle = math.radians(math.fmod(degrees, 360)) / 2
    sine = math.sin(half_angle)
    w = math.cos(half_angle)
    x, y, z = (component / length * sine for component in scaled_axis)

    # Convert the unit quaternion to a 3x4 affine rotation about the origin.
    matrix = (
        (1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w), 0),
        (2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w), 0),
        (2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y), 0),
    )
    return obj.transform(matrix)