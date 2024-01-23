import manifold3d as _m

from ._c import _chkGT, _chkTY, _chkGE, _chkV2

from . import *

def extrude_batch(paths: list[float, Obj2d | tuple[Obj2d, Obj2d]], initial_z: float = 0.0) -> Obj3d:
    """
    Extrude multiple Obj2d into a single Obj3d.

    ALL Obj2ds MUST HAVE THE NUMBER OF POINTS.

    Input list is `[height, Obj2d]`.

    If `height` is zero then it is a zero cap. (`Obj2d` should be `None`)

    if Obj2d is a tuple of two Obj2ds, then a capped wall is made between the two Obj2d.
    """

    def calc_mid_point(path):
        x_sum = 0
        y_sum = 0
        for x, y in path:
            x_sum += x
            y_sum += y
        x_mid = x_sum/len(path)
        y_mid = y_sum/len(path)
        return (x_mid, y_mid)

    vertex_map = {}
    vertex_list = []
    def v(f):
        if f in vertex_list:
            return vertex_map[f]
        idx = len(vertex_list)
        vertex_list.append(f)
        vertex_map[f] = idx
        return idx

    triangles = []
    cur_z = initial_z

    _chkGT("initial_z", initial_z, 0)
    for i in range(1, len(paths)-1):
        if paths[i][0] == 0:
            raise ValidationError("Caps can only be the first and/or last element of paths.")
    for i in range(0, len(paths)-1):
        if type(paths[i][1]) == tuple:
            raise ValidationError("A capped wall can only be the last item in paths.")

    def add_top_zero_cap(h, shape):
        path = shape.to_polygons[0]
        x_mid, y_mid = calc_mid_point(path)

        length = len(path)
        for i in range(0, length):
            v0x, v0y = path[i]
            v1x, v1y = path[(i+1)%length]
            triangles.append((v(v0x), v(v0y), v(h)), (v(v1x), v(v1y), v(h)), (v(x_mid), v(y_mid), v(h)))

    def add_bottom_zero_cap(h, shape):
        path = shape.to_polygons[0]
        x_mid, y_mid = calc_mid_point(path)

        # Bottom caps are reversed.
        length = len(path)
        for i in range(0, length):
            v0x, v0y = path[i]
            v1x, v1y = path[(i+1)%length]
            triangles.append((v(x_mid), v(y_mid), v(h)), (v(v1x), v(v1y), v(h)), (v(v0x), v(v0y), v(h)))

    def add_top_cap(h, shape):
        path = shape.to_polygons[0]

        tris =_m.triangulate(path)
        for t in tris:
            i1, i2, i3 = t
            x1, y1  = path[i1]
            x2, y2  = path[i2]
            x3, y3  = path[i3]
            triangles.append(((v(x1), v(y1), v(h))), ((v(x2), v(y2), v(h))), ((v(x3), v(y3), v(h))))

    def add_bottom_cap(h, shape):
        path = shape.to_polygons[0]

        # Bottom caps are reversed.
        tris =_m.triangulate(path)
        for t in tris:
            i1, i2, i3 = t
            x1, y1  = path[i1]
            x2, y2  = path[i2]
            x3, y3  = path[i3]
            triangles.append(((v(x3), v(y3), v(h))), ((v(x2), v(y2), v(h))), ((v(x1), v(y1), v(h))))

    cur_idx = 0
    capped_wall = None
    if type(paths[-1])[1] == tuple:
        last = len(paths)-1
        capped_wall =  paths[-1]
    if paths[-1][0] == 0:
        last = len(paths)-1
    else:
        last = len(paths)
        capped_wall = None
    

    cur = paths[0]
    if cur[0] == 0:
        cur = paths[1]
        cur_idx = 1
        add_bottom_zero_cap(cur_z, cur)
    else:
        add_bottom_cap(cur_z, cur)

    while (cur_idx < last):
        cur = paths[cur_idx]
        h = cur[0]
        path = cur[1].to_polygons[0]

        cur_z += h
        cur_idx += 1
    
    if capped_wall != None:
        pass # LATER need to do this.
    elif paths[-1][0] == 0:
        add_top_zero_cap(cur_z, paths[-2])
    else:
        add_top_cap(cur_z, paths[-1])