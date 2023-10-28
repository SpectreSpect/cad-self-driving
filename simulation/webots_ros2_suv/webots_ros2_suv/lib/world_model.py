import rclpy
import os
import pathlib
import yaml
import numpy as np
from ament_index_python.packages import get_package_share_directory
from .car_model import CarModel

class WorldModel(object):
    '''
    Класс, моделирующий параметры внешней среды в привязке к глобальной карте.
    '''
    def __init__(self):
        self.__car_model = CarModel()
        # корректировка координат, необходима для установления соотвествия между координатами симулятора и OSM карты
        # кортеж значений (x, y, direction)
        self.__coord_corrections = (0, 0, 0)
        self.__load_config()

        self.__EARTH_RADIUS_KM = 6378.137

    def __get_latitude(self, latitude: float, meters: float) -> float:
        m: float = (1 / ((2 * math.pi / 360) * self.__EARTH_RADIUS_KM)) / 1000
        return latitude + (meters * m)

    def __get_longitude(self, longitude: float, meters: float) -> float:
        latitude: float = 0.0
        m: float = (1 / ((2 * math.pi / 360) * self.__EARTH_RADIUS_KM)) / 1000
        return longitude + (meters * m) / math.cos(latitude * (math.pi / 180))

    def __load_config(self):
        package_dir = get_package_share_directory('webots_ros2_suv')
        config_path = os.path.join(package_dir,
                                    pathlib.Path(os.path.join(package_dir, 'config', 'global_coords.yaml')))
        if not os.path.exists(config_path):
            print('Global map coords config file file not found. Use default values')
            return
        with open(config_path) as file:
            config = yaml.full_load(file)
        self.__coord_corrections = (config['x'], config['y'], config['orientation'])
        print('Translation coordinates: ', self.__coord_corrections)

    def get_global_coords(self, lat, lon):
        latitude = self.__get_latitude(self.__coord_corrections[0], lat)
        longitude = self.__get_longitude(self.__coord_corrections[1], lon)
        self.__car_model.update(lat=latitude, lon=longitude)
        return latitude, longitude

    def get_current_position(self):
        return self.__car_model.get_position()
