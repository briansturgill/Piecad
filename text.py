from piecad import *

_height = 18.0
_descender = 4.0
_midline = 10.0
_lcline = 15.0
_width = 12.0
_midbar = _width / 2.0

def draw_0(f, stroke):
    o_r_x = _width * f / 2.0
    o_r_y = _height * f / 2.0
    i_r_x = o_r_x - stroke
    i_r_y = o_r_y - stroke
    return union(
        difference(ellipse(radii=[o_r_x, o_r_y]), ellipse(radii=[i_r_x, i_r_y])),
        rectangle([stroke, _height * f], center=True).rotate(-45),
    ).translate([o_r_x, o_r_y])


def draw_1(f, stroke):
    s = stroke / 2.0
    return union(
        rectangle([stroke, _height * f]).translate([_midbar * f - s, 0]),
        rectangle([_width * f, stroke]),
        rectangle([_width * f / 2.0, stroke])
        .rotate(180 + 45)
        .translate([_midbar * f - s, _height * f]),
    )


def draw_2(f, stroke):
    o_r = _width * f / 2.0
    i_r = _width * f / 2.0 - stroke
    e = 180
    s = 0
    i = o_r * 2
    return union(
        polygon(
            [
                [
                    (0.0, stroke),
                    (i - stroke, _width * f),
                    (i, _width * f),
                    (stroke, stroke),
                ]
            ]
        ),
        rectangle([_width * f, stroke]),
        difference(
            circle(radius=o_r).piecut(e, s), circle(radius=i_r).piecut(e, s)
        ).translate([o_r, _height * f - o_r]),
    )


def draw_3(f, stroke):
    w = _width * f
    h = _height * f
    mb = _midbar * f
    o_r_x = w / 2.0
    o_r_y = (h + stroke) / 4.0
    i_r_x = o_r_x - stroke
    i_r_y = o_r_y - stroke
    u_e = 180
    u_s = -90
    l_e = 90
    l_s = 180
    return union(
        difference(
            ellipse(radii=[o_r_x, o_r_y]).piecut(u_e, u_s),
            ellipse(radii=[i_r_x, i_r_y]).piecut(u_e, u_s),
        ).translate([o_r_x, _height * f - o_r_y]),
        difference(
            ellipse(radii=[o_r_x, o_r_y]).piecut(l_e, l_s),
            ellipse(radii=[i_r_x, i_r_y]).piecut(l_e, l_s),
        ).translate([o_r_x, o_r_y]),
        rectangle([mb/2, stroke]).translate([mb/2.001, o_r_y * 2 - stroke]),
    )


def draw_4(f, stroke):
    h = _height * f
    w = _width * f
    ln = h / 4
    bar = w - w / 4
    s = stroke / 2.0
    return union(
        polygon([[(0.0, ln + stroke), (bar - s, h), (bar + s, h), (stroke, ln)]]),
        rectangle([stroke, h]).translate([bar, 0]),
        rectangle([w, stroke]).translate([0, ln]),
    )


def draw_5(f, stroke):
    h = _height * f
    w = _width * f
    m = _midline * f
    o_r = m / 2.0
    i_r = m / 2.0 - stroke
    side = h - m
    s = 90
    e = -90
    return union(
        rectangle([w, stroke]).translate([0, h - stroke]),
        rectangle([stroke, side]).translate([0, h - side - stroke]),
        difference(
            circle(radius=o_r).piecut(s, e), circle(radius=i_r).piecut(s, e)
        ).translate([w-o_r, o_r]),
        rectangle([w / 2+stroke, stroke]).translate([0, 0]),
        rectangle([w / 2+stroke, stroke]).translate([0, o_r * 2 - stroke]),
    )


def draw_6(f, stroke):
    o_r = _width * f / 2.0
    i_r = o_r - stroke
    h = _height * f
    return union(
        difference(
            circle(radius=o_r).piecut(180, 30),
            circle(radius=i_r).piecut(180, 30),
        ).translate([o_r, h - o_r]),
        difference(circle(radius=o_r), circle(radius=i_r)).translate(
            [o_r, o_r]
        ),
        rectangle([stroke, o_r]).translate([0, o_r])
    )


