"""
## Miscellaneous (but important) functions
"""

import atexit
import threading
import manifold3d as _m
import inspect
import os.path
import time
from pathlib import Path as _Path
from . import Obj2d, Obj3d, Config, _chkGE, _chkGO, ValidationError, np, trimesh

from ._export_3mf import export_3mf as _export_3mf
from ._check_mesh import check_mesh as _check_mesh
from ._check_mesh import quick_check_mesh as _quick_check_mesh

__all__ = [
    "check_mesh",
    "load",
    "quick_check_mesh",
    "save",
    "view",
    "view_all_now",
    "winding",
]


def _info_str(tag):  # Must be called from inside another function.
    csf = inspect.stack()[2]
    info = inspect.getframeinfo(csf[0])
    str = f"{tag}@{os.path.basename(info.filename)}:{info.lineno}"
    return str



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
    mesh = trimesh.exchange.load.load(
        filename, ext, force="mesh", process=True, validate=False
    )
    if type(mesh) == trimesh.path.Path2D:
        raise ValidationError("Currently 2d objects are no supported.")
    else:
        vertices = np.array(mesh.vertices, np.float64)
        faces = np.array(mesh.faces, np.uint64)
        o = Obj3d(_m.Manifold(_m.Mesh64(vertices, faces)))

    return o


_save_dir = None


def _get_save_dir():
    global _save_dir

    if _save_dir is not None:
        return _save_dir

    import platform
    import os

    _save_dir = os.getenv("PIECAD_SAVE_DIR", None)
    if _save_dir is not None:
        return _save_dir
    if platform.system == "Windows":
        import winreg

        sub_key = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\Shell Folders"
        downloads_guid = "{374DE290-123F-4565-9164-39C4925E467B}"
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, sub_key) as key:
            _save_dir = winreg.QueryValueEx(key, downloads_guid)[0]
    else:  # Linux/Unix and MacOS
        _save_dir = str(_Path.home() / "Downloads")
    return _save_dir


