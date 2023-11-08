from ultralytics import YOLO
from PIL import Image
import cv2
import numpy as np
import os
import yaml
from fastseg.image import colorize
import time

class IPMTransformer(object):
    def __init__(self, homography_matrix=None):
        """
        Конструктор класса IPMTransformer.

        Args:
            homography_matrix (numpy.ndarray, optional): Матрица гомографии, инициализируется пустой матрицей, если не предоставлена.
        """
        self.__h = homography_matrix

    def calc_homography(self, pts_src, pts_dst):
        """
        Метод для вычисления матрицы гомографии на основе набора исходных точек (pts_src) и соответствующих точек назначения (pts_dst).
        Использует функцию cv2.findHomography для выполнения вычислений.

        Args:
            pts_src (numpy.ndarray): Массив исходных точек.
            pts_dst (numpy.ndarray): Массив точек назначения.

        Returns:
            numpy.ndarray: Матрица гомографии.
        """
        self.__h, status = cv2.findHomography(pts_src, pts_dst, cv2.RANSAC)
        return self.__h

    def get_homography_matrix(self):
        """
        Метод для получения матрицы гомографии, которая была вычислена или установлена ранее.

        Returns:
            numpy.ndarray: Матрица гомографии.
        """
        return self.__h

    def get_ipm(self, im_src, dst_size=(1200, 800), horizont=0, is_mono=False, need_cut=True):
        """
        Метод для выполнения обратного преобразования перспективы (Inverse Perspective Mapping) на исходном изображении im_src.

        Args:
            im_src (numpy.ndarray): Исходное изображение, на которое будет применено обратное преобразование перспективы.
            dst_size (tuple, optional): Размер целевого изображения после преобразования (по умолчанию (1200, 800)).
            horizont (int, optional): Высота горизонтальной линии, используемой для обрезки изображения (по умолчанию 0).
            is_mono (bool, optional): Флаг, указывающий, является ли исходное изображение монохромным (по умолчанию False).
            need_cut (bool, optional): Флаг, указывающий, нужно ли обрезать изображение для удаления нулевых строк и столбцов в результате (по умолчанию True).

        Returns:
            numpy.ndarray: Преобразованное изображение после применения обратного преобразования перспективы.
        """
        im_src = im_src[horizont:, :]  # Обрезаем изображение по горизонтали, если задана высота горизонтали
        im_dst = cv2.warpPerspective(im_src, self.__h, dst_size)  # Применяем матрицу гомографии
        if not need_cut:
            return im_dst
        if not is_mono:
            rows = np.sum(im_dst, axis=(1, 2))
            cols = np.sum(im_dst, axis=(0, 2))
        else:
            rows = np.sum(im_dst, axis=(1))
            cols = np.sum(im_dst, axis=(0))

        nonzero_rows = len(rows[np.nonzero(rows)])  # Находим ненулевые строки
        nonzero_cols = len(cols[np.nonzero(cols)])  # Находим ненулевые столбцы
        im_dst = im_dst[:nonzero_rows, :nonzero_cols]  # Обрезаем изображение до ненулевых строк и столбцов
        im_dst = cv2.resize(im_dst, (im_dst.shape[1], im_dst.shape[1]), interpolation=cv2.INTER_AREA)  # Изменяем размер
        return im_dst


