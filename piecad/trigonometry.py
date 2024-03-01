"""
Trigonometry functions that use and return degrees.

They also take pains to make sure commonly used angles that should
come out exact, DO come out exact.
"""

import math as _math


def deg_to_rad(angleInDegrees):
    "Convert degrees to radians."
    return angleInDegrees * (_math.pi / 180)


def rad_to_deg(angleInRadians):
    "Convert radians to degrees."
    return angleInRadians * (180 / _math.pi)


_quickSin = {}
_quickCos = {}
_quickTan = {}


_quickSin[0] = 0
_quickSin[30] = 0.5
_quickSin[45] = _math.sin(_math.pi / 4)
_quickSin[60] = _math.sin(_math.pi / 3)
_quickSin[90] = 1
_quickSin[120] = _math.sin(2 * _math.pi / 3)
_quickSin[135] = _math.sin(3 * _math.pi / 4)
_quickSin[150] = 0.5
_quickSin[180] = 0
_quickSin[210] = -0.5
_quickSin[225] = _math.sin(5 * _math.pi / 4)
_quickSin[240] = _math.sin(4 * _math.pi / 3)
_quickSin[270] = -1
_quickSin[300] = _math.sin(5 * _math.pi / 3)
_quickSin[315] = _math.sin(7 * _math.pi / 4)
_quickSin[330] = -0.5
_quickSin[360] = 0

_quickCos[0] = 1
_quickCos[30] = _math.cos(_math.pi / 6)
_quickCos[45] = _math.cos(_math.pi / 4)
_quickCos[60] = 0.5
_quickCos[90] = 0
_quickCos[120] = -0.5
_quickCos[135] = _math.cos(3 * _math.pi / 4)
_quickCos[150] = _math.cos(5 * _math.pi / 6)
_quickCos[180] = -1
_quickCos[210] = _math.cos(7 * _math.pi / 6)
_quickCos[225] = _math.cos(5 * _math.pi / 4)
_quickCos[240] = -0.5
_quickCos[270] = 0
_quickCos[300] = 0.5
_quickCos[315] = _math.cos(7 * _math.pi / 4)
_quickCos[330] = _math.cos(11 * _math.pi / 6)
_quickCos[360] = 1

_quickTan[0] = 0
_quickTan[30] = _math.tan(_math.pi / 6)
_quickTan[45] = 1
_quickTan[60] = _math.tan(_math.pi / 3)
# Undefined _quickTan[90] = _math.tan(_math.pi/2)
_quickTan[120] = _math.tan(2 * _math.pi / 3)
_quickTan[135] = -1
_quickTan[150] = _math.tan(5 * _math.pi / 6)
_quickTan[180] = 0
_quickTan[210] = _math.tan(7 * _math.pi / 6)
_quickTan[225] = 1
_quickTan[240] = _math.tan(4 * _math.pi / 3)
# Undefined _quickTan[270] = _math.tan(3*_math.pi/2)
_quickTan[300] = _math.tan(5 * _math.pi / 3)
_quickTan[315] = -1
_quickTan[330] = _math.tan(11 * _math.pi / 6)
_quickTan[360] = 0


def cos(angleInDegrees: float) -> float:
    "Cosine of angle in degrees."
    angleInDegrees = abs(angleInDegrees % 360.0)
    if angleInDegrees in _quickCos:
        return _quickCos[angleInDegrees]
    return _math.cos(deg_to_rad(angleInDegrees))


def sin(angleInDegrees: float) -> float:
    "Sine of angle in degrees."
    angleInDegrees = abs(angleInDegrees % 360.0)
    if angleInDegrees in _quickSin:
        return _quickSin[angleInDegrees]
    return _math.sin(deg_to_rad(angleInDegrees))


def tan(angleInDegrees: float) -> float:
    "Tangent of angle in degrees."
    angleInDegrees = abs(angleInDegrees % 360.0)
    if angleInDegrees in _quickTan:
        return _quickTan[angleInDegrees]
    return _math.tan(deg_to_rad(angleInDegrees))


def cosh(angleInDegrees: float) -> float:
    "Hyperbolic cosine of angle in degrees."
    return _math.cosh(deg_to_rad(angleInDegrees))


def sinh(angleInDegrees: float) -> float:
    "Hyperbolic sine of angle in degrees."
    return _math.sinh(deg_to_rad(angleInDegrees))


def tanh(angleInDegrees: float) -> float:
    "Hyperbolic tangent of angle in degrees."
    return _math.tanh(deg_to_rad(angleInDegrees))


def acos(cosVal: float) -> float:
    "ArcCosine of cosVal returning angle in degrees."
    return rad_to_deg(_math.acos(cosVal))


def asin(sinVal: float) -> float:
    "ArcSine of sinVal returning angle in degrees."
    return rad_to_deg(_math.asin(sinVal))


def atan(tanVal: float) -> float:
    "ArcTan of tanVal returning angle in degrees."
    return rad_to_deg(_math.atan(tanVal))


def atan2(y: float, x: float) -> float:
    "ArcTan of quotient of y and x returning angle in degrees."
    return rad_to_deg(_math.atan2(y, x))


def acosh(cosVal: float) -> float:
    "ArcCosine of hyperbolic cosVal returning angle in degrees."
    return rad_to_deg(_math.acosh(cosVal))


def asinh(sinVal: float) -> float:
    "ArcSine of hyperbolic sinVal returning angle in degrees"
    return rad_to_deg(_math.asinh(sinVal))


def atanh(tanVal: float) -> float:
    "ArcTan of hyperbolic tanVal returning angle in degrees."
    return rad_to_deg(_math.atanh(tanVal))
