import pytest
from piecad import *


def test_text():
    s = "ABCDEFGHIJKLMNOPQRSTUVWXYZ abcdefghijklmnopqrstuvwxyz"
    o = text(6, s)
    assert o.num_verts() == 24065
    s = "0123456789 !\"#$%&'()*+,-./:;<=>?@[\\]|^|_|`|{|}~"
    o = text(6, s)
    assert o.num_verts() == 21390


if __name__ == "__main__":
    l = []
    l.append("0123456789")
    l.append("!\"#$%&'()*+,-./:;<=>?@[\\]^_`{|}~")
    l.append("ABCDEFGHIJKLMNOPQRSTUVWXYZ")
    l.append("abcdefghijklmnopqrstuvwxyz")

    for sz in [3, 4, 5, 6, 8, 10]:
        for s in l:
            c = text(sz, s)
            pad = 2
            x1, y1, x2, y2 = c.bounding_box()
            h = (y2 - y1) + 4 * pad
            w = (x2 - x1) + 4 * pad
            obj = rounded_rectangle([w, h], 2).extrude(2).translate([0, 0, -3])
            c3d = sunken_text(obj, sz, s, pad=pad)
            view(c3d)
            if s[0] == "A":
                n = "U"
            elif s[0] == "a":
                n = "l"
            elif s[0] == "!":
                n = "S"
            else:
                n = "d"
            save(f"/tmp/text_{sz}_{n}.obj", c3d)
