from piecad import *

_height = 18.0
_descender = 4.0
_midline = 10.0
_lcline = 15.0
_width = 12.0
_midbar = _width / 2.0

_line_pos = 0

draw = {}

def draw_exclamation(f, stroke):
    global _line_pos
    h = _height * f
    w = _width * f
    ml = _midline * f
    _line_pos += stroke
    return union(
        circle(radius=stroke / 2).translate([stroke / 2, stroke / 2]),
        rectangle([stroke, h-2*stroke]).translate([0, 2 * stroke]),
    )

def draw_dquote(f, stroke):
    global _line_pos
    h = _height * f
    _line_pos += 3*stroke
    return union(
        rectangle([stroke, 2*stroke]).translate([0, h-2*stroke]),
        rectangle([stroke, 2*stroke]).translate([2*stroke, h-2*stroke]),
    )

def draw_sharp(f, stroke):
    global _line_pos
    h = _height * f
    w = _width * f
    _line_pos += w
    return union(
        rectangle([stroke, h]).translate([w/3-stroke/2, 0]),
        rectangle([stroke, h]).translate([2*w/3-stroke/2, 0]),
        rectangle([w, stroke]).translate([0, h/3-stroke/2]),
        rectangle([w, stroke]).translate([0, 2*h/3-stroke/2]),
    )

def draw_dollar(f, stroke):
    global _line_pos
    w = _width * f
    h = _height * f
    hs = _height * f * 0.80
    o_r_x = w / 2.0
    o_r_y = (hs + stroke) / 4.0
    i_r_x = o_r_x - stroke
    i_r_y = o_r_y - stroke
    s_u = -90
    e_u = 0
    s_l = 90
    e_l = 180
    _line_pos += w
    return union(
        union(
            difference(
                ellipse(radii=[o_r_x, o_r_y]).piecut(s_u, e_u),
                ellipse(radii=[i_r_x, i_r_y]).piecut(s_u, e_u),
            ).translate([o_r_x, hs - o_r_y]),
            difference(
                ellipse(radii=[o_r_x, o_r_y]).piecut(s_l, e_l),
                ellipse(radii=[i_r_x, i_r_y]).piecut(s_l, e_l),
            ).translate([o_r_x, o_r_y]),
        ).translate([0, (h-hs)/2]),
        rectangle([stroke, h]).translate([w/2-stroke/2, 0]) 
    )



def draw_percent(f, stroke):
    global _line_pos
    h = _height * f
    w = _width * f
    o_r = w/4
    i_r = o_r - stroke
    _line_pos += w
    return union(
        polygon(
            [
                [
                    (0, 0),
                    (w-stroke, h),
                    (w, h),
                    (stroke, 0),
                ]
            ]
        ),
        difference(circle(radius=o_r), circle(radius=i_r)).translate([o_r, h-o_r]),
        difference(circle(radius=o_r), circle(radius=i_r)).translate([w-o_r, o_r]),
    )

def draw_ampersand(f, stroke):
    global _line_pos
    h = _height * f
    w = _width * f
    mb = _midbar * f
    mid = h/2
    _line_pos += w
    return union(
        rectangle([stroke, h]).translate([mb, 0]),
        rectangle([w, stroke]).translate([0, mid]),
        polygon(
            [
                [
                    (mb+stroke, 0),
                    (0, mid+stroke),
                    (0, mid),
                    (mb, 0),
                ]
            ]
        ),
    )

def draw_squote(f, stroke):
    global _line_pos
    h = _height * f
    _line_pos += stroke
    return union(
        rectangle([stroke, 2*stroke]).translate([0, h-2*stroke]),
    )


def draw_lparen(f, stroke):
    global _line_pos
    h = _height * f
    w = _width * f
    r = h/2
    p = h/3
    _line_pos += p
    return difference(
        circle(radius=r).translate([r, r]),
        circle(radius=r-stroke).translate([r, r]),
        rectangle([h, h]).translate([p, 0]),
    )

def draw_rparen(f, stroke):
    # Handled by draw_lparen global _line_pos; _line_pos += p
    h = _height * f
    p = h/3
    return draw_lparen(f, stroke).rotate(180).translate([p, h])

def draw_squote(f, stroke):
    global _line_pos
    h = _height * f
    _line_pos += stroke
    return union(
        rectangle([stroke, 2*stroke]).translate([0, h-2*stroke]),
    )


def draw_lparen(f, stroke):
    global _line_pos
    h = _height * f
    w = _width * f
    r = h/2
    p = h/3
    _line_pos += p
    return difference(
        circle(radius=r).translate([r, r]),
        circle(radius=r-stroke).translate([r, r]),
        rectangle([h, h]).translate([p, 0]),
    )

def draw_rparen(f, stroke):
    # Handled by draw_lparen global _line_pos; _line_pos += p
    h = _height * f
    p = h/3
    return draw_lparen(f, stroke).rotate(180).translate([p, h])

def draw_star(f, stroke):
    global _line_pos
    h = _height * f
    w = _width * f
    mb = _midbar * f
    _line_pos += w
    return union(
        rectangle([stroke, w]).translate([-stroke/2, -w/2]),
        rectangle([stroke, w]).translate([-stroke/2, -w/2]).rotate(60),
        rectangle([stroke, w]).translate([-stroke/2, -w/2]).rotate(-60),
    ).translate([w/2, h/2])

def draw_plus(f, stroke):
    global _line_pos
    h = _height * f
    w = _width * f
    mb = _midbar * f
    mid = w/2
    _line_pos += w
    return union(
        rectangle([stroke, w]).translate([mb, stroke/2]),
        rectangle([w, stroke]).translate([stroke/2, mid]),
    ).translate([0, h-w-1.5*stroke])

def draw_dash(f, stroke):
    global _line_pos
    h = _height * f
    w = _width * f
    _line_pos += w/2
    return union(
        rectangle([w/2, stroke]).translate([0, h/2]),
    )

def draw_comma(f, stroke):
    global _line_pos
    h = _height * f
    w = _width * f
    ml = _midline * f
    _line_pos += stroke
    return union(
        circle(radius=stroke / 2).translate([stroke / 2, stroke / 2]),
        rectangle([stroke/3, stroke]).translate([stroke/2, -stroke/2]).rotate(-20)
    )

