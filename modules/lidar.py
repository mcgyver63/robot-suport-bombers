#!/usr/bin/env python3
"""
Mòdul de LiDAR (LidarManager)
=============================
Gestiona les dades del LiDAR, processa les lectures,
crea mapes de l'entorn i detecta obstacles.
"""

import numpy as np
import time
import logging
from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot, QTimer
from scipy.interpolate import griddata

# Configuració de logging
logger = logging.getLogger("LiDAR")

class LidarData:
    """Classe per emmagatzemar i processar dades del LiDAR."""
    
    def __init__(self, max_points=1000, max_range=3000):
        """
        Inicialitza l'objecte de dades del LiDAR.
        
        Args:
            max_points (int, optional): Màxim de punts a emmagatzemar. Defaults to 1000.
            max_range (int, optional): Rang màxim en mm. Defaults to 3000.
        """
        self.max_points = max_points
        self.max_range = max_range
        
        # Dades raw
        self.angles = []  # Llista d'angles en radians
        self.distances = []  # Llista de distàncies en mm
        
        # Dades processades
        self.cartesian_points = []  # Llista de tuples (x, y)
        self.obstacle_map = None  # Mapa d'obstacles
        
        # Metadades
        self.timestamp = None
        self.scan_id = 0
    
    def update(self, scan_data):
        """
        Actualitza les dades amb una nova lectura.
        
        Args:
            scan_data (list): Llista de tuples (angle, distància)
            
        Returns:
            bool: True si s'ha actualitzat correctament, False en cas contrari
        """
        try:
            # Comprova si hi ha dades
            if not scan_data or len(scan_data) < 10:
                logger.warning("Poques dades LiDAR rebudes, ignorant scan")
                return False
            
            # Actualitzar timestamp i ID
            self.timestamp = time.time()
            self.scan_id += 1
            
            # Reiniciar llistes
            self.angles = []
            self.distances = []
            self.cartesian_points = []
            
            # Processar dades
            for angle, distance in scan_data:
                # Convertir angle a radians
                angle_rad = np.radians(angle)
                
                # Filtrar mesures invàlides o massa llunyanes
                if distance <= 0 or distance > self.max_range:
                    continue
                
                # Afegir a les llistes
                self.angles.append(angle_rad)
                self.distances.append(distance)
                
                # Convertir a coordenades cartesianes (x endavant, y esquerra)
                x = distance * np.cos(angle_rad)
                y = distance * np.sin(angle_rad)
                self.cartesian_points.append((x, y))
            
            # Limitar el nombre de punts si és necessari
            if len(self.angles) > self.max_points:
                # Seleccionar punts aleatoris
                indices = np.random.choice(
                    len(self.angles), self.max_points, replace=False)
                
                self.angles = [self.angles[i] for i in indices]
                self.distances = [self.distances[i] for i in indices]
                self.cartesian_points = [self.cartesian_points[i] for i in indices]
            
            # Recalcular mapa d'obstacles
            self._update_obstacle_map()
            
            return True
            
        except Exception as e:
            logger.error(f"Error actualitzant dades LiDAR: {e}")
            return False
    
    def _update_obstacle_map(self):
        """Actualitza el mapa d'obstacles basat en les dades actuals."""
        try:
            if not self.cartesian_points:
                return
            
            # Convertir punts a arrays numpy
            points = np.array(self.cartesian_points)
            
            # Crear una malla regular per a la interpolació
            grid_size = 100  # punts en cada dimensió
            min_x, max_x = -self.max_range, self.max_range
            min_y, max_y = -self.max_range, self.max_range
            
            x_grid = np.linspace(min_x, max_x, grid_size)
            y_grid = np.linspace(min_y, max_y, grid_size)
            X, Y = np.meshgrid(x_grid, y_grid)
            
            # Calcular distàncies des de l'origen a cada punt
            distances = np.sqrt(points[:, 0]**2 + points[:, 1]**2)
            
            # Interpolar les distàncies en la malla regular
            try:
                # Intentar interpolació cúbica primer
                Z = griddata(points, distances, (X, Y), method='cubic')
            except:
                try:
                    # Si falla, intentar interpolació lineal
                    Z = griddata(points, distances, (X, Y), method='linear')
                except:
                    # Si tot falla, utilitzar el mètode més simple
                    Z = griddata(points, distances, (X, Y), method='nearest')
            
            # Crear mapa d'obstacles
            self.obstacle_map = {
                'X': X,
                'Y': Y,
                'Z': Z,
                'resolution': (grid_size, grid_size),
                'bounds': (min_x, max_x, min_y, max_y)
            }
            
        except Exception as e:
            logger.error(f"Error actualitzant mapa d'obstacles: {e}")
    
    def get_nearest_obstacle(self, angle_range=None):
        """
        Obté l'obstacle més proper en un rang d'angles.
        
        Args:
            angle_range (tuple, optional): Rang d'angles en radians (min, max).
                                         Defaults to None (tot el rang).
            
        Returns:
            tuple: (angle en radians, distància en mm) o (None, None) si no hi ha obstacles
        """
        if not self.angles or not self.distances:
            return None, None
        
        # Si no s'especifica rang, utilitzar tot el rang
        if angle_range is None:
            idx = np.argmin(self.distances)
            return self.angles[idx], self.distances[idx]
        
        # Filtrar per rang d'angles
        min_angle, max_angle = angle_range
        indices = [i for i, angle in enumerate(self.angles)
                  if min_angle <= angle <= max_angle]
        
        if not indices:
            return None, None
        
        # Obtenir l'obstacle més proper
        filtered_distances = [self.distances[i] for i in indices]
        min_idx = np.argmin(filtered_distances)
        idx = indices[min_idx]
        
        return self.angles[idx], self.distances[idx]
    
    def get_sector_data(self, num_sectors=8):
        """
        Divideix el cercle en sectors i obté la distància mínima per sector.
        
        Args:
            num_sectors (int, optional): Nombre de sectors. Defaults to 8.
            
        Returns:
            list: Llista de tuples (angle_central, distància_mínima)
        """
        if not self.angles or not self.distances:
            return []
        
        # Calcular amplada del sector
        sector_width = 2 * np.pi / num_sectors
        
        # Inicialitzar llista de resultats
        sector_data = []
        
        # Per cada sector
        for i in range(num_sectors):
            # Calcular límits del sector
            min_angle = i * sector_width - np.pi
            max_angle = (i + 1) * sector_width - np.pi
            mid_angle = (min_angle + max_angle) / 2
            
            # Obtenir punts dins del sector
            indices = [j for j, angle in enumerate(self.angles)
                      if min_angle <= angle < max_angle]
            
            # Si no hi ha punts, utilitzar màxim rang
            if not indices:
                sector_data.append((mid_angle, self.max_range))
                continue
            
            # Obtenir distància mínima
            distances = [self.distances[j] for j in indices]
            min_distance = min(distances)
            
            # Afegir a la llista
            sector_data.append((mid_angle, min_distance))
        
        return sector_data
    
    def get_polar_plot_data(self):
        """
        Obté dades pels gràfics polars.
        
        Returns:
            tuple: (angles, distàncies)
        """
        return self.angles, self.distances
    
    def get_cartesian_plot_data(self):
        """
        Obté dades pels gràfics cartesians.
        
        Returns:
            tuple: (xs, ys)
        """
        if not self.cartesian_points:
            return [], []
        
        xs = [p[0] for p in self.cartesian_points]
        ys = [p[1] for p in self.cartesian_points]
        
        return xs, ys
    
    def get_contour_data(self):
        """
        Obté dades pel gràfic de contorn.
        
        Returns:
            dict: Dades pel gràfic de contorn o None si no estan disponibles
        """
        return self.obstacle_map
    
    def is_path_clear(self, direction, distance_threshold=500):
        """
        Comprova si hi ha un camí lliure en una direcció.
        
        Args:
            direction (float): Direcció en radians
            distance_threshold (int, optional): Llindar de distància en mm. Defaults to 500.
            
        Returns:
            bool: True si el camí està lliure, False en cas contrari
        """
        if not self.angles or not self.distances:
            return True
        
        # Calcular rang d'angles a comprovar (±30 graus)
        angle_range = 0.5  # radians (≈30 graus)
        min_angle = direction - angle_range
        max_angle = direction + angle_range
        
        # Obtenir punts dins del rang
        indices = [i for i, angle in enumerate(self.angles)
                  if min_angle <= angle <= max_angle]
        
        if not indices:
            return True
        
        # Obtenir distàncies
        distances = [self.distances[i] for i in indices]
        min_distance = min(distances)
        
        # Comprovar si hi ha obstacles
        return min_distance > distance_threshold


