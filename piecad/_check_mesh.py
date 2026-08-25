import trimesh
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
from collections import defaultdict


def find_problem_edges(mesh):
    edges = mesh.edges_sorted

    # Groups of identical edges
    groups = trimesh.grouping.group_rows(edges, require_count=None)

    boundary = []
    non_manifold = []

    for group in groups:
        count = len(group)

        edge = edges[group[0]]

        if count == 1:
            boundary.append(edge)

        elif count > 2:
            non_manifold.append(edge)

    return (non_manifold, boundary)


def find_problem_vertices(mesh):
    faces = np.asarray(mesh.faces, dtype=np.int64)

    vertex_faces = [[] for _ in range(len(mesh.vertices))]

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

            others = face[face != v]

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

    nonmanifold = np.unique(nonmanifold)

    return nonmanifold


def find_bad_winding_pairs(mesh):
    bad_pairs = []

    # Get adjacency info: each row is [face_a, face_b]
    adjacency = mesh.face_adjacency
    adjacency_edges = mesh.face_adjacency_edges

    for (f1, f2), edge in zip(adjacency, adjacency_edges):
        # Get the face vertex indices
        face1 = mesh.faces[f1]
        face2 = mesh.faces[f2]

        # Find the order of the shared edge in each face
        idx1 = np.where(face1 == edge[0])[0][0]
        idx1_next = (idx1 + 1) % 3
        edge1_dir = (face1[idx1], face1[idx1_next])

        idx2 = np.where(face2 == edge[0])[0][0]
        idx2_next = (idx2 + 1) % 3
        edge2_dir = (face2[idx2], face2[idx2_next])

        # If the edge is in the same direction in both faces, winding is bad
        if edge1_dir == edge2_dir:
            bad_pairs.append(f1)
            bad_pairs.append(f2)

    return np.unique(bad_pairs).tolist()


def check_mesh(
    vertices: list[tuple[float, float, float]],
    faces: list[tuple[int, int, int]],
    quick=False,
) -> bool:
    mesh = trimesh.Trimesh(vertices, faces, process=False, validate=False)

    if not mesh.is_watertight:
        non_manifold_edges, boundary_edges = find_problem_edges(mesh)
        if len(non_manifold_edges) > 0:
            if quick:
                return "non-manifold edges"
            print(f"Your mesh has {len(non_manifold_edges)} non-manifold edges.")
            print("This means that it is adjacent to more than 1 other edge.")
            print(f"The edges are: {non_manifold_edges}")
            view_mesh(
                mesh,
                title="Edges in red are non-manifold edges. (adjacent count > 2)",
                check_edges=non_manifold_edges,
                show_normals=False,
            )
            return False
        elif len(boundary_edges) > 0:
            if quick:
                return "boundary edges"
            print(f"Your mesh has {len(boundary_edges)} boundary-edges.")
            print("This means that it is not adjacent any other edge.")
            print("This is usually because you left a hole in the mesh.")
            print("Check for a missing face..")
            print(f"The edges are: {boundary_edges}")
            view_mesh(
                mesh,
                title="Edges in red are boundary edges. (adjacent count = 1)",
                check_edges=boundary_edges,
                show_normals=False,
            )
            return False

    non_manifold_vertices = find_problem_vertices(mesh)
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
            mesh,
            title="Vertices in red are non-manifold vertices.",
            check_vertices=non_manifold_vertices,
            show_normals=False,
        )
        return False

    if not mesh.is_winding_consistent:
        if quick:
            return "some bad windings"
        bad_winding = find_bad_winding_pairs(mesh)
        print(f"Your mesh has {len(bad_winding)} _POSSIBLY_ bad face windings.")
        print(
            "View each mesh listed and look for red arrows that point inside your mesh."
        )
        print(
            "The easiest way to correct the bad winding is reverse the last two numbers in the face."
        )
        print(f"The faces that need to be manually checked are: {bad_winding}")
        view_mesh(
            mesh,
            title="Faces with arrow pointing inside have an incorrect winding",
            check_faces=bad_winding,
            show_normals=True,
        )
        return False

    if mesh.volume < 0:
        if quick:
            return "probably all windings are bad"
        print(
            "Your 3d object is watertight (is manifold) and your winding is consistent."
        )
        print("Your objects volume is less than zero.")
        print("This almost certainly means that ALL you faces have the wrong winding.")
        view_mesh(
            mesh,
            title="Faces with arrow pointing inside have an incorrect winding",
            check_faces=list(range(0, len(mesh.faces))),
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
    mesh, title, check_faces=[], check_edges=[], check_vertices=[], show_normals=False
):
    print("Would you like to look at a matplotlib visualization of the problem?")
    ans = input("[Y]es, [n]o: ")
    ans = ans.lower()
    if ans.startswith("n"):
        return

    def on_key(event):
        """Close the figure when 'q' or 'Escape' is pressed."""
        if event.key in ["q", "escape"]:
            plt.close(event.canvas.figure)

    v = mesh.vertices
    f = mesh.faces

    cf = []
    for fi in check_faces:
        face = f[fi]
        cf.append(f[fi])
    cf = np.array(cf, np.uint64)

    ces = []
    for ei in check_edges:
        ces.append(ei[0])
        ces.append(ei[1])
    ces = np.array([ces], np.uint64)

    # Compute face normals
    def per_face_normals(vertices, faces):
        v = vertices
        f = faces
        n = np.zeros((len(f), 3))
        for i, face in enumerate(f):
            a, b, c = face
            e1 = v[b] - v[a]
            e2 = v[c] - v[a]
            n[i] = np.cross(e1, e2)
        return n

    if show_normals:
        normals = per_face_normals(v, f)

    # Create figure and 3D axis
    fig = plt.figure(figsize=(10, 8))
    fig.canvas.mpl_connect("key_press_event", on_key)
    ax = fig.add_subplot(111, projection="3d")
    mi, mx = mesh.bounds
    ax.set_xlim(mi[0], mx[0])
    ax.set_ylim(mi[1], mx[1])
    ax.set_zlim(mi[2], mx[2])

    # Plot mesh faces
    pc = Poly3DCollection(v[f], linewidths=1, edgecolors="black")
    pc.set_facecolor((0, 0, 0.5, 0.3))
    ax.add_collection(pc)

    if len(check_faces) > 0:
        pc = Poly3DCollection(v[cf], linewidths=1, edgecolors="green")
        pc.set_facecolor((0, 0.9, 0, 0.3))
        ax.add_collection(pc)

    if len(check_edges) > 0:
        pc = Poly3DCollection(v[ces], linewidths=5, edgecolors="red")
        pc.set_facecolor((0, 0, 0.5, 0.3))
        ax.add_collection(pc)

    if len(check_vertices) > 0:
        for vi in check_vertices:
            x, y, z = v[vi]
            ax.scatter(
                x, y, z, color="red", s=100, zorder=5, label="Highlighted Vertex"
            )

    if show_normals:
        # Add face numbers and normals
        for i, face in enumerate(f):
            # Face number label
            centroid = np.mean(v[face], axis=0)
            ax.text(*centroid, f"Face {i}", color="blue", fontsize=20, zorder=10)

            # Normal vector label
            norm_vec = normals[i]
            norm_len = np.linalg.norm(norm_vec)
            if norm_len > 0:
                norm_vec /= norm_len  # unit vector
                norm_end = centroid + 0.1 * norm_vec
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