def draw_period(f, stroke):
    global _line_pos
    h = _height * f
    w = _width * f
    ml = _midline * f
    _line_pos += stroke
    return union(
        circle(radius=stroke / 2).translate([stroke / 2, stroke / 2]),
    )

def draw_slash(f, stroke):
    global _line_pos
    h = _height * f
    w = _width * f
    _line_pos += w
    return union(
        polygon(
            [
                [
                    (0, 0),
                    (w-stroke, h),
                    (w, h),
                    (stroke, 0),
                ]
            ]
        ),
    )

def draw_colon(f, stroke):
    global _line_pos
    h = _height * f
    w = _width * f
    ml = _midline * f
    _line_pos += stroke
    return union(
        circle(radius=stroke / 2).translate([stroke / 2, 2*stroke+stroke / 2]),
        circle(radius=stroke / 2).translate([stroke / 2, stroke / 2]),
    )

def draw_semicolon(f, stroke):
    global _line_pos
    h = _height * f
    w = _width * f
    ml = _midline * f
    _line_pos += stroke
    return union(
        circle(radius=stroke / 2).translate([stroke / 2, 2*stroke+stroke / 2]),
        circle(radius=stroke / 2).translate([stroke / 2, stroke / 2]),
        rectangle([stroke/3, stroke]).translate([stroke/2, -stroke/2]).rotate(-20)
    )

def draw_less_than(f, stroke):
    global _line_pos
    h = _height * f
    w = _width * f * 0.75
    _line_pos += w
    return union(
        rectangle([w, stroke]).rotate(22.5),
        rectangle([w, stroke]).rotate(-22.5),
    ).translate([0, h/2])


def draw_equals(f, stroke):
    global _line_pos
    h = _height * f
    w = _width * f * 0.75
    _line_pos += w
    return union(
        rectangle([w, stroke]).translate([0, 2*stroke]),
        rectangle([w, stroke])
    ).translate([0, h/2-stroke])

def draw_greater_than(f, stroke):
    global _line_pos
    h = _height * f
    w = _width * f * 0.75
    _line_pos += w
    return union(
        rectangle([w, stroke]).rotate(22.5),
        rectangle([w, stroke]).rotate(-22.5),
    ).translate([-w, -h/2-stroke]).rotate(180)

def draw_question(f, stroke):
    global _line_pos
    h = _height * f
    w = _width * f
    mb = _midbar * f
    o_r = w/2
    i_r = o_r - stroke
    s = 210
    e = -95
    _line_pos += w
    return union(
        difference(circle(radius=o_r), circle(radius=i_r)).piecut(s, e).translate([o_r, h-o_r]),
        rectangle([stroke, h-w]).translate([o_r-stroke/2, stroke]),
        circle(radius=stroke / 2).translate([o_r, 0]),
    )

def draw_at(f, stroke):
    global _line_pos
    w = _width * f
    o_r = w / 2
    i_r = o_r - stroke
    a_o_r = w / 4
    a_i_r = a_o_r - stroke
    _line_pos += w
    return union(
        union(
            difference(circle(radius=a_o_r), circle(radius=a_i_r)).translate([a_o_r, a_o_r]),
            rectangle([stroke, a_o_r*2]).translate([a_o_r*2 - stroke, 0]),
        ).translate([o_r-a_o_r, o_r-a_o_r]),
        difference(circle(radius=o_r), circle(radius=i_r)).translate([o_r, o_r]),
    )

def draw_lbracket(f, stroke):
    global _line_pos
    h = _height * f
    w = _width * f
    ml = _midline * f
    _line_pos += w/3
    return union(
        rectangle([w/3, stroke]).translate([0, h-stroke]),
        rectangle([stroke, h]),
        rectangle([w/3, stroke]),
    )


def draw_backslash(f, stroke):
    global _line_pos
    h = _height * f
    w = _width * f
    _line_pos += w
    return union(
        polygon(
            [
                [
                    (0, h),
                    (stroke, h),
                    (w, 0),
                    (w-stroke, 0),
                ]
            ]
        ),
    )


def draw_rbracket(f, stroke):
    global _line_pos
    h = _height * f
    w = _width * f
    ml = _midline * f
    _line_pos += w/3
    return union(
        rectangle([w/3, stroke]).translate([0, h-stroke]),
        rectangle([stroke, h]).translate([w/3-stroke, 0]),
        rectangle([w/3, stroke]).translate([0, 0]),
    )


def draw_caret(f, stroke):
    global _line_pos
    h = _height * f
    w = _width * f
    mid = w/2+stroke/2
    cs = w/2
    _line_pos += cs*0.85
    return union(
        rectangle([stroke, cs]).rotate(30+180),
        rectangle([stroke, cs]).translate([-stroke/2, stroke/2]).rotate(-30+180),
    ).translate([cs*0.5, h])

def draw_underscore(f, stroke):
    global _line_pos
    h = _height * f
    w = _width * f
    ml = _midline * f
    _line_pos += w
    return union(
        rectangle([w, stroke]),
    )

def draw_grave(f, stroke):
    global _line_pos
    h = _height * f
    _line_pos += 1.5*stroke
    return union(
        rectangle([stroke, 2*stroke]).translate([3*stroke, h-3*stroke]).rotate(20),
    )

def draw_lbrace(f, stroke):
    global _line_pos
    h = _height * f
    w = _width * f
    ml = _midline * f
    r = w/4
    _line_pos += w/3 + r
    return union(
        union(
            rectangle([w/3, stroke]).translate([0, h-stroke]),
            rectangle([stroke, h]),
            rectangle([w/3, stroke]),
        ).translate([r, 0]),
        circle(radius=r).translate([r, h/2]).piecut(-90, 90)
    )

def draw_vbar(f, stroke):
    global _line_pos
    h = _height * f
    _line_pos += stroke
    return difference(
        rectangle([stroke, h]),
        rectangle([stroke, stroke/2]).translate([0, h/2-stroke/4]),
    )

