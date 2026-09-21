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

import numpy as np


def _quaternion_from_rotation_matrix(rotation):
    """Return a unit quaternion ``[w, x, y, z]`` for a 3x3 rotation."""
    rotation = np.asarray(rotation, dtype=float)
    trace = np.trace(rotation)

    if trace > 0.0:
        s = 2.0 * np.sqrt(trace + 1.0)
        w = 0.25 * s
        x = (rotation[2, 1] - rotation[1, 2]) / s
        y = (rotation[0, 2] - rotation[2, 0]) / s
        z = (rotation[1, 0] - rotation[0, 1]) / s
    elif rotation[0, 0] > rotation[1, 1] and rotation[0, 0] > rotation[2, 2]:
        s = 2.0 * np.sqrt(1.0 + rotation[0, 0] - rotation[1, 1] - rotation[2, 2])
        w = (rotation[2, 1] - rotation[1, 2]) / s
        x = 0.25 * s
        y = (rotation[0, 1] + rotation[1, 0]) / s
        z = (rotation[0, 2] + rotation[2, 0]) / s
    elif rotation[1, 1] > rotation[2, 2]:
        s = 2.0 * np.sqrt(1.0 + rotation[1, 1] - rotation[0, 0] - rotation[2, 2])
        w = (rotation[0, 2] - rotation[2, 0]) / s
        x = (rotation[0, 1] + rotation[1, 0]) / s
        y = 0.25 * s
        z = (rotation[1, 2] + rotation[2, 1]) / s
    else:
        s = 2.0 * np.sqrt(1.0 + rotation[2, 2] - rotation[0, 0] - rotation[1, 1])
        w = (rotation[1, 0] - rotation[0, 1]) / s
        x = (rotation[0, 2] + rotation[2, 0]) / s
        y = (rotation[1, 2] + rotation[2, 1]) / s
        z = 0.25 * s

    quaternion = np.array([w, x, y, z])
    return quaternion / np.linalg.norm(quaternion)


