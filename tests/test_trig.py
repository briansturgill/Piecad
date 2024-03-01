import pytest
from piecad import *
import math as _math


def test_deg_to_rad():
    assert deg_to_rad(360) == _math.pi * 2
    assert deg_to_rad(180) == _math.pi
    assert deg_to_rad(90) == _math.pi / 2
    assert deg_to_rad(45) == _math.pi / 4


def test_rad_to_deg():
    assert rad_to_deg(_math.pi * 2) == 360
    assert rad_to_deg(_math.pi) == 180
    assert rad_to_deg(_math.pi / 2) == 90
    assert rad_to_deg(_math.pi / 4) == 45


def test_deg_to_rad_and_back():
    for i in range(360 * 10 + 1):
        assert round(rad_to_deg(deg_to_rad(i)), 12) == i


def test_acos_cos_degree():
    for i in range(180 + 1):
        assert round(acos(cos(i)), 12) == i


def test_asin_sin_degree():
    for i in range(90 + 1):
        assert round(asin(sin(i)), 12) == i


def test_atan_tan_degree():
    for i in range(90 + 1):
        assert round(atan(tan(i)), 12) == i


def test_acosh_cosh_degree():
    for i in range(180 + 1):
        assert round(acosh(cosh(i)), 12) == i


def test_asinh_sinh_degree():
    for i in range(90 + 1):
        assert round(asinh(sinh(i)), 12) == i


def test_atanh_tanh_degree():
    for i in range(90 + 1):
        assert round(atanh(tanh(i)), 12) == i


def test_special_cached_trig_values():
    dvals = [
        0,
        30,
        45,
        60,
        90,
        120,
        135,
        150,
        180,
        210,
        225,
        240,
        270,
        300,
        315,
        330,
        360,
    ]
    rvals = [
        0,
        _math.pi / 6,
        _math.pi / 4,
        _math.pi / 3,
        _math.pi / 2,
        2 * _math.pi / 3,
        3 * _math.pi / 4,
        5 * _math.pi / 6,
        _math.pi,
        7 * _math.pi / 6,
        5 * _math.pi / 4,
        4 * _math.pi / 3,
        3 * _math.pi / 2,
        5 * _math.pi / 3,
        7 * _math.pi / 4,
        11 * _math.pi / 6,
        2 * _math.pi,
    ]

    def _equalish(v1, v2):
        if abs(v1 - v2) <= 1e-15:
            return True
        return False

    assert len(dvals) == len(rvals)
    for i in range(len(dvals)):
        assert _equalish(deg_to_rad(dvals[i]), rvals[i])
        assert _equalish(cos(dvals[i]), _math.cos(rvals[i]))
        assert _equalish(sin(dvals[i]), _math.sin(rvals[i]))
        assert _equalish(tan(dvals[i]), _math.tan(rvals[i]))


def test_trig_bare_sin_speed(benchmark):
    benchmark(_math.sin, 1.23)


def test_trig_cache_hit_sin_speed(benchmark):
    benchmark(sin, 90)


def test_trig_cache_miss_sin_speed(benchmark):
    benchmark(sin, 123)


def test_trig_bare_cos_speed(benchmark):
    benchmark(_math.cos, 1.23)


def test_trig_cache_hit_cos_speed(benchmark):
    benchmark(cos, 90)


def test_trig_cache_miss_cos_speed(benchmark):
    benchmark(cos, 123)


def test_special_values():
    assert sin(30) == 0.5
    assert sin(90) == 1
    assert sin(0) == 0
    assert sin(150) == 0.5
    assert sin(180) == 0
    assert sin(210) == -0.5
    assert sin(270) == -1
    assert sin(330) == -0.5
    assert sin(360) == 0

    assert cos(0) == 1
    assert cos(60) == 0.5
    assert cos(90) == 0
    assert cos(120) == -0.5
    assert cos(180) == -1
    assert cos(240) == -0.5
    assert cos(270) == 0
    assert cos(300) == 0.5
    assert cos(360) == 1

    assert tan(0) == 0
    assert tan(45) == 1
    assert tan(135) == -1
    assert tan(180) == 0
    assert tan(225) == 1
    assert tan(315) == -1
    assert tan(360) == 0