def draw_rbrace(f, stroke):
    global _line_pos
    h = _height * f
    w = _width * f
    ml = _midline * f
    r = w/4
    _line_pos += w/3 + r
    return union(
        union(
            rectangle([w/3, stroke]).translate([0, h-stroke]),
            rectangle([stroke, h]).translate([w/3-stroke, 0]),
            rectangle([w/3, stroke]).translate([0, 0]),
        ).translate([r, 0]),
        circle(radius=r).translate([w/3+r, h/2]).piecut(90, -90)
    ).translate([-r, 0])


def draw_tilde(f, stroke):
    global _line_pos
    h = _height * f
    w = _width * f
    o_r = w/4
    i_r = o_r - stroke
    _line_pos += o_r*4-stroke
    return union(
        difference(circle(radius=o_r).piecut(180, 0), circle(radius=i_r).piecut(180, 0)),
        difference(circle(radius=o_r).piecut(0, 180), circle(radius=i_r).piecut(0, 180)).translate([2*o_r-stroke, 0]),
    ).rotate(22.5).translate([o_r, h-o_r])


def draw_0(f, stroke):
    global _line_pos
    o_r_x = _width * f / 2.0
    o_r_y = _height * f / 2.0
    i_r_x = o_r_x - stroke
    i_r_y = o_r_y - stroke
    _line_pos += _width * f
    return union(
        difference(ellipse(radii=[o_r_x, o_r_y]), ellipse(radii=[i_r_x, i_r_y])),
        rectangle([stroke, _height * f], center=True).rotate(-45),
    ).translate([o_r_x, o_r_y])


def draw_1(f, stroke):
    global _line_pos
    s = stroke / 2.0
    _line_pos += _width * f
    return union(
        rectangle([stroke, _height * f]).translate([_midbar * f - s, 0]),
        rectangle([_width * f, stroke]),
        rectangle([_width * f / 2.0, stroke])
        .rotate(180 + 45)
        .translate([_midbar * f - s, _height * f]),
    )


def draw_2(f, stroke):
    global _line_pos
    o_r = _width * f / 2.0
    i_r = _width * f / 2.0 - stroke
    e = 180
    s = 0
    i = o_r * 2
    _line_pos += _width * f
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
    global _line_pos
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
    _line_pos += w
    return union(
        difference(
            ellipse(radii=[o_r_x, o_r_y]).piecut(u_e, u_s),
            ellipse(radii=[i_r_x, i_r_y]).piecut(u_e, u_s),
        ).translate([o_r_x, _height * f - o_r_y]),
        difference(
            ellipse(radii=[o_r_x, o_r_y]).piecut(l_e, l_s),
            ellipse(radii=[i_r_x, i_r_y]).piecut(l_e, l_s),
        ).translate([o_r_x, o_r_y]),
        rectangle([mb / 2, stroke]).translate([mb / 2.001, o_r_y * 2 - stroke]),
    )


def draw_4(f, stroke):
    global _line_pos
    h = _height * f
    w = _width * f
    ln = h / 4
    bar = w - w / 4
    s = stroke / 2.0
    _line_pos += w
    return union(
        polygon([[(0.0, ln + stroke), (bar - s, h), (bar + s, h), (stroke, ln)]]),
        rectangle([stroke, h]).translate([bar, 0]),
        rectangle([w, stroke]).translate([0, ln]),
    )


def draw_5(f, stroke):
    global _line_pos
    h = _height * f
    w = _width * f
    m = _midline * f
    o_r = m / 2.0
    i_r = m / 2.0 - stroke
    side = h - m
    s = 90
    e = -90
    _line_pos += w
    return union(
        rectangle([w, stroke]).translate([0, h - stroke]),
        rectangle([stroke, side]).translate([0, h - side - stroke]),
        difference(
            circle(radius=o_r).piecut(s, e), circle(radius=i_r).piecut(s, e)
        ).translate([w - o_r, o_r]),
        rectangle([w / 2 + stroke, stroke]).translate([0, 0]),
        rectangle([w / 2 + stroke, stroke]).translate([0, o_r * 2 - stroke]),
    )


def draw_6(f, stroke):
    global _line_pos
    o_r = _width * f / 2.0
    i_r = o_r - stroke
    h = _height * f
    _line_pos += _width * f
    return union(
        difference(
            circle(radius=o_r).piecut(180, 30),
            circle(radius=i_r).piecut(180, 30),
        ).translate([o_r, h - o_r]),
        difference(circle(radius=o_r), circle(radius=i_r)).translate([o_r, o_r]),
        rectangle([stroke, o_r]).translate([0, o_r]),
    )


def draw_7(f, stroke):
    global _line_pos
    h = _height * f
    w = _width * f
    off = _midbar * f / 2
    _line_pos += w
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
    global _line_pos
    w = _width * f
    h = _height * f
    o_r_x = w / 2.0
    o_r_y = (h + stroke) / 4.0
    i_r_x = o_r_x - stroke
    i_r_y = o_r_y - stroke
    _line_pos += w
    return union(
        difference(
            ellipse(radii=[o_r_x, o_r_y]), ellipse(radii=[i_r_x, i_r_y])
        ).translate([o_r_x, _height * f - o_r_y]),
        difference(
            ellipse(radii=[o_r_x, o_r_y]), ellipse(radii=[i_r_x, i_r_y])
        ).translate([o_r_x, o_r_y]),
    )


def draw_9(f, stroke):
    # Handled by draw_6 global _line_pos; _line_pos += _width * f
    return draw_6(f, stroke).rotate(180).translate([_width * f, _height * f])