def draw_7(f, stroke):
    h = _height * f
    w = _width * f
    off = _midbar * f / 2
    return union(
        rectangle([w, stroke]).translate([0, h - stroke]),
        polygon(
            [
                [
                    (0.0 + off, 0.0),
                    (w - stroke, h - stroke),
                    (w, h - stroke),
                    (stroke + off, 0),
                ]
            ]
        ),
    )


def draw_8(f, stroke):
    w = _width * f
    h = _height * f
    o_r_x = w / 2.0
    o_r_y = (h + stroke) / 4.0
    i_r_x = o_r_x - stroke
    i_r_y = o_r_y - stroke
    return union(
        difference(
            ellipse(radii=[o_r_x, o_r_y]), ellipse(radii=[i_r_x, i_r_y])
        ).translate([o_r_x, _height * f - o_r_y]),
        difference(
            ellipse(radii=[o_r_x, o_r_y]), ellipse(radii=[i_r_x, i_r_y])
        ).translate([o_r_x, o_r_y]),
    )


def draw_9(f, stroke):
    return draw_6(f, stroke).rotate(180).translate([_width * f, _height * f])


def draw_A(f, stroke):
    h = _height * f
    w = 7.0 * f
    s = stroke / 2.0
    return union(
        polygon(
            [
                [
                    (0.0, 0.0),
                    (_midbar * f - s, _height * f),
                    (_midbar * f + s, _height * f),
                    (stroke, 0),
                ]
            ]
        ),
        polygon(
            [
                [
                    (_width * f - stroke, 0.0),
                    (_midbar * f - s, _height * f),
                    (_midbar * f + s, _height * f),
                    (_width * f, 0),
                ]
            ]
        ),
        rectangle([w, stroke]).translate([2.5 * f, 7 * f]),
    )

def draw_B(f, stroke):
    ml = _midline * f
    mb = _midbar * f
    w = _width * f
    h = _height * f
    o_r_t = (h-ml+stroke) / 2.0
    o_r_b = ml /2.0
    i_r_t = o_r_t - stroke
    i_r_b = o_r_b - stroke
    t_e = 90
    t_s = -90
    b_e = 90
    b_s = -90
    return union(
        difference(
            circle(radius=o_r_t).piecut(t_e, t_s),
            circle(radius=i_r_t).piecut(t_e, t_s),
        ).translate([w-o_r_t, h-o_r_t]),
        difference(
            circle(radius=o_r_b).piecut(b_e, b_s),
            circle(radius=i_r_b).piecut(b_e, b_s),
        ).translate([w-o_r_b, o_r_b]),
        rectangle([stroke, h]).translate([0, 0]),
        rectangle([mb, stroke]).translate([stroke, h-stroke]),
        rectangle([mb, stroke]).translate([stroke, h-2*o_r_t]),
        rectangle([mb, stroke]).translate([stroke, 0]),
    )

def draw_C(f, stroke):
    h = _height * f
    w = _width * f
    o_r_x = w / 2
    o_r_y = h / 2
    i_r_x = o_r_x - stroke
    i_r_y = o_r_y - stroke
    s = -40
    e = 40
    return difference(ellipse(radii=[o_r_x, o_r_y]), ellipse(radii=[i_r_x, i_r_y])).translate([o_r_x, o_r_y]).piecut(s, e)

def draw_D(f, stroke):
    h = _height * f
    w = _width * f
    o_r_x = w / 2
    o_r_y = h / 2
    i_r_x = o_r_x - stroke
    i_r_y = o_r_y - stroke
    s = 90
    e = -90
    return union(
        difference(ellipse(radii=[o_r_x, o_r_y]), ellipse(radii=[i_r_x, i_r_y])).translate([o_r_x, o_r_y]).piecut(s, e),
        rectangle([stroke, h]).translate([0, 0]),
        rectangle([w/2-stroke, stroke]).translate([stroke, h-stroke]),
        rectangle([w/2-stroke, stroke]).translate([stroke, 0]),
    )

