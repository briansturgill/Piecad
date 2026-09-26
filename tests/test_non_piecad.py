import manifold3d as _m
import pytest
import numpy as np

import random

data1 = [float(random.random()) for _ in range(20)]
data2 = [
    (float(random.random()), float(random.random()), float(random.random()))
    for _ in range(20)
]


def _test_np_asarray(dat):
    x = np.asarray(dat, dtype=np.float64)
    return x


def test_np_as_array(benchmark):
    x = benchmark(_test_np_asarray, data1)
    assert x.shape == (20,)


def _test_np_array(dat):
    x = np.array(dat, dtype=np.float64)
    return x


def test_np_array(benchmark):
    x = benchmark(_test_np_array, data1)
    assert x.shape == (20,)


def _test_py_list_copy(dat):
    x = dat[:]
    return x


def test_py_list_copy(benchmark):
    x = benchmark(_test_py_list_copy, data1)
    assert len(x) == 20


def _test_np_asarray_3d(dat):
    x = np.asarray(dat, dtype=np.float64)
    return x


def test_np_as_array_3d(benchmark):
    x = benchmark(_test_np_asarray_3d, data2)
    assert x.shape == (20, 3)


def _test_np_array_3d(dat):
    x = np.array(dat, dtype=np.float64)
    return x


def test_np_array_3d(benchmark):
    x = benchmark(_test_np_array_3d, data2)
    assert x.shape == (20, 3)


def _test_py_list_copy_3d(dat):
    x = dat[:]
    return x


def test_py_list_copy_3d(benchmark):
    x = benchmark(_test_py_list_copy_3d, data2)
    assert len(x) == 20


def _test_np_list_sum_3d(dat):
    x = [sum(t) for t in dat]
    return x


def test_np_list_sum_3d(benchmark):
    dat = np.array(data2)
    x = benchmark(_test_np_list_sum_3d, dat)
    assert len(x) == 20


def _test_py_list_sum_3d(dat):
    x = [sum(t) for t in dat]
    return x


def test_py_list_sum_3d(benchmark):
    x = benchmark(_test_py_list_sum_3d, data2)
    assert len(x) == 20