class LidarManager(QObject):
    """
    Gestiona les dades i funcionalitats del LiDAR.
    Processa les dades rebudes i proporciona mètodes per a la visualització i navegació.
    """
    
    # Signals
    lidar_data_updated = pyqtSignal(object)  # Dades del LiDAR actualitzades
    obstacle_detected = pyqtSignal(float, float)  # Angle, distància
    
    def __init__(self, config):
        """
        Inicialitza el gestor del LiDAR.
        
        Args:
            config (dict): Configuració del LiDAR
        """
        super().__init__()
        
        # Càrrega de configuració
        self.config = config
        lidar_config = config.get('lidar', {})
        
        # Paràmetres configurables
        self.enabled = lidar_config.get('enabled', True)
        self.scan_frequency = lidar_config.get('scan_frequency', 5)  # Hz
        self.max_range = lidar_config.get('max_distance', 3000)  # mm
        
        # Inicialitzar objecte de dades
        self.lidar_data = LidarData(max_range=self.max_range)
        
        # Estats
        self.scanning = False
        self.last_scan_time = 0
        
        # Timer per detector d'obstacles
        self.obstacle_timer = QTimer()
        self.obstacle_timer.timeout.connect(self._check_obstacles)
        
        logger.info("LidarManager inicialitzat")
    
    @pyqtSlot(dict)
    def process_data(self, data):
        """
        Processa dades rebudes del bridge.
        
        Args:
            data (dict): Dades rebudes en format JSON
        """
        # Si el LiDAR està desactivat, ignorar
        if not self.enabled:
            return
        
        # Comprovar tipus de dades
        if data.get('type') == 'lidar_data':
            # Obtenir dades del LiDAR
            scan_data = data.get('data', [])
            
            # Actualitzar dades
            if self.lidar_data.update(scan_data):
                # Actualitzar timestamp
                self.last_scan_time = time.time()
                
                # Establir estat d'escaneig
                self.scanning = True
                
                # Emetre senyal d'actualització
                self.lidar_data_updated.emit(self.lidar_data)
                
                logger.debug(f"Dades LiDAR actualitzades: {len(scan_data)} punts")
                
                # Iniciar timer d'obstacles si no està actiu
                if not self.obstacle_timer.isActive():
                    self.obstacle_timer.start(1000)  # 1 segon
    
    def start_scan(self, connection_manager):
        """
        Inicia l'escaneig del LiDAR.
        
        Args:
            connection_manager: Gestor de connexió per enviar la comanda
            
        Returns:
            bool: True si s'ha enviat correctament, False en cas contrari
        """
        if not self.enabled:
            logger.warning("LiDAR desactivat, no es pot iniciar escaneig")
            return False
        
        if not connection_manager:
            logger.error("No es pot iniciar escaneig: gestor de connexió no disponible")
            return False
        
        logger.info("Iniciant escaneig LiDAR")
        return connection_manager.send_command({
            "type": "lidar_control",
            "action": "start_scan"
        })
    
    def stop_scan(self, connection_manager):
        """
        Atura l'escaneig del LiDAR.
        
        Args:
            connection_manager: Gestor de connexió per enviar la comanda
            
        Returns:
            bool: True si s'ha enviat correctament, False en cas contrari
        """
        if not connection_manager:
            logger.error("No es pot aturar escaneig: gestor de connexió no disponible")
            return False
        
        logger.info("Aturant escaneig LiDAR")
        self.scanning = False
        
        return connection_manager.send_command({
            "type": "lidar_control",
            "action": "stop_scan"
        })
    
    def enable(self, enabled=True):
        """
        Activa o desactiva el LiDAR.
        
        Args:
            enabled (bool, optional): Estat d'activació. Defaults to True.
        """
        self.enabled = enabled
        logger.info(f"LiDAR {'activat' if enabled else 'desactivat'}")
    
    def is_scan_active(self):
        """
        Comprova si l'escaneig està actiu.
        
        Returns:
            bool: True si l'escaneig està actiu, False en cas contrari
        """
        # Comprovar si fa massa temps des de l'última lectura
        if time.time() - self.last_scan_time > 5:  # 5 segons
            self.scanning = False
        
        return self.scanning
    
    def get_current_data(self):
        """
        Obté les dades actuals del LiDAR.
        
        Returns:
            LidarData: Objecte amb les dades del LiDAR
        """
        return self.lidar_data
    
    def get_direction_safety(self, direction_radians):
        """
        Calcula la seguretat d'una direcció (0 = bloquejada, 1 = completament lliure).
        
        Args:
            direction_radians (float): Direcció en radians
            
        Returns:
            float: Valor de seguretat entre 0 i 1
        """
        # Si no hi ha dades, retornar seguretat mitjana
        if not self.lidar_data.angles or not self.lidar_data.distances:
            return 0.5
        
        # Calcular rang d'angles a comprovar (±45 graus)
        angle_range = 0.78  # radians (≈45 graus)
        min_angle = direction_radians - angle_range
        max_angle = direction_radians + angle_range
        
        # Obtenir punts dins del rang
        indices = [i for i, angle in enumerate(self.lidar_data.angles)
                  if min_angle <= angle <= max_angle]
        
        if not indices:
            return 0.5
        
        # Obtenir distàncies
        distances = [self.lidar_data.distances[i] for i in indices]
        min_distance = min(distances)
        
        # Calcular seguretat (0 = molt a prop, 1 = molt lluny)
        safety = min(1.0, max(0.0, min_distance / self.max_range))
        
        return safety
    
    def find_best_direction(self, current_direction, angle_resolution=16):
        """
        Troba la millor direcció per evitar obstacles.
        
        Args:
            current_direction (float): Direcció actual en radians
            angle_resolution (int, optional): Resolució d'angles a comprovar. Defaults to 16.
            
        Returns:
            float: Millor direcció en radians
        """
        # Si no hi ha dades, mantenir direcció actual
        if not self.lidar_data.angles or not self.lidar_data.distances:
            return current_direction
        
        # Dividir el cercle en sectors
        angles = []
        safety_values = []
        
        for i in range(angle_resolution):
            angle = i * (2 * np.pi / angle_resolution) - np.pi
            safety = self.get_direction_safety(angle)
            
            # Afegir a les llistes
            angles.append(angle)
            safety_values.append(safety)
        
        # Trobar les direccions més segures
        safe_indices = [i for i, safety in enumerate(safety_values)
                       if safety > 0.7]  # Llindar de seguretat
        
        if not safe_indices:
            # Si no hi ha direccions segures, utilitzar la més segura
            best_idx = np.argmax(safety_values)
        else:
            # Entre les direccions segures, trobar la més propera a l'actual
            angle_diffs = [abs(angles[i] - current_direction) for i in safe_indices]
            min_diff_idx = np.argmin(angle_diffs)
            best_idx = safe_indices[min_diff_idx]
        
        return angles[best_idx]
    
    @pyqtSlot()
    def _check_obstacles(self):
        """Comprova si hi ha obstacles propers i emet senyals."""
        if not self.enabled or not self.scanning:
            return
        
        # Obtenir l'obstacle més proper davant (±30 graus)
        angle, distance = self.lidar_data.get_nearest_obstacle((-0.5, 0.5))
        
        if angle is not None and distance < 500:  # 50 cm
            # Emetre senyal d'obstacle
            self.obstacle_detected.emit(angle, distance)
            logger.debug(f"Obstacle detectat: angle={angle:.2f} rad, distància={distance} mm")
    
    def cleanup(self):
        """Neteja recursos abans de tancar."""
        # Aturar timer
        if self.obstacle_timer.isActive():
            self.obstacle_timer.stop()
        
        logger.info("LidarManager netejat")