def draw_E(f, stroke):
    w = _width * f
    h = _height * f
    return union(
        rectangle([stroke, h]).translate([0, 0]),
        rectangle([w, stroke]).translate([0, h-stroke]),
        rectangle([w*0.75, stroke]).translate([0, h/2-stroke]),
        rectangle([w, stroke]).translate([0, 0]),
    )

def draw_F(f, stroke):
    w = _width * f
    h = _height * f
    return union(
        rectangle([stroke, h]).translate([0, 0]),
        rectangle([w, stroke]).translate([0, h-stroke]),
        rectangle([w, stroke]).translate([0, h/2-stroke]),
    )

def draw_O(f, stroke):
    o_r_x = _width * f / 2.0
    o_r_y = _height * f / 2.0
    i_r_x = o_r_x - stroke
    i_r_y = o_r_y - stroke
    return union(
        difference(ellipse(radii=[o_r_x, o_r_y]), ellipse(radii=[i_r_x, i_r_y]))
    ).translate([o_r_x, o_r_y])

def draw_V(f, stroke):
    h = _height * f
    w = _width * f
    mb = _midbar * f
    s = stroke/2
    return union(
        polygon(
            [
                [
                    (mb-s, 0),
                    (0, h),
                    (stroke, h),
                    (mb+s, 0),
                ]
            ]
        ),
        polygon(
            [
                [
                    (mb-s, 0),
                    (w - stroke, h),
                    (w, h),
                    (mb+s, 0),
                ]
            ]
        ),
    )

def draw_W(f, stroke):
    h = _height * f
    w = _width * f
    part = w/4
    s = stroke/2
    return union(
        polygon(
            [
                [
                    (part-s, 0),
                    (0, h),
                    (stroke, h),
                    (part+s, 0),
                ]
            ]
        ),
        polygon(
            [
                [
                    (part-s, 0),
                    (part*2-s, h/2),
                    (part*2+s, h/2),
                    (part+s, 0),
                ]
            ]
        ),
        polygon(
            [
                [
                    (part*2-s, h/2),
                    (part*3-s, 0),
                    (part*3+s, 0),
                    (part*2+s, h/2),
                ]
            ]
        ),
        polygon(
            [
                [
                    (part*3-s, 0),
                    (w - stroke, h),
                    (w, h),
                    (part*3+s, 0),
                ]
            ]
        ),
    )

def draw_X(f, stroke):
    h = _height * f
    w = _width * f
    return union(
        polygon(
            [
                [
                    (0, 0),
                    (w - stroke, h),
                    (w, h),
                    (stroke, 0),
                ]
            ]
        ),
        polygon(
            [
                [
                    (w-stroke, 0),
                    (0, h),
                    (stroke, h),
                    (w, 0),
                ]
            ]
        ),
    )

def draw_Y(f, stroke):
    h = _height * f
    w = _width * f
    mb = _midbar * f
    ml = _midline * f
    s = stroke/2
    return union(
        polygon(
            [
                [
                    (mb-s, ml - stroke),
                    (0, h),
                    (stroke, h),
                    (mb+s, ml - stroke),
                ]
            ]
        ),
        polygon(
            [
                [
                    (mb-s, ml - stroke),
                    (w - stroke, h),
                    (w, h),
                    (mb+s, ml - stroke),
                ]
            ]
        ),
        rectangle([stroke, ml]).translate([mb-s, 0])
    )


def draw_Z(f, stroke):
    h = _height * f
    w = _width * f
    return union(
        polygon(
            [
                [
                    (0.0, stroke),
                    (w - stroke, h-stroke),
                    (w, h-stroke),
                    (stroke, stroke),
                ]
            ]
        ),
        rectangle([w, stroke]),
        rectangle([w, stroke]).translate([0, h-stroke]),
    )

