import manifold3d as _m
import pytest
import numpy as np

import random

data1 = [float(random.random()) for _ in range(20)]
data2 = [
    (float(random.random()), float(random.random()), float(random.random()))
    for _ in range(20)
]
data3 = [
    (float(random.random()), float(random.random()), float(random.random()))
    for _ in range(1000)
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


def _test_np_list_sum_3d_by_row_20(dat):
    x = np.sum(dat, axis=1)
    return x


def test_np_list_sum_3d_by_row_20(benchmark):
    dat = np.array(data2, dtype=np.float64)
    x = benchmark(_test_np_list_sum_3d_by_row_20, dat)
    assert len(x) == 20


def _test_py_list_sum_3d_by_row_20(dat):
    x = []
    for t in dat:
        x.append(t[0] + t[1] + t[2])
    return x


def test_py_list_sum_3d_by_row_20(benchmark):
    x = benchmark(_test_py_list_sum_3d_by_row_20, data2)
    assert len(x) == 20


def _test_np_list_sum_3d_by_col_20(dat):
    x = np.sum(dat, axis=0)
    return x


def test_np_list_sum_3d_by_col_20(benchmark):
    dat = np.array(data2, dtype=np.float64)
    x = benchmark(_test_np_list_sum_3d_by_col_20, dat)
    assert len(x) == 3


def _test_py_list_sum_3d_by_col_20(dat):
    # x = list(map(sum, zip(*dat)))
    s = (0.0, 0.0, 0.0)
    for t in dat:
        s = (s[0] + t[0], s[1] + t[1], s[2] + t[2])
    return s


def test_py_list_sum_3d_by_col_20(benchmark):
    x = benchmark(_test_py_list_sum_3d_by_col_20, data2)
    assert len(x) == 3


def _test_np_list_sum_3d_by_row_1000(dat):
    x = np.sum(dat, axis=1)
    return x


def test_np_list_sum_3d_by_row_1000(benchmark):
    dat = np.array(data3, dtype=np.float64)
    x = benchmark(_test_np_list_sum_3d_by_row_1000, dat)
    assert len(x) == 1000


def _test_py_list_sum_3d_by_row_1000(dat):
    x = []
    for t in dat:
        x.append(t[0] + t[1] + t[2])
    return x


def test_py_list_sum_3d_by_row_1000(benchmark):
    x = benchmark(_test_py_list_sum_3d_by_row_1000, data3)
    assert len(x) == 1000


def _test_np_list_sum_3d_by_col_1000(dat):
    x = np.sum(dat, axis=0)
    return x


def test_np_list_sum_3d_by_col_1000(benchmark):
    dat = np.array(data3, dtype=np.float64)
    x = benchmark(_test_np_list_sum_3d_by_col_1000, dat)
    assert len(x) == 3


def _test_py_list_sum_3d_by_col_1000(dat):
    # x = list(map(sum, zip(*dat)))
    s = (0.0, 0.0, 0.0)
    for t in dat:
        s = (s[0] + t[0], s[1] + t[1], s[2] + t[2])
    return s


def test_py_list_sum_3d_by_col_1000(benchmark):
    x = benchmark(_test_py_list_sum_3d_by_col_1000, data3)
    assert len(x) == 3