def draw_A(f, stroke):
    global _line_pos
    h = _height * f
    w = 7.0 * f
    s = stroke / 2.0
    _line_pos += _width * f
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
    global _line_pos
    ml = _midline * f
    mb = _midbar * f
    w = _width * f
    h = _height * f
    o_r_t = (h - ml + stroke) / 2.0
    o_r_b = ml / 2.0
    i_r_t = o_r_t - stroke
    i_r_b = o_r_b - stroke
    t_e = 90
    t_s = -90
    b_e = 90
    b_s = -90
    _line_pos += w
    return union(
        difference(
            circle(radius=o_r_t).piecut(t_e, t_s),
            circle(radius=i_r_t).piecut(t_e, t_s),
        ).translate([w - o_r_t, h - o_r_t]),
        difference(
            circle(radius=o_r_b).piecut(b_e, b_s),
            circle(radius=i_r_b).piecut(b_e, b_s),
        ).translate([w - o_r_b, o_r_b]),
        rectangle([stroke, h]).translate([0, 0]),
        rectangle([mb, stroke]).translate([stroke, h - stroke]),
        rectangle([mb, stroke]).translate([stroke, h - 2 * o_r_t]),
        rectangle([mb, stroke]).translate([stroke, 0]),
    )


def draw_C(f, stroke):
    global _line_pos
    h = _height * f
    w = _width * f
    o_r_x = w / 2
    o_r_y = h / 2
    i_r_x = o_r_x - stroke
    i_r_y = o_r_y - stroke
    s = -40
    e = 40
    _line_pos += w
    return (
        difference(ellipse(radii=[o_r_x, o_r_y]), ellipse(radii=[i_r_x, i_r_y]))
        .translate([o_r_x, o_r_y])
        .piecut(s, e)
    )


def draw_D(f, stroke):
    global _line_pos
    h = _height * f
    w = _width * f
    o_r_x = w / 2
    o_r_y = h / 2
    i_r_x = o_r_x - stroke
    i_r_y = o_r_y - stroke
    s = 90
    e = -90
    _line_pos += w
    return union(
        difference(ellipse(radii=[o_r_x, o_r_y]), ellipse(radii=[i_r_x, i_r_y]))
        .translate([o_r_x, o_r_y])
        .piecut(s, e),
        rectangle([stroke, h]).translate([0, 0]),
        rectangle([w / 2 - stroke, stroke]).translate([stroke, h - stroke]),
        rectangle([w / 2 - stroke, stroke]).translate([stroke, 0]),
    )


def draw_E(f, stroke):
    global _line_pos
    w = _width * f
    h = _height * f
    _line_pos += w
    return union(
        rectangle([stroke, h]).translate([0, 0]),
        rectangle([w, stroke]).translate([0, h - stroke]),
        rectangle([w * 0.75, stroke]).translate([0, h / 2 - stroke]),
        rectangle([w, stroke]).translate([0, 0]),
    )


def draw_F(f, stroke):
    global _line_pos
    w = _width * f
    h = _height * f
    _line_pos += w
    return union(
        rectangle([stroke, h]).translate([0, 0]),
        rectangle([w - stroke, stroke]).translate([0, h - stroke]),
        rectangle([w - stroke, stroke]).translate([0, h / 2 - stroke]),
    )


def draw_G(f, stroke):
    global _line_pos
    h = _height * f
    w = _width * f
    o_r_x = w / 2
    o_r_y = h / 2
    i_r_x = o_r_x - stroke
    i_r_y = o_r_y - stroke
    s = 0
    e = 45
    _line_pos += w
    return union(
        difference(ellipse(radii=[o_r_x, o_r_y]), ellipse(radii=[i_r_x, i_r_y]))
        .translate([o_r_x, o_r_y])
        .piecut(s, e),
        rectangle([w / 4, stroke]).translate([3 * w / 4 - stroke, h / 2 - stroke]),
    )


def draw_H(f, stroke):
    global _line_pos
    w = _width * f
    h = _height * f
    m = _midline * f
    _line_pos += w
    return union(
        rectangle([stroke, h]).translate([0, 0]),
        rectangle([w, stroke]).translate([0, m - stroke]),
        rectangle([stroke, h]).translate([w - stroke, 0]),
    )


def draw_I(f, stroke):
    global _line_pos
    h = _height * f
    w = _width * f
    mb = _midbar * f
    bar = w / 3
    _line_pos += 2 * bar
    return union(
        rectangle([bar * 2, stroke]).translate([0, h - stroke]),
        rectangle([stroke, h]).translate([bar - stroke / 2, 0]),
        rectangle([bar * 2, stroke]).translate([0, 0]),
    )


def draw_J(f, stroke):
    global _line_pos
    h = _height * f
    w = _width * f
    mb = _midbar * f
    o_r = w / 3
    i_r = o_r - stroke
    s = 0
    e = 180
    _line_pos += 3 * o_r
    return union(
        difference(circle(radius=o_r), circle(radius=i_r))
        .piecut(s, e)
        .translate([o_r, o_r]),
        rectangle([o_r * 2, stroke]).translate([o_r - stroke / 2, h - stroke]),
        rectangle([stroke, h - o_r]).translate([2 * o_r - stroke, o_r]),
    )


def draw_K(f, stroke):
    global _line_pos
    w = _width * f
    h = _height * f
    m = _midline * f
    _line_pos += w
    return union(
        rectangle([stroke, h]).translate([0, 0]),
        polygon(
            [
                [
                    (0, m),
                    (w - stroke, h),
                    (w, h),
                    (0, m - stroke),
                ]
            ]
        ),
        polygon(
            [
                [
                    (0, m),
                    (w - stroke, 0),
                    (w, 0),
                    (0, m + stroke),
                ]
            ]
        ),
    )


def draw_L(f, stroke):
    global _line_pos
    w = _width * f
    h = _height * f
    _line_pos += w
    return union(
        rectangle([stroke, h]),
        rectangle([w, stroke]),
    )


def draw_M(f, stroke):
    global _line_pos
    h = _height * f
    w = _width * f
    m = _midbar * f
    s = stroke / 2
    _line_pos += w
    return union(
        rectangle([stroke, h]),
        polygon(
            [
                [
                    (0, h),
                    (m - s, h * 0.25),
                    (m + s, h * 0.25),
                    (stroke, h),
                ]
            ]
        ),
        polygon(
            [
                [
                    (m - s, h * 0.25),
                    (w - stroke, h),
                    (w, h),
                    (m + s, h * 0.25),
                ]
            ]
        ),
        rectangle([stroke, h]).translate([w - stroke, 0]),
    )


