from PIL import Image
from .utilities import obj3d_from_vertices_and_faces
import manifold3d as m
import trimesh


def load_heightmap(filename, max_dimension):
    img = Image.open(filename).convert("L")

    w, h = img.size
    scale = min(max_dimension / max(w, h), 1.0)

    if scale < 1.0:
        img = img.resize((int(w * scale), int(h * scale)), Image.Resampling.LANCZOS)

    return img


def add_vertex(v, vertices, lookup):
    key = tuple(round(coordinate, 5) for coordinate in v)
    if key in lookup:
        return lookup[key]

    lookup[key] = len(vertices)
    vertices.append(v)
    return lookup[key]


def create_lithophane(heightmap, pixel_size, min_thickness, max_thickness, base=0.0):

    cols, rows = heightmap.size

    vertices = []
    lookup = {}
    faces = []

    top = [[0 for _ in range(cols)] for _ in range(rows)]
    bottom = [[0 for _ in range(cols)] for _ in range(rows)]

    for y in range(rows):
        for x in range(cols):

            height = 1.0 - heightmap.getpixel((x, y)) / 255.0
            z = min_thickness + height * (max_thickness - min_thickness)

            top[y][x] = add_vertex(
                (x * pixel_size, (rows - 1 - y) * pixel_size, z),
                vertices,
                lookup,
            )

            bottom[y][x] = add_vertex(
                (x * pixel_size, (rows - 1 - y) * pixel_size, base),
                vertices,
                lookup,
            )

    # Top
    for y in range(rows - 1):
        for x in range(cols - 1):

            a = top[y][x]
            b = top[y][x + 1]
            c = top[y + 1][x]
            d = top[y + 1][x + 1]

            faces.append((a, c, b))
            faces.append((b, c, d))

    # Bottom
    for y in range(rows - 1):
        for x in range(cols - 1):

            a = bottom[y][x]
            b = bottom[y + 1][x]
            c = bottom[y][x + 1]
            d = bottom[y + 1][x + 1]

            faces.append((a, b, c))
            faces.append((c, b, d))

    # Perimeter walls
    def quad(t1, t2, b1, b2):
        faces.append((t1, b1, t2))
        faces.append((t2, b1, b2))

    # Left
    for y in range(rows - 1):
        quad(
            top[y][0],
            top[y + 1][0],
            bottom[y][0],
            bottom[y + 1][0],
        )

    # Right
    for y in range(rows - 1):
        quad(
            top[y + 1][cols - 1],
            top[y][cols - 1],
            bottom[y + 1][cols - 1],
            bottom[y][cols - 1],
        )

    # Top edge
    for x in range(cols - 1):
        quad(
            top[0][x + 1],
            top[0][x],
            bottom[0][x + 1],
            bottom[0][x],
        )

    # Bottom edge
    for x in range(cols - 1):
        quad(
            top[rows - 1][x],
            top[rows - 1][x + 1],
            bottom[rows - 1][x],
            bottom[rows - 1][x + 1],
        )

    mesh = trimesh.Trimesh(vertices=vertices, faces=faces, process=False, validate=True)

    vertices = [
        tuple(float(coordinate) for coordinate in vertex) for vertex in mesh.vertices
    ]
    faces = [tuple(int(index) for index in face) for face in mesh.faces]

    return obj3d_from_vertices_and_faces(vertices, faces)
