"""
Trigonometry functions that use and return degrees.

They also take pains to make sure commonly used angles that should
come out exact, DO come out exact.
"""

from . import math


def deg_to_rad(angleInDegrees: float) -> float:
    "Convert degrees to radians."
    return angleInDegrees * (math.pi / 180)


def rad_to_deg(angleInRadians: float) -> float:
    "Convert radians to degrees."
    return angleInRadians * (180 / math.pi)


_quickSin = {}
_quickCos = {}
_quickTan = {}


_quickSin[0] = 0
_quickSin[30] = 0.5
_quickSin[45] = math.sin(math.pi / 4)
_quickSin[60] = math.sin(math.pi / 3)
_quickSin[90] = 1
_quickSin[120] = math.sin(2 * math.pi / 3)
_quickSin[135] = math.sin(3 * math.pi / 4)
_quickSin[150] = 0.5
_quickSin[180] = 0
_quickSin[210] = -0.5
_quickSin[225] = math.sin(5 * math.pi / 4)
_quickSin[240] = math.sin(4 * math.pi / 3)
_quickSin[270] = -1
_quickSin[300] = math.sin(5 * math.pi / 3)
_quickSin[315] = math.sin(7 * math.pi / 4)
_quickSin[330] = -0.5
_quickSin[360] = 0

_quickCos[0] = 1
_quickCos[30] = math.cos(math.pi / 6)
_quickCos[45] = math.cos(math.pi / 4)
_quickCos[60] = 0.5
_quickCos[90] = 0
_quickCos[120] = -0.5
_quickCos[135] = math.cos(3 * math.pi / 4)
_quickCos[150] = math.cos(5 * math.pi / 6)
_quickCos[180] = -1
_quickCos[210] = math.cos(7 * math.pi / 6)
_quickCos[225] = math.cos(5 * math.pi / 4)
_quickCos[240] = -0.5
_quickCos[270] = 0
_quickCos[300] = 0.5
_quickCos[315] = math.cos(7 * math.pi / 4)
_quickCos[330] = math.cos(11 * math.pi / 6)
_quickCos[360] = 1

_quickTan[0] = 0
_quickTan[30] = math.tan(math.pi / 6)
_quickTan[45] = 1
_quickTan[60] = math.tan(math.pi / 3)
# Undefined _quickTan[90] = math.tan(math.pi/2)
_quickTan[120] = math.tan(2 * math.pi / 3)
_quickTan[135] = -1
_quickTan[150] = math.tan(5 * math.pi / 6)
_quickTan[180] = 0
_quickTan[210] = math.tan(7 * math.pi / 6)
_quickTan[225] = 1
_quickTan[240] = math.tan(4 * math.pi / 3)
# Undefined _quickTan[270] = math.tan(3*math.pi/2)
_quickTan[300] = math.tan(5 * math.pi / 3)
_quickTan[315] = -1
_quickTan[330] = math.tan(11 * math.pi / 6)
_quickTan[360] = 0


def cos(angleInDegrees: float) -> float:
    "Cosine of angle in degrees."
    angleInDegrees = abs(angleInDegrees % 360.0)
    if angleInDegrees in _quickCos:
        return _quickCos[angleInDegrees]
    return math.cos(deg_to_rad(angleInDegrees))


def sin(angleInDegrees: float) -> float:
    "Sine of angle in degrees."
    angleInDegrees = abs(angleInDegrees % 360.0)
    if angleInDegrees in _quickSin:
        return _quickSin[angleInDegrees]
    return math.sin(deg_to_rad(angleInDegrees))


def tan(angleInDegrees: float) -> float:
    "Tangent of angle in degrees."
    angleInDegrees = abs(angleInDegrees % 360.0)
    if angleInDegrees in _quickTan:
        return _quickTan[angleInDegrees]
    return math.tan(deg_to_rad(angleInDegrees))


def cosh(angleInDegrees: float) -> float:
    "Hyperbolic cosine of angle in degrees."
    return math.cosh(deg_to_rad(angleInDegrees))


def sinh(angleInDegrees: float) -> float:
    "Hyperbolic sine of angle in degrees."
    return math.sinh(deg_to_rad(angleInDegrees))


def tanh(angleInDegrees: float) -> float:
    "Hyperbolic tangent of angle in degrees."
    return math.tanh(deg_to_rad(angleInDegrees))


def acos(cosVal: float) -> float:
    "ArcCosine of cosVal returning angle in degrees."
    return rad_to_deg(math.acos(cosVal))


def asin(sinVal: float) -> float:
    "ArcSine of sinVal returning angle in degrees."
    return rad_to_deg(math.asin(sinVal))


def atan(tanVal: float) -> float:
    "ArcTan of tanVal returning angle in degrees."
    return rad_to_deg(math.atan(tanVal))


def atan2(y: float, x: float) -> float:
    "ArcTan of quotient of y and x returning angle in degrees."
    return rad_to_deg(math.atan2(y, x))


def acosh(cosVal: float) -> float:
    "ArcCosine of hyperbolic cosVal returning angle in degrees."
    return rad_to_deg(math.acosh(cosVal))


def asinh(sinVal: float) -> float:
    "ArcSine of hyperbolic sinVal returning angle in degrees"
    return rad_to_deg(math.asinh(sinVal))


def atanh(tanVal: float) -> float:
    "ArcTan of hyperbolic tanVal returning angle in degrees."
    return rad_to_deg(math.atanh(tanVal))
