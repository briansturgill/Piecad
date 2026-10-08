"""
Align a piecad `Obj3d` that has a rectangular pad -- with the pad's corner
at the local origin, its edge running along +X, and its face normal along
+Z (i.e. the object as created, before any placement) -- onto a matching
rectangular pad located anywhere on an existing object, using only
`Obj3d.rotate()` and `Obj3d.translate()` (no scaling, since the pads are
already the same size).

Pad description convention (matches the corner/edge/normal style used by
chamfer_cutter/fillet_filler elsewhere in this project):

    corner  - a corner of the rectangular pad (a 3-vector).
    x_dir   - direction of the pad edge leaving that corner, i.e. the
              pad's local "+X" direction (any nonzero vector, need not
              be unit length).
    normal  - the outward-facing normal of the pad's plane (any nonzero
              vector, need not be unit length). "Outward" means pointing
              away from the solid the pad belongs to.
"""

from math import asin, atan2, degrees, sqrt

from .lin_math import Vec3
from . import Const


def _matrix_multiply(first, second):
    return tuple(
        tuple(
            sum(first[row][k] * second[k][column] for k in range(3))
            for column in range(3)
        )
        for row in range(3)
    )


def _matrix_transpose(matrix):
    return tuple(tuple(matrix[row][column] for row in range(3)) for column in range(3))


def _matrix_vector_multiply(matrix, vector):
    return tuple(
        sum(row[index] * vector[index] for index in range(3)) for row in matrix
    )


def _basis_from_columns(*columns):
    return tuple(tuple(column[row] for column in columns) for row in range(3))


def _scale_vector(vector, scale):
    return tuple(component * scale for component in vector)


def _quaternion_from_rotation_matrix(rotation):
    """Return a unit quaternion ``[w, x, y, z]`` for a 3x3 rotation."""
    trace = rotation[0][0] + rotation[1][1] + rotation[2][2]

    if trace > 0.0:
        s = 2.0 * sqrt(trace + 1.0)
        w = 0.25 * s
        x = (rotation[2][1] - rotation[1][2]) / s
        y = (rotation[0][2] - rotation[2][0]) / s
        z = (rotation[1][0] - rotation[0][1]) / s
    elif rotation[0][0] > rotation[1][1] and rotation[0][0] > rotation[2][2]:
        s = 2.0 * sqrt(1.0 + rotation[0][0] - rotation[1][1] - rotation[2][2])
        w = (rotation[2][1] - rotation[1][2]) / s
        x = 0.25 * s
        y = (rotation[0][1] + rotation[1][0]) / s
        z = (rotation[0][2] + rotation[2][0]) / s
    elif rotation[1][1] > rotation[2][2]:
        s = 2.0 * sqrt(1.0 + rotation[1][1] - rotation[0][0] - rotation[2][2])
        w = (rotation[0][2] - rotation[2][0]) / s
        x = (rotation[0][1] + rotation[1][0]) / s
        y = 0.25 * s
        z = (rotation[1][2] + rotation[2][1]) / s
    else:
        s = 2.0 * sqrt(1.0 + rotation[2][2] - rotation[0][0] - rotation[1][1])
        w = (rotation[1][0] - rotation[0][1]) / s
        x = (rotation[0][2] + rotation[2][0]) / s
        y = (rotation[1][2] + rotation[2][1]) / s
        z = 0.25 * s

    length = sqrt(w * w + x * x + y * y + z * z)
    return (w / length, x / length, y / length, z / length)


def _rotation_matrix_from_quaternion(quaternion):
    """Return a 3x3 rotation matrix for a unit quaternion ``[w, x, y, z]``."""
    w, x, y, z = quaternion
    return (
        (1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)),
        (2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)),
        (2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)),
    )


def _rigid_transform(rotation, source_corner, target_corner):
    """Return a 3x4 rigid transform after normalizing ``rotation`` via a quaternion."""
    quaternion = _quaternion_from_rotation_matrix(rotation)
    rotation = _rotation_matrix_from_quaternion(quaternion)
    rotated_source_corner = _matrix_vector_multiply(rotation, source_corner)
    translation = tuple(
        target_corner[index] - rotated_source_corner[index] for index in range(3)
    )
    return tuple(
        tuple(float(value) for value in (*rotation[index], translation[index]))
        for index in range(3)
    )


def _normalize(v):
    n = Vec3.length(v)
    if n < Const.epsilon:
        raise ValueError(f"Cannot normalize a near-zero vector: {v}")
    return Vec3.normalize(v)


