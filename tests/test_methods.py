import pytest
from piecad import *


def _offset(o, d, jt):
    o = o.offset(d, jt)
    o.num_verts()
    return o


def test_version():
    assert type(version()) == str


def test_set_default_segments():
    cur = config["DefaultSegments"]
    assert cur == 36
    set_default_segments(40)
    cur = config["DefaultSegments"]
    assert cur == 40
    rr = rounded_rectangle((10, 15), 1.0)
    assert rr.num_verts() == 44
    set_default_segments(36)


def test_bounding_box_2d():
    c = circle(3)
    assert c.bounding_box() == (-3, -3, 3, 3)


def test_bounding_box_3d():
    c = cube(3)
    assert c.bounding_box() == (0, 0, 0, 3, 3, 3)


def test_center_3d():
    rr = rounded_rectangle((10, 20), 4).extrude(2)
    rr = rr.translate((3, 6, 20))
    assert rr.bounding_box() == (3.0, 6.0, 20.0, 13.0, 26.0, 22.0)
    rr = rr.center((False, True, True))
    assert rr.bounding_box() == (3.0, -10.0, -1.0, 13.0, 10.0, 1.0)


def test_center_2d():
    rr = rounded_rectangle((10, 20), 4)

    rr = rr.translate((3, 6))
    assert rr.bounding_box() == (3.0, 6.0, 13.0, 26.0)
    rr = rr.center((False, True), at=(1, 1))
    assert rr.bounding_box() == (3.0, -9.0, 13.0, 11.0)


def test_color_string_2d():
    c = circle(2).color("orange")
    assert c._color == (255, 165, 0)


def test_color_hex_2d():
    c = circle(2).color("#FF00FF")
    assert c._color == (255, 0, 255)


def test_color_rgb_2d():
    c = circle(2).color((255, 0, 255))
    assert c._color == (255, 0, 255)


def test_color_string_3d():
    c = cube(2).color("orange")
    assert c._color == (255, 165, 0)


def test_color_hex_3d():
    c = cube(2).color("#FF00FF")
    assert c._color == (255, 0, 255)


def test_color_rgb_3d():
    c = cube(2).color((255, 0, 255))
    assert c._color == (255, 0, 255)


def test_is_empty_2d():
    o = Obj2d()
    assert o.is_empty()


def test_is_empty_3d():
    o = Obj3d()
    assert o.is_empty()


def test_offset(benchmark):
    rr = rounded_rectangle((10, 10), 2.0, 36)
    c = benchmark(_offset, rr, 2, "round")
    assert c.num_verts() == 100


def test_mirror_2d():
    r = rectangle((5, 10)).translate((3, 3)).rotate(45)
    verts = r.num_verts()
    assert verts == r.mirror((True, False)).num_verts()
    assert verts == r.mirror((False, True)).num_verts()
    assert verts == r.mirror((True, True)).num_verts()


def test_mirror_3d():
    r = cuboid((5, 10, 15)).translate((3, 3, 3)).rotate((45, 0, 0))
    verts = r.num_verts()
    assert verts == r.mirror((True, False, False)).num_verts()
    assert verts == r.mirror((False, True, False)).num_verts()
    assert verts == r.mirror((True, True, False)).num_verts()
    assert verts == r.mirror((True, False, True)).num_verts()
    assert verts == r.mirror((False, True, True)).num_verts()
    assert verts == r.mirror((True, True, True)).num_verts()


def test_num_faces_3d():
    c = cube(2)
    assert c.num_faces() == 12


def test_num_verts_2d():
    s = square(2)
    assert s.num_verts() == 4


def test_num_verts_3d():
    c = cube(2)
    assert c.num_verts() == 8


def test_piecut_2d():
    s = square(5).piecut(1, 20)
    assert s.num_verts() == 7
    assert s.bounding_box() == (0, 0, 5, 5)


def test_piecut_2d_neg():
    s = square(5).piecut(-90, 20)
    assert s.num_verts() == 6
    assert s.bounding_box() == (0, 0, 5, 5)


def test_piecut_3d():
    c = cube(5).piecut(-1, 20)
    assert c.num_verts() == 12


def test_piecut_3d():
    c = cube(5).piecut(-90, 20)
    assert c.num_verts() == 12
    assert c.bounding_box() == (0, 0, 0, 5, 5, 5)


def test_project():
    c = cube(4)
    o = c.project()
    assert o.bounding_box() == (0, 0, 4, 4)


def test_slice():
    c = cube(4)
    o = c.slice(2)
    assert o.bounding_box() == (0, 0, 4, 4)


def test_split():
    c = cube(4)
    cut = cube(4).translate((2, 0, 0))
    o1, o2 = c.split(cut)
    assert o1.bounding_box() == (2.0, 0.0, 0.0, 4.0, 4.0, 4.0)
    assert o2.bounding_box() == (0.0, 0.0, 0.0, 2.0, 4.0, 4.0)


def test_transfrom_2d():
    c = circle(2)
    c2 = c.transform([[1, 0, 0], [0, 1, 0]])
    assert c2.num_verts() == c2.num_verts()


def test_transfrom_3d():
    c = cube(2)
    c2 = c.transform([[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0]])
    assert c2.num_verts() == c2.num_verts()
