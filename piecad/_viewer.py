from __future__ import annotations

from math import cos, radians, sin
from numbers import Integral
from typing import Any

import matplotlib.pyplot as plt

from .lin_math import Vec3

main_title = "Piecad Viewer - Type 'h' for help."

_HELP = """Piecad Viewer


    a              Toggle axis marker
    c              Toggle culling
    f              Toggle fullscreen
    g              Toggle grid
    h, ?, or ESC   View/dismiss this help
    q              Quit Piecad Viewer
    r, z           Reset view
    s              Save screenshot
    t              Toggle transparency
    w              Toggle wireframe

Arrow Keys:
    Left           Previous object
    Right          Next object
    SHIFT-Left     Rotate image left
    SHIFT-Right    Rotate image right
    SHIFT-Up       Rotate image up
    SHIFT-Down     Rotate image down

Mouse:
    Left drag                     Rotate
    Middle drag, SHIFT-Left drag  Move/pan
    Right drag,  CTRL-Left drag   Zoom
"""


def _on_close(event):
    from .utilities import _matplot_closed

    _matplot_closed()


class MeshViewer:
    def __init__(
        self,
        meshes: list[Any] | None = None,
        mesh_titles: list[Any] = [""],
    ):
        self.meshes = list(meshes or [])
        self.title = main_title
        self.titles = mesh_titles  # Individual mesh titles
        self.index = 0

        self.wireframe = False
        self.culling = False
        self.colors_visible = True
        self.axis_visible = True
        self.grid_visible = True
        self.help_visible = True

        self._view = (30.0, -60.0)
        self._view_limits: (
            tuple[tuple[float, float], tuple[float, float], tuple[float, float]] | None
        ) = None
        self._axis_length = 50.0  # 5 cm for millimetre model coordinates

        self.fig = None
        self.ax = None
        self.help_text = None
        self._dragging = False
        self.shift_pressed = False
        self.ctrl_pressed = False

    @staticmethod
    def _mesh_arrays(
        mesh: Any,
    ) -> tuple[list[tuple[float, float, float]], list[tuple[int, int, int]]]:
        """Return vertices and triangular faces as plain Python tuples."""
        if not hasattr(mesh, "vertices") or not hasattr(mesh, "faces"):
            raise TypeError("Meshes must be trimesh.Trimesh objects.")

        vertices = [tuple(float(value) for value in vertex) for vertex in mesh.vertices]
        faces = [tuple(int(index) for index in face) for face in mesh.faces]

        if any(len(vertex) != 3 for vertex in vertices):
            raise ValueError("Mesh vertices must have shape (N, 3).")

        if any(len(face) != 3 for face in faces):
            raise ValueError("Mesh faces must have shape (N, 3).")

        return vertices, faces

    @staticmethod
    def _face_colors(
        mesh: Any, count: int
    ) -> list[tuple[float, float, float, float]] | None:
        """Get Trimesh per-face colors as Matplotlib RGBA values."""
        if not hasattr(mesh, "visual"):
            return None

        colors = getattr(mesh.visual, "face_colors", None)
        if colors is None:
            return None

        if len(colors) != count:
            return None

        normalized_colors = []
        for color in colors:
            if len(color) not in (3, 4):
                return None
            if all(isinstance(channel, Integral) for channel in color):
                converted = [float(channel) / 255.0 for channel in color]
            else:
                converted = [float(channel) for channel in color]
            if len(converted) == 3:
                converted.append(int(255 * 0.3) / 255.0)
            normalized_colors.append(tuple(converted))

        return normalized_colors

    def clear(self) -> None:
        """Remove every mesh and its associated viewer data."""
        self.meshes.clear()
        self.titles.clear()
        self.index = -1

        if self.fig is not None:
            self._draw_mesh(reset_limits=True)

    def add_mesh(self, mesh: Any, mesh_title: str = "") -> None:
        """Add a mesh."""
        self._mesh_arrays(mesh)
        self.meshes.append(mesh)
        self.titles.append(mesh_title)
        self.index = 0

        if self.fig is not None:
            self._draw_mesh(reset_limits=True)

    def _current_mesh(self) -> Any:
        if not self.meshes:
            raise ValueError("The viewer contains no meshes.")
        return self.meshes[self.index]

    def _visible_faces(
        self,
        vertices: list[tuple[float, float, float]],
        faces: list[tuple[int, int, int]],
    ) -> list[bool]:
        if not self.culling:
            return [True] * len(faces)

        elevation = radians(self._view[0])
        azimuth = radians(self._view[1])
        camera = (
            cos(elevation) * cos(azimuth),
            cos(elevation) * sin(azimuth),
            sin(elevation),
        )

        visible = []
        for face in faces:
            first, second, third = (vertices[index] for index in face)
            normal = Vec3.cross(Vec3.sub(second, first), Vec3.sub(third, first))
            visible.append(Vec3.dot(normal, camera) > 0)
        return visible

    def _draw_axis(self, vertices: list[tuple[float, float, float]]) -> None:
        if not self.axis_visible:
            return

        model_size = max(
            max(vertex[axis] for vertex in vertices)
            - min(vertex[axis] for vertex in vertices)
            for axis in range(3)
        )
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
        vertices: list[tuple[float, float, float]],
        faces: list[tuple[int, int, int]],
        base_colors: list[tuple[float, float, float, float]],
    ) -> list[tuple[float, float, float, float]]:
        """Apply simple directional (Lambertian) shading to face colors."""
        # Light coming from roughly the camera direction, for a
        # consistent "headlamp" look.
        elevation = radians(self._view[0])
        azimuth = radians(self._view[1])
        light_dir = (
            cos(elevation) * cos(azimuth),
            cos(elevation) * sin(azimuth),
            sin(elevation),
        )

        shaded = []
        for face, color in zip(faces, base_colors):
            first, second, third = (vertices[index] for index in face)
            normal = Vec3.cross(Vec3.sub(second, first), Vec3.sub(third, first))
            normal_length = Vec3.length(normal)
            if normal_length > 0.0:
                normal = Vec3.normalize(normal)
            intensity = abs(Vec3.dot(normal, light_dir))
            brightness = max(0.0, min(1.0, 0.4 + 0.6 * intensity))
            shaded.append(
                (
                    color[0] * brightness,
                    color[1] * brightness,
                    color[2] * brightness,
                    color[3],
                )
            )
        return shaded

    def _draw_mesh(self, reset_limits: bool = False) -> None:
        from mpl_toolkits.mplot3d.art3d import Poly3DCollection

        if reset_limits:
            self._view_limits = None
        elif self._view_limits is not None:
            self._view_limits = (
                self.ax.get_xlim(),
                self.ax.get_ylim(),
                self.ax.get_zlim(),
            )

        self.ax.clear()

        if not self.meshes:
            self.ax.set_title(f"{self.title} [no meshes]")
            self.fig.canvas.draw_idle()
            return

        mesh = self._current_mesh()
        vertices, faces = self._mesh_arrays(mesh)
        visible = self._visible_faces(vertices, faces)

        visible_faces = [face for face, is_visible in zip(faces, visible) if is_visible]
        polygons = [[vertices[index] for index in face] for face in visible_faces]

        face_colors = None
        if self.colors_visible:
            all_colors = self._face_colors(mesh, len(faces))
            if all_colors is not None:
                face_colors = [
                    color
                    for color, is_visible in zip(all_colors, visible)
                    if is_visible
                ]

        if face_colors is None:
            face_colors = [(0.35, 0.65, 0.95, 0.3)] * len(visible_faces)

        face_colors = self._shade_colors(vertices, visible_faces, face_colors)

        collection = Poly3DCollection(
            polygons,
            facecolors=face_colors,
            edgecolors="black" if self.wireframe else "none",
            linewidths=0.5 if self.wireframe else 0.0,
        )
        self.ax.add_collection3d(collection)

        minimum = tuple(min(vertex[axis] for vertex in vertices) for axis in range(3))
        maximum = tuple(max(vertex[axis] for vertex in vertices) for axis in range(3))
        center = tuple((minimum[axis] + maximum[axis]) / 2.0 for axis in range(3))
        radius = max(maximum[axis] - minimum[axis] for axis in range(3)) / 2.0
        radius = max(radius, 1.0)

        limits = self._view_limits or (
            (center[0] - radius, center[0] + radius),
            (center[1] - radius, center[1] + radius),
            (center[2] - radius, center[2] + radius),
        )
        self.ax.set_xlim(*limits[0])
        self.ax.set_ylim(*limits[1])
        self.ax.set_zlim(*limits[2])
        self._view_limits = (
            self.ax.get_xlim(),
            self.ax.get_ylim(),
            self.ax.get_zlim(),
        )
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

    def _on_key_release(self, event) -> None:
        raw_key = event.key or ""
        key = raw_key.lower()

        if key == "control":
            self.ctrl_pressed = False

        if key == "shift":
            self.shift_pressed = False

    def _on_key(self, event) -> None:
        raw_key = event.key or ""
        key = raw_key.lower()

        if key == "control":
            self.ctrl_pressed = True

        if key == "shift":
            self.shift_pressed = True

        if key in {"h", "?"} or key in {"escape", "esc"}:
            self._toggle_help()
            return

        if raw_key in {"q"}:
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

        if key == "t":
            self.colors_visible = not self.colors_visible
            self._draw_mesh()
            return

        elif key == "w":
            self.wireframe = not self.wireframe
            self._draw_mesh()

        elif key in {"r", "z"}:
            self._view = (30.0, -60.0)
            self._draw_mesh(reset_limits=True)

        elif key == "left":
            if self.meshes:
                self.index = (self.index - 1) % len(self.meshes)
                self._draw_mesh(reset_limits=True)

        elif key == "right":
            if self.meshes:
                self.index = (self.index + 1) % len(self.meshes)
                self._draw_mesh(reset_limits=True)

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

    def _on_mouse_release(self, event) -> None:
        # Mouse-driven rotation is handled internally by Axes3D, which
        # updates self.ax.elev/azim directly without going through
        # self._view. Resync here so shading/culling (which are
        # computed from self._view) reflect the new camera orientation.
        if self.ax is None:
            return

        view = (float(self.ax.elev), float(self.ax.azim))
        if view != self._view:
            self._view = view
            self._draw_mesh()

    def _on_mouse_press(self, event) -> None:
        if event.button == 1 and event.inaxes is self.ax:
            self._dragging = True

        if self.ctrl_pressed and event.button == 1:  # Left click
            fake_event = type(event)(
                name=event.name,
                canvas=event.canvas,
                x=event.x,
                y=event.y,
                button=3,  # right button
                key=event.key,
                step=getattr(event, "step", None),
                dblclick=getattr(event, "dblclick", False),
                guiEvent=event.guiEvent,
            )
            self.fig.canvas.callbacks.process("button_press_event", fake_event)

        if self.shift_pressed and event.button == 1:  # Left click
            fake_event = type(event)(
                name=event.name,
                canvas=event.canvas,
                x=event.x,
                y=event.y,
                button=2,  # Middle button
                key=event.key,
                step=getattr(event, "step", None),
                dblclick=getattr(event, "dblclick", False),
                guiEvent=event.guiEvent,
            )
            self.fig.canvas.callbacks.process("button_press_event", fake_event)

    def _on_mouse_move(self, event) -> None:
        # Axes3D's own motion handler (connected earlier, inside
        # mouse_init) already updated self.ax.elev/azim for this event
        # by the time this runs, so resyncing here keeps shading and
        # culling live during the drag instead of only on release.
        if not self._dragging or self.ax is None:
            return

        view = (float(self.ax.elev), float(self.ax.azim))
        if view != self._view:
            self._view = view
            self._draw_mesh()

    def _on_mouse_release_stop_drag(self, event) -> None:
        self._dragging = False
        self._on_mouse_release(event)

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
        self.fig.canvas.mpl_connect("key_release_event", self._on_key_release)
        self.fig.canvas.mpl_connect("button_press_event", self._on_mouse_press)
        self.fig.canvas.mpl_connect("motion_notify_event", self._on_mouse_move)
        self.fig.canvas.mpl_connect(
            "button_release_event", self._on_mouse_release_stop_drag
        )

        self._draw_mesh()
        self._toggle_help()
        plt.show(block=block)

        return self


def _create_viewer(
    meshes: list[Any] | None = None,
    mesh_titles: list[str] | None = None,
) -> MeshViewer:
    """Create a non-blocking viewer."""
    return MeshViewer(meshes, mesh_titles).show(block=False)


def show_meshes(
    meshes: list[Any] | None = None,
    mesh_titles: list[str] | None = None,
) -> MeshViewer:
    """Display meshes and return the viewer after closing."""
    return MeshViewer(meshes, mesh_titles).show(block=True)