def draw_N(f, stroke):
    global _line_pos
    h = _height * f
    w = _width * f
    m = _midbar * f
    s = stroke / 2
    _line_pos += w
    return union(
        rectangle([stroke, h]),
        polygon(
            [
                [
                    (stroke, h),
                    (w, 0),
                    (w - stroke, 0),
                    (0, h),
                ]
            ]
        ),
        rectangle([stroke, h]).translate([w - stroke, 0]),
    )


def draw_O(f, stroke):
    global _line_pos
    o_r_x = _width * f / 2.0
    o_r_y = _height * f / 2.0
    i_r_x = o_r_x - stroke
    i_r_y = o_r_y - stroke
    _line_pos += _width * f
    return union(
        difference(ellipse(radii=[o_r_x, o_r_y]), ellipse(radii=[i_r_x, i_r_y]))
    ).translate([o_r_x, o_r_y])


def draw_P(f, stroke):
    global _line_pos
    h = _height * f
    w = _width * f
    o_r = w / 2
    i_r = o_r - stroke
    _line_pos += w
    return union(
        difference(circle(radius=o_r), circle(radius=i_r))
        .translate([o_r, h - o_r])
        .piecut(90, -90),
        rectangle([stroke, h]).translate([0, 0]),
        rectangle([w / 2 - stroke, stroke]).translate([stroke, h - stroke]),
        rectangle([w / 2 - stroke, stroke]).translate([stroke, h - 2 * o_r]),
    )


def draw_Q(f, stroke):
    global _line_pos
    h = _height * f
    w = _width * f
    m = _midline * f
    o_r_x = w / 2.0
    o_r_y = h / 2.0
    i_r_x = o_r_x - stroke
    i_r_y = o_r_y - stroke
    sh = o_r_x
    _line_pos += w
    return union(
        difference(
            ellipse(radii=[o_r_x, o_r_y]), ellipse(radii=[i_r_x, i_r_y])
        ).translate([o_r_x, o_r_y]),
        polygon(
            [
                [
                    (sh, sh),
                    (w, 0),
                    (w - stroke, 0),
                    (sh - stroke, sh),
                ]
            ]
        ),
    )


def draw_R(f, stroke):
    global _line_pos
    h = _height * f
    w = _width * f
    o_r = w / 2
    i_r = o_r - stroke
    _line_pos += w
    return union(
        difference(circle(radius=o_r), circle(radius=i_r))
        .translate([o_r, h - o_r])
        .piecut(90, -90),
        rectangle([stroke, h]).translate([0, 0]),
        rectangle([w / 2 - stroke, stroke]).translate([stroke, h - stroke]),
        rectangle([w / 2 - stroke, stroke]).translate([stroke, h - 2 * o_r]),
        polygon(
            [
                [
                    (o_r + stroke, h - o_r * 2),
                    (w, 0),
                    (w - stroke, 0),
                    (o_r, h - o_r * 2),
                ]
            ]
        ),
    )


def draw_S(f, stroke):
    global _line_pos
    w = _width * f
    h = _height * f
    o_r_x = w / 2.0
    o_r_y = (h + stroke) / 4.0
    i_r_x = o_r_x - stroke
    i_r_y = o_r_y - stroke
    s_u = -90
    e_u = 0
    s_l = 90
    e_l = 180
    _line_pos += w
    return union(
        difference(
            ellipse(radii=[o_r_x, o_r_y]).piecut(s_u, e_u),
            ellipse(radii=[i_r_x, i_r_y]).piecut(s_u, e_u),
        ).translate([o_r_x, _height * f - o_r_y]),
        difference(
            ellipse(radii=[o_r_x, o_r_y]).piecut(s_l, e_l),
            ellipse(radii=[i_r_x, i_r_y]).piecut(s_l, e_l),
        ).translate([o_r_x, o_r_y]),
    )


def draw_T(f, stroke):
    global _line_pos
    w = _width * f
    h = _height * f
    mb = _midbar * f
    s = stroke / 2.0
    _line_pos += w
    return union(
        rectangle([stroke, h]).translate([mb - s, 0]),
        rectangle([w, stroke]).translate([0, h - stroke]),
    )


def draw_U(f, stroke):
    global _line_pos
    h = _height * f
    w = _width * f
    o_r = w / 2.0
    i_r = o_r - stroke
    _line_pos += w
    return union(
        difference(
            circle(radius=o_r).piecut(0, 180), circle(radius=i_r).piecut(0, 180)
        ).translate([o_r, o_r]),
        rectangle([stroke, h - o_r]).translate([w - stroke, o_r]),
        rectangle([stroke, h - o_r]).translate([0, o_r]),
    )


def draw_V(f, stroke):
    global _line_pos
    h = _height * f
    w = _width * f
    mb = _midbar * f
    s = stroke / 2
    _line_pos += w
    return union(
        polygon(
            [
                [
                    (mb - s, 0),
                    (0, h),
                    (stroke, h),
                    (mb + s, 0),
                ]
            ]
        ),
        polygon(
            [
                [
                    (mb - s, 0),
                    (w - stroke, h),
                    (w, h),
                    (mb + s, 0),
                ]
            ]
        ),
    )


def draw_W(f, stroke):
    global _line_pos
    h = _height * f
    w = _width * f
    part = w / 4
    s = stroke / 2
    _line_pos += w
    return union(
        polygon(
            [
                [
                    (part - s, 0),
                    (0, h),
                    (stroke, h),
                    (part + s, 0),
                ]
            ]
        ),
        polygon(
            [
                [
                    (part - s, 0),
                    (part * 2 - s, h * 0.75),
                    (part * 2 + s, h * 0.75),
                    (part + s, 0),
                ]
            ]
        ),
        polygon(
            [
                [
                    (part * 2 - s, h * 0.75),
                    (part * 3 - s, 0),
                    (part * 3 + s, 0),
                    (part * 2 + s, h * 0.75),
                ]
            ]
        ),
        polygon(
            [
                [
                    (part * 3 - s, 0),
                    (w - stroke, h),
                    (w, h),
                    (part * 3 + s, 0),
                ]
            ]
        ),
    )


