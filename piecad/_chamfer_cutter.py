from piecad import *


def chamfer_cutter(
    v1: tuple[float, float, float],
    v2: tuple[float, float, float],
    n1: tuple[float, float, float],
    n2: tuple[float, float, float],
    radius: float = 1.0,
) -> Obj3d:
    """
    Create a triangular 3D cutter for beveling edges.

    Given an outer edge with two points and two adjacent face normals,
    construct a 3D bevel cutter shape by creating triangles on each
    face and connecting them to form a closed polyhedron.

    Args:
        v1: First endpoint of the edge.
        v2: Second endpoint of the edge.
        n1: Normal vector of the first adjacent face.
        n2: Normal vector of the second adjacent face.
        radius: Distance into each face for the bevel points (r).

    Returns:
        An Obj3d polyhedron representing the bevel cutter.

    Algorithm:
    The cutter is formed by creating a 3D shape with two triangles at each
    edge endpoint:

    1. At each edge endpoint, create a triangle with vertices:
       - The edge point (v1 or v2)
       - A point at distance r into face 1: v + r * perp_in_face1
       - A point at distance r into face 2: v + r * perp_in_face2

    2. For each face, perp_in_face is computed as: cross(face_normal, edge_direction)
       This gives the direction perpendicular to the edge within the face plane.

    3. Connect the two triangles by forming faces between corresponding vertices,
       creating a closed polyhedron.

    4. For 90-degree edges (perpendicular faces), the triangles are equilateral
       with side length equal to the circumradius * sqrt(3).

    Returns a polyhedron with 6 vertices and 8 triangular faces.
    """
    v1 = np.array(v1, dtype=float)
    v2 = np.array(v2, dtype=float)
    n1 = np.array(n1, dtype=float)
    n2 = np.array(n2, dtype=float)

    n1 = n1 / np.linalg.norm(n1)
    n2 = n2 / np.linalg.norm(n2)

    edge_dir = v2 - v1
    edge_length = np.linalg.norm(edge_dir)
    if edge_length < 1e-12:
        raise ValidationError("Edge endpoints must be distinct")
    edge_dir = edge_dir / edge_length

    perp_in_f1 = np.cross(edge_dir, n1)
    perp_in_f1_len = np.linalg.norm(perp_in_f1)
    if perp_in_f1_len > 1e-12:
        perp_in_f1 = perp_in_f1 / perp_in_f1_len
    else:
        raise ValidationError("Edge is parallel to face normal 1")

    perp_in_f2 = np.cross(edge_dir, n2)
    perp_in_f2_len = np.linalg.norm(perp_in_f2)
    if perp_in_f2_len > 1e-12:
        perp_in_f2 = perp_in_f2 / perp_in_f2_len
    else:
        raise ValidationError("Edge is parallel to face normal 2")

    is_vertical = abs(edge_dir[2]) > 0.9

    if is_vertical:
        if n1[1] * n2[0] < 0:
            perp_in_f1 = -perp_in_f1
        else:
            perp_in_f2 = -perp_in_f2
    else:
        if n2[2] < 0:
            perp_in_f1 = -perp_in_f1
        else:
            perp_in_f2 = -perp_in_f2

    offset1_in_f1 = perp_in_f1 * radius
    offset2_in_f2 = perp_in_f2 * radius

    v1_f1 = v1 + offset1_in_f1
    v1_f2 = v1 + offset2_in_f2

    v2_f1 = v2 + offset1_in_f1
    v2_f2 = v2 + offset2_in_f2

    vertices = [
        tuple(v1),
        tuple(v1_f1),
        tuple(v1_f2),
        tuple(v2),
        tuple(v2_f1),
        tuple(v2_f2),
    ]

    faces = [
        (1, 2, 0),
        (5, 4, 3),
        (4, 1, 0),
        (3, 4, 0),
        (5, 2, 1),
        (4, 5, 1),
        (3, 0, 2),
        (5, 3, 2),
    ]

    # Reverse winding for configurations where all faces end up CW
    needs_flip = False
    if not is_vertical and n2[2] > 0:
        needs_flip = True
    elif is_vertical and n1[1] * n2[0] > 0:
        needs_flip = True

    if needs_flip:
        faces = [tuple(reversed(f)) for f in faces]

    return polyhedron(vertices, faces, check="none")


if __name__ == "__main__":
    view_all_now()