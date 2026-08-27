"""
Use 2D stars to make a 3D star.
"""

from piecad import *
from piecad import _chkGE, _chkGT
import math


def star3d(
    num_points: int, outer_radius: float, inner_radius: float = 0.0, height: float = 6.0
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
    pts = []
    i_pts = []
    o_pts = []
    flat_height = 1
    deg_per_np = 360.0 / num_points
    ido = deg_per_np / 2.0  # inner_degree_offset

    ratio = cos(360.0 / num_points) / cos(180 / num_points)
    if inner_radius == 0.0:
        inner_radius = outer_radius * ratio

    offset = outer_radius * 0.1
    cur_height = 0
    for i in range(3):
        objs.append(
            star(num_points, outer_radius, inner_radius)
            .extrude(flat_height)
            .translate((0, 0, cur_height))
        )
        cur_height += flat_height
        outer_radius -= offset
        inner_radius -= offset * ratio

    cyl = cylinder(
        radius=inner_radius, height=height - cur_height, segments=36 * 3
    ).translate((0, 0, cur_height))
    objs.append(cyl)
    objs.append(
        star(num_points, inner_radius * 0.6, (inner_radius * 0.6) * ratio)
        .extrude(flat_height)
        .translate((0, 0, height))
    )

    faces = []
    verts = []
    vert_map = {}

    def add_face(v1, v2, v3):
        for v in [v1, v2, v3]:
            if v not in vert_map:
                vert_map[v] = len(verts)
                verts.append(v)
        faces.append([vert_map[v1], vert_map[v2], vert_map[v3]])

    deg = 90

    o_z = cur_height
    i_z = height
    o_x = outer_radius * cos(deg + ido)
    o_y = outer_radius * sin(deg + ido)
    i_x = inner_radius * cos(deg + ido)
    i_y = inner_radius * sin(deg + ido)
    n_i_x = inner_radius * cos(deg + ido + deg_per_np)
    n_i_y = inner_radius * sin(deg + ido + deg_per_np)

    def make_wing():
        irad = inner_radius - offset * ratio
        i_x = irad * cos(deg + ido)
        i_y = irad * sin(deg + ido)
        n_i_x = irad * cos(deg + ido + deg_per_np)
        n_i_y = irad * sin(deg + ido + deg_per_np)
        ext = 0.6
        i_chord = math.sqrt((n_i_x - i_x) ** 2 + (n_i_y - i_y) ** 2)
        ic_half = i_chord / 2.0
        front_pt_low = (outer_radius, 0, o_z)
        front_pt_high = (outer_radius, 0, o_z + flat_height)
        left_pt_low = (irad, -ic_half, o_z)
        left_pt_high = (irad, -ic_half, i_z)
        right_pt_low = (irad, ic_half, o_z)
        right_pt_high = (irad, ic_half, i_z)
        add_face(front_pt_low, left_pt_low, right_pt_low)
        add_face(front_pt_high, right_pt_high, left_pt_high)
        add_face(front_pt_low, right_pt_low, front_pt_high)
        add_face(front_pt_high, left_pt_low, front_pt_low)
        add_face(front_pt_high, right_pt_low, right_pt_high)
        add_face(front_pt_high, left_pt_high, left_pt_low)
        add_face(left_pt_low, left_pt_high, right_pt_high)
        add_face(left_pt_low, right_pt_high, right_pt_low)
        return polyhedron(vertices=verts, faces=faces)

    wing = make_wing()
    for i in range(0, num_points):
        objs.append(wing.rotate((0, 0, deg)))
        deg += deg_per_np

    return union(*objs)


st3d = star3d(5, 60)
save("star_3d.obj", st3d)
view(st3d)
