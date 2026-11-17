import pytest

from piecad import (
    Obj2d,
    circle,
    ellipse,
    rectangle,
    rounded_rectangle,
    square,
    star,
)


@pytest.mark.parametrize(
    "make",
    [
        pytest.param(lambda: circle(0), id="circle"),
        pytest.param(lambda: ellipse((0, 1)), id="ellipse-zero-x-radius"),
        pytest.param(lambda: ellipse((1, 0)), id="ellipse-zero-y-radius"),
        pytest.param(lambda: square(0), id="square"),
        pytest.param(lambda: rectangle((0, 1)), id="rectangle-zero-width"),
        pytest.param(lambda: rectangle((1, 0)), id="rectangle-zero-height"),
        pytest.param(
            lambda: rounded_rectangle((0, 1)), id="rounded-rectangle-zero-width"
        ),
        pytest.param(
            lambda: rounded_rectangle((1, 0)), id="rounded-rectangle-zero-height"
        ),
        pytest.param(lambda: star(5, 0), id="star"),
    ],
)
def test_zero_size_2d_primitives_are_empty_obj2d(make):
    obj = make()

    assert isinstance(obj, Obj2d)
    assert obj.is_empty()
    assert obj.area() == 0.0
