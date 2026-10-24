"""
Make a sign.
"""

from piecad import *

if __name__ == "__main__":
    sign_text = "NO SOLICITING"

    def gen_test_output(tag, fname):
        text_set_font(fname)
        l = []
        pad = 4
        thk = 2
        sz = 20
        s = f"{sign_text}"
        txt_3d = (
            text(sz, s, 0).simplify(1e-3).translate([pad, 4]).extrude(thk).color("gold")
        )
        x1, y1, z1, x2, y2, z2 = txt_3d.bounding_box()
        h = y2 - y1
        w = x2 - x1
        obj = union(
            difference(
                union(
                    rounded_rectangle([w + 4 + pad * 4, h + 4 + pad * 4], 4)
                    .extrude(thk)
                    .color("red"),
                    rounded_rectangle([w + 4 + pad * 4, h + 4 + pad * 4], 4)
                    .extrude(2 * thk)
                    .translate((0, 0, thk))
                    .color("gold"),
                ),
                rounded_rectangle([w + pad * 4, h + pad * 4], 2)
                .extrude(2 * thk)
                .translate((2, 2, thk)),
            ),
            txt_3d.translate([pad, 1.5 * pad, thk]),
        )
        save(f"{tag}.3mf", obj)

    gen_test_output("sign", "Roboto-Regular.ttf")
    print(
        "View tends to work poorly on models with large amounts of text (too many vertices)."
    )
