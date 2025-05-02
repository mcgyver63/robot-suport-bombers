"""
Sistema de Control de Robot per a Bombers
=========================================
Aplicació principal per al control i monitorització del robot.
"""

# Imports de biblioteques estàndard
import os
import sys
import logging
from logging.handlers import RotatingFileHandler
import configparser
import time
import datetime
import traceback
import sqlite3

# Imports de biblioteques de tercers
from PyQt5.QtWidgets import QApplication, QSplashScreen, QMessageBox
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt, QTimer

# Imports locals
from modules.config import ConfigManager
from modules.connection import ConnectionManager
from modules.sensors import SensorManager
from modules.lidar import LidarManager
from modules.camera import CameraManager
from modules.navigation import NavigationManager
from modules.db import DBManager
from ui.main_window import MainWindow
from ui.project_dialog import ProjectDialog
from modules.ai import AIManager

# Configuració inicial de logging
log_formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("MainApp")


class MainApp:
    """Classe principal de l'aplicació."""

    def __init__(self):
        """Inicialitza l'aplicació principal."""
        # Directoris base de l'aplicació
        self.base_dir = os.path.abspath(os.path.dirname(__file__))
        self.app_data_dir = os.path.join(
            os.path.expanduser("~"),
            "AppData",
            "Local",
            "UPC",
            "Sistema de Control de Robot per a Bombers")
        self.config_file = os.path.join(self.app_data_dir, "config.ini")

        # Inicialitzar logging
        self._init_logging()

        # Inicialitzar directoris
        self._init_directories()

        # Inicialitzar base de dades
        self._init_database()

        # Carregar configuració
        self._load_config()

        # Inicialitzar components i finestra principal
        self._init_application()

        # Connectar signals/slots
        self._connect_signals()

        logger.info("Aplicació inicialitzada correctament")
        
    def _init_logging(self):
        """Inicialitza el sistema de logging."""
        try:
            # Crear directori de logs si no existeix
            logs_dir = os.path.join(self.app_data_dir, "logs")
            os.makedirs(logs_dir, exist_ok=True)

            # Fitxer de log amb rotació
            log_file = os.path.join(logs_dir, "robot_control.log")
            file_handler = RotatingFileHandler(
                log_file, maxBytes=5 * 1024 * 1024, backupCount=5)
            file_handler.setFormatter(log_formatter)
            file_handler.setLevel(logging.INFO)

            # Handler de consola
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(log_formatter)
            console_handler.setLevel(logging.DEBUG)

            # Configurar el logger principal
            root_logger = logging.getLogger()
            root_logger.setLevel(logging.INFO)
            root_logger.addHandler(file_handler)
            root_logger.addHandler(console_handler)

            logger.info("Sistema de logging inicialitzat")
        except Exception as e:
            print(f"Error inicialitzant logging: {e}")
            raise

    def _init_directories(self):
        """Inicialitza els directoris necessaris per a l'aplicació."""
        try:
            # Directori d'AppData
            os.makedirs(self.app_data_dir, exist_ok=True)

            # Directoris per a dades
            data_dir = os.path.join(self.app_data_dir, "data")
            os.makedirs(data_dir, exist_ok=True)

            # Directori per a captures
            captures_dir = os.path.join(self.app_data_dir, "captures")
            os.makedirs(captures_dir, exist_ok=True)

            # Directoris per a registres
            logs_dir = os.path.join(self.app_data_dir, "logs")
            os.makedirs(logs_dir, exist_ok=True)

            logger.info("Directoris de l'aplicació inicialitzats")
        except Exception as e:
            logger.error(f"Error inicialitzant directoris: {e}")
            raise

    def _init_database(self):
        """Inicialitza la base de dades."""
        try:
            # Directori per a la base de dades
            db_dir = os.path.join(self.base_dir, "db")
            os.makedirs(db_dir, exist_ok=True)

            # Ruta al fitxer de la base de dades
            db_file = os.path.join(db_dir, "projects.db")

            # Inicialitzar gestor de base de dades
            self.db_manager = DBManager(db_file)
            self.db_manager.init_db()

            logger.info(f"Base de dades inicialitzada: {db_file}")
        except Exception as e:
            logger.error(f"Error inicialitzant base de dades: {e}")
            raise

    def _load_config(self):
        """Carrega la configuració de l'aplicació."""
        try:
            # Inicialitzar gestor de configuració
            self.config_manager = ConfigManager(self.config_file)
            config = self.config_manager.config

            # Assegurar-se que les seccions bàsiques existeixen
            if 'connection' not in config:
                config['connection'] = {}
                config['connection']['host'] = '192.168.1.100'
                config['connection']['port'] = '9999'

            # Assegurar que la configuració de sensors existeix amb estructura correcta
            if 'sensors' not in config:
                config['sensors'] = {}
            
            # Definir les propietats per cada tipus de sensor
            sensor_types = {
                'temperature': {'threshold': 45.0, 'unit': '°C'},
                'humidity': {'threshold': 90.0, 'unit': '%'},
                'gas': {'threshold': 1000.0, 'unit': 'ppm'},
                'co': {'threshold': 50.0, 'unit': 'ppm'},
                'smoke': {'threshold': 30.0, 'unit': '%'},
                'battery': {'threshold': 20.0, 'unit': '%'}
            }
            
            # Afegir configuració per cada sensor si no existeix
            for sensor_type, properties in sensor_types.items():
                if sensor_type not in config['sensors']:
                    config['sensors'][sensor_type] = {}
                if 'threshold' not in config['sensors'][sensor_type]:
                    config['sensors'][sensor_type]['threshold'] = properties['threshold']
                if 'unit' not in config['sensors'][sensor_type]:
                    config['sensors'][sensor_type]['unit'] = properties['unit']

            # Assegurar que la configuració de LiDAR existeix
            if 'lidar' not in config:
                config['lidar'] = {}
                config['lidar']['enabled'] = True
                config['lidar']['scan_frequency'] = 5  # Hz
                config['lidar']['max_distance'] = 3000  # mm

            # Assegurar que la configuració de càmera existeix
            if 'camera' not in config:
                config['camera'] = {}
                config['camera']['enabled'] = True
                config['camera']['resolution'] = '640x480'
                config['camera']['fps'] = 15

            # Assegurar que la configuració de navegació existeix
            if 'navigation' not in config:
                config['navigation'] = {}
                config['navigation']['default_speed'] = 150
                config['navigation']['obstacle_threshold'] = 500  # mm

            # Desar canvis si s'han fet
            self.config_manager.save_config()

        except Exception as e:
            logger.error(f"Error carregant configuració: {e}")
            raise

    
    def _check_dependencies(self):
        """Comprova que totes les dependències estiguin instal·lades."""
        # Comprovar PyQt5
        try:
            from PyQt5.QtCore import QT_VERSION_STR
            logger.info(f"PyQt5 disponible (versió {QT_VERSION_STR})")
        except ImportError:
            logger.error("PyQt5 no està instal·lat")
            QMessageBox.critical(
                None,
                "Error de dependències",
                "PyQt5 no està instal·lat.\nInstal·leu-lo amb: pip install PyQt5"
            )
            sys.exit(1)
        
        # Comprovar altres dependències essencials
        try:
            import numpy
            logger.info(f"NumPy disponible (versió {numpy.__version__})")
        except ImportError:
            logger.warning("NumPy no està instal·lat. Algunes funcionalitats poden no funcionar correctament.")
        
        # Comprovar Matplotlib (opcional però recomanat per a visualitzacions)
        try:
            import matplotlib
            logger.info(f"Matplotlib disponible (versió {matplotlib.__version__})")
        except ImportError:
            logger.warning("Matplotlib no està instal·lat. Les visualitzacions de LiDAR seran limitades.")
        
        # Comprovar OpenCV (opcional però recomanat per a processament d'imatge)
        try:
            import cv2
            logger.info(f"OpenCV disponible (versió {cv2.__version__})")
        except ImportError:
            logger.warning("OpenCV no està instal·lat. El processament d'imatges serà limitat.")
        
        # Comprovar SQLite (necessari per a la base de dades)
        try:
            sqlite_version = sqlite3.sqlite_version
            logger.info(f"SQLite disponible (versió {sqlite_version})")
        except Exception as e:
            logger.error(f"Error comprovant SQLite: {e}")
            QMessageBox.critical(
                None,
                "Error de dependències",
                "No s'ha pogut verificar SQLite, necessari per a la base de dades."
            )
            sys.exit(1)
        
    def _init_application(self):
        """Inicialitza els components principals de l'aplicació."""
        try:
            # Obtenir configuració
            config = self.config_manager.config

            # Inicialitzar gestor de connexió
            connection_config = {
                'connection': {
                    'host': config['connection']['host'],
                    'port': int(config['connection']['port']),
                    'auto_reconnect': True,
                    'reconnect_interval': 5
                }
            }
            self.connection_manager = ConnectionManager(connection_config)

            # Inicialitzar gestor de sensors
            # Passem la configuració completa, ja que el SensorManager sap com trobar els paràmetres
            self.sensor_manager = SensorManager(config)

            # Inicialitzar gestor de LiDAR
            lidar_config = {
                'lidar': {
                    'enabled': True,
                    'scan_frequency': config['lidar'].get('scan_frequency', 5),
                    'max_distance': config['lidar'].get('max_distance', 3000)
                }
            }
            self.lidar_manager = LidarManager(lidar_config)

            # Inicialitzar gestor de càmera
            camera_config = {
                'camera': {
                    'enabled': True,
                    'resolution': config['camera'].get('resolution', '640x480'),
                    'fps': int(config['camera'].get('fps', 15))
                }
            }
            self.camera_manager = CameraManager(camera_config)

            # Inicialitzar gestor de navegació
            navigation_config = {
                'navigation': {
                    'default_speed': config['navigation'].get('default_speed', 150),
                    'obstacle_threshold': config['navigation'].get('obstacle_threshold', 500)
                }
            }
            self.navigation_manager = NavigationManager(navigation_config)

            # Configurar components interdependents
            self.navigation_manager.setup_components(
                self.connection_manager,
                self.lidar_manager
            )

            # Inicialitzar gestor d'IA
            ai_config = {
                'ai': {
                    'enabled': True,
                    'model_path': os.path.join(self.base_dir, "models", "object_detection_model")
            }
}
            self.ai_manager = AIManager(ai_config)

            # Inicialitzar finestra principal
            self.main_window = MainWindow(
                config=config,
                connection_manager=self.connection_manager,
                sensor_manager=self.sensor_manager,
                lidar_manager=self.lidar_manager,
                camera_manager=self.camera_manager,
                navigation_manager=self.navigation_manager,
                db_manager=self.db_manager,
                config_manager=self.config_manager,
                ai_manager=self.ai_manager 
            )

            # Mostrar finestra
            self.main_window.show()

            # Iniciar projecte per defecte
            self._init_default_project()

            # Iniciar sessió
            self._start_session()

        except Exception as e:
            logger.error(f"Error inicialitzant l'aplicació: {e}")
            logger.error(traceback.format_exc())
            QMessageBox.critical(
                None,
                "Error d'inicialització",
                f"No s'ha pogut inicialitzar l'aplicació:\n{str(e)}"
            )
            raise

    def _connect_signals(self):
        """Connecta els signals/slots entre components."""
        try:
            # Connectar signal d'actualització de sensors a la UI
            if hasattr(self.sensor_manager, 'sensors_updated') and \
               hasattr(self.main_window, 'update_all_sensors_data'):
                self.sensor_manager.sensors_updated.connect(
                    self.main_window.update_all_sensors_data)

            # Connectar signal d'actualització de LiDAR a la UI
            if hasattr(self.lidar_manager, 'lidar_data_updated') and \
               hasattr(self.main_window, 'update_lidar_view'):
                self.lidar_manager.lidar_data_updated.connect(
                    self.main_window.update_lidar_view)

            # Connectar signal d'actualització de càmera a la UI
            if hasattr(self.camera_manager, 'camera_frame_ready') and \
               hasattr(self.main_window, 'update_camera_view'):
                self.camera_manager.camera_frame_ready.connect(
                    self.main_window.update_camera_view)

            logger.info("Signals/slots connectats correctament")
        except Exception as e:
            logger.warning(f"Error connectant signals/slots: {e}")           ("NumPy no està instal·lat. Algunes funcionalitats poden no funcionar correctament.")
    
    def _init_default_project(self):
        """Inicialitza el projecte per defecte si no existeix."""
        try:
            # Comprovar si existeix algun projecte
            projects = self.db_manager.get_projects()

            if not projects:
                # Crear projecte per defecte
                project_id = self.db_manager.save_project(
                    "Projecte per defecte",
                    "Projecte creat automàticament en la primera execució de l'aplicació."
                )

                if project_id:
                    logger.info(
                        f"Projecte desat: Projecte per defecte (ID: {project_id})")
                else:
                    logger.warning(
                        "No s'ha pogut crear el projecte per defecte")
        except Exception as e:
            logger.error(f"Error inicialitzant projecte per defecte: {e}")

    def _start_session(self):
        """Inicia una nova sessió de treball."""
        try:
            # Obtenir el primer projecte (normalment el projecte per defecte)
            projects = self.db_manager.get_projects()

            if projects:
                project_id = projects[0]['id']

                # Crear una nova sessió
                if hasattr(self.db_manager, 'start_session'):
                    session_id = self.db_manager.start_session(project_id)

                    if session_id:
                        self.current_session_id = session_id
                        self.session_start_time = time.time()
                        logger.info(
                            f"Sessió iniciada: {session_id} (Projecte: {project_id})")

                        # Si la MainWindow té un mètode per actualitzar la
                        # sessió, cridar-lo
                        if hasattr(self.main_window, 'set_current_session'):
                            self.main_window.set_current_session(session_id)
                    else:
                        logger.warning("No s'ha pogut iniciar la sessió")
                        self.current_session_id = None
                else:
                    logger.info(
                        "Funció 'start_session' no implementada al DBManager")
                    self.current_session_id = 1  # Valor per defecte
                    self.session_start_time = time.time()
                    logger.info(f"Sessió iniciada: {self.current_session_id}")
            else:
                logger.warning(
                    "No hi ha projectes disponibles per iniciar una sessió")
                self.current_session_id = None
        except Exception as e:
            logger.error(f"Error iniciant sessió: {e}")
            self.current_session_id = None

    def _end_session(self):
        """Finalitza la sessió actual."""
        try:
            if self.current_session_id is not None:
                session_duration = time.time() - self.session_start_time

                # Finalitzar la sessió a la base de dades
                if hasattr(self.db_manager, 'end_session'):
                    success = self.db_manager.end_session(
                        self.current_session_id,
                        duration_seconds=session_duration
                    )

                    if success:
                        logger.info(
                            f"Sessió finalitzada: {self.current_session_id} (Durada: {session_duration:.1f}s)")
                    else:
                        logger.warning(
                            f"No s'ha pogut finalitzar la sessió: {self.current_session_id}")
                else:
                    logger.info(
                        "Funció 'end_session' no implementada al DBManager")
                    logger.info(
                        f"Sessió finalitzada: {self.current_session_id}")

                self.current_session_id = None
        except Exception as e:
            logger.error(f"Error finalitzant sessió: {e}")

    def cleanup(self):
        """Neteja recursos abans de sortir."""
        # Finalitzar sessió
        self._end_session()

        # Netejar recursos del gestor de connexió
        if hasattr(self, 'connection_manager'):
            self.connection_manager.cleanup()

        # Netejar recursos del gestor de LiDAR
        if hasattr(self, 'lidar_manager'):
            self.lidar_manager.cleanup()

        # Netejar recursos del gestor de càmera
        if hasattr(self, 'camera_manager'):
            self.camera_manager.cleanup()

        # Netejar recursos del gestor de sensors
        if hasattr(self, 'sensor_manager'):
            self.sensor_manager.cleanup()

        logger.info("Neteja completada. Sortint de l'aplicació.")