def draw_X(f, stroke):
    global _line_pos
    h = _height * f
    w = _width * f
    _line_pos += w
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
                    (w - stroke, 0),
                    (0, h),
                    (stroke, h),
                    (w, 0),
                ]
            ]
        ),
    )


def draw_Y(f, stroke):
    global _line_pos
    h = _height * f
    w = _width * f
    mb = _midbar * f
    ml = _midline * f
    s = stroke / 2
    _line_pos += w
    return union(
        polygon(
            [
                [
                    (mb - s, ml - stroke),
                    (0, h),
                    (stroke, h),
                    (mb + s, ml - stroke),
                ]
            ]
        ),
        polygon(
            [
                [
                    (mb - s, ml - stroke),
                    (w - stroke, h),
                    (w, h),
                    (mb + s, ml - stroke),
                ]
            ]
        ),
        rectangle([stroke, ml]).translate([mb - s, 0]),
    )


def draw_Z(f, stroke):
    global _line_pos
    h = _height * f
    w = _width * f
    _line_pos += w
    return union(
        polygon(
            [
                [
                    (0.0, stroke),
                    (w - stroke, h - stroke),
                    (w, h - stroke),
                    (stroke, stroke),
                ]
            ]
        ),
        rectangle([w, stroke]),
        rectangle([w, stroke]).translate([0, h - stroke]),
    )


def draw_a(f, stroke):
    global _line_pos
    w = _width * f
    m = _midline * f
    o_r = m / 2
    i_r = m / 2 - stroke
    _line_pos += m
    return union(
        difference(circle(radius=o_r), circle(radius=i_r)).translate([o_r, o_r]),
        rectangle([stroke, m]).translate([m - stroke, 0]),
    )


def draw_b(f, stroke):
    global _line_pos
    w = _width * f
    m = _midline * f
    ll = _lcline * f
    o_r = m / 2
    i_r = m / 2 - stroke
    _line_pos += m
    return union(
        difference(circle(radius=o_r), circle(radius=i_r)).translate([o_r, o_r]),
        rectangle([stroke, ll]),
    )


def draw_c(f, stroke):
    global _line_pos
    w = _width * f
    m = _midline * f
    ll = _lcline * f
    o_r = m / 2
    i_r = m / 2 - stroke
    s = -30
    e = 30
    _line_pos += m
    return (
        difference(circle(radius=o_r), circle(radius=i_r))
        .translate([o_r, o_r])
        .piecut(s, e)
    )


def draw_d(f, stroke):
    global _line_pos
    w = _width * f
    m = _midline * f
    ll = _lcline * f
    o_r = m / 2
    i_r = m / 2 - stroke
    _line_pos += m
    return union(
        difference(circle(radius=o_r), circle(radius=i_r)).translate([o_r, o_r]),
        rectangle([stroke, ll]).translate([m - stroke, 0]),
    )


def draw_e(f, stroke):
    global _line_pos
    w = _width * f
    m = _midline * f
    o_r = m / 2
    i_r = m / 2 - stroke
    s = -20
    e = 0
    _line_pos += m
    return union(
        difference(circle(radius=o_r), circle(radius=i_r))
        .translate([o_r, o_r])
        .piecut(s, e),
        rectangle([o_r * 2, stroke]).translate([0, o_r]),
    )


def draw_f(f, stroke):
    global _line_pos
    h = _height * f
    w = _width * f
    ml = _midline * f
    d = (h - ml) / 2
    mid = _midbar * f - stroke / 2
    o_r = w / 4
    i_r = o_r - stroke
    s = 180
    e = 45
    _line_pos += 2 * o_r
    return union(
        difference(circle(radius=o_r), circle(radius=i_r))
        .piecut(s, e)
        .translate([o_r, ml + o_r]),
        rectangle([stroke, ml + o_r]),
        rectangle([o_r * 2, stroke]).translate([-o_r / 2 - stroke / 4, ml - stroke]),
    ).translate([o_r / 2, 0])


def draw_g(f, stroke):
    global _line_pos
    w = _width * f
    m = _midline * f
    d = _descender * f
    o_r = m / 2
    i_r = m / 2 - stroke
    s = 0
    e = 200
    _line_pos += m
    return union(
        difference(circle(radius=o_r), circle(radius=i_r)).translate([o_r, o_r]),
        difference(circle(radius=o_r), circle(radius=i_r))
        .translate([m - o_r, o_r - d])
        .piecut(s, e),
        rectangle([stroke, m]).translate([m - stroke, 0]),
    )


def draw_h(f, stroke):
    global _line_pos
    w = _width * f
    m = _midline * f
    ll = _lcline * f
    o_r = m / 2
    i_r = m / 2 - stroke
    s = 180
    e = 0
    _line_pos += m
    return union(
        difference(circle(radius=o_r), circle(radius=i_r))
        .translate([o_r, o_r])
        .piecut(s, e),
        rectangle([stroke, ll]),
        rectangle([stroke, o_r]).translate([m - stroke, 0]),
    )


def draw_i(f, stroke):
    global _line_pos
    h = _height * f
    w = _width * f
    ml = _midline * f
    _line_pos += stroke
    return union(
        circle(radius=stroke / 2).translate([stroke / 2, ml + stroke]),
        rectangle([stroke, ml]).translate([0, 0]),
    )


def draw_j(f, stroke):
    global _line_pos
    h = _height * f
    w = _width * f
    ml = _midline * f
    d = (h - ml) / 2
    mid = _midbar * f - stroke / 2
    o_r = w / 4
    i_r = o_r - stroke
    s = 0
    e = 180
    _line_pos += o_r + stroke
    return union(
        difference(circle(radius=o_r), circle(radius=i_r))
        .piecut(s, e)
        .translate([-o_r + stroke, 0]),
        circle(radius=stroke / 2).translate([stroke / 2, ml + stroke]),
        rectangle([stroke, ml]).translate([0, 0]),
    ).translate([o_r, 0])


