import math

from . import Config, Obj3d, ValidationError, cube, cuboid, cylinder, difference
from ._pad_align import move_pad_to_pad_xy
from .lin_math import Vec3


def _scale_vector(vector, scalar):
    return tuple(component * scalar for component in vector)


def _normalize(vector):
    length = Vec3.length(vector)
    if length < 1e-12:
        raise ValidationError("Cannot normalize a zero-length vector")
    return Vec3.normalize(vector)


def cutter(
    fillet: bool,
    v1: tuple[float, float, float],
    v2: tuple[float, float, float],
    n1: tuple[float, float, float],
    n2: tuple[float, float, float],
    radius: float,
) -> Obj3d:
    """
    Create a cutter surface: rectangular base with 1/4 cylinder on top.

    The base is a rectangle matching the bevel/fillet footprint.

    Args:
        fillet: Whether the cutter is for a fillet (True) or chamfer (False).
        v1: First endpoint of the edge.
        v2: Second endpoint of the edge.
        n1: Normal vector of the first adjacent face.
        n2: Normal vector of the second adjacent face.
        radius: Radius of the 1/4 cylinder (same as chamfer_cutter radius).

    Returns:
        An Obj3d polyhedron representing the fillet surface.
    """
    n1 = _normalize(n1)
    n2 = _normalize(n2)

    edge_dir = Vec3.sub(v2, v1)
    edge_length = Vec3.length(edge_dir)
    if edge_length < 1e-12:
        raise ValidationError("Edge endpoints must be distinct")
    edge_dir = Vec3.normalize(edge_dir)

    perp_in_f1 = Vec3.cross(edge_dir, n1)
    perp_in_f1_len = Vec3.length(perp_in_f1)
    if perp_in_f1_len > 1e-12:
        perp_in_f1 = Vec3.normalize(perp_in_f1)
    else:
        raise ValidationError("Edge is parallel to face normal 1")

    perp_in_f2 = Vec3.cross(edge_dir, n2)
    perp_in_f2_len = Vec3.length(perp_in_f2)
    if perp_in_f2_len > 1e-12:
        perp_in_f2 = Vec3.normalize(perp_in_f2)
    else:
        raise ValidationError("Edge is parallel to face normal 2")

    # Each perpendicular has two possible signs. Select the one that points
    # into the other face's half-space (opposite its outward normal), which
    # is the material side of a convex edge. This is independent of the
    # edge's orientation in world coordinates.
    if Vec3.dot(perp_in_f1, n2) > 0:
        perp_in_f1 = Vec3.neg(perp_in_f1)
    if Vec3.dot(perp_in_f2, n1) > 0:
        perp_in_f2 = Vec3.neg(perp_in_f2)

    offset1_in_f1 = _scale_vector(perp_in_f1, radius)
    offset2_in_f2 = _scale_vector(perp_in_f2, radius)

    v1_f1 = Vec3.add(v1, offset1_in_f1)
    v1_f2 = Vec3.add(v1, offset2_in_f2)
    v2_f1 = Vec3.add(v2, offset1_in_f1)

    pObjPad = v1_f1
    dir_a = Vec3.sub(v2_f1, v1_f1)  # along the edge (fillet's length)
    dir_b = Vec3.sub(v1_f2, v1_f1)  # across the edge (fillet's width)

    if fillet:
        obj = fillet_cutter(radius, edge_length)
    else:
        obj = chamfer_cutter(radius, edge_length)
    outward = Vec3.add(n1, n2)
    outward_length = Vec3.length(outward)
    if outward_length < 1e-12:
        raise ValidationError("Adjacent face normals must not be opposite")

    # The base rectangle fixes the transform's local +Z direction as
    # cross(dir_a, dir_b). If that direction is into the solid instead of
    # toward the convex edge's outward bisector, reflect the source mesh
    # across its base.
    if Vec3.dot(Vec3.cross(dir_a, dir_b), outward) < 0:
        obj = obj.mirror((0, 0, 1))

    return move_pad_to_pad_xy(obj, pObjPad, dir_a, dir_b)


def fillet_cutter(radius, height):
    segments = math.ceil(2 * radius / Config.get_layer_resolution())
    height = float(height)
    radius = float(radius)

    cb = cuboid((height, radius, radius))
    ck = (
        cylinder(radius=radius, height=height, segments=4 * segments)
        .rotate((0, 90, 0))
        .corner()
    )
    cutter = difference(cb, ck)
    cutter = cutter.rotate((-135, 0, 0)).corner()
    _, _, _, _, _, zmax = cutter.bounding_box()
    cutter = cutter.translate((0, 0, radius - zmax))
    return cutter


def chamfer_cutter(bevel_size, length):
    length = float(length)
    bevel_size = float(bevel_size)
    width = math.sqrt(bevel_size * bevel_size / 2)
    cut = cube((length, width, width))
    cut = cut.rotate((0, 0, 90))
    cut = cut.miter_cut(-45, (0, 0, 0))[0]
    cut = cut.rotate((0, 135, 0)).corner()
    cut = cut.rotate((0, 0, -90)).corner()
    cut = cut.rotate((180, 0, 0)).corner()
    _, _, _, _, _, zmax = cut.bounding_box()
    cut = cut.translate((0, 0, bevel_size - zmax))
    return cut


if __name__ == "__main__":
    from . import save, view, view_all_now

    sc = fillet_cutter(radius=1, height=10)
    print(sc.bounding_box())
    save("scraper.3mf", sc)
    view(sc)
    cut = chamfer_cutter(radius=1, length=10)
    print(cut.bounding_box())
    save("cutter.3mf", cut)
    view(cut)

    view_all_now()
