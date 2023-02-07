#!/usr/bin/env python
from typing import Tuple, Dict, Union, NoReturn
import numpy as np

from PlaxisRectangleGrid import utils
from PlaxisRectangleGrid.calc_func import distance_euc


class Point(object):
    def __init__(self, pt):
        self._coords = pt

    @property
    def x(self):
        return self._coords[0]

    @x.setter
    def x(self, x):
        self._coords[0] = x

    @property
    def z(self):
        return self._coords[1]

    @z.setter
    def z(self, z):
        self._coords[0] = z

    @property
    def u_y(self) -> float:
        return self._coords[2]

    @u_y.setter
    def u_y(self, u_y: Union[int, float]) -> NoReturn:
        self._coords[2] = u_y

    @property
    def coords(self):
        return self._coords

    @coords.setter
    def coords(self, new_coords):
        self._coords = np.ndarray(new_coords, dtype='float')

    @property
    def xz(self):
        return self._coords[:2]

    def nearby_points(self,
                      points: np.ndarray,
                      eps_x=1,
                      eps_z=1
                      ) -> Tuple[np.ndarray, list]:
        """
        Функция поиска ближайщих точек массива для данной точки. Ищет в
        заданной окрестности (eps_x, eps_z). Поиск происходит делением
        точек на 4 части (верх-право, верх-лево, низ-право, низ-лево)
        относительно самой точки(центр) и последующим нахождением минимального
        расстояния(евклидова метрика) из расстояний каждой точки до центра в
        каждой четверти.

        :param points: массив точек [[x1, z1, u_y1], [x2, z2, u_y2] ...]
        :param eps_x: окрестность поиска по горизонтальной оси
        (имеет смысл задавать как шаг сетки)
        :param eps_z: окрестность поиска по вертикальной оси
        (имеет смысл задавать как шаг сетки)
        :return: возвращает массив ближайщих точек(максимум 4) и
        массив расстояний от этих точек до данной точки
        """

        right_limit = self.x + eps_x  # правая граница поиска
        left_limit = self.x - eps_x  # левая граница поиска
        upper_limit = self.z + eps_z  # верхняя граница поиска
        lower_limit = self.z - eps_z  # нижняя граница поиска

        # Ищем точки в заданной окрестности (eps_x, eps_z)
        eps_area = points[np.where(
            (points[:, 0] <= right_limit) &
            (points[:, 0] >= left_limit) &
            (points[:, 1] <= upper_limit) &
            (points[:, 1] >= lower_limit))]

        # создаем маску для точек лежащие левее(и на вертикальной линии
        # проходящей через данную точку) и правее от данной точки
        mask_vertical = eps_area[:, 0] <= self.x

        # в случае если все точки окажутся левее пробуем более строгое условие,
        # т.к. некоторые точки могут оказаться на вертикальной линии проходящей
        # через данную точку
        if np.sum(mask_vertical == True) == len(eps_area):
            mask_vertical = eps_area[:, 0] < self.x

        # по маске создаем массивы точек лежащих слева и справа
        right = eps_area[mask_vertical]
        left = eps_area[~mask_vertical]

        # для левых и правых точек создаем маски для точек лежащие выше(и на
        # горизонтальной линии проходящей через данную точку) и ниже от
        # данной точки
        right_mask = right[:, 1] >= self.z
        left_mask = left[:, 1] >= self.z

        # в случае если все точки окажутся выше пробуем более строгое условие,
        # т.к. некоторые точки могут оказаться на горизонтальной
        # линии проходящей через данную точку
        if np.sum(right_mask == True) == len(right):
            right_mask = right[:, 1] > self.z

        if np.sum(left_mask == True) == len(left):
            left_mask = left[:, 1] > self.z

        # по маскам создаем массивы точек лежащих в четвертях
        nearby_points = [right[right_mask],
                         right[~right_mask],
                         left[left_mask],
                         left[~left_mask]]

        nearby = []
        nearby_dist = []

        # для каждой четверти выбираем точку с наименьшим расстоянием
        for pts in nearby_points:
            if len(pts):
                dist = distance_euc(self.xz, pts[:, :-1])
                min_idx = dist.argmin()
                nearby.append(pts[min_idx])
                nearby_dist.append(dist[min_idx])
        return np.array(nearby), nearby_dist

    def point4vectors2d(self, points: np.ndarray) -> np.ndarray:
        """
        Определяет положение точки относительно векторов образованных из
        массива точек на плоскости. с помощью векторного произведения векторов.
        0 - принадлежит вектору,
        1 - лежит правее,
        -1 - лежит левее.

        :param points: массив точек
        :return: результат векторных произведений.
        """

        start_point = points[0, :-1]  # точка начала векторов
        end_points = points[1:, :-1]  # точки конца векторов

        vec_1 = self.xz - start_point  # вектор до данной точки
        vec_2 = end_points - start_point  # векторы до остальных точек

        # массив знаков векторных произведений
        return np.sign(np.cross(vec_2, vec_1))

    def __repr__(self):
        x, z, u_z = self._coords
        return f"x: {x}, z: {z} u_z: {u_z}"


