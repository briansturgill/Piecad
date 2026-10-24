import pytest
from piecad import *
from piecad import _text as _text_module

ALPHA = "ABCDEFGHIJKLMNOPQRSTUVWXYZ abcdefghijklmnopqrstuvwxyz"
PUNCT = "0123456789 !\"#$%&'()*+,-./:;<=>?@[\\]|^|_|`|{|}~"


@pytest.fixture(autouse=True)
def default_font():
    text_set_font("Roboto-Regular.ttf")
    yield
    text_set_font("Roboto-Regular.ttf")


def test_text():
    # Vertex counts depend on curve flattening; allow a small tolerance.
    assert text(6, ALPHA).num_verts() == pytest.approx(22904, rel=0.02)
    assert text(6, PUNCT).num_verts() == pytest.approx(20594, rel=0.02)


@pytest.mark.parametrize("s", ["A", "H", "x", "8", "Hello, World!"])
def test_text_nonempty(s):
    o = text(6, s)
    assert not o.is_empty()
    assert o.area() > 0


@pytest.mark.parametrize("c", [chr(i) for i in range(33, 127)])
def test_text_printable_ascii(c):
    assert not text(6, c).is_empty()


@pytest.mark.parametrize("size", [3, 6, 10.5])
def test_text_cap_height_matches_size(size):
    x1, y1, x2, y2 = text(size, "H").bounding_box()
    assert y1 == pytest.approx(0)
    assert y2 == pytest.approx(size)


def test_text_scales_linearly():
    a = text(6, "Hello").bounding_box()
    b = text(12, "Hello").bounding_box()
    for u, v in zip(a, b):
        assert v == pytest.approx(2 * u)


def test_text_descender_below_baseline():
    assert text(6, "g").bounding_box()[1] < 0
    assert text(6, "H").bounding_box()[1] == pytest.approx(0)


def test_text_width_grows_with_length():
    w = []
    for s in ["H", "HH", "HHH"]:
        x1, _, x2, _ = text(6, s).bounding_box()
        w.append(x2 - x1)
    assert w[0] < w[1] < w[2]


def test_text_repeated_chars_evenly_spaced():
    w1 = text(6, "H").bounding_box()
    w2 = text(6, "HH").bounding_box()
    w3 = text(6, "HHH").bounding_box()
    assert (w3[2] - w2[2]) == pytest.approx(w2[2] - w1[2])


def test_text_glyph_holes():
    # "O" is a ring: 2 contours, and its area is less than its bounding box.
    o = text(6, "O")
    assert len(o.to_paths()) == 2
    x1, y1, x2, y2 = o.bounding_box()
    assert o.area() < (x2 - x1) * (y2 - y1)


def test_text_no_overlaps_between_contours():
    # Overlapping contours must be merged (non-zero fill): the area of
    # a glyph equals the area of its extrusion footprint.
    o = text(6, "g")
    assert o.extrude(1).volume() == pytest.approx(o.area())


def test_text_underscore_below_baseline():
    o = text(6, "_")
    x1, y1, x2, y2 = o.bounding_box()
    assert y2 - y1 == pytest.approx(6)


def test_flatten_cubic_segment_and_close_contour():
    paths = _text_module._flatten_segments(
        [
            ("moveTo", (0, 0)),
            ("curveTo", ((0, 20), (20, 20), (20, 0))),
            ("closePath", ()),
        ]
    )

    assert len(paths) == 1
    assert len(paths[0]) > 4
    assert paths[0][0] == paths[0][-1] == (0, 0)
    assert max(y for _, y in paths[0]) > 0


def test_flatten_segments_close_open_contours():
    paths = _text_module._flatten_segments(
        [
            ("moveTo", (0, 0)),
            ("lineTo", (4, 0)),
            ("moveTo", (10, 10)),
            ("lineTo", (14, 10)),
        ]
    )

    assert paths == [
        [(0, 0), (4, 0), (0, 0)],
        [(10, 10), (14, 10), (10, 10)],
    ]


@pytest.mark.parametrize("s", ["", " ", "   "])
def test_text_blank_is_empty(s):
    assert text(6, s).is_empty()


def test_text_inter_char_space():
    def width(ics):
        x1, _, x2, _ = text(6, "HH", inter_char_space=ics).bounding_box()
        return x2 - x1

    assert width(3) - width(1) == pytest.approx(2)
    assert width(0) < width(None) < width(5)


def test_text_default_inter_char_space_is_size_over_3():
    assert text(6, "HH").bounding_box() == pytest.approx(
        text(6, "HH", inter_char_space=2).bounding_box()
    )


def test_text_set_font_changes_output():
    a = text(6, "Hello").bounding_box()
    text_set_font("Hack-Regular.ttf")
    b = text(6, "Hello").bounding_box()
    assert a != b


def test_text_set_font_path():
    from importlib import resources
    import piecad

    by_name = text(6, "Hello").bounding_box()
    path = str(resources.files(piecad._fonts) / "Roboto-Regular.ttf")
    text_set_font(path)
    assert text(6, "Hello").bounding_box() == pytest.approx(by_name)


def test_text_set_font_missing_file():
    with pytest.raises(Exception):
        text_set_font("no-such-font.ttf")
