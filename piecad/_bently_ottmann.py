from typing import List, Tuple, Optional

Point = Tuple[float, float]
Segment = Tuple[Point, Point]
Intersection = Tuple[Point, Segment, Segment]


def segment_intersection(
    s1: Segment, s2: Segment, include_endpoint_touches: bool = False, eps: float = 1e-10
) -> Optional[Point]:
    """
    Return the intersection point of two line segments.

    Returns None if they do not intersect.

    If include_endpoint_touches is False, intersections occurring
    exactly at an endpoint are ignored.
    """

    (x1, y1), (x2, y2) = s1
    (x3, y3), (x4, y4) = s2

    dx1 = x2 - x1
    dy1 = y2 - y1
    dx2 = x4 - x3
    dy2 = y4 - y3

    denominator = dx1 * dy2 - dy1 * dx2

    # Parallel or collinear
    if abs(denominator) < eps:
        return None

    dx3 = x3 - x1
    dy3 = y3 - y1

    t = (dx3 * dy2 - dy3 * dx2) / denominator
    u = (dx3 * dy1 - dy3 * dx1) / denominator

    if include_endpoint_touches:
        if not (-eps <= t <= 1 + eps and -eps <= u <= 1 + eps):
            return None
    else:
        # Strictly inside both segments
        if not (eps < t < 1 - eps and eps < u < 1 - eps):
            return None

    return (x1 + t * dx1, y1 + t * dy1)


def find_self_intersections(
    segments: List[Segment], include_endpoint_touches: bool = False, eps: float = 1e-10
) -> List[Intersection]:
    """
    Find all self-intersections in a polygon represented by segments.

    Returns:
        [
            (intersection_point, segment1, segment2),
            ...
        ]

    Normal shared-endpoint intersections are ignored by default.

    The function works with multiple loops, so the segment list can
    contain an outer polygon and any number of holes.
    """

    intersections = []

    n = len(segments)

    for i in range(n):
        s1 = segments[i]

        for j in range(i + 1, n):
            s2 = segments[j]

            # Ignore segments that share an endpoint.
            #
            # These are normally just the ordinary vertices of a
            # polygon boundary.
            if not include_endpoint_touches:
                if _shares_endpoint(s1, s2, eps):
                    continue

            point = segment_intersection(
                s1, s2, include_endpoint_touches=include_endpoint_touches, eps=eps
            )

            if point is not None:
                intersections.append((point, s1, s2))

    return intersections


def _shares_endpoint(s1: Segment, s2: Segment, eps: float) -> bool:
    """Return True if two segments have a common endpoint."""

    for p1 in s1:
        for p2 in s2:
            if abs(p1[0] - p2[0]) <= eps and abs(p1[1] - p2[1]) <= eps:
                return True

    return False