def write_log(method):
    """
    Декоратор для записи лога операции над точками
    :param method: метод возвращающий команду и массив точек
    :return: возвращающая команду и массив точек
    """
    def wrapper(self, *args, **kwargs):
        command, points = method(self, *args, **kwargs)
        self.logs.append([command, points])
        return command, points
    return wrapper


class GridPoint(Point):
    """
    Класс узла сетки.
    """
    def __init__(self, pt):
        super().__init__(pt)
        self.logs = []

    @write_log
    def point4point2d(self,
                      points: np.ndarray,
                      dist: np.ndarray,
                      eps_match=0
                      ) -> Tuple[str, np.ndarray]:
        """
        Определяет взаимное положение точки относительно точки на плоскости.
        Возвращает кортеж из: командa ('point' - совпадают,
        'no_point' - не совпадают), ближайшая точка [x1, y1, z1].

        :param points: массив точек ([[x1, y1, z1], [x2, y2, z2], ...])
        :param dist: массив расстояний ([dist1, dist2, ....])
        :param eps_match: окрестность в которой точки можно считать совпадающим
        :return: (команда: 'point'/'no_point', ближайщая точка: [[x1, y1, z1]])
        """
        idx = np.argmin(dist)
        command = 'point' if dist[idx] <= eps_match else 'no_point'
        return command, points[idx].reshape(1, 3)

    @write_log
    def point4lines2d(self, points: np.ndarray) -> Tuple[str, np.ndarray]:
        """
        Определяет взаимное положение точки относительно прямой, заданной двумя
        точками на плоскости.
        Возвращает кортеж из: командa ('line' - принадлежит,
        'outside' - не принадлежит), points.
        :param points: массив из двух точек ([[x1, y1, z1], [x2, y2, z2]])
        :return: (команда: 'line'/'outside', [[x1, y1, z1], [x2, y2, z2]])
        """
        sign = self.point4vectors2d(points)

        if sign == 0:
            return 'line', points
        else:
            return 'outside', points

    @write_log
    def point4triangle2d(self, points: np.ndarray) -> Tuple[str, np.ndarray]:
        """
        Определяет положение точки относительно треугольника образованного
        тремя точками. Из 1ой точки проводим вектора V1,V2 до остальных двух и
        V3 до данной точки.
        Берем знаки векторных произведений (V1, V3), (V2, V3). Если знаки
        различны - данная точка лежит между этими векторами(внутри) и повторяем
        данные операции для следующей точки. Если знаки также различны - точка
        точка лежит внутри треугольника.
        Если знаки одинаковы - вне данных векторов и следовательно вне
        треугольника.
        Если произведение равно 0, то точка принадлежит данному вектору,
        следовательно можно применить методы и функции для точки и линии.

        Возвращает кортеж из: командa ('line' - принадлежит линии,
        'inside' - принадлежит области, 'outside' - не принадлежит области),
        points.

        :param points: массив из двух точек ([[x1, y1, z1], [x2, y2, z2], ,
        [x3, y3, z3]])
        :return: ('line', [[x, y, z], [x*, y*, z*]]) \\ ('outside'/'inside',
        [[x1, y1, z1], [x2, y2, z2], [x3, y3, z3]])
        """
        # создаем 2 набора точек.
        # Для второго набора делаем смещение элементов вправо на 1 шаг.
        sets_points = np.array([points, np.roll(points, 1, axis=0)])
        for set_ in sets_points:
            sign = self.point4vectors2d(set_)  # знаки векторного произведения

            if np.any(sign == 0):
                # возвращаем пару точек при которых векторное произведение
                # равно 0
                end_point = set_[1:][sign == 0].reshape(-1)
                return 'line', np.array([set_[0], end_point])

            elif np.all(sign == sign[0]):
                return 'outside', np.array(points)

        return 'inside', np.array(points)


