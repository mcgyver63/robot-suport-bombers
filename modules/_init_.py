"""
Paquet de mòduls per al Sistema de Control de Robot per a Bombers.
Conté els components funcionals modulars per a la comunicació, sensors, LiDAR, càmera, 
navegació i configuració.
"""

__version__ = '1.0.0'

# Importar els mòduls per facilitar l'accés
from . import connection
from . import sensors
from . import lidar
from . import camera
from . import navigation
from . import config
from . import utils
from . import ai

# Exportar classes principals per accés directe
from .connection import ConnectionManager
from .sensors import SensorManager
from .lidar import LidarManager
from .camera import CameraManager
from .navigation import NavigationManager, Mode, Direction
from .config import ConfigManager
from .ai import AIManager

__all__ = [
    'ConnectionManager',
    'SensorManager',
    'LidarManager',
    'CameraManager',
    'NavigationManager',
    'ConfigManager',
    'AIManager',
    'Mode',
    'Direction',
    'connection',
    'sensors',
    'lidar',
    'camera',
    'navigation',
    'config',
    'utils',
    'ai',
]

    

