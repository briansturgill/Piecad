from piecad import *
import numpy as np


def fillet_filler(
    v1: tuple[float, float, float],
    v2: tuple[float, float, float],
    n1: tuple[float, float, float],
    n2: tuple[float, float, float],
    radius: float = 1.0,
    segs: int = 4,
) -> Obj3d:
    """
    Create a fillet surface: rectangular base with 1/4 cylinder on top.

    The base is a rectangle matching the bevel footprint. On top is a 1/4
    cylindrical surface that rounds the edge when glued to a chamfered object.

    Args:
        v1: First endpoint of the edge.
        v2: Second endpoint of the edge.
        n1: Normal vector of the first adjacent face.
        n2: Normal vector of the second adjacent face.
        radius: Radius of the 1/4 cylinder (same as chamfer_cutter radius).
        segs: Number of segments for the 1/4 cylinder arc.

    Returns:
        An Obj3d polyhedron representing the fillet surface.
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

    # The mating rectangle for the fillet's flat base is the quad
    # v1_f1 -> v2_f1 -> v2_f2 -> v1_f2, i.e. corner v1_f1 with in-plane
    # edges (v2_f1 - v1_f1) along the fillet's length and
    # (v1_f2 - v1_f1) across it. quarter_cylinder's base is *not*
    # symmetric across its length edge (the cylindrical bulge only rises
    # from one side, along local +Z = cross((1,0,0),(0,1,0))), so we
    # must match both in-plane edges explicitly (move_pad_to_pad_xy)
    # rather than a corner/x_dir/normal (whose derived in-plane "y"
    # direction has a sign ambiguity that can silently mirror the
    # footprint to the wrong side of the edge).
    #
    # v2_f1-v1_f1 always maps to local +X and v1_f2-v1_f1 to local +Y
    # (see below for why these can't be swapped/negated to fix bulge
    # direction); which side quarter_cylinder's bulge ends up on is
    # instead controlled by mirroring the source mesh itself when
    # needed.
    pObjPad = v1_f1
    dir_a = v2_f1 - v1_f1  # along the edge (fillet's length)
    dir_b = v1_f2 - v1_f1  # across the edge (fillet's width)

    # dir_a and dir_b are *both* fixed by the geometry (they must map
    # exactly onto the fillet's mating rectangle, corners v1_f1/v2_f1/
    # v1_f2/v2_f2), so cross(dir_a, dir_b) -- the direction the flat
    # rectangle's normal points -- is not a free choice; it flips
    # between edges depending on which of n1/n2 the caller happens to
    # pass first. quarter_cylinder's bulge always rises toward its own
    # local +Z (= cross(local +X, local +Y)), so simply swapping which
    # of dir_a/dir_b maps to local X vs Y would *also* swap which
    # physical corner each maps to, breaking the mating rectangle --
    # negating one of them instead just spins the cylinder 180 degrees
    # about its length axis, moving the bulge somewhere else entirely,
    # not mirroring it. What must actually flip is which side of the
    # rectangle plane quarter_cylinder's own bulge sits on, i.e. the
    # source mesh itself needs mirroring in Z for those edges (verified
    # against every edge's actual chamfer_cutter cavity via
    # intersect() overlap: this condition is the exact set of edges
    # where cross(dir_a, dir_b) points away from the missing material
    # instead of into it).
    needs_mirror = (not is_vertical and n2[2] < 0) or (
        is_vertical and n1[1] * n2[0] < 0
    )

    cy = quarter_cylinder(radius, edge_length)
    if needs_mirror:
        cy = cy.mirror((0, 0, 1))

    return move_pad_to_pad_xy(cy, pObjPad, dir_a, dir_b)


def quarter_cylinder(radius, height):
    segments = math.ceil(2*radius/Config.get_layer_resolution())
    #cyl = union(
    #    sphere(radius=radius, segments=segments).translate((0, 0, radius)),
    #    cylinder(radius=radius, height=height-2*radius, segments=segments).translate((0, 0, radius)),
    #    sphere(radius=radius, segments=segments).translate((0, 0, height-radius)),
    #).simplify(1e-12)
    height = float(height)
    radius = float(radius)
    roff = radius/2.0
    cyl = cylinder(radius=radius, height=height-2*roff, segments=segments)
    cyl = cyl.miter_cut(90, (0, 0, 0))[1]
    cyl = cyl.rotate((0, 0, 90))
    cyl = cyl.miter_cut(90, (0, 0, 0))[1]
    cyl = cyl.rotate((0, 0, -45))
    cyl = cyl.miter_cut(90, ((sin(45)*radius), 0, 0))[1]
    cyl = cyl.rotate((0, -90, 0)).corner()
    #xmin, ymin, zmin, xmax, ymax, zmax = cyl.bounding_box()
    #hf = height/(xmax - xmin)
    #cyl = cyl.scale((hf, 1, 1))
    cyl = cyl.translate((roff, 0, 0))
    return cyl


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
    degrees, offsets = pad_alignment_xy(
        target_corner,
        target_x_dir,
        target_y_dir,
        source_corner=source_corner,
        source_x_dir=source_x_dir,
        source_y_dir=source_y_dir,
    )
    return new_obj.rotate(degrees).translate(offsets)


if __name__ == "__main__":
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
    print("existing + new volume (no overlap check):", existing.volume() + moved.volume())
    view(existing)
    view(moved)
    view(union_obj)
    view_all_now()

if __name__ == "__main__":
    qc = quarter_cylinder(radius=1, height=10)
    save("quarter_cylinder.obj", qc)
    view(qc)
    view_all_now()
