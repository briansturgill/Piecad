import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
from .lin_math import Vec3


def find_problem_edges(faces):
    edge_faces = {}
    for face in faces:
        for index in range(3):
            edge = tuple(sorted((face[index], face[(index + 1) % 3])))
            edge_faces.setdefault(edge, []).append(face)

    boundary = []
    non_manifold = []
    for edge, adjacent_faces in edge_faces.items():
        if len(adjacent_faces) == 1:
            boundary.append(edge)
        elif len(adjacent_faces) > 2:
            non_manifold.append(edge)
    return non_manifold, boundary


def find_problem_vertices(faces, vertex_count):
    vertex_faces = [[] for _ in range(vertex_count)]

    for face_index, face in enumerate(faces):
        for v in face:
            vertex_faces[v].append(face_index)

    nonmanifold = []

    for v, incident_faces in enumerate(vertex_faces):

        if len(incident_faces) <= 1:
            continue

        edge_to_faces = {}

        for f in incident_faces:
            face = faces[f]
            others = [u for u in face if u != v]
            for u in others:
                edge = (min(v, u), max(v, u))
                edge_to_faces.setdefault(edge, []).append(f)

        neighbors = {f: [] for f in incident_faces}

        for edge_faces in edge_to_faces.values():

            # Normally 1 or 2.
            # >2 is itself a non-manifold edge.
            if len(edge_faces) > 2:
                nonmanifold.append(v)
                break

            if len(edge_faces) == 2:
                a, b = edge_faces
                neighbors[a].append(b)
                neighbors[b].append(a)

        else:
            remaining = set(incident_faces)
            components = 0

            while remaining:
                components += 1

                if components > 1:
                    nonmanifold.append(v)
                    break

                start = remaining.pop()
                stack = [start]

                while stack:
                    f = stack.pop()

                    for n in neighbors[f]:
                        if n in remaining:
                            remaining.remove(n)
                            stack.append(n)

    return sorted(set(nonmanifold))


def find_bad_winding_pairs(faces):
    edge_faces = {}
    for face_index, face in enumerate(faces):
        for index in range(3):
            directed_edge = (face[index], face[(index + 1) % 3])
            edge = tuple(sorted(directed_edge))
            edge_faces.setdefault(edge, []).append((face_index, directed_edge))

    bad_pairs = set()
    for adjacent_faces in edge_faces.values():
        if len(adjacent_faces) == 2:
            (first_index, first_edge), (second_index, second_edge) = adjacent_faces
            if first_edge == second_edge:
                bad_pairs.update((first_index, second_index))
    return sorted(bad_pairs)


def _signed_volume(vertices, faces):
    six_times_volume = 0.0
    for face in faces:
        a, b, c = (vertices[index] for index in face)
        six_times_volume += Vec3.dot(a, Vec3.cross(b, c))
    return six_times_volume / 6.0


def check_mesh(
    vertices: list[tuple[float, float, float]],
    faces: list[tuple[int, int, int]],
    quick=False,
) -> bool:
    non_manifold_edges, boundary_edges = find_problem_edges(faces)
    if non_manifold_edges:
        if quick:
            return "non-manifold edges"
        print(f"Your mesh has {len(non_manifold_edges)} non-manifold edges.")
        print("This means that it is adjacent to more than 1 other edge.")
        print(f"The edges are: {non_manifold_edges}")
        view_mesh(
            vertices,
            faces,
            title="Edges in red are non-manifold edges. (adjacent count > 2)",
            check_edges=non_manifold_edges,
            show_normals=False,
        )
        return False
    elif boundary_edges:
        if quick:
            return "boundary edges"
        print(f"Your mesh has {len(boundary_edges)} boundary-edges.")
        print("This means that it is not adjacent any other edge.")
        print("This is usually because you left a hole in the mesh.")
        print("Check for a missing face..")
        print(f"The edges are: {boundary_edges}")
        view_mesh(
            vertices,
            faces,
            title="Edges in red are boundary edges. (adjacent count = 1)",
            check_edges=boundary_edges,
            show_normals=False,
        )
        return False

    non_manifold_vertices = find_problem_vertices(faces, len(vertices))
    if len(non_manifold_vertices) > 0:
        if quick:
            return "non-manifold vertices"
        print(
            "Your object has non-manifold vertices, look at these indices in your vertices list:"
        )
        print(non_manifold_vertices)
        print(
            "Usual causes: an extraneous point, a degenerate triangle (zero area), or a single point of contact."
        )
        view_mesh(
            vertices,
            faces,
            title="Vertices in red are non-manifold vertices.",
            check_vertices=non_manifold_vertices,
            show_normals=False,
        )
        return False

    bad_winding = find_bad_winding_pairs(faces)
    if bad_winding:
        if quick:
            return "some bad windings"
        print(f"Your mesh has {len(bad_winding)} _POSSIBLY_ bad face windings.")
        print(
            "View each mesh listed and look for red arrows that point inside your mesh."
        )
        print(
            "The easiest way to correct the bad winding is reverse the last two numbers in the face."
        )
        print(f"The faces that need to be manually checked are: {bad_winding}")
        view_mesh(
            vertices,
            faces,
            title="Faces with arrow pointing inside have an incorrect winding",
            check_faces=bad_winding,
            show_normals=True,
        )
        return False

    if _signed_volume(vertices, faces) < 0:
        if quick:
            return "probably all windings are bad"
        print(
            "Your 3d object is watertight (is manifold) and your winding is consistent."
        )
        print("Your objects volume is less than zero.")
        print("This almost certainly means that ALL you faces have the wrong winding.")
        view_mesh(
            vertices,
            faces,
            title="Faces with arrow pointing inside have an incorrect winding",
            check_faces=list(range(len(faces))),
            show_normals=True,
        )
        return False

    if quick:
        return ""  # Means all is well
    return True