class RectangleGrid(object):
    """
    Класс создает массив точек(узлов) прямоугольной сетки.
    """

    def __init__(self,
                 length: Union[int, float],
                 depth: Union[int, float],
                 step_z: Dict[int, Union[int, float]]):
        self.length = length
        self.depth = depth
        self._step_x = self.set_step_x()
        self._step_z = self.set_step_z(step_z)
        self._grid_x = None
        self._grid_z = None
        self.journal_pts = self.create_grid()
        self.main_info = {'Points': len(self.journal_pts),
                          'Success': 0,
                          'Errors': 0
                          }

    def set_step_z(self, step: Dict[int, Union[int, float]]) -> float:
        """
        Устанавливает шаг сетки по Z.
        """
        return float(step[self.depth])

    def set_step_x(self) -> float:
        """
        Устанавливает шаг сетки по X.
        """
        return 1. if self.length < 60 else 5.

    @property
    def grid_x(self) -> np.ndarray:
        return self._grid_x

    @grid_x.setter
    def grid_x(self, array: np.ndarray) -> NoReturn:
        self._grid_x = array

    @property
    def grid_z(self) -> np.ndarray:
        return self._grid_z

    @grid_z.setter
    def grid_z(self, array: np.ndarray) -> NoReturn:
        self._grid_z = array

    @property
    def step_x(self) -> float:
        return self._step_x

    @property
    def step_z(self) -> float:
        return self._step_z

    def create_grid(self) -> Dict[Tuple[int, int], GridPoint]:
        """
        Создает узлы сетки как класс GridPoint для каждого узла,
        на длине и глубине равной self.length, self.depth и шагом
        self._step_x, self._step_z. Узел имеет координаты [x, z, 0.].
        Связывает эти узлы с координатами ячейки на листе в excel.
        :return: Возвращает словарь, где ключ - координатами ячейки на
        листе в excel; значение - объект GridPoint([x, z, 0.])
        """

        length = self.length
        depth = self.depth
        step_x = self._step_x
        step_z = self._step_z

        self._grid_x = np.arange(-length / 2, length / 2 + 1, step_x)
        grid_z = np.arange(0, depth + step_z, step_z)
        grid_z[-1] = self.depth
        self._grid_z = grid_z

        journal_pts = {(row, col): GridPoint([x, z, 0.])
                       for col, x in enumerate(self._grid_x, 2)
                       for row, z in enumerate(self._grid_z, 2)}
        return journal_pts


