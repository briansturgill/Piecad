"""Stroke open polylines using the existing Manifold cross-section engine."""

import math

import manifold3d as _m


def _rounded(value):
    return math.floor(value + 0.5) if value >= 0 else math.ceil(value - 0.5)


def stroke(points, radius, join, cap):
    """Return integer contours for an open polyline with the given half-width."""
    if not math.isfinite(radius) or radius <= 0:
        raise ValueError("Stroke radius must be positive and finite")
    if join not in ("square", "round", "miter"):
        raise ValueError(f"Unsupported stroke join: {join}")
    if cap not in ("butt", "round", "square"):
        raise ValueError(f"Unsupported stroke cap: {cap}")

    coordinate_limit = (1 << 62) - 1
    if radius >= coordinate_limit:
        raise OverflowError("Stroke radius exceeds the coordinate limit")
    vertices = []
    for point in points:
        p = (int(point[0]), int(point[1]))
        if any(abs(value) + radius > coordinate_limit for value in p):
            raise OverflowError("Stroke coordinates exceed the coordinate limit")
        if not vertices or p != vertices[-1]:
            vertices.append(p)
    if len(vertices) < 2:
        raise ValueError("An open stroke requires at least two distinct points")

    directions = []
    for a, b in zip(vertices, vertices[1:]):
        dx, dy = b[0] - a[0], b[1] - a[1]
        length = math.hypot(dx, dy)
        directions.append((dx / length, dy / length))

    polygons = []

    def add_polygon(points):
        rounded = [(_rounded(x), _rounded(y)) for x, y in points]
        area = sum(
            a[0] * b[1] - a[1] * b[0]
            for a, b in zip(rounded, rounded[1:] + rounded[:1])
        )
        if area:
            polygons.append(rounded if area > 0 else rounded[::-1])

    def add_arc(center, normal, sweep):
        tolerance = min(0.25, radius * 0.25)
        step = 4 * math.asin(math.sqrt(tolerance / (2 * radius)))
        count = max(1, math.ceil(abs(sweep) / step))
        angle = math.atan2(normal[1], normal[0])
        add_polygon(
            [center]
            + [
                (
                    center[0] + radius * math.cos(angle + sweep * i / count),
                    center[1] + radius * math.sin(angle + sweep * i / count),
                )
                for i in range(count + 1)
            ]
        )

    for i, (a, b) in enumerate(zip(vertices, vertices[1:])):
        dx, dy = directions[i]
        nx, ny = -dy * radius, dx * radius
        start = radius if cap == "square" and i == 0 else 0
        end = radius if cap == "square" and i == len(directions) - 1 else 0
        add_polygon(
            [
                (a[0] - dx * start + nx, a[1] - dy * start + ny),
                (a[0] - dx * start - nx, a[1] - dy * start - ny),
                (b[0] + dx * end - nx, b[1] + dy * end - ny),
                (b[0] + dx * end + nx, b[1] + dy * end + ny),
            ]
        )

    if cap == "round":
        add_arc(vertices[0], (-directions[0][1], directions[0][0]), math.pi)
        add_arc(vertices[-1], (directions[-1][1], -directions[-1][0]), math.pi)

    for i in range(1, len(vertices) - 1):
        p = vertices[i]
        u, v = directions[i - 1], directions[i]
        cross = u[0] * v[1] - u[1] * v[0]
        dot = max(-1.0, min(1.0, u[0] * v[0] + u[1] * v[1]))
        if abs(cross) < 1e-12 and dot > 0:
            continue
        if join == "round":
            side = -1 if cross >= 0 else 1
            add_arc(
                p,
                (-u[1] * side, u[0] * side),
                math.atan2(cross, dot) if abs(cross) >= 1e-12 else math.pi,
            )
            continue
        if abs(cross) < 1e-12 and dot < 0:
            nx, ny = -u[1] * radius, u[0] * radius
            add_polygon(
                [
                    (p[0] + nx, p[1] + ny),
                    (p[0] - nx, p[1] - ny),
                    (p[0] + u[0] * radius - nx, p[1] + u[1] * radius - ny),
                    (p[0] + u[0] * radius + nx, p[1] + u[1] * radius + ny),
                ]
            )
            continue
        side = -1 if cross > 0 else 1
        n1 = (-u[1] * side, u[0] * side)
        n2 = (-v[1] * side, v[0] * side)
        a = (p[0] + n1[0] * radius, p[1] + n1[1] * radius)
        b = (p[0] + n2[0] * radius, p[1] + n2[1] * radius)
        if join == "miter" and 1 + dot >= 0.5:
            m = (
                p[0] + (n1[0] + n2[0]) * radius / (1 + dot),
                p[1] + (n1[1] + n2[1]) * radius / (1 + dot),
            )
            add_polygon([p, a, m, b])
        else:
            t = radius * math.tan(abs(math.atan2(cross, dot)) / 4)
            add_polygon(
                [
                    p,
                    a,
                    (a[0] + u[0] * t, a[1] + u[1] * t),
                    (b[0] - v[0] * t, b[1] - v[1] * t),
                    b,
                ]
            )

    return [
        [(_rounded(x), _rounded(y)) for x, y in contour]
        for contour in _m.CrossSection(polygons, _m.FillRule.Positive).to_polygons()
    ]