def _face_colors(mesh):
    flen = len(mesh.tri_verts)
    face_colors = np.zeros((flen, 3), dtype=np.uint8)
    for i in range(0, len(mesh.run_index) - 1):
        for j in range(mesh.run_index[i] // 3, mesh.run_index[i + 1] // 3):
            id = mesh.run_original_id[i]
            if id == -1 or id not in Obj3d.color_map:
                color = Config.get_default_color()
            else:
                color = Obj3d.color_map[id]
            face_colors[j][0] = color[0]
            face_colors[j][1] = color[1]
            face_colors[j][2] = color[2]
    return face_colors


def save(filename: str, *objs: Obj3d | Obj2d) -> None:
    """
    Save a 3d or 2d object in a file suitable for printing, etc.

    If [p filename] does not contain a path separator character (`'/'` or `'\\'`) the
    `Downloads` directory for you platform is prepended. Thus if you set
    [p filename] to `output.obj`, the place where the file is saved is
    `c:\\Users\\username\\Downloads\\output.obj` on Windows or
    `/home/username/Downloads/output.obj` on Linux and MacOS.
    If you want a file saved in the current directory, prepend `'./'` or `'.\\'`.

    You can override the `Downloads` directory by setting the global environment variable
    `PIECAD_SAVE_DIR`.

    The model format placed in [p:filename] is determined by the file's extention.

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

    if filename.find("/") == -1 and filename.find("\\") == -1:
        filename = str(_Path(_get_save_dir()) / filename)
        print("Saving: " + filename)
    _chkGE("len(objs)", len(objs), 1)
    dot_idx = filename.rindex(".")
    ext = filename[dot_idx + 1 :]
    if type(objs[0]) == Obj3d:
        if len(objs) == 1:
            obj = objs[0]
            if filename.endswith(".3mf"):
                _export_3mf(
                    filename,
                    obj.mo,
                    Obj3d.color_map,
                    Config.get_default_units(),
                    Config.get_default_color(),
                )
                return
            mesh = obj.mo.to_mesh64()
            if mesh.vert_properties.shape[1] > 3:
                vertices = mesh.vert_properties[:, :3]
            else:
                vertices = mesh.vert_properties

            face_colors = _face_colors(mesh)
            mesh_output = trimesh.Trimesh(
                vertices=vertices,
                faces=mesh.tri_verts,
                face_colors=face_colors,
                process=True,
                validate=False,
            )
            # Manifold3d has a different definition than Trimesh
            if not mesh_output.is_watertight:
                print("WARNING: output mesh is not watertight")
            trimesh.exchange.export.export_mesh(mesh_output, filename, ext)
        else:
            scene = trimesh.Scene()
            for obj in objs:
                mesh = obj.mo.to_mesh()
                if mesh.vert_properties.shape[1] > 3:
                    vertices = mesh.vert_properties[:, :3]
                else:
                    vertices = mesh.vert_properties
                face_colors = _face_colors(mesh)
                mesh_output = trimesh.Trimesh(
                    vertices=vertices,
                    faces=mesh.tri_verts,
                    face_colors=face_colors,
                    process=True,
                    validate=False,
                )
                # Manifold3d has a different definition than Trimesh
                if not mesh_output.is_watertight:
                    print("WARNING: output mesh is not watertight")
                scene.add_geometry(mesh_output)
            if filename.endswith(".3mf"):
                s_mesh = scene.to_mesh64()
                s_vertices = np.array(s_mesh.vertices, np.float64)
                s_faces = np.array(s_mesh.faces, np.uint64)
                mo = _m.Manifold(_m.Mesh64(s_vertices, s_faces))
                _export_3mf(
                    filename,
                    mo,
                    Obj3d.color_map,
                    Config.get_default_units(),
                    Config.get_default_color(),
                )
                return
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
    units = Config.get_default_units()

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
        color = obj._color if obj._color is not None else (128, 128, 128)
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


_view_meshes = []
_view_meshes_titles = []


def view(obj: Obj3d | Obj2d, title: str = "") -> None:
    """
    Use `Piecad-Viewer` to display the geometry object.

    Returns obj unchanged... so that it works well in return statements.

    If you have trouble viewing and are using a graphical debugger,
    see the `view_all_now()` function below.

    ```
    return union(o1, o2, o3)
    # can be displayed in 3 parts and the whole object, like this:
    return view(union(view(o1), view(o2), view(o3)))
    ```

    """
    global _view_meshes, _view_meshes_titles

    _chkGO("obj", obj)

    if title == "":
        title = _info_str("view")

    if type(obj) == Obj2d:
        color = obj._color
        if color is not None:
            color = Config.get_default_color()
        obj = Obj3d(_m.Manifold.extrude(obj.mo, 0.1)).color(color)

    mesh = obj.mo.to_mesh64()
    if mesh.vert_properties.shape[1] > 3:
        vertices = mesh.vert_properties[:, :3]
    else:
        vertices = mesh.vert_properties
    faces = mesh.tri_verts
    mesh_output = trimesh.Trimesh(
                vertices=vertices,
                faces=faces,
                face_colors=_face_colors(mesh),
                process=True,
                validate=False,
            )
    if len(_view_meshes) == 0:
        atexit.register(_wait_for_view_handler_exit)
    _view_meshes.append(mesh_output)
    _view_meshes_titles.append(title)
    return obj

_viewer_closed_event = threading.Event()

def _matplot_closed():
    _viewer_closed_event.set()


def _wait_for_view_handler_exit():
    if len(_view_meshes) > 0:
        view_all_now()

def view_all_now() -> None:
    """
    The `view()` function mearly records a list of objects to be displayed.
    By default, a function to view the meshes is called from `atexit`.
    Unfortunately a number of graphical debuggers (e.g. Visual Studio Code
    and PyCharm) have a short timeout for `atexit` functions.
    To avoid this issue, use `view_all_now()` at the end of your script to
    display all objects recorded by `view()` with no timeout.
    Alternatively run the script witout debugging.
    """
    from . _viewer import show_meshes
    v = show_meshes(_view_meshes, "Piecad CAD Viewer", _view_meshes_titles)
    _viewer_closed_event.wait()
    v.clear()
    _view_meshes.clear()
    _view_meshes_titles.clear()
    _viewer_closed_event.clear()


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


def check_mesh(
    vertices: list[tuple[float, float, float]], faces: list[tuple[int, int, int]]
) -> bool:
    """
    Check manifold and winding of the mesh defined in vertices and faces.

    Returns true if all is well. Otherwise diagnostics will be offered and false is returned.
    """
    return _check_mesh(vertices, faces)


def quick_check_mesh(
    vertices: list[tuple[float, float, float]], faces: list[tuple[int, int, int]]
) -> str:
    """
    Same checking as check_mesh, but no advice is offered

    Returns an empty string `""` if all is well, otherwise a short string describing the problem is
    returned.
    """
    return _quick_check_mesh(vertices, faces)