class SheetInfo:
    """
    Класс для создания журнала операций на листе excel.
    Производит оформление листа.
    Производит запись операции по узлу GridPoint(Point).
    Вид операции для записи имеет вид:
    GridPoint[x, z, u_y] [('команда', массив_точек), ........ ]
    Использует стили оформления таблицы из класса SheetInfoStyles.
    """

    TITLE_HEADER = {'grid_X': 1,
                    'grid_Z': 2,
                    'grid_u_Y': 3,
                    'command': 4,
                    'X': 5,
                    'Z': 6,
                    'u_Y': 7
                    }

    def __init__(self, sheet, main_info: dict) -> None:
        """
        Инициализация атрибутов экземпляра класса. Создает строки с основной
        информацией содержащейся в переданном словаре main_info.
        Создает атрибут с экземпляром класса SheetInfoStyles являющийся набором
        шаблонов стилей оформления ячеек.

        :param sheet: лист в excel файле
        :param main_info: {'Points': 12345,'Success': 12340, 'Errors': 5}
        """

        self.sheet = sheet
        self.row = 1  # используем как указатель для строки
        self.col = 1
        self.styles = utils.SheetInfoStyles()  # стили оформления
        self.__main_info(main_info)
        self.__header()

    def __main_info(self, main_info: dict) -> NoReturn:
        """
        Создает строки с основной информацией по узлам сетки.
        :param main_info: {'Points': 12345,'Success': 12340, 'Errors': 5}
        :return: NoReturn
        """
        field_col = self.col  # номер столбца полей
        value_col = self.col + 1  # номер столбца для значений полей

        for row, (field, value) in enumerate(main_info.items(), self.row):
            # устанавливаем высоту строк
            self.sheet.row_dimensions[row].height = 20

            # Записываем название поля и оформляем ячейку
            cell = self.sheet.cell(row=row, column=field_col, value=field)
            cell.style = self.styles.main_cell
            cell.number_format = '@'

            # Записываем значение поля и оформляем ячейку
            cell = self.sheet.cell(row=row, column=value_col, value=value)
            cell.style = self.styles.main_cell
            cell.number_format = '0'

            self.row += 1  # перемещаем на следующую строку
        self.row += 2  # пустые строки до таблицы

    def __header(self) -> NoReturn:
        """
        Оформление шапки таблицы операций. Записываем названия столбцов из
        атрибута класса TITLE_HEADER.
        :return: NoReturn
        """
        # устанавливаем высоту строки шапки
        self.sheet.row_dimensions[self.row].height = 25

        # заполняем шапку таблицы
        for field, col in self.TITLE_HEADER.items():
            cell = self.sheet.cell(row=self.row, column=col, value=field)
            cell.style = self.styles.header
            cell.number_format = '@'

            # устанавливаем ширину столбца
            col_letter = cell.column_letter  # получаем букву столбца
            self.sheet.column_dimensions[col_letter].width = 13
        self.row += 1  # перемещаем указатель на новую строку

    def write_journal(self, point: GridPoint) -> NoReturn:
        """
        Запись журнала операций для узла GridPoint.
        Вид операции для записи имеет вид:
        GridPoint[x, z, u_y] [('команда', [массив_точек]), ........ ]
        Использует стили оформления таблицы из класса SheetInfoStyles.
        :param point: экземпляр класса GridPoint
        :return: NoReturn
        """

        # устанавливаем высоту первой стоки строки
        self.sheet.row_dimensions[self.row].height = 20
        column = self.col  # локальный счетчик для столбцов

        """
        используем 2 стиля оформления для визуальной индикации успеха/не_успеха
        найденного перемещения в узле:
              self.styles.success - если значение перемещения не равно None;
              self.styles.errors - если значение перемещения равно None;
        """
        style = self.styles.errors if point.u_y is None else self.styles.success

        # записываем координаты узла
        for col, value in enumerate(point.coords, column):
            cell = self.sheet.cell(row=self.row, column=col, value=value)
            cell.style = style
            cell.font = self.styles.grid_pt_font

            # это условие требуется тк. для координаты u_y требуется повышенное
            # отображение десятичных знаков
            if col == 3:
                cell.number_format = '0.000000'
            else:
                cell.number_format = '0.00'
            column += 1

        # записываем произведенные операции над ближайшими точками узла
        for logs in point.logs:
            # лог имеет вид ('команда', [массив_точек])
            command, points = logs

            # записываем команду
            cell = self.sheet.cell(row=self.row, column=column, value=command)
            cell.style = style

            # в цикле записываем все точки над которыми производилась операция
            for point in points:
                # покоординатно записываем все координаты точки в свой столбец
                for col, value in enumerate(point, column + 1):

                    cell = self.sheet.cell(row=self.row,
                                           column=col,
                                           value=value)
                    cell.style = style
                    cell.number_format = '0.000000'
                self.row += 1  # перемещаем указатель на новую строку
            # перемещаем указатель на новую строку
            # (для визуального разделения операций и узлов)
            self.row += 1