def draw_k(f, stroke):
    global _line_pos
    w = _midline * f * 0.80
    h = _midline * f
    ll = _lcline * f
    m = _midline * f / 2
    _line_pos += w
    return union(
        rectangle([stroke, ll]).translate([0, 0]),
        polygon(
            [
                [
                    (0, m),
                    (w - stroke, h),
                    (w, h),
                    (0, m - stroke),
                ]
            ]
        ),
        polygon(
            [
                [
                    (0, m),
                    (w - stroke, 0),
                    (w, 0),
                    (0, m + stroke),
                ]
            ]
        ),
    )


def draw_l(f, stroke):
    global _line_pos
    ll = _lcline * f
    _line_pos += stroke
    return union(
        rectangle([stroke, ll]).translate([0, 0]),
    )


def draw_m(f, stroke):
    global _line_pos
    m = _midline * f
    o_r = (m + 2 * stroke) / 4
    i_r = o_r - stroke
    s = 180
    e = 0
    _line_pos += m + stroke
    return union(
        difference(circle(radius=o_r), circle(radius=i_r))
        .translate([3 * o_r - stroke, m - o_r])
        .piecut(s, e),
        difference(circle(radius=o_r), circle(radius=i_r))
        .translate([o_r, m - o_r])
        .piecut(s, e),
        rectangle([stroke, m]),
        rectangle([stroke, m - o_r]).translate([o_r * 2 - stroke, 0]),
        rectangle([stroke, m - o_r]).translate([m, 0]),
    )


def draw_n(f, stroke):
    global _line_pos
    m = _midline * f
    o_r = m / 2
    i_r = m / 2 - stroke
    s = 180
    e = 0
    _line_pos += m
    return union(
        difference(circle(radius=o_r), circle(radius=i_r))
        .translate([o_r, o_r])
        .piecut(s, e),
        rectangle([stroke, m]),
        rectangle([stroke, o_r]).translate([m - stroke, 0]),
    )


def draw_o(f, stroke):
    global _line_pos
    w = _width * f
    m = _midline * f
    o_r = m / 2
    i_r = m / 2 - stroke
    _line_pos += m
    return difference(circle(radius=o_r), circle(radius=i_r)).translate([o_r, o_r])


def draw_p(f, stroke):
    global _line_pos
    w = _width * f
    m = _midline * f
    d = _descender * f
    bar = m + d
    o_r = m / 2
    i_r = m / 2 - stroke
    _line_pos += m
    return union(
        difference(circle(radius=o_r), circle(radius=i_r)).translate([o_r, o_r]),
        rectangle([stroke, bar]).translate([0, -d]),
    )


def draw_q(f, stroke):
    global _line_pos
    w = _width * f
    m = _midline * f
    d = _descender * f
    bar = m + d
    o_r = m / 2
    i_r = m / 2 - stroke
    _line_pos += m
    return union(
        difference(circle(radius=o_r), circle(radius=i_r)).translate([o_r, o_r]),
        rectangle([stroke, bar]).translate([m - stroke, -d]),
    )


def draw_r(f, stroke):
    global _line_pos
    w = _width * f
    m = _midline * f
    o_r = m / 2
    i_r = m / 2 - stroke
    _line_pos += m - stroke
    return union(
        difference(circle(radius=o_r), circle(radius=i_r))
        .translate([o_r, o_r])
        .piecut(180, 10),
        rectangle([stroke, m]),
    )


def draw_s(f, stroke):
    global _line_pos
    w = _midline * f
    h = _midline * f + stroke
    o_r_x = w / 2.0
    o_r_y = h / 4.0
    i_r_x = o_r_x - stroke
    i_r_y = o_r_y - stroke
    s_u = -90
    e_u = 10
    s_l = 90
    e_l = 190
    _line_pos += 2 * o_r_x
    return union(
        difference(
            ellipse(radii=[o_r_x, o_r_y]).piecut(s_u, e_u),
            ellipse(radii=[i_r_x, i_r_y]).piecut(s_u, e_u),
        ).translate([o_r_x, h - stroke - o_r_y]),
        difference(
            ellipse(radii=[o_r_x, o_r_y]).piecut(s_l, e_l),
            ellipse(radii=[i_r_x, i_r_y]).piecut(s_l, e_l),
        ).translate([o_r_x, o_r_y]),
    )


def draw_t(f, stroke):
    global _line_pos
    h = _height * f
    w = _width * f
    ml = _midline * f
    d = (h - ml) / 2
    mid = _midbar * f - stroke / 2
    o_r = w / 4
    i_r = o_r - stroke
    s = 10
    e = 180
    _line_pos += 2 * o_r
    return union(
        difference(circle(radius=o_r), circle(radius=i_r))
        .piecut(s, e)
        .translate([o_r, o_r]),
        rectangle([stroke, ml]).translate([0, o_r]),
        rectangle([o_r * 2, stroke]).translate([-o_r / 2 - stroke / 4, ml - stroke]),
    )


def draw_u(f, stroke):
    global _line_pos
    h = _midline * f
    w = _midline * f
    o_r = w / 2.0
    i_r = o_r - stroke
    _line_pos += w
    return union(
        difference(
            circle(radius=o_r).piecut(0, 180), circle(radius=i_r).piecut(0, 180)
        ).translate([o_r, o_r]),
        rectangle([stroke, h - o_r]).translate([w - stroke, o_r]),
        rectangle([stroke, h - o_r]).translate([0, o_r]),
        rectangle([stroke, o_r]).translate([w - stroke, 0]),
    )


def draw_v(f, stroke):
    global _line_pos
    h = _midline * f
    w = _midline * f
    mb = _midbar * f
    s = stroke / 2
    _line_pos += w
    return union(
        polygon(
            [
                [
                    (mb - s, 0),
                    (0, h),
                    (stroke, h),
                    (mb + s, 0),
                ]
            ]
        ),
        polygon(
            [
                [
                    (mb - s, 0),
                    (w - stroke, h),
                    (w, h),
                    (mb + s, 0),
                ]
            ]
        ),
    )


