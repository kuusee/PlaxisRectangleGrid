#!/usr/bin/env python
import numpy as np


def distance_euc(point: np.ndarray, points: np.ndarray) -> np.ndarray:
    """
    Функция для подсчета евклидова расстояния методом "Соглашение Эйнштейна"

    https://habr.com/ru/post/544498/

    https://stackoverflow.com/questions/1401712/how-can-the-euclidean-distance
    -be-calculated-with-numpy

    :param point: начальная точка ([x, z])
    :param points: вторые точки ([[x1, z1], [x2, z2], [x3, z3]...)
    :return: расстояния от point до points ([dist1, dist2, dist3, ...])
    """
    vector_coords = (points - point).T
    return np.sqrt(np.einsum("ij,ij->j", vector_coords, vector_coords))


def intersect(point: np.ndarray, points: np.ndarray) -> float:
    """
    Функция вычисляет точку пересечения плоскости образованной
    3 точками(points) и прямой проходящей через точку point перпендикулярной
    плоскости (XoY). В основе лежит преобразованный метод из аналитической
    геометрии.

    :param point: точка на плоскости XoY ([x, y])
    :param points: точки пространства ([[x1, y1, z1], [x2, y2, z2],
    [x3, y3, z3]])
    :return: координата пересечения прямой и плоскости
    """
    p1 = points[0]
    p2 = points[1]
    p3 = points[2]

    p1x, p1y, p1z = p1
    nx, ny = point[0], point[1]

    vec_1 = p2 - p1
    vec_2 = p3 - p1

    a = np.cross(vec_1[1:], vec_2[1:])  # минор 1.1
    b = (-1) * np.cross(vec_1[[0, 2]], vec_2[[0, 2]])  # минор 1.2
    c = np.cross(vec_1[:2], vec_2[:2])  # минор 1.3

    ax = a * (nx - p1x)
    by = b * (ny - p1y)
    cz = c * p1z

    nz = (-1) * (ax + by - cz) / c
    return nz


def interpolate(point: np.ndarray, points: np.ndarray) -> float:
    """
    Функция вычисляет значение в точке методом линейной интерполяции.
    Точка point должна принадлежать проекции линии проходящей через
    2 точки points на плоскость XoY.

    :param point: точка на плоскости XoY ([x, y])
    :param points: точки пространства ([[x1, y1, z1], [x2, y2, z2]])
    :return: перемещение для точки point по 3ей координате
    """
    p1x, p1z, p1_uy = points[0]
    p2x, p2z, p2_uy = points[1]
    y1, y2 = p1_uy, p2_uy
    nx, nz = point[:-1]

    if p1x == p2x:
        x1, x2 = p1z, p2z
        x = nz

    elif p1z == p2z:
        x1, x2 = p1x, p2x
        x = nx

    else:
        x1, x2 = 0, distance_euc(points[0][:-1], points[1][:-1])
        x = distance_euc(points[0][:-1], point[:-1])

    u_y = (y1 - y2) * (x - x2) / (x1 - x2) + y2

    return u_y
