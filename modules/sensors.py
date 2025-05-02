"""
Gestor de Sensors (SensorManager)
===============================
Gestiona els sensors del robot, incloent la lectura, processament i alertes
de dades dels diferents tipus de sensors.
"""

import logging
import time
from PyQt5.QtCore import QObject, pyqtSignal, QTimer

# Configuració del logger
logger = logging.getLogger("Sensors")

class SensorManager(QObject):
    """
    Gestor dels sensors del robot.
    Coordina la lectura i el processament de dades de tots els sensors.
    """
    
    # Senyals per comunicar canvis d'estat
    sensor_data_updated = pyqtSignal(str, float)  # Tipus de sensor, valor
    sensor_alert = pyqtSignal(str, str)           # Tipus de sensor, missatge
    sensors_status_updated = pyqtSignal(dict)     # Dict amb tots els valors
    
    # Definició dels tipus de sensors i propietats
    SENSOR_TYPES = {
        'temperature': {
            'name': 'Temperatura',
            'unit': '°C',
            'threshold': 45.0,
            'alert_message': 'Temperatura elevada detectada: {value}°C'
        },
        'humidity': {
            'name': 'Humitat',
            'unit': '%',
            'threshold': 90.0,
            'alert_message': 'Humitat elevada detectada: {value}%'
        },
        'gas': {
            'name': 'Gas',
            'unit': 'ppm',
            'threshold': 1000.0,
            'alert_message': 'Nivell de gas perillós detectat: {value} ppm'
        },
        'co': {
            'name': 'Monòxid de Carboni',
            'unit': 'ppm',
            'threshold': 50.0,
            'alert_message': 'Nivell perillós de CO detectat: {value} ppm'
        },
        'smoke': {
            'name': 'Fum',
            'unit': '%',
            'threshold': 30.0,
            'alert_message': 'Fum detectat: {value}%'
        },
        'battery': {
            'name': 'Bateria',
            'unit': '%',
            'threshold': 20.0,
            'alert_message': 'Nivell de bateria baix: {value}%'
        }
    }
    
    def __init__(self, config):
        """
        Inicialitza el gestor de sensors.
        
        Args:
            config (dict): Configuració general
        """
        super().__init__()
        
        # Assegurem que config és un diccionari
        if not isinstance(config, dict):
            logger.error(f"Config ha de ser un diccionari, però s'ha rebut: {type(config).__name__}")
            config = {}
        
        logger.info("Inicialitzant SensorManager")
        
        # Guardar referència a configuració
        self.config = config
        
        # Inicialitzar l'estat dels sensors
        self.sensor_values = {sensor_type: 0.0 for sensor_type in self.SENSOR_TYPES}
        self.sensor_thresholds = {}
        
        # Carregar llindars dels sensors de la configuració
        self._load_sensor_thresholds(config)
        
        # Timer per a simulació de lectures si no hi ha connexió real
        self.simulation_timer = QTimer()
        self.simulation_timer.timeout.connect(self._simulate_readings)
        self.simulation_active = False
        
        logger.info("SensorManager inicialitzat")
    
    def _load_sensor_thresholds(self, config):
        """
        Carrega els llindars dels sensors de la configuració.
        
        Args:
            config (dict): Configuració general
        """
        try:
            # Obtenir secció de configuració de sensors (si existeix)
            sensor_config = config.get('sensors', {})
            
            # Si sensor_config no és un diccionari, crear-ne un de buit
            if not isinstance(sensor_config, dict):
                logger.warning(f"La configuració de sensors no és un diccionari: {sensor_config}")
                sensor_config = {}
            
            # Carregar llindars per cada tipus de sensor
            for sensor_type, properties in self.SENSOR_TYPES.items():
                # Obtenir configuració específica per aquest sensor (si existeix)
                sensor_specific_config = sensor_config.get(sensor_type.lower(), {})
                
                # Si la configuració específica no és un diccionari, usar valors per defecte
                if not isinstance(sensor_specific_config, dict):
                    logger.warning(f"Configuració per '{sensor_type}' no és un diccionari: {sensor_specific_config}")
                    threshold = properties['threshold']
                else:
                    # Obtenir llindar de configuració o usar valor per defecte
                    threshold = sensor_specific_config.get('threshold', properties['threshold'])
                
                # Guardar llindar
                self.sensor_thresholds[sensor_type] = threshold
                logger.info(f"Llindar per {properties['name']}: {threshold} {properties['unit']}")
        
        except Exception as e:
            logger.error(f"Error carregant llindars de sensors: {e}")
            # Establir llindars per defecte
            self.sensor_thresholds = {sensor_type: properties['threshold'] 
                                     for sensor_type, properties in self.SENSOR_TYPES.items()}
    
    def start_simulation(self):
        """Inicia la simulació de lectures de sensors."""
        if not self.simulation_active:
            logger.info("Iniciant simulació de sensors")
            self.simulation_active = True
            self.simulation_timer.start(1000)  # Actualitzar cada segon
    
    def stop_simulation(self):
        """Atura la simulació de lectures de sensors."""
        if self.simulation_active:
            logger.info("Aturant simulació de sensors")
            self.simulation_active = False
            self.simulation_timer.stop()
    
    def _simulate_readings(self):
        """Genera lectures simulades per a tots els sensors."""
        import random
        
        for sensor_type, properties in self.SENSOR_TYPES.items():
            # Generar valor simulat (propera al llindar per veure alertes ocasionalment)
            base_value = self.sensor_thresholds[sensor_type] * 0.8
            variance = self.sensor_thresholds[sensor_type] * 0.4
            value = base_value + random.uniform(-variance, variance)
            
            # Assegurar que els valors estan dins de rangs raonables
            if sensor_type == 'humidity' or sensor_type == 'battery':
                value = max(0, min(100, value))  # 0-100%
            elif sensor_type == 'temperature':
                value = max(15, min(60, value))  # 15-60°C
            
            # Actualitzar valor
            self.update_sensor_value(sensor_type, value)
    
    def update_sensor_value(self, sensor_type, value):
        """
        Actualitza el valor d'un sensor i comprova si s'ha de generar una alerta.
        
        Args:
            sensor_type (str): Tipus de sensor
            value (float): Nou valor
        """
        # Validar tipus de sensor
        if sensor_type not in self.SENSOR_TYPES:
            logger.warning(f"Tipus de sensor desconegut: {sensor_type}")
            return
        
        # Actualitzar valor
        self.sensor_values[sensor_type] = value
        
        # Emetre senyal d'actualització
        self.sensor_data_updated.emit(sensor_type, value)
        
        # Comprovar si cal generar alerta
        self._check_threshold(sensor_type, value)
        
        # Actualitzar estat general
        self.sensors_status_updated.emit(self.sensor_values.copy())
    
    def _check_threshold(self, sensor_type, value):
        """
        Comprova si un valor ha superat el llindar i genera l'alerta si cal.
        
        Args:
            sensor_type (str): Tipus de sensor
            value (float): Valor a comprovar
        """
        properties = self.SENSOR_TYPES[sensor_type]
        threshold = self.sensor_thresholds[sensor_type]
        
        # Condició d'alerta (depèn del tipus de sensor)
        if sensor_type == 'battery':
            # Per la bateria, l'alerta és si el valor és MENOR que el llindar
            if value < threshold:
                message = properties['alert_message'].format(value=round(value, 1))
                self.sensor_alert.emit(sensor_type, message)
                logger.warning(message)
        else:
            # Per la resta de sensors, l'alerta és si el valor és MAJOR que el llindar
            if value > threshold:
                message = properties['alert_message'].format(value=round(value, 1))
                self.sensor_alert.emit(sensor_type, message)
                logger.warning(message)
    
    def get_sensor_value(self, sensor_type):
        """
        Obté el valor actual d'un sensor.
        
        Args:
            sensor_type (str): Tipus de sensor
        
        Returns:
            float: Valor actual del sensor
        """
        return self.sensor_values.get(sensor_type, 0.0)
    
    def get_all_sensor_values(self):
        """
        Obté els valors de tots els sensors.
        
        Returns:
            dict: Diccionari amb els valors actuals
        """
        return self.sensor_values.copy()
    
    def set_threshold(self, sensor_type, threshold):
        """
        Estableix un nou llindar per a un sensor.
        
        Args:
            sensor_type (str): Tipus de sensor
            threshold (float): Nou valor de llindar
        
        Returns:
            bool: True si s'ha pogut establir, False en cas contrari
        """
        if sensor_type not in self.SENSOR_TYPES:
            logger.warning(f"Tipus de sensor desconegut per establir llindar: {sensor_type}")
            return False
        
        logger.info(f"Canviant llindar de {self.SENSOR_TYPES[sensor_type]['name']} a {threshold}")
        self.sensor_thresholds[sensor_type] = threshold
        return True
    
    def get_threshold(self, sensor_type):
        """
        Obté el llindar actual d'un sensor.
        
        Args:
            sensor_type (str): Tipus de sensor
        
        Returns:
            float: Llindar actual
        """
        return self.sensor_thresholds.get(sensor_type, 
                                         self.SENSOR_TYPES.get(sensor_type, {}).get('threshold', 0.0))
    
    def cleanup(self):
        """Neteja i allibera recursos."""
        logger.info("Netejant recursos de SensorManager")
        self.stop_simulation()
