"""
Make font plates testing Roboto and Hack fonts in sizes 4mm - 8mm.
"""
from piecad import *

if __name__ == "__main__":
    test_text = "012-ABCQ.abcg {/:;|}"
    sizes = [4, 5, 6, 7, 8]

    def gen_test_output(tag, fname):
        text_set_font(fname)
        l = []
        pad = 4
        thk = 2
        last_sz = sizes[0]
        off = sizes[0] / 2
        for sz in sizes:
            s = f"{tag}{sz}: {test_text}"
            c = text(sz, s, 0).translate([pad, off]).simplify(1e-2).color("red")
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
        save(f"{tag}.3mf", obj)

    gen_test_output("hack", "Hack-Regular.ttf")
    gen_test_output("robo", "Roboto-Regular.ttf")
    print("View tends to work poorly on models with large amounts of text (too many vertices).")
