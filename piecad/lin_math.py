from __future__ import annotations
from typing import Tuple, List
import math


class Vec2:
    """
    Namespace holding functions that operate on plain 2-tuples.
    """

    @staticmethod
    def abs(v1: Tuple[float, float]) -> Tuple[float, float]:
        """
        Returns the absolute value of the vector v1.
        """
        return (math.fabs(v1[0]), math.fabs(v1[1]))

    @staticmethod
    def add(v1: Tuple[float, float], v2: Tuple[float, float]) -> Tuple[float, float]:
        """
        Returns a vector that is vector v1 added to vector v2)
        """
        return (v1[0] + v2[0], v1[1] + v2[1])

    @staticmethod
    def mul(v1: Tuple[float, float], v2: Tuple[float, float]) -> Tuple[float, float]:
        """
        Returns a vector that is vector v1 multiplied by vector v2.
        """
        return (v1[0] * v2[0], v1[1] * v2[1])

    @staticmethod
    def neg(v1: Tuple[float, float]) -> Tuple[float, float]:
        """
        Returns a vector that is the negation of vector v1.
        """
        return (-v1[0], -v1[1])

    @staticmethod
    def pos(v1: Tuple[float, float]) -> Tuple[float, float]:
        """
        Returns a vector that is the positive of vector v1 (same as vector v1).
        """
        return v1

    @staticmethod
    def sub(v1: Tuple[float, float], v2: Tuple[float, float]) -> Tuple[float, float]:
        """
        Returns a vector that is vector v1 subtracted by vector v2.
        """
        return (v1[0] - v2[0], v1[1] - v2[1])

    @staticmethod
    def div(v1: Tuple[float, float], v2: Tuple[float, float]) -> Tuple[float, float]:
        """
        Returns a vector that is vector v1 divided by vector v2.
        """
        return (v1[0] / v2[0], v1[1] / v2[1])

    @staticmethod
    def cross(
        v1: Tuple[float, float], v2: Tuple[float, float]
    ) -> Tuple[float, float, float]:
        """
        Returns the cross product of vector v1 with vector v2.
        """
        return (0, 0, v1[0] * v2[1] - v1[1] * v2[0])

    @staticmethod
    def distance(v1: Tuple[float, float], v2: Tuple[float, float]) -> float:
        """
        Returns the distance between vector v1 and vector v2.
        """
        x = v2[0] - v1[0]
        y = v2[1] - v1[1]
        return math.sqrt(x * x + y * y)

    @staticmethod
    def dot(v1: Tuple[float, float], v2: Tuple[float, float]) -> float:
        """
        Returns the dot product of vector v1 with vector v2.
        """
        return v1[0] * v2[0] + v1[1] * v2[1]

    @staticmethod
    def length(v1: Tuple[float, float]) -> float:
        """
        Returns the length of vector v1.
        """
        return math.sqrt(v1[0] * v1[0] + v1[1] * v1[1])

    @staticmethod
    def normalize(v1: Tuple[float, float]) -> Tuple[float, float]:
        """
        Returns a normalized (unit length) vector in the same direction as vector v1.
        If the vector has zero length, returns a zero vector.
        """
        length = math.sqrt(v1[0] * v1[0] + v1[1] * v1[1])
        if length > 0:
            return (v1[0] / length, v1[1] / length)
        return (0, 0)

    @staticmethod
    def squaredDistance(v1: Tuple[float, float], v2: Tuple[float, float]) -> float:
        x = v2[0] - v1[0]
        y = v2[1] - v1[1]
        return x * x + y * y

    @staticmethod
    def squaredLength(v1: Tuple[float, float]) -> float:
        return v1[0] * v1[0] + v1[1] * v1[1]


