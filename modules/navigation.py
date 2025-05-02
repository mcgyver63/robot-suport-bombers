"""
Mòdul de Navegació (NavigationManager)
======================================
Gestiona el control de moviment del robot, implementa els modes manual i autònom,
i proporciona funcions per la navegació basada en LiDAR.
"""

import time
import math
import logging
import numpy as np
from enum import Enum
from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot, QTimer

# Configuració de logging
logger = logging.getLogger("Navigation")

# Definició de comandes
class Direction(Enum):
    STOP = "stop"
    FORWARD = "forward"
    BACKWARD = "backward"
    LEFT = "left"
    RIGHT = "right"
    SOFT_LEFT = "soft_left"
    SOFT_RIGHT = "soft_right"

class Mode(Enum):
    MANUAL = "manual"
    ASSISTED = "assisted"
    AUTONOMOUS = "autonomous"

class NavigationManager(QObject):
    """
    Gestiona la navegació del robot.
    Implementa modes manual i autònom, i proporciona mètodes de moviment.
    """
    
    # Signals
    navigation_status_changed = pyqtSignal(str, dict)  # Mode, estat
    obstacle_alert = pyqtSignal(str, float, float)  # Direcció, angle, distància
    
    def __init__(self, config):
        """
        Inicialitza el gestor de navegació.
        
        Args:
            config (dict): Configuració de navegació
        """
        super().__init__()
        
        # Càrrega de configuració
        self.config = config
        nav_config = config.get('navigation', {})
        
        # Paràmetres configurables
        self.default_speed = nav_config.get('default_speed', 150)
        self.auto_stop_timeout = nav_config.get('auto_stop_timeout', 30)  # segons
        self.obstacle_threshold = nav_config.get('obstacle_threshold', 500)  # mm
        
        # Estat actual
        self.current_mode = Mode.MANUAL
        self.current_direction = Direction.STOP
        self.current_speed = self.default_speed
        self.is_moving = False
        self.last_command_time = 0
        self.auto_target_direction = 0  # Radians
        
        # Timer per a navegació autònoma
        self.auto_timer = QTimer()
        self.auto_timer.timeout.connect(self._auto_navigation_step)
        
        # Timer per a auto-stop
        self.auto_stop_timer = QTimer()
        self.auto_stop_timer.timeout.connect(self._check_auto_stop)
        self.auto_stop_timer.start(1000)  # 1 segon
        
        # Referència a altres components
        self.connection_manager = None
        self.lidar_manager = None
        
        logger.info("NavigationManager inicialitzat")
    
    def setup_components(self, connection_manager, lidar_manager):
        """
        Configura les referències a altres components necessaris.
        
        Args:
            connection_manager: Gestor de connexió
            lidar_manager: Gestor de LiDAR
        """
        self.connection_manager = connection_manager
        self.lidar_manager = lidar_manager
        
        # Connectar senyals si existeixen
        if lidar_manager:
            lidar_manager.obstacle_detected.connect(self._on_obstacle_detected)
    
    def set_mode(self, mode):
        """
        Estableix el mode de navegació.
        
        Args:
            mode (Mode): Nou mode de navegació
            
        Returns:
            bool: True si s'ha canviat correctament, False en cas contrari
        """
        if not isinstance(mode, Mode):
            try:
                mode = Mode(mode)
            except ValueError:
                logger.error(f"Mode de navegació no vàlid: {mode}")
                return False
        
        # Si és el mateix mode, no fer res
        if mode == self.current_mode:
            return True
        
        # Aturar el robot per seguretat quan es canvia de mode
        self.stop()
        
        # Canviar mode
        old_mode = self.current_mode
        self.current_mode = mode
        
        # Accions específiques segons el mode
        if mode == Mode.AUTONOMOUS:
            # Iniciar navegació autònoma
            if self.lidar_manager and not self.lidar_manager.is_scan_active():
                self.lidar_manager.start_scan(self.connection_manager)
            
            # Iniciar timer de navegació autònoma
            self.auto_timer.start(200)  # 5 Hz
            logger.info("Mode de navegació autònoma activat")
        else:
            # Aturar timer de navegació autònoma
            if self.auto_timer.isActive():
                self.auto_timer.stop()
        
        # Emetre senyal de canvi d'estat
        self.navigation_status_changed.emit(
            mode.value,
            {
                "previous_mode": old_mode.value,
                "speed": self.current_speed,
                "is_moving": self.is_moving
            }
        )
        
        logger.info(f"Mode de navegació canviat de {old_mode.value} a {mode.value}")
        return True
    
    def set_speed(self, speed):
        """
        Estableix la velocitat del robot.
        
        Args:
            speed (int): Nova velocitat (0-255)
            
        Returns:
            bool: True si s'ha canviat correctament, False en cas contrari
        """
        # Validar velocitat
        if not isinstance(speed, int) or speed < 0 or speed > 255:
            logger.error(f"Velocitat no vàlida: {speed}")
            return False
        
        # Canviar velocitat
        self.current_speed = speed
        
        # Enviar comanda de velocitat si està connectat
        if self.connection_manager and self.connection_manager.connected:
            self.connection_manager.send_command({
                "type": "robot_control",
                "action": "set_speed",
                "value": speed
            })
            logger.info(f"Velocitat canviada a {speed}")
        
        return True
    
    def move(self, direction):
        """
        Mou el robot en una direcció específica.
        
        Args:
            direction (Direction): Direcció de moviment
            
        Returns:
            bool: True si s'ha enviat correctament, False en cas contrari
        """
        if not isinstance(direction, Direction):
            try:
                direction = Direction(direction)
            except ValueError:
                logger.error(f"Direcció no vàlida: {direction}")
                return False
        
        # Verificar si estem en mode manual
        if self.current_mode == Mode.AUTONOMOUS and direction != Direction.STOP:
            logger.warning("No es pot moure manualment en mode autònom")
            return False
        
        # Comprovar si tenim connexió
        if not self.connection_manager or not self.connection_manager.connected:
            logger.error("No es pot moure: no hi ha connexió")
            return False
        
        # Desar direcció actual
        self.current_direction = direction
        
        # Actualitzar estat de moviment
        if direction == Direction.STOP:
            self.is_moving = False
        else:
            self.is_moving = True
            self.last_command_time = time.time()
        
        # Enviar comanda al robot
        command = {
            "type": "robot_control",
            "action": direction.value
        }
        
        success = self.connection_manager.send_command(command)
        
        if success:
            logger.info(f"Moviment {direction.value} enviat")
            
            # Emetre senyal de canvi d'estat
            self.navigation_status_changed.emit(
                self.current_mode.value,
                {
                    "direction": direction.value,
                    "speed": self.current_speed,
                    "is_moving": self.is_moving
                }
            )
        else:
            logger.error(f"Error enviant comanda de moviment {direction.value}")
        
        return success
    
    def forward(self):
        """
        Mou el robot endavant.
        
        Returns:
            bool: True si s'ha enviat correctament, False en cas contrari
        """
        return self.move(Direction.FORWARD)
    
    def backward(self):
        """
        Mou el robot endarrere.
        
        Returns:
            bool: True si s'ha enviat correctament, False en cas contrari
        """
        return self.move(Direction.BACKWARD)
    
    def left(self):
        """
        Gira el robot a l'esquerra.
        
        Returns:
            bool: True si s'ha enviat correctament, False en cas contrari
        """
        return self.move(Direction.LEFT)
    
    def right(self):
        """
        Gira el robot a la dreta.
        
        Returns:
            bool: True si s'ha enviat correctament, False en cas contrari
        """
        return self.move(Direction.RIGHT)
    
    def soft_left(self):
        """
        Gira suaument el robot a l'esquerra.
        
        Returns:
            bool: True si s'ha enviat correctament, False en cas contrari
        """
        return self.move(Direction.SOFT_LEFT)
    
    def soft_right(self):
        """
        Gira suaument el robot a la dreta.
        
        Returns:
            bool: True si s'ha enviat correctament, False en cas contrari
        """
        return self.move(Direction.SOFT_RIGHT)
    
    def stop(self):
        """
        Atura el robot.
        
        Returns:
            bool: True si s'ha enviat correctament, False en cas contrari
        """
        return self.move(Direction.STOP)
    
    def set_auto_target_direction(self, direction_radians):
        """
        Estableix la direcció objectiu per a la navegació autònoma.
        
        Args:
            direction_radians (float): Direcció en radians
        """
        self.auto_target_direction = direction_radians
        logger.debug(f"Direcció objectiu autònoma establerta a {direction_radians} radians")
    
    @pyqtSlot()
    def _auto_navigation_step(self):
        """Executa un pas de navegació autònoma."""
        if self.current_mode != Mode.AUTONOMOUS:
            return
        
        # Verificar si tenim gestors de LiDAR i connexió
        if not self.lidar_manager or not self.connection_manager:
            logger.warning("No es pot navegar autònomament: falta gestor de LiDAR o connexió")
            return
        
        # Obtenir dades actuals del LiDAR
        lidar_data = self.lidar_manager.get_current_data()
        
        # Si no hi ha dades de LiDAR, aturar-se per seguretat
        if not lidar_data or not lidar_data.angles or not lidar_data.distances:
            logger.warning("No hi ha dades de LiDAR disponibles, aturant robot")
            self.stop()
            return
        
        # Trobar millor direcció per evitar obstacles
        best_direction = self.lidar_manager.find_best_direction(self.auto_target_direction)
        
        # Calcular diferència d'angle
        angle_diff = best_direction - self.auto_target_direction
        
        # Normalitzar a [-π, π]
        angle_diff = (angle_diff + math.pi) % (2 * math.pi) - math.pi
        
        # Decidir quin moviment fer
        if abs(angle_diff) < 0.2:  # ±11 graus
            # Recte
            self.move(Direction.FORWARD)
        elif abs(angle_diff) < 0.5:  # ±29 graus
            # Gir suau
            if angle_diff > 0:
                self.move(Direction.SOFT_LEFT)
            else:
                self.move(Direction.SOFT_RIGHT)
        else:
            # Gir pronunciat
            if angle_diff > 0:
                self.move(Direction.LEFT)
            else:
                self.move(Direction.RIGHT)
        
        logger.debug(f"Navegació autònoma: direcció={best_direction:.2f}, diff={angle_diff:.2f}")
    
    @pyqtSlot(float, float)
    def _on_obstacle_detected(self, angle, distance):
        """
        Gestiona la detecció d'obstacles.
        
        Args:
            angle (float): Angle de l'obstacle en radians
            distance (float): Distància de l'obstacle en mm
        """
        # Determinar direcció de l'obstacle
        direction = "frontal"
        if angle > 0.5:
            direction = "esquerra"
        elif angle < -0.5:
            direction = "dreta"
        
        # Emetre senyal d'alerta
        self.obstacle_alert.emit(direction, angle, distance)
        
        # Si estem en mode assistit, ajudar a evitar l'obstacle
        if self.current_mode == Mode.ASSISTED and self.is_moving:
            # Si l'obstacle és molt proper, aturar-se
            if distance < self.obstacle_threshold / 2:
                logger.warning(f"Obstacle molt proper ({distance} mm), aturant robot")
                self.stop()
            # Si estem anant endavant i hi ha un obstacle frontal, ajudar a evitar-lo
            elif self.current_direction == Direction.FORWARD and abs(angle) < 0.5:
                # Decidir cap a on girar
                if angle > 0:
                    logger.info(f"Obstacle frontal ({distance} mm), ajudant a girar a la dreta")
                    self.move(Direction.SOFT_RIGHT)
                else:
                    logger.info(f"Obstacle frontal ({distance} mm), ajudant a girar a l'esquerra")
                    self.move(Direction.SOFT_LEFT)
    
    @pyqtSlot()
    def _check_auto_stop(self):
        """Comprova si cal aturar automàticament el robot per inactivitat."""
        if not self.is_moving:
            return
        
        # Comprovar si ha passat massa temps des de l'última comanda
        time_since_last_command = time.time() - self.last_command_time
        
        if time_since_last_command > self.auto_stop_timeout:
            logger.warning(f"Auto-stop per inactivitat ({self.auto_stop_timeout} segons)")
            self.stop()
