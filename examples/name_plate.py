from piecad import *

txt = text(10, "Brian Sturgill").rotate(-90)

x1, y1, x2, y2 = txt.bounding_box()

txt = txt.translate([-x1, -y1])

bottom = rounded_rectangle([y2 - y1, x2 - x1]).extrude(2)

txt = revolve(txt, segments=100, revolve_degrees=65).rotate([90, 180 + 65, 90])

x1, y1, z1, x2, y2, z2 = txt.bounding_box()

obj = union(txt.translate([-x1, -y1, 2]), bottom)

save("/tmp/txt.obj", obj)
