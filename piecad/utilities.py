"""
## Miscellaneous (but important) functions
"""

import atexit
import http.client
import json
import queue
import threading
import manifold3d as _m
import trimesh
import inspect
import os.path


def _info_str(tag):  # Must be called from inside another function.
    csf = inspect.stack()[2]
    info = inspect.getframeinfo(csf[0])
    str = f"{tag}@{os.path.basename(info.filename)}:{info.lineno}"
    return str


from . import Obj2d, Obj3d, config, _chkGE, _chkGO, ValidationError

_viewer_available = config["CADViewerEnabled"]


def load(filename: str) -> Obj3d | Obj2d:
    """
    Load a 3d object from a file.

    The format read from `filename` is determined by the file's extention.

    The available formats for 3D are:

    | Type        | Extension    |
    |:------------|:------------:|
    | 3MF         |   .3mf       |
    | GLB         |   .glb       |
    | GLTF        |   .gltf      |
    | OBJ         |   .obj       |
    | PLY         |   .ply       |
    | STL         |   .stl_ascii |
    | STL binary  |   .stl       |

    \\(See [https://github/mikedh/trimesh] for more formats.\\)

    Currently 2d objects are not supported.
    """
    dot_idx = filename.rindex(".")
    ext = filename[dot_idx + 1 :]
    mesh = trimesh.exchange.load.load(filename, ext, force="mesh")
    if type(mesh) == trimesh.path.Path2D:
        raise ValidationError("Currently 2d objects are no supported.")
    else:
        o = Obj3d(_m.Manifold.create_from_verts_and_faces(mesh.vertices, mesh.faces))

    return o


def save(filename: str, *objs: Obj3d | Obj2d) -> None:
    """
    Save a 3d or 2d object in a file suitable for printing, etc.

    The format placed in [p:filename] is determined by the file's extention.

    The available formats for 3D are:

    | Type        | Extension    |
    |:------------|:------------:|
    | 3MF         |   .3mf       |
    | GLB         |   .glb       |
    | GLTF        |   .gltf      |
    | OBJ         |   .obj       |
    | PLY         |   .ply       |
    | STL         |   .stl_ascii |
    | STL binary  |   .stl       |

    \\(See [https://github/mikedh/trimesh] for more formats.\\)

    For 2D, only the SVG (.svg) format is available.
    """
    _chkGE("len(objs)", len(objs), 1)
    dot_idx = filename.rindex(".")
    ext = filename[dot_idx + 1 :]
    if type(objs[0]) == Obj3d:
        if len(objs) == 1:
            obj = objs[0]
            mesh = obj.mo.to_mesh()
            if mesh.vert_properties.shape[1] > 3:
                vertices = mesh.vert_properties[:, :3]
            else:
                vertices = mesh.vert_properties
            mesh_output = trimesh.Trimesh(vertices=vertices, faces=mesh.tri_verts)
            if obj._color != None:
                mesh_output.visual.vertex_colors = obj._color
            # Manifold3d has a different definition than Trimesh
            # if not mesh_output.is_watertight:
            #    print("WARNING: output mesh is not watertight")
            trimesh.exchange.export.export_mesh(mesh_output, filename, ext)
        else:
            scene = trimesh.Scene()
            for obj in objs:
                mesh = obj.mo.to_mesh()
                if mesh.vert_properties.shape[1] > 3:
                    vertices = mesh.vert_properties[:, :3]
                else:
                    vertices = mesh.vert_properties
                mesh_output = trimesh.Trimesh(vertices=vertices, faces=mesh.tri_verts)
                if obj._color != None:
                    mesh_output.visual.vertex_colors = obj._color
                # Manifold3d has a different definition than Trimesh
                # if not mesh_output.is_watertight:
                #    print("WARNING: output mesh is not watertight")
                scene.add_geometry(mesh_output)
            trimesh.exchange.export.export_scene(scene, filename, ext)
        # trimesh obj file export does not end with newline
        # currently this upsets prusa_slicer
        if ext == "obj":
            with open(filename, "a") as f:
                f.write("\n")
    else:  # Obj2d
        if ext != "svg":
            raise (ValidationError("Only the SVG format is supported for Obj2d."))
        _save_svg(filename, *objs)