if __name__ == "__main__":
    try:
        # Iniciar aplicació
        app = QApplication(sys.argv)
        
        # Mostrar splash screen
        splash_pixmap = QPixmap("resources/icons/splash.png")  # Primer intentem amb aquesta ruta
        if not splash_pixmap.isNull():
            splash = QSplashScreen(splash_pixmap)
            splash.show()
            app.processEvents()
        else:
            # Intentar amb ruta alternativa
            splash_pixmap = QPixmap("resources/images/splash.png")
            if not splash_pixmap.isNull():
                splash = QSplashScreen(splash_pixmap)
                splash.show()
                app.processEvents()
            else:
                logger.warning("No s'ha pogut carregar la imatge de splash")
                splash = None
        
        # Configurar estil de l'aplicació
        app.setStyle("Fusion")
        
        # Carregar full d'estils
        style_path = os.path.join(
            os.path.dirname(__file__),
            "resources",
            "styles",
            "main.qss"
        )
        
        try:
            with open(style_path, "r", encoding='utf-8') as file:
                app.setStyleSheet(file.read())
                logger.info("Full d'estils carregat correctament")
        except Exception as e:
            logger.warning(f"Error carregant full d'estils: {e}")
        
        # Crear l'aplicació principal amb delay per veure el splash
        QTimer.singleShot(1000, lambda: setattr(app, 'main_app', MainApp()))
        
        # Ocultar splash després de la inicialització
        if splash:
            QTimer.singleShot(2000, splash.close)
        
        # Executar bucle principal
        exit_code = app.exec_()
        
        # Netejar recursos abans de sortir
        if hasattr(app, 'main_app'):
            app.main_app.cleanup()
        
        sys.exit(exit_code)
    
    except Exception as e:
        logger.critical(f"Error fatal iniciant aplicació: {e}")
        logger.critical(traceback.format_exc())
        
        if 'app' in locals():
            QMessageBox.critical(
                None,
                "Error fatal",
                f"S'ha produït un error fatal:\n{str(e)}"
            )
        
        sys.exit(1)