def _basis_from_xy(x_dir, y_dir):
    """
    Build a right-handed orthonormal basis (ex, ey, ez) for a pad from
    its two in-plane edge directions (both leaving the same corner),
    with ez = cross(ex, ey). Unlike `_orthonormal_basis`, this takes
    both in-plane directions explicitly, so there is no sign ambiguity
    about which side of the x-edge the pad's footprint extends toward
    -- important for asymmetric footprints (e.g. a fillet's
    quarter-cylinder base, which only extends to one side of its length
    edge).

    Returns a 3x3 matrix whose *columns* are ex, ey, ez.
    """
    ex = _normalize(x_dir)
    # Re-orthogonalize y_dir against x_dir so the pair is exactly
    # perpendicular even if the inputs have numerical noise.
    y_proj = Vec3.sub(y_dir, _scale_vector(ex, Vec3.dot(y_dir, ex)))
    if Vec3.length(y_proj) < Const.epsilon:
        raise ValueError(
            "y_dir is parallel (or too close) to x_dir; cannot derive "
            "an in-plane basis."
        )
    ey = _normalize(y_proj)
    ez = Vec3.cross(ex, ey)

    return _basis_from_columns(ex, ey, ez)


def _rotation_to_xyz_degrees(R):
    """
    Decompose a 3x3 rotation matrix R into [rx, ry, rz] degrees such that
    R == Rz(rz) @ Ry(ry) @ Rx(rx) -- i.e. the "rotate about global X,
    then global Y, then global Z" order that manifold3d's
    `Manifold.rotate([x, y, z])` uses (see manifold3d.pyi: "From the
    global reference frame, a model will be rotated in x-y-z order.").
    """
    # Standard Tait-Bryan (extrinsic X-Y-Z) decomposition.
    sy = max(-1.0, min(1.0, -R[2][0]))
    cy = sqrt(1.0 - sy * sy)

    if cy > Const.epsilon:
        rx = atan2(R[2][1], R[2][2])
        ry = asin(sy)
        rz = atan2(R[1][0], R[0][0])
    else:
        # Gimbal lock (ry = +/-90 deg): rx and rz become coupled, so pick
        # rz = 0 and fold the remaining rotation into rx.
        rx = atan2(sy * R[0][1], R[1][1])
        ry = asin(sy)
        rz = 0.0

    return [float(degrees(rx)), float(degrees(ry)), float(degrees(rz))]


# def pad_alignment(
#     target_corner,
#     target_x_dir,
#     target_normal,
#     source_corner=(0.0, 0.0, 0.0),
#     source_x_dir=(1.0, 0.0, 0.0),
#     source_normal=(0.0, 0.0, 1.0),
#     flip_normal=True,
# ):
#     """Calculate placement from one edge direction and a pad normal."""
#     src_basis = _orthonormal_basis(source_x_dir, source_normal)
#     tgt_normal = Vec3.neg(target_normal) if flip_normal else target_normal
#     tgt_basis = _orthonormal_basis(target_x_dir, tgt_normal)
#     rotation = _matrix_multiply(tgt_basis, _matrix_transpose(src_basis))
#     rotated_source_corner = _matrix_vector_multiply(rotation, source_corner)
#     offsets = Vec3.sub(target_corner, rotated_source_corner)
#     return _rotation_to_xyz_degrees(rotation), list(offsets)
#
#
# def move_pad_to_pad(
#     new_obj,
#     target_corner,
#     target_x_dir,
#     target_normal,
#     source_corner=(0.0, 0.0, 0.0),
#     source_x_dir=(1.0, 0.0, 0.0),
#     source_normal=(0.0, 0.0, 1.0),
#     flip_normal=True,
# ):
#     """Place an object using its pad corner, one edge direction, and normal."""
#     rotation, offsets = pad_alignment(
#         target_corner,
#         target_x_dir,
#         target_normal,
#         source_corner=source_corner,
#         source_x_dir=source_x_dir,
#         source_normal=source_normal,
#         flip_normal=flip_normal,
#     )
#     return new_obj.rotate(rotation).translate(offsets)


