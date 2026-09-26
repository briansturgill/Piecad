# Prompt:
# I need a python program that will take a mesh (input is vertices, faces) I need
# two lists of edges, one that needs an inner fillet and one that needs an outer fillet.

from collections import defaultdict
from typing import Sequence
from . import *
from ._cutter import cutter
from .lin_math import Vec3
from .trigonometry import atan2


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
    *,
    angle_tolerance: float = 1e-6,
) -> tuple[list[tuple[int, int]], list[tuple[int, int]]]:
    """
    Classify mesh edges as inner (concave) or outer (convex) fillet edges.

    Args:
        vertices:
            Vertex positions, e.g. [(x, y, z), ...].
        faces:
            Polygon faces represented by vertex-index loops.  Faces must use
            consistent winding, with outward-facing normals.
        angle_tolerance:
            Ignore nearly coplanar edges whose dihedral angle is within this
            tolerance, in radians.

    Returns:
        A tuple of:
            - inner_edges: concave edges, suitable for an inner fillet
            - outer_edges: convex edges, suitable for an outer fillet

        Each edge is a sorted `(vertex_a, vertex_b)` vertex-index tuple.

    Notes:
        Boundary edges and non-manifold edges are ignored because they do not
        have exactly two adjacent faces.
    """
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
            outer_edges.append((edge, signed_angle, first_normal, second_normal))
        elif signed_angle < -angle_tolerance:
            inner_edges.append((edge, signed_angle, first_normal, second_normal))

    return inner_edges, outer_edges


def _f_and_c(
    obj: Obj3d,
    fillet: bool,
    radius: float = 2,
    include: list[tuple[float, float, float]] = None,
    exclude: list[tuple[float, float, float]] = None,
    angle_tolerance: float = 1e-6,
):
    vertices, faces = obj.to_verts_and_faces()

    inner_edges, outer_edges = classify_edges(vertices, faces)

    to_fill = []
    to_cut = []

    for t in outer_edges:
        edge, signed_angle, first_normal, second_normal = t
        v1, v2 = edge
        v1 = vertices[v1]
        v2 = vertices[v2]

        if fillet:
            fill = cutter(fillet, v1, v2, first_normal, second_normal, radius=radius)
            to_fill.append(fill)
        else:
            cut = cutter(fillet, v1, v2, first_normal, second_normal, radius=radius)
            to_cut.append(cut)

    if fillet:
        o = difference(obj, *to_fill)
        view(union(*to_fill))
    else:
        o = difference(obj, *to_cut)
        view(union(*to_cut))
    return o
