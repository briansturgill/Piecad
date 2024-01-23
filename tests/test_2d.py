import pytest
from piecad import *


def _polygon(pts):
    o = polygon(pts)
    o.mo.num_vert()
    return o


def _star(np, r):
    o = star(np, r)
    o.mo.num_vert()
    return o


def _square(s):
    o = square(s)
    o.mo.num_vert()
    return o


def _rectangle(t):
    o = rectangle(t)
    o.mo.num_vert()
    return o


def _rounded_rectangle(t, r, s):
    o = rounded_rectangle(t, r, s)
    o.mo.num_vert()
    return o


def _ellipse(r, s):
    c = ellipse(r, s)
    c.mo.num_vert()
    return c


def _circle(r, s):
    c = circle(r, s)
    c.mo.num_vert()
    return c


def test_circle_10(benchmark):
    o = benchmark(_circle, 3, 10)
    assert o.mo.num_vert() == 10


def test_circle_100(benchmark):
    o = benchmark(_circle, 3, 100)
    assert o.mo.num_vert() == 100


def test_ellipse_10(benchmark):
    o = benchmark(_ellipse, (3, 12), 10)
    assert o.mo.num_vert() == 10


def test_ellipse_100(benchmark):
    o = benchmark(_ellipse, (3, 12), 100)
    assert o.mo.num_vert() == 100


def test_square(benchmark):
    o = benchmark(_square, 10)
    assert o.mo.num_vert() == 4


def test_rectangle(benchmark):
    o = benchmark(_rectangle, [10, 10])
    assert o.mo.num_vert() == 4


def test_rectangle2(benchmark):
    o = benchmark(_rectangle, (10, 10))  # Check list vs tuple
    assert o.mo.num_vert() == 4


def test_rounded_rectangle(benchmark):
    o = benchmark(_rounded_rectangle, (10, 10), 2.0, 36)
    assert o.mo.num_vert() == 40


def test_star(benchmark):
    o = benchmark(_star, 5, 20)
    assert o.mo.num_vert() == 10

# For this last 2 functions, we are trying to see if winding makes a speed difference
pts = [[-0.2       ,  0.        ],
       [-0.19696155, -0.03472964],
       [-0.18793853, -0.06840403],
       [-0.17320508, -0.1       ],
       [-0.1532089 , -0.12855752],
       [-0.12855752, -0.1532089 ],
       [-0.1       , -0.17320508],
       [-0.06840403, -0.18793853],
       [-0.03472964, -0.19696155],
       [ 0.        , -0.2       ],
       [10.        , -0.2       ],
       [10.03473   , -0.19696155],
       [10.068404  , -0.18793853],
       [10.1       , -0.17320508],
       [10.128557  , -0.1532089 ],
       [10.153209  , -0.12855752],
       [10.173205  , -0.1       ],
       [10.187939  , -0.06840403],
       [10.196961  , -0.03472964],
       [10.2       ,  0.        ],
       [10.2       , 10.        ],
       [10.196961  , 10.03473   ],
       [10.187939  , 10.068404  ],
       [10.173205  , 10.1       ],
       [10.153209  , 10.128557  ],
       [10.128557  , 10.153209  ],
       [10.1       , 10.173205  ],
       [10.068404  , 10.187939  ],
       [10.03473   , 10.196961  ],
       [10.        , 10.2       ],
       [ 0.        , 10.2       ],
       [-0.03472964, 10.196961  ],
       [-0.06840403, 10.187939  ],
       [-0.1       , 10.173205  ],
       [-0.12855752, 10.153209  ],
       [-0.1532089 , 10.128557  ],
       [-0.17320508, 10.1       ],
       [-0.18793853, 10.068404  ],
       [-0.19696155, 10.03473   ],
       [-0.2       , 10.        ]]

def test_polygon(benchmark):
    c = benchmark(_polygon, pts)

def test_polygon_rev(benchmark):
    rev = pts.reverse()
    c = benchmark(_polygon, pts)