class MapBuilder(object):
    def __init__(self, model_path, ipm_config):
        self.__model = YOLO(model_path)
        self.load_ipm_config(ipm_config)
        self.__corr_depth_pos = (0, 10)


    def detect_objects(self, image):
        #results = self.__model.predict(source=image, save=False, save_txt=False)
        results = self.__model.track(source=image, persist=True)
        return results

    def load_ipm_config(self, config_path):
        if not os.path.exists(config_path):
            print('Config file not found. Use default values')
            return
        with open(config_path) as file:
            config = yaml.full_load(file)
        self.__homograpthy_matrix = np.array(config['homography'])
        self.__horizont_line_height = config['horizont']
        self.__img_height = config['height']
        self.__img_width = config['width']


    def generate_ipm(self, image, is_mono = False, need_cut=True):
        ipm_transformer = IPMTransformer(homography_matrix=self.__homograpthy_matrix)
        img_ipm = ipm_transformer.get_ipm(image, is_mono=is_mono, horizont=self.__horizont_line_height, need_cut=need_cut)
        return img_ipm

    def get_labels(self):
        labels = {0: u'__background__', 1: u'person', 2: u'bicycle', 3: u'car', 4: u'motorcycle', 5: u'airplane',
                    6: u'bus', 7: u'train', 8: u'truck', 9: u'boat', 10: u'traffic light', 11: u'fire hydrant',
                    12: u'stop sign', 13: u'parking meter', 14: u'bench', 15: u'bird', 16: u'cat', 17: u'dog',
                    18: u'horse', 19: u'sheep', 20: u'cow', 21: u'elephant', 22: u'bear', 23: u'zebra', 24: u'giraffe',
                    25: u'backpack', 26: u'umbrella', 27: u'handbag', 28: u'tie', 29: u'suitcase', 30: u'frisbee',
                    31: u'skis', 32: u'snowboard', 33: u'sports ball', 34: u'kite', 35: u'baseball bat',
                    36: u'baseball glove', 37: u'skateboard', 38: u'surfboard', 39: u'tennis racket', 40: u'bottle',
                    41: u'wine glass', 42: u'cup', 43: u'fork', 44: u'knife', 45: u'spoon', 46: u'bowl', 47: u'banana',
                    48: u'apple', 49: u'sandwich', 50: u'orange', 51: u'broccoli', 52: u'carrot', 53: u'hot dog',
                    54: u'pizza', 55: u'donut', 56: u'cake', 57: u'chair', 58: u'couch', 59: u'potted plant', 60: u'bed',
                    61: u'dining table', 62: u'toilet', 63: u'tv', 64: u'laptop', 65: u'mouse', 66: u'remote',
                    67: u'keyboard', 68: u'cell phone', 69: u'microwave', 70: u'oven', 71: u'toaster', 72: u'sink',
                    73: u'refrigerator', 74: u'book', 75: u'clock', 76: u'vase', 77: u'scissors', 78: u'teddy bear',
                    79: u'hair drier', 80: u'toothbrush'}

        return labels

    def calc_box_distance(self, boxes, depth_map):
        box_depths = []
        for box in boxes:
            depths = []
            for i in range(int(box[0]), int(box[2])):
                for j in range(int(box[1]) - self.__horizont_line_height, int(box[3]) - self.__horizont_line_height):
                    depths.append(depth_map[j + self.__corr_depth_pos[1], i + self.__corr_depth_pos[0]])
            depths.sort(reverse=True)
            box_depths.append(np.percentile(depths, 90))
        return box_depths

    def calc_bev_point(self, p):
        m = self.__homograpthy_matrix
        px = ((m[0][0] * p[0] + m[0][1] * p[1] + m[0][2])
              / ((m[2][0] * p[0] + m[2][1] * p[1] + m[2][2])))
        py = ((m[1][0] * p[0] + m[1][1] * p[1] + m[1][2])
              / ((m[2][0] * p[0] + m[2][1] * p[1] + m[2][2])))
        return (int(px), int(py))

    def transform_boxes(self, boxes):
        box_points = []
        widths = []
        for box in boxes:
            # p = np.asarray([box[0] + (box[2] - box[0]) / 2, box[1] + (box[3] - box[1]) / 2 - self.__horizont_line_height], dtype='float32')
            p = np.asarray([box[0] + (box[2] - box[0]) / 2, box[3] - self.__horizont_line_height], dtype='float32')
            widths.append(box[2] - box[0])
            box_points.append(self.calc_bev_point(p))
        return box_points, widths

    def resize_img(self, image):
        return cv2.resize(image, (self.__img_width, self.__img_height))


