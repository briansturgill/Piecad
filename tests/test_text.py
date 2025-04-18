import pytest
from piecad import *


def test_text():
    s = "ABCDEFGHIJKLMNOPQRSTUVWXYZ abcdefghijklmnopqrstuvwxyz"
    o = text(6, s)
    assert o.num_verts() == 2101
    assert round(o.height) == 7
    assert round(o.width) == 283
    s = "0123456789 !\"#$%&'()*+,-./:;<=>?@[\\]|^|_|`|{|}~"
    o = text(6, s)
    assert o.num_verts() == 1799
    assert round(o.height) == 7
    assert round(o.width) == 214


if __name__ == "__main__":
    l = []
    l.append("0123456789")
    l.append("!\"#$%&'()*+,-./:;<=>?@[\\]^_`{|}~")
    l.append("ABCDEFGHIJKLMNOPQRSTUVWXYZ")
    l.append("abcdefghijklmnopqrstuvwxyz")

    for sz in [3, 6, 8]:
        for s in l:
            c = text(sz, s)
            h = c.height + 2 * sz
            w = c.width + 2 * sz
            c3d = difference(cube([w, h, 3]), c.extrude(2).translate([sz, sz, 2]))
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
