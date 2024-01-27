"""
## Miscellaneous (but important) functions
"""

import atexit
import http.client
import json
import queue
import threading
import manifold3d as _m
import numpy as np
import trimesh
from typing import Union

from ._c import _chkGT, _chkTY, _chkGE
from . import *

_viewer_available = config["CADViewerEnabled"]


def save(filename: str, obj: Union[Obj3d, Obj2d]) -> None:
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
    if type(obj) != Obj3d and type(obj) != Obj2d:
        raise (ValidationError("Object must be of type Obj3d or Obj2d."))
    if config["CADViewDoNotSendSaves"] == False and _viewer_available:
        view(obj, filename)
    if type(obj) == Obj3d:
        mesh = obj.mo.to_mesh()
        if mesh.vert_properties.shape[1] > 3:
            vertices = mesh.vert_properties[:, :3]
        else:
            vertices = mesh.vert_properties
        mesh_output = trimesh.Trimesh(vertices=vertices, faces=mesh.tri_verts)
        if obj._color != None:
            mesh_output.visual.vertex_colors = obj._color
        # LATER assert mesh_output.is_watertight
        dot_idx = filename.rindex(".")
        ext = filename[dot_idx + 1 :]
        trimesh.exchange.export.export_mesh(mesh_output, filename, ext)
    else:  # Obj2d
        ext = filename[dot_idx + 1 :]
        if ext != "svg":
            raise (ValidationError("Only the SVG format is supported for Obj2d."))


_view_queue = queue.Queue()
_view_thread = None


def view(obj: Union[Obj3d, Obj2d], title: str = "") -> None:
    """
    Use CADView protocol to display the geometry object.

    Returns obj unchanged... so that it works well in return statements.
    """

    global _view_thread
    if _viewer_available == False:
        return

    if type(obj) != Obj3d and type(obj) != Obj2d:
        raise (ValidationError("Object must be of type Obj3d or Obj2d."))

    if type(obj) == Obj2d:
        color = obj.color
        obj = extrude(obj, 0.1)
        obj.color = color

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
    view_data["color"] = [210, 180, 140]  # LATER make better, use Color
    view_data["vertices"] = vertices.tolist()
    fl = faces.tolist()
    for one in fl:
        one.insert(0, len(one))
    fl.insert(0, len(fl))
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
        print(response.status)