def draw_w(f, stroke):
    global _line_pos
    h = _midline * f
    w = _midline * f
    part = w / 4
    s = stroke / 2
    _line_pos += w
    return union(
        polygon(
            [
                [
                    (part - s, 0),
                    (0, h),
                    (stroke, h),
                    (part + s, 0),
                ]
            ]
        ),
        polygon(
            [
                [
                    (part - s, 0),
                    (part * 2 - s, h * 0.75),
                    (part * 2 + s, h * 0.75),
                    (part + s, 0),
                ]
            ]
        ),
        polygon(
            [
                [
                    (part * 2 - s, h * 0.75),
                    (part * 3 - s, 0),
                    (part * 3 + s, 0),
                    (part * 2 + s, h * 0.75),
                ]
            ]
        ),
        polygon(
            [
                [
                    (part * 3 - s, 0),
                    (w - stroke, h),
                    (w, h),
                    (part * 3 + s, 0),
                ]
            ]
        ),
    )


def draw_x(f, stroke):
    global _line_pos
    h = _midline * f
    w = _midline * f
    _line_pos += w
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
                    (w - stroke, 0),
                    (0, h),
                    (stroke, h),
                    (w, 0),
                ]
            ]
        ),
    )


def draw_y(f, stroke):
    global _line_pos
    h = _midline * f
    w = _midline * f
    mb = _midbar * f
    d = _descender * f
    s = stroke / 2
    _line_pos += w
    return union(
        polygon(
            [
                [
                    (mb - s, 0),
                    (0, h),
                    (stroke, h),
                    (mb + s, 0),
                ]
            ]
        ),
        polygon(
            [
                [
                    (mb - s - f, -d),
                    (w - stroke, h),
                    (w, h),
                    (mb + s - f, -d),
                ]
            ]
        ),
    )


def draw_z(f, stroke):
    global _line_pos
    h = _midline * f
    w = _midline * f
    _line_pos += w
    return union(
        polygon(
            [
                [
                    (0.0, stroke),
                    (w - stroke, h - stroke),
                    (w, h - stroke),
                    (stroke, stroke),
                ]
            ]
        ),
        rectangle([w, stroke]),
        rectangle([w, stroke]).translate([0, h - stroke]),
    )


draw["0"] = draw_0
draw["1"] = draw_1
draw["2"] = draw_2
draw["3"] = draw_3
draw["4"] = draw_4
draw["5"] = draw_5
draw["6"] = draw_6
draw["7"] = draw_7
draw["8"] = draw_8
draw["9"] = draw_9
draw["A"] = draw_A
draw["B"] = draw_B
draw["C"] = draw_C
draw["D"] = draw_D
draw["E"] = draw_E
draw["F"] = draw_F
draw["G"] = draw_G
draw["H"] = draw_H
draw["I"] = draw_I
draw["J"] = draw_J
draw["K"] = draw_K
draw["L"] = draw_L
draw["M"] = draw_M
draw["N"] = draw_N
draw["O"] = draw_O
draw["P"] = draw_P
draw["Q"] = draw_Q
draw["R"] = draw_R
draw["S"] = draw_S
draw["T"] = draw_T
draw["U"] = draw_U
draw["V"] = draw_V
draw["W"] = draw_W
draw["X"] = draw_X
draw["Y"] = draw_Y
draw["Z"] = draw_Z
draw["a"] = draw_a
draw["b"] = draw_b
draw["c"] = draw_c
draw["d"] = draw_d
draw["e"] = draw_e
draw["f"] = draw_f
draw["g"] = draw_g
draw["h"] = draw_h
draw["i"] = draw_i
draw["j"] = draw_j
draw["k"] = draw_k
draw["l"] = draw_l
draw["m"] = draw_m
draw["n"] = draw_n
draw["o"] = draw_o
draw["p"] = draw_p
draw["q"] = draw_q
draw["r"] = draw_r
draw["s"] = draw_s
draw["t"] = draw_t
draw["u"] = draw_u
draw["v"] = draw_v
draw["w"] = draw_w
draw["x"] = draw_x
draw["y"] = draw_y
draw["z"] = draw_z
draw["!"] = draw_exclamation
draw["\""] = draw_dquote
draw["#"] = draw_sharp
draw["$"] = draw_dollar
draw["%"] = draw_percent
draw["&"] = draw_ampersand
draw["'"] = draw_squote
draw["("] = draw_lparen
draw[")"] = draw_rparen
draw["*"] = draw_star
draw["+"] = draw_plus
draw[","] = draw_comma
draw["-"] = draw_dash
draw["."] = draw_period
draw["/"] = draw_slash
draw[":"] = draw_colon
draw[";"] = draw_semicolon
draw["<"] = draw_less_than
draw["="] = draw_equals
draw[">"] = draw_greater_than
draw["?"] = draw_question
draw["@"] = draw_at
draw["["] = draw_lbracket
draw["\\"] = draw_backslash
draw["]"] = draw_rbracket
draw["^"] = draw_caret
draw["_"] = draw_underscore
draw["`"] = draw_grave
draw["{"] = draw_lbrace
draw["|"] = draw_vbar
draw["}"] = draw_rbrace
draw["~"] = draw_tilde



def text(sz, tstr, stroke=None, inter_char_space=None):
    global _line_pos
    _line_pos = 0
    f = sz / _height
    if stroke == None:
        stroke = 2 * f
    if inter_char_space == None:
        inter_char_space = 3 * f
    l = []
    for c in tstr:
        if c == " ":
            _line_pos += _width * f / 2
        else:
            pos = _line_pos
            l.append(draw[c](f, stroke).translate([pos, 0]))
            _line_pos += inter_char_space
    return union(*l)


if __name__ == "__main__":
    sz = 6
    h = sz * 3
    s = "ASsTtUuVvWwXxYyZzA"
    s = "afiklgmnijmj"
    s = "0123456789 ABCDEFGHIJKLMNOPQRSTUVWXYZ abcdefghijklmnopqrstuvwxyz"
    s = "!\"#$%&'()*+,-./:;<=>?@[\\]|^|_|`|{|}~"
    w = (len(s) + 2) * sz
    c = text(sz, s)
    c3d = difference(cube([w, h, 3]), c.extrude(2).translate([sz, sz, 2]))
    view(c3d)
    view(c)
    save("/tmp/text.obj", c3d)
