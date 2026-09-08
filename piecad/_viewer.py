from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path
from typing import Any
import matplotlib.pyplot as plt

import numpy as np
import trimesh

_HELP = """Piecad CAD Viewer

a              Toggle axis marker
c              Toggle culling
C              Toggle colors
f              Toggle fullscreen
g              Toggle grid
h, ? or ESC    View/dismiss this help
q, ESC         Quit CAD Viewer
w              Toggle wireframe
z              Reset view

LEFT           Previous object
RIGHT          Next object
SHIFT-LEFT     Rotate image left
SHIFT-RIGHT    Rotate image right
SHIFT-UP       Rotate image up
SHIFT-DOWN     Rotate image down

Mouse:
  Left drag    Rotate
  Middle drag  Move/pan
  Right drag   Zoom
"""


def _on_close(event):
    from .utilities import _matplot_closed

    _matplot_closed()


class MeshViewer:
    def __init__(
        self,
        meshes: list[Any] | None = None,
        title: str = "Piecad CAD Viewer",
        mesh_titles: list[Any] = [""],
    ):
        self.meshes = list(meshes or [])
        self.title = title
        self.titles = mesh_titles  # Individual mesh titles
        self.index = len(meshes) - 1

        self.wireframe = False
        self.culling = False
        self.colors_visible = False
        self.axis_visible = True
        self.grid_visible = True
        self.help_visible = True

        self._view = (30.0, -60.0)
        self._axis_length = 50.0  # 5 cm for millimetre model coordinates

        self.fig = None
        self.ax = None
        self.help_text = None

    @staticmethod
    def _mesh_arrays(mesh: Any) -> tuple[np.ndarray, np.ndarray]:
        """Return vertices and triangular faces from a Trimesh-like object."""
        if not hasattr(mesh, "vertices") or not hasattr(mesh, "faces"):
            raise TypeError("Meshes must be trimesh.Trimesh objects.")

        vertices = np.asarray(mesh.vertices, dtype=float)
        faces = np.asarray(mesh.faces, dtype=np.int64)

        if vertices.ndim != 2 or vertices.shape[1] != 3:
            raise ValueError("Mesh vertices must have shape (N, 3).")

        if faces.ndim != 2 or faces.shape[1] != 3:
            raise ValueError("Mesh faces must have shape (N, 3).")

        return vertices, faces

    @staticmethod
    def _face_colors(mesh: Any, count: int) -> np.ndarray | None:
        """Get Trimesh per-face colors as Matplotlib RGBA values."""
        if not hasattr(mesh, "visual"):
            return None

        colors = getattr(mesh.visual, "face_colors", None)
        if colors is None:
            return None

        colors = np.asarray(colors)

        if len(colors) != count:
            return None

        if colors.dtype.kind in "ui":
            colors = colors.astype(float) / 255.0
        else:
            colors = colors.astype(float)

        if colors.shape[1] == 3:
            alpha = np.full(len(colors), int(255 * 0.3), dtype=np.uint8)
            colors = np.hstack((colors, alpha))

        return colors

    def clear(self) -> None:
        """Remove every mesh and its associated viewer data."""
        self.meshes.clear()
        self.titles.clear()
        self.index = -1

        if self.fig is not None:
            self._draw_mesh()

    def add_mesh(self, mesh: Any, mesh_title: str = "") -> None:
        """Add a mesh and make it the current mesh."""
        self._mesh_arrays(mesh)
        self.meshes.append(mesh)
        self.titles.append(mesh_title)
        self.index = len(self.meshes) - 1

        if self.fig is not None:
            self._draw_mesh()

    def _current_mesh(self) -> Any:
        if not self.meshes:
            raise ValueError("The viewer contains no meshes.")
        return self.meshes[self.index]

    def _visible_faces(
        self,
        vertices: np.ndarray,
        faces: np.ndarray,
    ) -> np.ndarray:
        if not self.culling:
            return np.ones(len(faces), dtype=bool)

        triangles = vertices[faces]
        normals = np.cross(
            triangles[:, 1] - triangles[:, 0],
            triangles[:, 2] - triangles[:, 0],
        )

        elevation = np.deg2rad(self._view[0])
        azimuth = np.deg2rad(self._view[1])

        camera = np.array(
            [
                np.cos(elevation) * np.cos(azimuth),
                np.cos(elevation) * np.sin(azimuth),
                np.sin(elevation),
            ]
        )

        return np.einsum("ij,j->i", normals, camera) > 0

    def _draw_axis(self, vertices: np.ndarray) -> None:
        if not self.axis_visible:
            return

        model_size = float(np.ptp(vertices, axis=0).max())
        length = max(self._axis_length, model_size * 0.25)

        endpoints = (
            (length, 0.0, 0.0),
            (0.0, length, 0.0),
            (0.0, 0.0, length),
        )
        colors = ("red", "green", "blue")
        labels = ("X", "Y", "Z")

        for endpoint, color, label in zip(endpoints, colors, labels):
            self.ax.plot(
                (0.0, endpoint[0]),
                (0.0, endpoint[1]),
                (0.0, endpoint[2]),
                color=color,
                linewidth=2.5,
                marker="o",
                markersize=4,
            )
            self.ax.text(
                endpoint[0],
                endpoint[1],
                endpoint[2],
                label,
                color=color,
                weight="bold",
            )

    def _shade_colors(
        self,
        vertices: np.ndarray,
        faces: np.ndarray,
        base_colors: np.ndarray,
    ) -> np.ndarray:
        """Apply simple directional (Lambertian) shading to face colors."""
        triangles = vertices[faces]
        normals = np.cross(
            triangles[:, 1] - triangles[:, 0],
            triangles[:, 2] - triangles[:, 0],
        )
        norm_lengths = np.linalg.norm(normals, axis=1, keepdims=True)
        norm_lengths[norm_lengths == 0] = 1.0
        normals = normals / norm_lengths

        # Light coming from roughly the camera direction, for a
        # consistent "headlamp" look.
        elevation = np.deg2rad(self._view[0])
        azimuth = np.deg2rad(self._view[1])
        light_dir = np.array(
            [
                np.cos(elevation) * np.cos(azimuth),
                np.cos(elevation) * np.sin(azimuth),
                np.sin(elevation),
            ]
        )

        intensity = np.abs(np.einsum("ij,j->i", normals, light_dir))

        ambient = 0.4
        diffuse = 0.6
        brightness = (ambient + diffuse * intensity).clip(0.0, 1.0)

        shaded = base_colors.copy()
        shaded[:, 0:3] *= brightness[:, None]
        return shaded

    def _draw_mesh(self) -> None:
        from mpl_toolkits.mplot3d.art3d import Poly3DCollection

        self.ax.clear()

        if not self.meshes:
            self.ax.set_title(f"{self.title} [no meshes]")
            self.fig.canvas.draw_idle()
            return

        mesh = self._current_mesh()
        vertices, faces = self._mesh_arrays(mesh)
        visible = self._visible_faces(vertices, faces)

        polygons = [vertices[face] for face in faces[visible]]

        face_colors = None
        if self.colors_visible:
            all_colors = self._face_colors(mesh, len(faces))
            if all_colors is not None:
                face_colors = all_colors[visible]

        if face_colors is None:
            face_colors = np.tile(
                (0.35, 0.65, 0.95, 0.3), (visible.sum(), 1)
            )

        face_colors = self._shade_colors(vertices, faces[visible], face_colors)

        collection = Poly3DCollection(
            polygons,
            facecolors=face_colors,
            edgecolors="black" if self.wireframe else "none",
            linewidths=0.5 if self.wireframe else 0.0,
        )
        self.ax.add_collection3d(collection)

        minimum = vertices.min(axis=0)
        maximum = vertices.max(axis=0)
        center = (minimum + maximum) / 2.0
        radius = float(np.ptp(vertices, axis=0).max()) / 2.0
        radius = max(radius, 1.0)

        self.ax.set_xlim(center[0] - radius, center[0] + radius)
        self.ax.set_ylim(center[1] - radius, center[1] + radius)
        self.ax.set_zlim(center[2] - radius, center[2] + radius)
        self.ax.set_box_aspect((1, 1, 1))
        self.ax.view_init(elev=self._view[0], azim=self._view[1])

        self.ax.set_title(
            f"{self.titles[self.index]} [{self.index + 1}/{len(self.meshes)}]"
        )
        self.ax.grid(self.grid_visible)
        self._draw_axis(vertices)

        self.fig.canvas.draw_idle()

    def _toggle_help(self) -> None:
        self.help_visible = not self.help_visible

        if self.help_text is None:
            self.help_text = self.fig.text(
                0.02,
                0.98,
                _HELP,
                va="top",
                ha="left",
                family="monospace",
                fontsize=11,
                color="white",
                bbox={
                    "facecolor": "black",
                    "alpha": 0.9,
                    "pad": 12,
                },
            )

        self.help_text.set_visible(self.help_visible)
        self.fig.canvas.draw_idle()

    def _on_key(self, event) -> None:
        raw_key = event.key or ""
        key = raw_key.lower()

        if raw_key in {"C", "shift+c"}:
            self.colors_visible = not self.colors_visible
            self._draw_mesh()
            return

        if key in {"h", "?"} or key in {"escape", "esc"}:
            self._toggle_help()
            return

        if key == "q" or key in {"escape", "esc"}:
            plt.close(self.fig)
            return

        if key == "a":
            self.axis_visible = not self.axis_visible
            self._draw_mesh()

        elif key == "c":
            self.culling = not self.culling
            self._draw_mesh()

        elif key == "f":
            manager = self.fig.canvas.manager
            if hasattr(manager, "full_screen_toggle"):
                manager.full_screen_toggle()

        elif key == "g":
            self.grid_visible = not self.grid_visible
            self.ax.grid(self.grid_visible)
            self.fig.canvas.draw_idle()

        elif key == "w":
            self.wireframe = not self.wireframe
            self._draw_mesh()

        elif key == "z":
            self._view = (30.0, -60.0)
            self._draw_mesh()

        elif key == "left":
            if self.meshes:
                self.index = (self.index - 1) % len(self.meshes)
                self._draw_mesh()

        elif key == "right":
            if self.meshes:
                self.index = (self.index + 1) % len(self.meshes)
                self._draw_mesh()

        elif key == "shift+left":
            self._view = (self._view[0], self._view[1] - 15.0)
            self._draw_mesh()

        elif key == "shift+right":
            self._view = (self._view[0], self._view[1] + 15.0)
            self._draw_mesh()

        elif key == "shift+up":
            self._view = (min(90.0, self._view[0] + 15.0), self._view[1])
            self._draw_mesh()

        elif key == "shift+down":
            self._view = (max(-90.0, self._view[0] - 15.0), self._view[1])
            self._draw_mesh()

    def show(self, block: bool = True) -> "MeshViewer":
        plt.ion()
        self.fig = plt.figure(figsize=(10, 8))
        self.fig.canvas.mpl_connect("close_event", _on_close)

        self.fig.canvas.manager.set_window_title(self.title)
        self.ax = self.fig.add_subplot(111, projection="3d")

        self.ax.mouse_init(
            rotate_btn=1,
            pan_btn=2,
            zoom_btn=3,
        )

        self.fig.canvas.mpl_connect("key_press_event", self._on_key)

        self._draw_mesh()
        self._toggle_help()
        plt.show(block=block)

        return self


def _create_viewer(
    meshes: list[Any] | None = None,
    title: str = "Piecad CAD Viewer",
    mesh_titles: list[str] | None = None,
) -> MeshViewer:
    """Create a non-blocking viewer."""
    return MeshViewer(meshes, title, mesh_titles).show(block=False)


def show_meshes(
    meshes: list[Any] | None = None,
    title: str = "Piecad CAD Viewer",
    mesh_titles: list[str] | None = None,
) -> MeshViewer:
    """Display meshes and return the viewer after closing."""
    return MeshViewer(meshes, title, mesh_titles).show(block=True)