def draw_a(f, stroke):
    w = _width * f
    m = _midline * f
    o_r = m / 2
    i_r = m / 2 - stroke
    off = (w-m)/2.0
    return union(
        difference(circle(radius=o_r), circle(radius=i_r)).translate([o_r, o_r]),
        rectangle([stroke, m]).translate([m - stroke, 0])
    ).translate([off, 0])

def draw_b(f, stroke):
    w = _width * f
    m = _midline * f
    ll = _lcline * f
    o_r = m / 2
    i_r = m / 2 - stroke
    off = (w-m)/2.0
    return union(
        difference(circle(radius=o_r), circle(radius=i_r)).translate([o_r, o_r]),
        rectangle([stroke, ll])
    ).translate([off, 0])

def draw_c(f, stroke):
    w = _width * f
    m = _midline * f
    ll = _lcline * f
    o_r = m / 2
    i_r = m / 2 - stroke
    s = -30
    e = 30
    off = (w-m)/2.0
    return difference(circle(radius=o_r), circle(radius=i_r)).translate([o_r, o_r]).piecut(s, e).translate([off, 0])

def draw_d(f, stroke):
    w = _width * f
    m = _midline * f
    ll = _lcline * f
    o_r = m / 2
    i_r = m / 2 - stroke
    off = (w-m)/2.0
    return union(
        difference(circle(radius=o_r), circle(radius=i_r)).translate([o_r, o_r]),
        rectangle([stroke, ll]).translate([m - stroke, 0])
    ).translate([off, 0])

def draw_e(f, stroke):
    w = _width * f
    m = _midline * f
    o_r = m / 2
    i_r = m / 2 - stroke
    s = -20
    e = 0
    off = (w-m)/2.0
    return union(
        difference(circle(radius=o_r), circle(radius=i_r)).translate([o_r, o_r]).piecut(s, e),
        rectangle([o_r*2, stroke]).translate([0, o_r])
    ).translate([off, 0])

def draw_f(f, stroke):
    h = _height * f
    w = _width * f
    ml = _midline * f
    d = (h - ml) / 2
    mid = _midbar * f - stroke/2
    o_r = w / 4
    i_r = o_r - stroke
    s = 180
    e = 45
    off = (w-o_r)/2.0
    print(w, off)
    return union(
        difference(circle(radius=o_r), circle(radius=i_r)).piecut(s, e).translate([o_r, ml+o_r]),
        rectangle([stroke, ml+o_r]),
        rectangle([o_r*2, stroke]).translate([-o_r/2-stroke/2, ml-stroke])
    ).translate([off, 0])

def draw_o(f, stroke):
    w = _width * f
    m = _midline * f
    o_r = m / 2
    i_r = m / 2 - stroke
    off = (w-m)/2.0
    return difference(circle(radius=o_r), circle(radius=i_r)).translate([o_r+off, o_r])

def draw_v(f, stroke):
    h = _midline * f
    w = _midline * f
    mb = _midbar * f
    s = stroke/2
    off = (_width * f - _midline*f)/2.0
    return union(
        polygon(
            [
                [
                    (mb-s, 0),
                    (0, h),
                    (stroke, h),
                    (mb+s, 0),
                ]
            ]
        ),
        polygon(
            [
                [
                    (mb-s, 0),
                    (w - stroke, h),
                    (w, h),
                    (mb+s, 0),
                ]
            ]
        ),
    ).translate([off, 0])

