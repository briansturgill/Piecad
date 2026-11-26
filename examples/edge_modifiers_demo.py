"""
Make a series of demos of the edge modifiers on a cube and a cylinder.
"""

from piecad import *


if __name__ == "__main__":
    num = 0
    for mod_type in ("bevel", "fillet", "comma", "faceted", "sawtooth"):
        flip_settings = (True, False) if mod_type == "comma" else (True,)
        for flip_on_top in flip_settings:
            for orientation, rotation in (
                ("unrotated", (0, 0, 0)),
                ("rotated", (45, 30, 50)),
            ):
                shape = cuboid((40, 60, 30))
                shape = shape.rotate(rotation)
                label = f"{mod_type} {orientation}"
                filename = f"{mod_type}_{orientation}"
                if mod_type == "comma":
                    label += f" flip_on_top={flip_on_top}"
                    filename += f"_flip_{str(flip_on_top).lower()}"
                o = shape.modify_edges(mod_type, size=6)
                if rotation == (0, 0, 0):
                    o = union(o, text(5,
                                f"{mod_type}{' '+str(flip_on_top)[0] if mod_type== 'comma' else ''}",0)
                                .extrude(2).translate((10, -20, 30)).rotate((0,0,90)))
                view(o, f"{label} difference")
                num += 1
                o = o.color("blue")
                save(f"{num}_{filename}_difference.3mf", o)

    inner_radius, outer_radius, edge_size = 10, 25, 6
    for mod_type in ("bevel", "fillet", "comma", "faceted", "sawtooth"):
        for shape_name, y_scale in (("circular", 1), ("elliptical", 1.5)):
            ring = difference(cylinder(30, outer_radius), cylinder(30, inner_radius))
            ring = ring.scale((1, y_scale, 1))
            for outward in (True, False):
                radius = outer_radius if outward else inner_radius
                radii = radius if y_scale == 1 else (radius, radius * y_scale)
                result = ring
                for height in (0, 30):
                    result = result.modify_circular_edges(
                        mod_type, (0, 0, height), radii, outward, size=edge_size
                    )
                rim = "outer" if outward else "hole"
                num += 1
                label_y = (
                    (inner_radius + outer_radius + (-edge_size if outward else edge_size))
                    / 2 * y_scale
                )
                result = union(
                    result,
                    text(4, f"{num}{mod_type[0:3].upper()}", 0).extrude(2)
                    .center((True, True, False)).translate((0, label_y, 30)),
                )
                view(result, f"{mod_type} {shape_name} {rim}")
                result = result.color("red")
                save(f"{num}_{mod_type}_{shape_name}_{rim}.3mf", result)
            #break # Skip elliptical shapes
    view_all_now()
