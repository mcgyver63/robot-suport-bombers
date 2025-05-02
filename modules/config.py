"""
Mòdul de Configuració (ConfigManager)
=====================================
Gestiona la configuració del sistema, càrrega i emmagatzematge de
paràmetres, i perfils de configuració.
"""

import os
import json
import logging
import configparser
from PyQt5.QtCore import QObject, pyqtSignal, QStandardPaths

# Configuració de logging
logger = logging.getLogger("Config")

# Constants
DEFAULT_CONFIG_FILE = "config.ini"
DEFAULT_PROFILES_DIR = "profiles"

class ConfigManager(QObject):
    """
    Gestiona la configuració del sistema.
    Permet carregar i guardar configuracions, gestionar perfils,
    i proporcionar valors per defecte.
    """
    
    # Signals
    config_updated = pyqtSignal(dict)  # Configuració actualitzada
    
    def __init__(self, config_file=None):
        """
        Inicialitza el gestor de configuració.
        
        Args:
            config_file (str, optional): Fitxer de configuració. Defaults to None.
        """
        super().__init__()
        
        # Obtenir ruta de configuració
        self.config_dir = self._get_config_directory()
        
        # Ruta al fitxer de configuració
        if config_file is None:
            self.config_file = os.path.join(self.config_dir, DEFAULT_CONFIG_FILE)
        else:
            self.config_file = config_file
        
        # Ruta al directori de perfils
        self.profiles_dir = os.path.join(self.config_dir, DEFAULT_PROFILES_DIR)
        
        # Assegurar que existeixen els directoris
        os.makedirs(self.config_dir, exist_ok=True)
        os.makedirs(self.profiles_dir, exist_ok=True)
        
        # Configuració actual
        self.config = self._load_default_config()
        
        # Carregar configuració guardada si existeix
        self._load_config_file()
        
        logger.info("ConfigManager inicialitzat")
    
    def _get_config_directory(self):
        """
        Obté el directori de configuració de l'aplicació.
        
        Returns:
            str: Ruta al directori de configuració
        """
        # Utilitzar directori estàndard de l'aplicació per a configuració
        app_config_dir = QStandardPaths.writableLocation(QStandardPaths.AppConfigLocation)
        
        # Si no es pot obtenir, utilitzar el directori de treball actual
        if not app_config_dir:
            app_config_dir = os.path.join(os.getcwd(), "config")
        
        return app_config_dir
    
    def _load_default_config(self):
        """
        Carrega la configuració per defecte.
        
        Returns:
            dict: Configuració per defecte
        """
        return {
            # Configuració de connexió
            'connection': {
                'host': '192.168.1.100',
                'port': 9999,
                'auto_reconnect': True,
                'reconnect_interval': 5
            },
            
            # Configuració de sensors
            'sensors': {
                'mq2': {
                    'threshold': 400,
                    'calibration': None
                },
                'mq135': {
                    'threshold': 100,
                    'calibration': None
                },
                'temp': {
                    'threshold': 50,
                    'calibration': None
                },
                'flame': {
                    'threshold': 1,
                    'calibration': None
                },
                'sound': {
                    'threshold': 500,
                    'calibration': None
                },
                'mpu': {
                    'threshold': 2.0,
                    'calibration': None
                },
                'bat': {
                    'threshold': 10.0,
                    'calibration': None
                }
            },
            
            # Configuració de LiDAR
            'lidar': {
                'enabled': True,
                'scan_frequency': 5,  # Hz
                'max_distance': 3000  # mm
            },
            
            # Configuració de càmera
            'camera': {
                'enabled': True,
                'resolution': [640, 480],
                'fps': 15
            },
            
            # Configuració de navegació
            'navigation': {
                'default_speed': 150,
                'auto_stop_timeout': 30,  # segons
                'obstacle_threshold': 500  # mm
            },
            
            # Configuració d'interfície
            'ui': {
                'theme': 'light',
                'language': 'ca',
                'sound_alerts': True,
                'show_statistics': True
            }
        }
    
    def _load_config_file(self):
        """
        Carrega la configuració des del fitxer.
        """
        try:
            if os.path.exists(self.config_file):
                # Utilitzem configparser per carregar el fitxer INI
                parser = configparser.ConfigParser()
                parser.read(self.config_file)
                
                # Convertir el configparser a diccionari
                config_dict = {}
                for section in parser.sections():
                    section_dict = {}
                    for key, value in parser.items(section):
                        # Intentar convertir valor a tipus apropiat
                        try:
                            # Intentar com a número
                            if '.' in value:
                                section_dict[key] = float(value)
                            else:
                                section_dict[key] = int(value)
                        except ValueError:
                            # Intentar com a boolean
                            if value.lower() in ['true', 'yes', '1']:
                                section_dict[key] = True
                            elif value.lower() in ['false', 'no', '0']:
                                section_dict[key] = False
                            else:
                                # Text pla
                                section_dict[key] = value
                    
                    # Afegir la secció al diccionari principal
                    config_dict[section] = section_dict
                
                # Actualitzar la configuració combinant els valors carregats amb els per defecte
                self._update_dict_recursive(self.config, config_dict)
                
                logger.info(f"Configuració carregada des de {self.config_file}")
            else:
                logger.info(f"No s'ha trobat fitxer de configuració. S'utilitzen valors per defecte.")
                # Guardar la configuració per defecte
                self.save_config()
        
        except Exception as e:
            logger.error(f"Error carregant configuració: {e}")
            # Si hi ha un error, utilitzar valors per defecte
            self.config = self._load_default_config()
    
    def _update_dict_recursive(self, d, u):
        """
        Actualitza un diccionari de forma recursiva.
        
        Args:
            d (dict): Diccionari a actualitzar
            u (dict): Diccionari amb nous valors
            
        Returns:
            dict: Diccionari actualitzat
        """
        for k, v in u.items():
            if isinstance(v, dict) and k in d and isinstance(d[k], dict):
                d[k] = self._update_dict_recursive(d[k], v)
            else:
                d[k] = v
        return d
    
    def load_config(self):
        """
        Carrega i retorna la configuració actual.
        
        Returns:
            dict: Configuració actual
        """
        return self.config
    
    def save_config(self):
        """
        Guarda la configuració actual al fitxer.
        
        Returns:
            bool: True si s'ha guardat correctament, False en cas contrari
        """
        try:
            # Convertir el diccionari a configparser
            parser = configparser.ConfigParser(interpolation=None)
            
            for section, values in self.config.items():
                parser.add_section(section)
                for key, value in values.items():
                    parser.set(section, key, str(value))
            
            # Guardar al fitxer
            with open(self.config_file, 'w') as f:
                parser.write(f)
            
            logger.info(f"Configuració guardada a {self.config_file}")
            return True
            
        except Exception as e:
            logger.error(f"Error guardant configuració: {e}")
            return False
    
    def update_config(self, section, key, value):
        """
        Actualitza un valor específic de la configuració.
        
        Args:
            section (str): Secció de la configuració
            key (str): Clau a actualitzar
            value: Nou valor
            
        Returns:
            bool: True si s'ha actualitzat correctament, False en cas contrari
        """
        try:
            # Comprovar si existeix la secció
            if section not in self.config:
                self.config[section] = {}
            
            # Actualitzar valor
            self.config[section][key] = value
            
            # Emetre senyal d'actualització
            self.config_updated.emit(self.config)
            
            logger.debug(f"Configuració actualitzada: {section}.{key} = {value}")
            return True
            
        except Exception as e:
            logger.error(f"Error actualitzant configuració: {e}")
            return False
    
    def update_section(self, section, values):
        """
        Actualitza tota una secció de la configuració.
        
        Args:
            section (str): Secció de la configuració
            values (dict): Nous valors
            
        Returns:
            bool: True si s'ha actualitzat correctament, False en cas contrari
        """
        try:
            # Actualitzar secció
            if section not in self.config:
                self.config[section] = values
            else:
                self.config[section].update(values)
            
            # Emetre senyal d'actualització
            self.config_updated.emit(self.config)
            
            logger.debug(f"Secció {section} actualitzada")
            return True
            
        except Exception as e:
            logger.error(f"Error actualitzant secció {section}: {e}")
            return False
    
    def get_value(self, section, key, default=None):
        """
        Obté un valor específic de la configuració.
        
        Args:
            section (str): Secció de la configuració
            key (str): Clau a obtenir
            default: Valor per defecte si no es troba
            
        Returns:
            Valor de la configuració o valor per defecte
        """
        try:
            return self.config.get(section, {}).get(key, default)
        except:
            return default
    
    def reset_to_defaults(self):
        """
        Restableix la configuració als valors per defecte.
        
        Returns:
            bool: True si s'ha restablert correctament, False en cas contrari
        """
        try:
            self.config = self._load_default_config()
            
            # Emetre senyal d'actualització
            self.config_updated.emit(self.config)
            
            logger.info("Configuració restablerta als valors per defecte")
            return True
            
        except Exception as e:
            logger.error(f"Error restablint configuració: {e}")
            return False
    
    def save_profile(self, profile_name):
        """
        Guarda la configuració actual com a perfil.
        
        Args:
            profile_name (str): Nom del perfil
            
        Returns:
            bool: True si s'ha guardat correctament, False en cas contrari
        """
        try:
            profile_file = os.path.join(self.profiles_dir, f"{profile_name}.json")
            
            # Guardar en format JSON per mantenir tipus de dades
            with open(profile_file, 'w') as f:
                json.dump(self.config, f, indent=4)
            
            logger.info(f"Perfil '{profile_name}' guardat a {profile_file}")
            return True
            
        except Exception as e:
            logger.error(f"Error guardant perfil '{profile_name}': {e}")
            return False
    
    def load_profile(self, profile_name):
        """
        Carrega un perfil de configuració.
        
        Args:
            profile_name (str): Nom del perfil
            
        Returns:
            bool: True si s'ha carregat correctament, False en cas contrari
        """
        try:
            profile_file = os.path.join(self.profiles_dir, f"{profile_name}.json")
            
            if not os.path.exists(profile_file):
                logger.warning(f"El perfil '{profile_name}' no existeix")
                return False
            
            # Carregar des de format JSON
            with open(profile_file, 'r') as f:
                profile_config = json.load(f)
            
            # Actualitzar configuració
            self.config = profile_config
            
            # Emetre senyal d'actualització
            self.config_updated.emit(self.config)
            
            logger.info(f"Perfil '{profile_name}' carregat")
            return True
            
        except Exception as e:
            logger.error(f"Error carregant perfil '{profile_name}': {e}")
            return False
    
    def get_available_profiles(self):
        """
        Obté la llista de perfils disponibles.
        
        Returns:
            list: Llista de noms de perfils
        """
        try:
            profiles = []
            
            for file_name in os.listdir(self.profiles_dir):
                if file_name.endswith('.json'):
                    profiles.append(file_name[:-5])  # Eliminar extensió .json
            
            return profiles
            
        except Exception as e:
            logger.error(f"Error obtenint perfils disponibles: {e}")
            return []
    
    def delete_profile(self, profile_name):
        """
        Elimina un perfil.
        
        Args:
            profile_name (str): Nom del perfil
            
        Returns:
            bool: True si s'ha eliminat correctament, False en cas contrari
        """
        try:
            profile_file = os.path.join(self.profiles_dir, f"{profile_name}.json")
            
            if not os.path.exists(profile_file):
                logger.warning(f"El perfil '{profile_name}' no existeix")
                return False
            
            # Eliminar fitxer
            os.remove(profile_file)
            
            logger.info(f"Perfil '{profile_name}' eliminat")
            return True
            
        except Exception as e:
            logger.error(f"Error eliminant perfil '{profile_name}': {e}")
            return False