def draw_w(f, stroke):
    h = _midline * f
    w = _midline * f
    part = w/4
    s = stroke/2
    off = (_width * f - _midline*f)/2.0
    return union(
        polygon(
            [
                [
                    (part-s, 0),
                    (0, h),
                    (stroke, h),
                    (part+s, 0),
                ]
            ]
        ),
        polygon(
            [
                [
                    (part-s, 0),
                    (part*2-s, h/2),
                    (part*2+s, h/2),
                    (part+s, 0),
                ]
            ]
        ),
        polygon(
            [
                [
                    (part*2-s, h/2),
                    (part*3-s, 0),
                    (part*3+s, 0),
                    (part*2+s, h/2),
                ]
            ]
        ),
        polygon(
            [
                [
                    (part*3-s, 0),
                    (w - stroke, h),
                    (w, h),
                    (part*3+s, 0),
                ]
            ]
        ),
    ).translate([off, 0])

def draw_x(f, stroke):
    h = _midline * f
    w = _midline * f
    off = (_width * f - _midline*f)/2.0
    return union(
        polygon(
            [
                [
                    (0, 0),
                    (w - stroke, h),
                    (w, h),
                    (stroke, 0),
                ]
            ]
        ),
        polygon(
            [
                [
                    (w-stroke, 0),
                    (0, h),
                    (stroke, h),
                    (w, 0),
                ]
            ]
        ),
    ).translate([off, 0])

def draw_y(f, stroke):
    h = _midline * f
    w = _midline * f
    mb = _midbar * f
    d = _descender * f
    s = stroke/2
    off = (_width * f - _midline*f)/2.0
    return union(
        polygon(
            [
                [
                    (mb-s, 0),
                    (0, h),
                    (stroke, h),
                    (mb+s, 0),
                ]
            ]
        ),
        polygon(
            [
                [
                    (mb-s-f, -d),
                    (w - stroke, h),
                    (w, h),
                    (mb+s-f, -d),
                ]
            ]
        ),
    ).translate([off, 0])


def draw_z(f, stroke):
    h = _midline * f
    w = _midline * f
    off = (_width * f - _midline*f)/2.0
    return union(
        polygon(
            [
                [
                    (0.0, stroke),
                    (w - stroke, h-stroke),
                    (w, h-stroke),
                    (stroke, stroke),
                ]
            ]
        ),
        rectangle([w, stroke]),
        rectangle([w, stroke]).translate([0, h-stroke]),
    ).translate([off, 0])

_draw = {}
_draw["0"] = draw_0
_draw["1"] = draw_1
_draw["2"] = draw_2
_draw["3"] = draw_3
_draw["4"] = draw_4
_draw["5"] = draw_5
_draw["6"] = draw_6
_draw["7"] = draw_7
_draw["8"] = draw_8
_draw["9"] = draw_9
_draw["A"] = draw_A
_draw["B"] = draw_B
_draw["C"] = draw_C
_draw["D"] = draw_D
_draw["E"] = draw_E
_draw["F"] = draw_F
_draw["O"] = draw_O
_draw["V"] = draw_V
_draw["W"] = draw_W
_draw["X"] = draw_X
_draw["Y"] = draw_Y
_draw["Z"] = draw_Z
_draw["a"] = draw_a
_draw["b"] = draw_b
_draw["c"] = draw_c
_draw["d"] = draw_d
_draw["e"] = draw_e
_draw["f"] = draw_f
_draw["o"] = draw_o
_draw["v"] = draw_v
_draw["w"] = draw_w
_draw["x"] = draw_x
_draw["y"] = draw_y
_draw["z"] = draw_z


def text(sz, tstr, stroke=0.6):
    char_space = 0
    l = []
    for c in tstr:
        if c == " ":
            char_space += _width*f/2
        else:
            f = sz / _height
            l.append(_draw[c](f, stroke).translate([char_space, 0]))
            char_space += (_width + 2) * f
    return union(*l)


if __name__ == "__main__":
    sz = 6
    h = sz * 3
    s = "0123456789 AaBbCcDdEeFfDFOo"
    s = "AVvWwXxYyZzA"
    w = (len(s) + 2) * sz
    c = text(sz, s, 0.6)
    c3d = difference(cube([w, h, 3]), c.extrude(2).translate([sz, sz, 2]))
    view(c3d)
    view(c)
    save("/tmp/text.obj", c3d)
