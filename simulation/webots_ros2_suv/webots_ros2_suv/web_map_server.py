import cherrypy
import json
from PIL import Image
from io import BytesIO
import os
import csv
import traceback
import yaml

BASE_PATH = '/Users/hiber/ros_ws/src/webots_ros2_suv/'
STATIC_PATH = BASE_PATH + 'map-server/dist/'
YAML_PATH = BASE_PATH + 'resource/map-config/robocross.yaml'
ASSETS_PATH = STATIC_PATH + 'assets/'

class MapServer(object):
    def __init__(self):
        try:
            pass
        except  Exception as err:
            print(''.join(traceback.TracebackException.from_exception(err).format()))

    @cherrypy.expose
    def index(self):
        raise cherrypy.HTTPRedirect("/static/index.html")
    
    @cherrypy.expose
    @cherrypy.tools.json_out()
    def get_point_types(self):
        try:
            with open(YAML_PATH, 'r') as file:
                point_types = yaml.safe_load(file)
                print(point_types)
                return {'status': 'ok', 'pointtypes': point_types}
        except Exception as err:
            return {'status': ''.join(traceback.TracebackException.from_exception(err).format())}
    
def main(args=None):
    try:
        cherrypy.quickstart(MapServer(), '/', {'global':
                                                   {'server.socket_host': '127.0.0.1',
                                                    'server.socket_port': 8008,
                                                    'tools.staticdir.root': STATIC_PATH,
                                                    'log.error_file': 'site.log'
                                                    },
                                               '/static': {
                                                   'tools.staticdir.on': True,
                                                   'tools.staticdir.dir': STATIC_PATH,
                                                   'tools.staticdir.index': 'index.html'
                                               },
                                               '/assets': {
                                                   'tools.staticdir.on': True,
                                                   'tools.staticdir.dir': ASSETS_PATH,
                                                   'tools.staticdir.index': 'index.html'
                                               }
                                               })
    except  Exception as err:
        print(''.join(traceback.TracebackException.from_exception(err).format()))

if __name__ == '__main__':
    main()