def _save_svg(filename, *objs):
    txt = []
    bb = [0.0, 0.0, 0.0, 0.0]
    for obj in objs:
        obb = obj.bounding_box()
        bb[0] = min(obb[0], bb[0])
        bb[1] = min(obb[1], bb[1])
        bb[2] = max(obb[2], bb[2])
        bb[3] = max(obb[3], bb[3])
    width = round(bb[2] - bb[0], 5)
    height = round(bb[3] - bb[1], 5)
    units = config["DefaultUnits"]

    txt.append('<?xml version="1.0" encoding="UTF-8"?>')
    txt.append("<!-- Created by Piecad. -->")
    txt.append(
        '<!DOCTYPE svg PUBLIC "-//W3C//DTD SVG 1.1 Tiny//EN" "http://www.w3.org/Graphics/SVG/1.1/DTD/svg11-tiny.dtd">'
    )
    txt.append(
        f'<svg width="{width}{units}" height="{height}{units}" viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg" fill-rule="evenodd">'
    )

    off_x = 0 - bb[0]
    off_y = 0 - bb[1]
    y_size = bb[3] - bb[1]
    for obj in objs:
        color = obj._color if obj._color != None else (128, 128, 128)
        txt.append(f'<g><path fill="rgb({color[0]},{color[1]},{color[2]})" d="')
        paths = obj.to_paths()
        for path in paths:
            for i in range(len(path)):
                vert = path[i]
                x = round(vert[0] + off_x, 5)
                y = round(y_size - (vert[1] + off_y), 5)
                if i == 0:
                    txt.append(f"M{x} {y}")
                else:
                    txt.append(f"L{x} {y}")

        txt.append('"/></g>\n')

    txt.append("</svg>")

    with open(filename, "w") as f:
        f.write("\n".join(txt))


_view_queue = queue.Queue()
_view_thread = None


def view(obj: Obj3d | Obj2d, title: str = "") -> None:
    """
    Use CADView protocol to display the geometry object.

    Returns obj unchanged... so that it works well in return statements.
    """
    global _view_thread
    if _viewer_available == False:
        return

    _chkGO("obj", obj)

    if title == "":
        title = _info_str("view")

    if type(obj) == Obj2d:
        color = obj._color
        obj = Obj2d(_m.Manifold.extrude(obj.mo, 0.1))
        obj._color = color

    if _view_thread == None:
        _view_thread = threading.Thread(target=_view_handler, daemon=True)
        _view_thread.start()
        atexit.register(_tell_view_handler_to_exit)

    mesh = obj.mo.to_mesh()
    if mesh.vert_properties.shape[1] > 3:
        vertices = mesh.vert_properties[:, :3]
    else:
        vertices = mesh.vert_properties
    faces = mesh.tri_verts
    view_data = {}
    view_data["title"] = title
    view_data["color"] = [210, 180, 140] if obj._color == None else obj._color
    view_data["vertices"] = vertices.tolist()
    fl = faces.tolist()
    # for one in fl:
    #    one.insert(0, len(one))
    # fl.insert(0, len(fl))
    view_data["faces"] = fl
    _view_queue.put(view_data)
    return obj


def _tell_view_handler_to_exit():
    _view_queue.put(None)
    _view_thread.join()


def _view_handler():
    global _viewer_available
    try:
        conn = http.client.HTTPConnection(config["CADViewerHostAndPort"])
        content = json.dumps('{"clear":true}')
        conn.request("POST", "/", content)
        response = conn.getresponse()
    except:
        _viewer_available = False
        return

    while True:
        view_data = _view_queue.get()
        if view_data == None:
            break
        content = json.dumps(view_data)
        view_data = None
        conn.request("POST", "/", content)
        response = conn.getresponse()
        content = None


def winding(lt: list[tuple[float, float]]) -> str:
    """
    String description of winding of a 2D polygon.

    Returns one of `"cw"`, `"ccw"`, `"zero"` or `"too small"`.
    """

    def wstr(winding):
        if winding > 0:
            return "cw"
        if winding < 0:
            return "ccw"
        return "zero"

    length = len(lt)
    if length < 3:
        return "too small"
    winding = 0.0
    for i in range(0, length):
        winding += (lt[(i + 1) % length][0] - lt[i][0]) * (
            lt[(i + 1) % length][1] + lt[i][1]
        )
    return wstr(winding)
