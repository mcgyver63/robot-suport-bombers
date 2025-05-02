#!/usr/bin/env python3
"""
Mòdul de Càmera (CameraManager)
===============================
Gestiona la recepció i processament d'imatges de la càmera del robot.
"""

import base64
import time
import logging
import numpy as np
from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot, QTimer
from PyQt5.QtGui import QImage, QPixmap

# Intentar importar OpenCV
try:
    import cv2
    HAS_OPENCV = True
except ImportError:
    HAS_OPENCV = False
    logging.warning("OpenCV no instal·lat. Funcionalitats de càmera limitades.")

# Configuració de logging
logger = logging.getLogger("Camera")

class CameraManager(QObject):
    """
    Gestiona la càmera del robot.
    Processa les trames rebudes i proporciona mètodes per iniciar/aturar l'streaming.
    """
    
    # Signals
    camera_frame_ready = pyqtSignal(QImage)  # Imatge processada
    camera_status_changed = pyqtSignal(bool, str)  # Actiu, missatge
    
    def __init__(self, config):
        """
        Inicialitza el gestor de càmera.
        
        Args:
            config (dict): Configuració de la càmera
        """
        super().__init__()
        
        # Verificar si tenim OpenCV
        self.has_opencv = HAS_OPENCV
        
        # Càrrega de configuració
        self.config = config
        camera_config = config.get('camera', {})
        
        # Paràmetres configurables
        self.enabled = camera_config.get('enabled', True)
        self.resolution = camera_config.get('resolution', [640, 480])
        self.fps = camera_config.get('fps', 15)
        
        # Estats
        self.streaming = False
        self.last_frame_time = 0
        self.current_frame = None
        self.frame_count = 0
        self.fps_real = 0
        
        # Timer per calcular FPS real
        self.fps_timer = QTimer()
        self.fps_timer.timeout.connect(self._update_fps)
        self.fps_timer.start(1000)  # 1 segon
        
        # Inicialitzar processament d'imatge si és possible
        if self.has_opencv:
            # Inicialitzar variables per processament
            self.processing_enabled = False
            self.brightness = 0
            self.contrast = 1.0
            self.enable_edge_detection = False
            self.enable_motion_detection = False
            self.previous_frame = None
            self.motion_threshold = 25
        
        logger.info("CameraManager inicialitzat")
    
    @pyqtSlot(dict)
    def process_data(self, data):
        """
        Processa dades rebudes del bridge.
        
        Args:
            data (dict): Dades rebudes en format JSON
        """
        # Si la càmera està desactivada, ignorar
        if not self.enabled:
            return
        
        # Comprovar tipus de dades
        if data.get('type') == 'camera_frame':
            # Processar trama de càmera
            self._process_camera_frame(data)
    
    def _process_camera_frame(self, data):
        """
        Processa una trama de càmera.
        
        Args:
            data (dict): Dades de la trama
        """
        # Si no tenim OpenCV, no podem processar la imatge
        if not self.has_opencv:
            logger.warning("No es pot processar la trama: OpenCV no disponible")
            return
        
        try:
            # Obtenir dades de la imatge en base64
            frame_data = data.get('data', '')
            
            if not frame_data:
                logger.warning("Trama de càmera buida rebuda")
                return
            
            # Descodificar base64 a bytes
            img_bytes = base64.b64decode(frame_data)
            
            # Convertir bytes a numpy array
            nparr = np.frombuffer(img_bytes, np.uint8)
            
            # Descodificar a imatge
            frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            if frame is None:
                logger.warning("No s'ha pogut descodificar la imatge")
                return
            
            # Actualitzar estat
            self.streaming = True
            self.last_frame_time = time.time()
            self.frame_count += 1
            
            # Aplicar processament d'imatge si està activat
            if self.processing_enabled:
                frame = self._apply_image_processing(frame)
            
            # Convertir de BGR a RGB (OpenCV utilitza BGR per defecte)
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # Convertir a QImage
            h, w, ch = frame_rgb.shape
            bytes_per_line = ch * w
            qt_image = QImage(frame_rgb.data, w, h, bytes_per_line, QImage.Format_RGB888)
            
            # Desar trama actual
            self.current_frame = qt_image
            
            # Emetre senyal amb la imatge processada
            self.camera_frame_ready.emit(qt_image)
            
            # Debug
            logger.debug(f"Trama {self.frame_count} processada ({w}x{h})")
            
        except Exception as e:
            logger.error(f"Error processant trama de càmera: {e}")
    
    def _apply_image_processing(self, frame):
        """
        Aplica processament d'imatge a la trama.
        
        Args:
            frame (numpy.ndarray): Trama en format OpenCV
            
        Returns:
            numpy.ndarray: Trama processada
        """
        try:
            # Ajustar brillantor i contrast
            if self.brightness != 0 or self.contrast != 1.0:
                frame = cv2.convertScaleAbs(frame, alpha=self.contrast, beta=self.brightness)
            
            # Detecció de vores
            if self.enable_edge_detection:
                # Convertir a escala de grisos
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                
                # Aplicar filtre gaussià per reduir soroll
                blurred = cv2.GaussianBlur(gray, (5, 5), 0)
                
                # Detectar vores amb Canny
                edges = cv2.Canny(blurred, 50, 150)
                
                # Convertir de nou a BGR per superposar
                edges_colored = cv2.cvtColor(edges, cv2.COLOR_GRAY2BGR)
                
                # Superposar vores a la imatge original
                frame = cv2.addWeighted(frame, 0.7, edges_colored, 0.3, 0)
            
            # Detecció de moviment
            if self.enable_motion_detection and self.previous_frame is not None:
                # Convertir a escala de grisos
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                gray_prev = cv2.cvtColor(self.previous_frame, cv2.COLOR_BGR2GRAY)
                
                # Calcular diferència absoluta
                frame_diff = cv2.absdiff(gray, gray_prev)
                
                # Aplicar llindar
                _, thresh = cv2.threshold(frame_diff, self.motion_threshold, 255, cv2.THRESH_BINARY)
                
                # Aplicar operacions morfològiques per eliminar soroll
                kernel = np.ones((5, 5), np.uint8)
                thresh = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel)
                thresh = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
                
                # Trobar contorns
                contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                
                # Dibuixar contorns
                cv2.drawContours(frame, contours, -1, (0, 255, 0), 2)
            
            # Guardar trama actual per a la següent iteració
            self.previous_frame = frame.copy()
            
            return frame
            
        except Exception as e:
            logger.error(f"Error aplicant processament d'imatge: {e}")
            return frame
    
    def start_stream(self, connection_manager):
        """
        Inicia l'streaming de la càmera.
        
        Args:
            connection_manager: Gestor de connexió per enviar la comanda
            
        Returns:
            bool: True si s'ha enviat correctament, False en cas contrari
        """
        if not self.enabled:
            logger.warning("Càmera desactivada, no es pot iniciar streaming")
            return False
        
        if not connection_manager or not connection_manager.connected:
            logger.error("No es pot iniciar streaming: gestor de connexió no disponible")
            return False
        
        logger.info("Iniciant streaming de càmera")
        self.camera_status_changed.emit(True, "Iniciant streaming")
        
        return connection_manager.send_command({
            "type": "camera_control",
            "action": "start_stream",
            "fps": self.fps,
            "resolution": self.resolution
        })
    
    def stop_stream(self, connection_manager):
        """
        Atura l'streaming de la càmera.
        
        Args:
            connection_manager: Gestor de connexió per enviar la comanda
            
        Returns:
            bool: True si s'ha enviat correctament, False en cas contrari
        """
        if not connection_manager or not connection_manager.connected:
            logger.error("No es pot aturar streaming: gestor de connexió no disponible")
            return False
        
        logger.info("Aturant streaming de càmera")
        self.streaming = False
        self.camera_status_changed.emit(False, "Streaming aturat")
        
        return connection_manager.send_command({
            "type": "camera_control",
            "action": "stop_stream"
        })
    
    def capture_snapshot(self):
        """
        Captura una instantània de la trama actual.
        
        Returns:
            QImage: Imatge capturada o None si no hi ha trama disponible
        """
        if self.current_frame is None:
            logger.warning("No hi ha cap trama disponible per capturar")
            return None
        
        # Crear una còpia de la imatge actual
        snapshot = QImage(self.current_frame)
        
        logger.info("Instantània capturada")
        return snapshot
    
    def save_snapshot(self, file_path):
        """
        Guarda una instantània en un fitxer.
        
        Args:
            file_path (str): Ruta del fitxer
            
        Returns:
            bool: True si s'ha guardat correctament, False en cas contrari
        """
        snapshot = self.capture_snapshot()
        
        if snapshot is None:
            return False
        
        try:
            success = snapshot.save(file_path)
            
            if success:
                logger.info(f"Instantània guardada a {file_path}")
            else:
                logger.error(f"No s'ha pogut guardar la instantània a {file_path}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error guardant instantània: {e}")
            return False
    
    def is_streaming(self):
        """
        Comprova si l'streaming està actiu.
        
        Returns:
            bool: True si l'streaming està actiu, False en cas contrari
        """
        # Comprovar si fa massa temps des de l'última trama
        if time.time() - self.last_frame_time > 5:  # 5 segons
            self.streaming = False
            self.camera_status_changed.emit(False, "Streaming perdut")
        
        return self.streaming
    
    def enable_processing(self, enabled=True):
        """
        Activa o desactiva el processament d'imatge.
        
        Args:
            enabled (bool, optional): Estat d'activació. Defaults to True.
        """
        if not self.has_opencv:
            logger.warning("No es pot activar processament: OpenCV no disponible")
            return False
        
        self.processing_enabled = enabled
        logger.info(f"Processament d'imatge {'activat' if enabled else 'desactivat'}")
        return True
    
    def set_brightness(self, value):
        """
        Estableix la brillantor de la imatge.
        
        Args:
            value (int): Valor de brillantor (-100 a 100)
        """
        self.brightness = max(-100, min(100, value))
    
    def set_contrast(self, value):
        """
        Estableix el contrast de la imatge.
        
        Args:
            value (float): Valor de contrast (0.0 a 3.0)
        """
        self.contrast = max(0.0, min(3.0, value))
    
    def toggle_edge_detection(self, enabled=None):
        """
        Activa o desactiva la detecció de vores.
        
        Args:
            enabled (bool, optional): Estat d'activació. Si és None, commuta l'estat actual.
        """
        if enabled is None:
            self.enable_edge_detection = not self.enable_edge_detection
        else:
            self.enable_edge_detection = enabled
    
    def toggle_motion_detection(self, enabled=None):
        """
        Activa o desactiva la detecció de moviment.
        
        Args:
            enabled (bool, optional): Estat d'activació. Si és None, commuta l'estat actual.
        """
        if enabled is None:
            self.enable_motion_detection = not self.enable_motion_detection
        else:
            self.enable_motion_detection = enabled
    
    def set_motion_threshold(self, value):
        """
        Estableix el llindar per a la detecció de moviment.
        
        Args:
            value (int): Valor de llindar (0 a 100)
        """
        self.motion_threshold = max(0, min(100, value))
    
    def get_current_frame(self):
        """
        Obté la trama actual.
        
        Returns:
            QImage: Trama actual o None si no hi ha trama disponible
        """
        return self.current_frame
    
    def get_fps(self):
        """
        Obté els frames per segon actuals.
        
        Returns:
            float: FPS reals
        """
        return self.fps_real
    
    @pyqtSlot()
    def _update_fps(self):
        """Actualitza el càlcul de FPS reals."""
        # Guardar valor actual
        old_count = self.frame_count
        
        # Reiniciar comptador
        self.frame_count = 0
        
        # Calcular FPS
        self.fps_real = old_count
        
        logger.debug(f"FPS reals: {self.fps_real}")
    
    def cleanup(self):
        """Neteja recursos abans de tancar."""
        # Aturar timer
        if self.fps_timer.isActive():
            self.fps_timer.stop()
        
        # Alliberar recursos
        self.current_frame = None
        self.previous_frame = None
        
        logger.info("CameraManager netejat")