def _rotation_matrix_from_quaternion(quaternion):
    """Return a 3x3 rotation matrix for a unit quaternion ``[w, x, y, z]``."""
    w, x, y, z = np.asarray(quaternion, dtype=float)
    return np.array(
        [
            [1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
            [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
            [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)],
        ]
    )


def _rigid_transform(rotation, source_corner, target_corner):
    """Return a 3x4 rigid transform after normalizing ``rotation`` via a quaternion."""
    quaternion = _quaternion_from_rotation_matrix(rotation)
    rotation = _rotation_matrix_from_quaternion(quaternion)
    translation = np.asarray(target_corner, dtype=float) - rotation @ np.asarray(
        source_corner, dtype=float
    )
    return tuple(
        tuple(float(value) for value in (*row, translation[index]))
        for index, row in enumerate(rotation)
    )


def _rectangle_frame(points, name):
    """Return a corner and right-handed frame from four ordered rectangle points."""
    points = np.asarray(points, dtype=float)
    if points.shape != (4, 3):
        raise ValueError(f"{name} must contain exactly four 3D points.")

    corner, x_corner, opposite, y_corner = points
    x_edge = x_corner - corner
    y_edge = y_corner - corner
    x_length = np.linalg.norm(x_edge)
    y_length = np.linalg.norm(y_edge)
    if x_length < 1e-12 or y_length < 1e-12:
        raise ValueError(f"{name} contains a zero-length rectangle edge.")

    x_axis = x_edge / x_length
    y_projection = y_edge - np.dot(y_edge, x_axis) * x_axis
    y_projection_length = np.linalg.norm(y_projection)
    if y_projection_length < 1e-12:
        raise ValueError(f"{name} rectangle edges must not be parallel.")
    y_axis = y_projection / y_projection_length
    z_axis = np.cross(x_axis, y_axis)

    expected_opposite = corner + x_edge + y_edge
    if not np.allclose(opposite, expected_opposite, rtol=1e-9, atol=1e-9):
        raise ValueError(f"{name} points must be ordered around a rectangle.")

    return corner, np.column_stack((x_axis, y_axis, z_axis)), (x_length, y_length)


def rectangular_pad_transform(source_points, target_points):
    """
    Return a rigid 3x4 transform mapping four source pad corners to four target
    pad corners.

    Points must correspond in winding order:
    ``[corner, corner + x, corner + x + y, corner + y]``.  The returned
    transform contains no scale or shear; its rotation is constructed through
    a quaternion and its translation maps the source corner exactly.
    """
    source_corner, source_frame, source_size = _rectangle_frame(
        source_points, "source_points"
    )
    target_corner, target_frame, target_size = _rectangle_frame(
        target_points, "target_points"
    )
    if not np.allclose(source_size, target_size, rtol=1e-9, atol=1e-9):
        raise ValueError("Source and target rectangular pads must have the same size.")

    return _rigid_transform(target_frame @ source_frame.T, source_corner, target_corner)


def move_rectangular_pad(new_obj, source_points, target_points):
    """Rigidly place ``new_obj`` so its four source pad corners match targets."""
    return new_obj.transform(rectangular_pad_transform(source_points, target_points))


def _normalize(v):
    v = np.asarray(v, dtype=float)
    n = np.linalg.norm(v)
    if n < 1e-12:
        raise ValueError(f"Cannot normalize a near-zero vector: {v}")
    return v / n


def _orthonormal_basis(x_dir, normal):
    """
    Build a right-handed orthonormal basis (ex, ey, ez) for a pad, where
    ez is the (unit) plane normal and ex is the (unit) edge direction,
    re-orthogonalized against the normal so it lies exactly in the pad
    plane (this tolerates x_dir/normal that aren't perfectly
    perpendicular due to numerical noise).

    Returns a 3x3 matrix whose *columns* are ex, ey, ez.

    NOTE: Because ey is *derived* as cross(ez, ex), this only pins down
    the pad's plane and its "x" edge -- it does not know which side of
    that edge the pad's other in-plane direction ("y") should point.
    That's fine for pads that are symmetric about their x-axis edge (or
    when you only care about matching planes), but it is *not* safe for
    asymmetric footprints (like a quarter-cylinder's rectangular base,
    which only extends to one side). For asymmetric footprints use
    `_basis_from_xy` / `pad_alignment_xy` / `move_pad_to_pad_xy`
    instead, which take the second in-plane direction explicitly instead
    of guessing it from a cross product.
    """
    ez = _normalize(normal)
    x_dir = np.asarray(x_dir, dtype=float)

    x_proj = x_dir - np.dot(x_dir, ez) * ez
    if np.linalg.norm(x_proj) < 1e-9:
        raise ValueError(
            "x_dir is parallel (or too close) to the normal; "
            "cannot derive an in-plane edge direction."
        )
    ex = _normalize(x_proj)
    ey = np.cross(ez, ex)

    return np.column_stack((ex, ey, ez))


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
    x_dir = np.asarray(x_dir, dtype=float)
    y_dir = np.asarray(y_dir, dtype=float)

    ex = _normalize(x_dir)
    # Re-orthogonalize y_dir against x_dir so the pair is exactly
    # perpendicular even if the inputs have numerical noise.
    y_proj = y_dir - np.dot(y_dir, ex) * ex
    if np.linalg.norm(y_proj) < 1e-9:
        raise ValueError(
            "y_dir is parallel (or too close) to x_dir; cannot derive "
            "an in-plane basis."
        )
    ey = _normalize(y_proj)
    ez = np.cross(ex, ey)

    return np.column_stack((ex, ey, ez))


def _rotation_to_xyz_degrees(R):
    """
    Decompose a 3x3 rotation matrix R into [rx, ry, rz] degrees such that
    R == Rz(rz) @ Ry(ry) @ Rx(rx) -- i.e. the "rotate about global X,
    then global Y, then global Z" order that manifold3d's
    `Manifold.rotate([x, y, z])` uses (see manifold3d.pyi: "From the
    global reference frame, a model will be rotated in x-y-z order.").
    """
    R = np.asarray(R, dtype=float)

    # Standard Tait-Bryan (extrinsic X-Y-Z) decomposition.
    sy = -R[2, 0]
    sy = np.clip(sy, -1.0, 1.0)
    cy = np.sqrt(1.0 - sy * sy)

    if cy > 1e-8:
        rx = np.arctan2(R[2, 1], R[2, 2])
        ry = np.arcsin(sy)
        rz = np.arctan2(R[1, 0], R[0, 0])
    else:
        # Gimbal lock (ry = +/-90 deg): rx and rz become coupled, so pick
        # rz = 0 and fold the remaining rotation into rx.
        rx = np.arctan2(-R[0, 1], R[1, 1])
        ry = np.arcsin(sy)
        rz = 0.0

    return [float(np.degrees(rx)), float(np.degrees(ry)), float(np.degrees(rz))]


def pad_alignment(
    target_corner,
    target_x_dir,
    target_normal,
    source_corner=(0.0, 0.0, 0.0),
    source_x_dir=(1.0, 0.0, 0.0),
    source_normal=(0.0, 0.0, 1.0),
    flip_normal=True,
):
    """
    Compute the rotation (degrees, XYZ order) and translation needed to
    move a pad defined in local/source coordinates onto a pad defined in
    world/target coordinates.

    Returns (degrees, offsets), each a list of 3 floats, suitable for
    `obj.rotate(degrees).translate(offsets)`.
    """
    target_corner = np.asarray(target_corner, dtype=float)
    source_corner = np.asarray(source_corner, dtype=float)

    src_basis = _orthonormal_basis(source_x_dir, source_normal)  # columns ex,ey,ez

    tgt_normal = np.asarray(target_normal, dtype=float)
    if flip_normal:
        tgt_normal = -tgt_normal
    tgt_basis = _orthonormal_basis(target_x_dir, tgt_normal)

    # Rotation that maps source basis vectors onto target basis vectors:
    # R @ src_basis == tgt_basis  =>  R = tgt_basis @ src_basis^T
    # (src_basis is orthonormal, so its transpose is its inverse.)
    R = tgt_basis @ src_basis.T

    # rotate() rotates about the local/global origin, so apply the
    # rotation first, then translate the (now-rotated) source corner
    # onto the target corner.
    rotated_source_corner = R @ source_corner
    offsets = target_corner - rotated_source_corner

    degrees = _rotation_to_xyz_degrees(R)
    return degrees, offsets.tolist()


def move_pad_to_pad(
    new_obj,
    target_corner,
    target_x_dir,
    target_normal,
    source_corner=(0.0, 0.0, 0.0),
    source_x_dir=(1.0, 0.0, 0.0),
    source_normal=(0.0, 0.0, 1.0),
    flip_normal=True,
):
    """
    Rotate and translate a piecad `Obj3d` (`new_obj`) so that its pad
    (described by source_corner/source_x_dir/source_normal, in
    new_obj's own local coordinates -- by default the corner at the
    origin, edge along +X, face normal along +Z) lands exactly on a pad
    on an existing object (described by target_corner/target_x_dir/
    target_normal, in world coordinates).

    Parameters
    ----------
    new_obj : piecad.Obj3d
        The object to move (not mutated; a new Obj3d is returned, as is
        piecad's convention).
    target_corner : array-like (3,)
        A corner of the pad on the existing object, in world space.
    target_x_dir : array-like (3,)
        Direction of the target pad's edge leaving target_corner.
    target_normal : array-like (3,)
        Outward normal of the target pad (pointing away from the
        existing object's solid).
    source_corner, source_x_dir, source_normal :
        Same description, but for new_obj's own pad, expressed in
        new_obj's local coordinates (i.e. before any move). Defaults
        match "left/bottom corner at the origin, pad edge along +X, pad
        facing +Z".
    flip_normal : bool, default True
        If True (typical when mating two pads flush for a union), the
        moved pad's normal ends up opposite the target normal, so the
        two faces point at each other instead of the same way. Set
        False to make the normals point the same direction instead
        (e.g. stacking one pad on top of another).

    Returns
    -------
    piecad.Obj3d
        A new object, equal to new_obj rotated then translated into
        place.
    """
    degrees, offsets = pad_alignment(
        target_corner,
        target_x_dir,
        target_normal,
        source_corner=source_corner,
        source_x_dir=source_x_dir,
        source_normal=source_normal,
        flip_normal=flip_normal,
    )
    return new_obj.rotate(degrees).translate(offsets)


def pad_alignment_xy(
    target_corner,
    target_x_dir,
    target_y_dir,
    source_corner=(0.0, 0.0, 0.0),
    source_x_dir=(1.0, 0.0, 0.0),
    source_y_dir=(0.0, 1.0, 0.0),
):
    """
    Like `pad_alignment`, but for pads/footprints whose in-plane
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
    target_corner = np.asarray(target_corner, dtype=float)
    source_corner = np.asarray(source_corner, dtype=float)

    src_basis = _basis_from_xy(source_x_dir, source_y_dir)
    tgt_basis = _basis_from_xy(target_x_dir, target_y_dir)

    # Rotation that maps source basis vectors onto target basis vectors:
    # R @ src_basis == tgt_basis  =>  R = tgt_basis @ src_basis^T
    R = tgt_basis @ src_basis.T

    rotated_source_corner = R @ source_corner
    offsets = target_corner - rotated_source_corner

    degrees = _rotation_to_xyz_degrees(R)
    return degrees, offsets.tolist()


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
    edge direction) is used instead of `move_pad_to_pad`'s
    corner/x_dir/normal for asymmetric footprints.
    """
    source_frame = _basis_from_xy(source_x_dir, source_y_dir)
    target_frame = _basis_from_xy(target_x_dir, target_y_dir)
    return new_obj.transform(
        _rigid_transform(
            target_frame @ source_frame.T,
            source_corner,
            target_corner,
        )
    )


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

    moved = move_pad_to_pad(
        new_obj,
        target_corner=(10.0, 0.0, 0.0),
        target_x_dir=(0.0, 1.0, 0.0),
        target_normal=(1.0, 0.0, 0.0),
        source_corner=(0.0, 0.0, 0.0),
        source_x_dir=(1.0, 0.0, 0.0),
        source_normal=(0.0, 0.0, -1.0),  # new_obj's pad is its bottom face
    )

    verts, _ = moved.to_verts_and_faces()
    verts = np.asarray(verts)
    print("moved bounding box:")
    print("  min:", verts.min(axis=0))
    print("  max:", verts.max(axis=0))
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