def pad_alignment_xy(
    target_corner,
    target_x_dir,
    target_y_dir,
    source_corner=(0.0, 0.0, 0.0),
    source_x_dir=(1.0, 0.0, 0.0),
    source_y_dir=(0.0, 1.0, 0.0),
):
    """
    Like normal-based pad alignment, but for pads/footprints whose in-plane
    "footprint" is *not* symmetric about its x-edge (e.g. a fillet's
    quarter-cylinder base, which only extends to one side of its length
    edge, with the curved bulge rising out of a specific side of the
    plane). Instead of a normal (which only pins down the plane, and
    leaves the in-plane "y" direction to be *guessed* via a cross
    product -- an operation with a sign ambiguity that silently mirrors
    asymmetric footprints), this takes the pad's second in-plane edge
    direction explicitly, so there's no ambiguity: ex/ey/ez for the
    source and target are built the same way, from directly
    corresponding edges, and the whole local frame (including its
    z-bulge direction) is carried over rigidly and correctly.

    Parameters
    ----------
    target_corner : array-like (3,)
        A corner of the target footprint, in world space.
    target_x_dir : array-like (3,)
        Direction of the target footprint's first in-plane edge, leaving
        target_corner.
    target_y_dir : array-like (3,)
        Direction of the target footprint's second in-plane edge,
        leaving target_corner (the edge that pins down which side of
        the x-edge the footprint extends toward).
    source_corner, source_x_dir, source_y_dir :
        Same description, but for the source footprint, in its own
        local coordinates. Defaults match a footprint with its corner at
        the origin, first edge along +X, second edge along +Y.

    Returns
    -------
    (degrees, offsets)
        degrees: [rx, ry, rz] in the XYZ order manifold3d's
            `Manifold.rotate` expects.
        offsets: [tx, ty, tz] translation to apply after that rotation.
    """
    src_basis = _basis_from_xy(source_x_dir, source_y_dir)
    tgt_basis = _basis_from_xy(target_x_dir, target_y_dir)

    # Rotation that maps source basis vectors onto target basis vectors:
    # R @ src_basis == tgt_basis  =>  R = tgt_basis @ src_basis^T
    R = _matrix_multiply(tgt_basis, _matrix_transpose(src_basis))

    rotated_source_corner = _matrix_vector_multiply(R, source_corner)
    offsets = Vec3.sub(target_corner, rotated_source_corner)

    degrees = _rotation_to_xyz_degrees(R)
    return degrees, list(offsets)


def move_pad_to_pad_xy(
    new_obj,
    target_corner,
    target_x_dir,
    target_y_dir,
    source_corner=(0.0, 0.0, 0.0),
    source_x_dir=(1.0, 0.0, 0.0),
    source_y_dir=(0.0, 1.0, 0.0),
):
    """
    Rotate and translate a piecad `Obj3d` (`new_obj`) so that its
    footprint (source_corner/source_x_dir/source_y_dir, in new_obj's own
    local coordinates) lands exactly on a footprint on an existing
    object (target_corner/target_x_dir/target_y_dir, in world
    coordinates). See `pad_alignment_xy` for why this (explicit second
    edge direction) is used instead of normal-only placement for
    asymmetric footprints.
    """
    source_frame = _basis_from_xy(source_x_dir, source_y_dir)
    target_frame = _basis_from_xy(target_x_dir, target_y_dir)
    rotation = _matrix_multiply(target_frame, _matrix_transpose(source_frame))
    return new_obj.transform(_rigid_transform(rotation, source_corner, target_corner))


if __name__ == "__main__":
    from piecad import *

    # New object: a thin pad-like block whose bottom face is the "pad",
    # corner at the origin, edge along +X, face normal -Z (pointing down,
    # out of the block).
    new_obj = cuboid([4.0, 3.0, 1.0])  # spans x:[0,4] y:[0,3] z:[0,1]

    # Existing object: a big cube, target pad is its +X face, with the
    # corner at (10, 0, 0), edge running along +Y, normal pointing +X
    # (outward).
    existing = cuboid([10.0, 10.0, 10.0])

    moved = move_pad_to_pad_xy(
        new_obj,
        target_corner=(10.0, 0.0, 0.0),
        target_x_dir=(0.0, 1.0, 0.0),
        target_y_dir=(0.0, 0.0, 1.0),
        source_corner=(0.0, 0.0, 0.0),
        source_x_dir=(1.0, 0.0, 0.0),
        source_y_dir=(0.0, 1.0, 0.0),
    )

    verts, _ = moved.to_verts_and_faces()
    mins = tuple(min(vertex[axis] for vertex in verts) for axis in range(3))
    maxs = tuple(max(vertex[axis] for vertex in verts) for axis in range(3))
    print("moved bounding box:")
    print("  min:", mins)
    print("  max:", maxs)
    print(
        "expected: pad corner (local 0,0,0) lands on (10,0,0); block "
        "extends +1 unit further out along +X (away from the cube), "
        "+3 along +Y, +4 along +Z from that corner."
    )

    union_obj = union(existing, moved)
    print("union volume:", union_obj.volume())
    print(
        "existing + new volume (no overlap check):", existing.volume() + moved.volume()
    )
    view(existing)
    view(moved)
    view(union_obj)
    view_all_now()