class Vec3:
    """
    Namespace holding functions that operate on plain 3-tuples.
    """

    @staticmethod
    def abs(v1: Tuple[float, float, float]) -> Tuple[float, float, float]:
        """
        Returns a vector that is the absolute value of the given vector.
        """
        return (math.fabs(v1[0]), math.fabs(v1[1]), math.fabs(v1[2]))

    @staticmethod
    def add(
        v1: Tuple[float, float, float], v2: Tuple[float, float, float]
    ) -> Tuple[float, float, float]:
        """
        Returns a vector that is vector v1 added to vector v2)
        """
        return (v1[0] + v2[0], v1[1] + v2[1], v1[2] + v2[2])

    @staticmethod
    def mul(
        v1: Tuple[float, float, float], v2: Tuple[float, float, float]
    ) -> Tuple[float, float, float]:
        """
        Returns a vector that is vector v1 multiplied by vector v2.
        """
        return (v1[0] * v2[0], v1[1] * v2[1], v1[2] * v2[2])

    @staticmethod
    def neg(v1: Tuple[float, float, float]) -> Tuple[float, float, float]:
        """
        Returns a vector that is the negation of vector v1.
        """
        return (-v1[0], -v1[1], -v1[2])

    @staticmethod
    def pos(v1: Tuple[float, float, float]) -> Tuple[float, float, float]:
        """
        Returns a vector that is the positive of vector v1 (same as vector v1).
        """
        return v1

    @staticmethod
    def sub(
        v1: Tuple[float, float, float], v2: Tuple[float, float, float]
    ) -> Tuple[float, float, float]:
        """
        Subtracts vector v2 from vector v1.
        """
        return (v1[0] - v2[0], v1[1] - v2[1], v1[2] - v2[2])

    @staticmethod
    def div(
        v1: Tuple[float, float, float], v2: Tuple[float, float, float]
    ) -> Tuple[float, float, float]:
        """
        Returns a vector that is vector v1 divided by vector v2.
        """
        return (v1[0] / v2[0], v1[1] / v2[1], v1[2] / v2[2])

    @staticmethod
    def cross(
        v1: Tuple[float, float, float], v2: Tuple[float, float, float]
    ) -> Tuple[float, float, float]:
        """
        Computes the cross product of vector v1 with vector v2.
        """
        ax = v1[0]
        ay = v1[1]
        az = v1[2]
        bx = v2[0]
        by = v2[1]
        bz = v2[2]

        return (ay * bz - az * by, az * bx - ax * bz, ax * by - ay * bx)

    @staticmethod
    def distance(
        v1: Tuple[float, float, float], v2: Tuple[float, float, float]
    ) -> float:
        """
        Calculates the Euclidian distance between vector v1 and v2 vector.
        """
        x = v2[0] - v1[0]
        y = v2[1] - v1[1]
        z = v2[2] - v1[2]
        return (x * x + y * y + z * z) ** 0.5

    @staticmethod
    def dot(v1: Tuple[float, float, float], v2: Tuple[float, float, float]) -> float:
        """
        Calculates the dot product of vector v1 with vector v2.
        """
        return v1[0] * v2[0] + v1[1] * v2[1] + v1[2] * v2[2]

    @staticmethod
    def length(v1: Tuple[float, float, float]) -> float:
        """
        Calculates the length (magnitude) of the vector.
        """
        return (v1[0] * v1[0] + v1[1] * v1[1] + v1[2] * v1[2]) ** 0.5

    @staticmethod
    def normalize(v1: Tuple[float, float, float]) -> Tuple[float, float, float]:
        """
        Normalizes the vector (makes it have a length of 1).
        """
        x = v1[0]
        y = v1[1]
        z = v1[2]
        len = x * x + y * y + z * z
        if len > 0:
            len = 1 / (len**0.5)
        return (x * len, y * len, z * len)

    @staticmethod
    def squaredDistance(
        v1: Tuple[float, float, float], v2: Tuple[float, float, float]
    ) -> float:
        """
        Calculates the squared Euclidian distance between v1 vector and v2 vector.
        """
        x = v2[0] - v1[0]
        y = v2[1] - v1[1]
        z = v2[2] - v1[2]
        return x * x + y * y + z * z

    @staticmethod
    def squaredLength(v1: Tuple[float, float, float]) -> float:
        """
        Calculates the squared length of the vector.
        """
        x = v1[0]
        y = v1[1]
        z = v1[2]
        return x * x + y * y + z * z


class Mat3:
    @staticmethod
    def determinant(m: List[Tuple[float, float, float]]) -> float:
        """
        Calculates the determinant of a 3x3 matrix.
        """
        return (
            m[0][0] * (m[1][1] * m[2][2] - m[1][2] * m[2][1])
            - m[0][1] * (m[1][0] * m[2][2] - m[1][2] * m[2][0])
            + m[0][2] * (m[1][0] * m[2][1] - m[1][1] * m[2][0])
        )


class Geom:
    """
    Namespace holding geometric functions and utilities.
    """

    @staticmethod
    def coplanar(vl: List[Tuple[float, float, float]]) -> bool:
        """
        Checks if a list of vectors are coplanar.
        """
        if len(vl) < 4:
            return True
        v0, v1, v2 = vl[0], vl[1], vl[2]
        normal = Vec3.cross(Vec3.sub(v1, v0), Vec3.sub(v2, v0))
        for v in vl[3:]:
            if abs(Vec3.dot(normal, Vec3.sub(v, v0))) > 1e-6:
                return False
        return True