def quick_check_mesh(
    vertices: list[tuple[float, float, float]], faces: list[tuple[int, int, int]]
) -> bool:
    return check_mesh(vertices, faces, True)


def view_mesh(
    vertices,
    faces,
    title,
    check_faces=None,
    check_edges=None,
    check_vertices=None,
    show_normals=False,
):
    check_faces = check_faces or []
    check_edges = check_edges or []
    check_vertices = check_vertices or []

    print("Would you like to look at a matplotlib visualization of the problem?")
    ans = input("[Y]es, [n]o: ")
    ans = ans.lower()
    if ans.startswith("n"):
        return

    def on_key(event):
        """Close the figure when 'q' or 'Escape' is pressed."""
        if event.key in ["q", "escape"]:
            plt.close(event.canvas.figure)

    face_vertices = [[vertices[index] for index in face] for face in faces]

    # Create figure and 3D axis
    fig = plt.figure(figsize=(10, 8))
    fig.canvas.mpl_connect("key_press_event", on_key)
    ax = fig.add_subplot(111, projection="3d")
    ax.set_xlim(
        min(vertex[0] for vertex in vertices), max(vertex[0] for vertex in vertices)
    )
    ax.set_ylim(
        min(vertex[1] for vertex in vertices), max(vertex[1] for vertex in vertices)
    )
    ax.set_zlim(
        min(vertex[2] for vertex in vertices), max(vertex[2] for vertex in vertices)
    )

    # Plot mesh faces
    pc = Poly3DCollection(face_vertices, linewidths=1, edgecolors="black")
    pc.set_facecolor((0, 0, 0.5, 0.3))
    ax.add_collection(pc)

    if len(check_faces) > 0:
        highlighted_faces = [face_vertices[index] for index in check_faces]
        pc = Poly3DCollection(highlighted_faces, linewidths=1, edgecolors="green")
        pc.set_facecolor((0, 0.9, 0, 0.3))
        ax.add_collection(pc)

    if len(check_edges) > 0:
        for first, second in check_edges:
            ax.plot(
                (vertices[first][0], vertices[second][0]),
                (vertices[first][1], vertices[second][1]),
                (vertices[first][2], vertices[second][2]),
                color="red",
                linewidth=5,
            )

    if len(check_vertices) > 0:
        for vi in check_vertices:
            x, y, z = vertices[vi]
            ax.scatter(
                x, y, z, color="red", s=100, zorder=5, label="Highlighted Vertex"
            )

    if show_normals:
        # Add face numbers and normals
        for i, face in enumerate(faces):
            # Face number label
            centroid = tuple(
                sum(vertices[index][axis] for index in face) / 3 for axis in range(3)
            )
            ax.text(*centroid, f"Face {i}", color="blue", fontsize=20, zorder=10)

            # Normal vector label
            a, b, c = (vertices[index] for index in face)
            norm_vec = Vec3.cross(Vec3.sub(b, a), Vec3.sub(c, a))
            norm_len = Vec3.length(norm_vec)
            if norm_len > 0.0:
                norm_vec = Vec3.normalize(norm_vec)
                ax.quiver(
                    *centroid,
                    *norm_vec,
                    color="red",
                    length=0.75,
                    arrow_length_ratio=0.4,
                )

    # Labels and title
    ax.set_xlabel("X")
    ax.set_ylabel("Y")
    ax.set_zlabel("Z")
    ax.set_title(title + " - type 'q' to quit")

    plt.show()
