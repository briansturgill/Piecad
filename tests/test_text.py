import pytest
from piecad import *


def test_text():
    s = "ABCDEFGHIJKLMNOPQRSTUVWXYZ abcdefghijklmnopqrstuvwxyz"
    o = text(6, s)
    assert o.num_verts() == 22865
    s = "0123456789 !\"#$%&'()*+,-./:;<=>?@[\\]|^|_|`|{|}~"
    o = text(6, s)
    assert o.num_verts() == 20551


if __name__ == "__main__":
    test_text = "012-ABCQ.abcg {/:;|}"
    sizes = [3, 4, 5, 6, 8, 10]

    def gen_test_output(tag, fname):
        text_set_font(fname)
        l = []
        pad = 4
        thk = 2
        last_sz = sizes[0]
        off = sizes[0] / 2
        for sz in sizes:
            s = f"{tag}{sz}: {test_text}"
            c = text(sz, s).translate([pad, off])
            l.append(c)
            off += last_sz + sz
            last_sz = sz
        txt3d = union(*l).extrude(thk)
        x1, y1, z1, x2, y2, z2 = txt3d.bounding_box()
        h = y2 - y1
        w = x2 - x1
        obj = union(
            difference(
                rounded_rectangle([w + pad * 4, h + pad * 4], 3).extrude(2 * thk),
                rounded_rectangle([w + pad * 2, h + pad * 2], 3)
                .extrude(thk)
                .translate([pad, pad, thk]),
            ),
            txt3d.translate([pad, 2 * pad, thk]),
        )
        view(obj)
        save(f"/tmp/{tag}.obj", obj)

    gen_test_output("hack", "Hack-Regular.ttf")
    gen_test_output("robo", "Roboto-Regular.ttf")
