"""
Use 2D stars to make a 3D star.
"""

from piecad import *
from piecad import _chkGE, _chkGT


def star3d(
    num_points: int,
    outer_radius: float,
    inner_radius: float = 0.0,
    height: float = 10.0,
) -> Obj3d:
    """
    Make a regular 3D star of a given number of points.

    If `inner_radius` is `0.0` then it will be calculated based on outer_radius.

    Stars are created with the center at `(0,0)`.
    """
    _chkGE("num_points", num_points, 3)
    _chkGT("outer_radius", outer_radius, 0.0)
    _chkGE("inner_radius", inner_radius, 0.0)
    _chkGE("height", height, 5.0)

    objs = []
    flat_height = 2
    deg_per_np = 360.0 / num_points
    ido = deg_per_np / 2.0  # inner_degree_offset

    ratio = cos(360.0 / num_points) / cos(180 / num_points)
    if inner_radius == 0.0:
        inner_radius = outer_radius * ratio

    offset = outer_radius * 0.1
    cur_height = 0
    for i in range(2):
        s = star(num_points, outer_radius, inner_radius)
        if i == 0:
            s = s.offset(-1.0, "round").offset(2.0, "round")
        s = s.extrude(flat_height).translate((0, 0, cur_height))
        objs.append(s)
        cur_height += flat_height
        outer_radius -= offset
        inner_radius -= offset * ratio

    deg = 90

    o_z = cur_height
    i_z = height

    def make_wing():
        irad = inner_radius + 2 * offset * ratio
        i_x = irad * cos(deg + ido)
        i_y = irad * sin(deg + ido)
        n_i_x = irad * cos(deg + ido + deg_per_np)
        n_i_y = irad * sin(deg + ido + deg_per_np)
        i_chord = math.sqrt((n_i_x - i_x) ** 2 + (n_i_y - i_y) ** 2)
        ic_half = i_chord / 2.0
        front_pt_low = (outer_radius, 0, o_z)
        left_pt_low = (0, -ic_half, o_z)
        right_pt_low = (0, ic_half, o_z)
        top_pt = (0, 0, i_z)
        t = tetrahedron([front_pt_low, left_pt_low, right_pt_low, top_pt])
        t = t.color("gold")
        return t

    wing = make_wing()
    for i in range(0, num_points):
        objs.append(wing.rotate((0, 0, deg)))
        deg += deg_per_np

    return union(*objs)


if __name__ == "__main__":
    Config.set_default_color("copper")
    st3d = star3d(5, 60)
    save("star_3d.3mf", st3d)
    view(st3d)
