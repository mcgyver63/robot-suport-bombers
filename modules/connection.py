#!/usr/bin/env python3
"""
Mòdul de Connexió (ConnectionManager)
=====================================
Gestiona la comunicació entre el PC i el Bridge Raspberry Pi,
implementant un protocol TCP/IP robust amb reconnexió automàtica.
"""

import socket
import json
import threading
import time
import queue
import logging
from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot, QTimer

# Configuració de logging
logger = logging.getLogger("Connection")

class ConnectionManager(QObject):
    """
    Gestiona la connexió amb el bridge de la Raspberry Pi.
    Proporciona mètodes per enviar i rebre dades, i reconnectar automàticament.
    """
    
    # Signals
    connection_status_changed = pyqtSignal(bool, str)  # Estat, missatge
    data_received = pyqtSignal(dict)  # Dades JSON rebudes
    connection_error = pyqtSignal(str)  # Missatge d'error
    
    def __init__(self, config):
        """
        Inicialitza el gestor de connexió.
        
        Args:
            config (dict): Configuració amb host i port.
        """
        super().__init__()
        
        # Configuració de connexió
        self.host = config.get('connection', {}).get('host', '192.168.1.100')
        self.port = config.get('connection', {}).get('port', 9999)
        self.auto_reconnect = config.get('connection', {}).get('auto_reconnect', True)
        self.reconnect_interval = config.get('connection', {}).get('reconnect_interval', 5)  # segons
        
        # Variables d'estat
        self.socket = None
        self.connected = False
        self.running = False
        self.last_heartbeat = 0
        self.heartbeat_timeout = 10  # segons
        
        # Cues per a missatges
        self.send_queue = queue.Queue()
        self.receive_queue = queue.Queue(maxsize=100)  # Limitar per evitar memory leaks
        
        # Threads
        self.receive_thread = None
        self.process_thread = None
        self.reconnect_timer = None
        
        # Comptador de reconnexions
        self.reconnect_attempts = 0
        self.max_reconnect_attempts = 5
        
        logger.info(f"ConnectionManager inicialitzat: {self.host}:{self.port}")
    
    def connect(self):
        """
        Estableix connexió amb el bridge.
        
        Returns:
            bool: True si la connexió s'ha establert, False en cas contrari.
        """
        if self.connected:
            logger.info("Ja connectat al bridge")
            return True
        
        logger.info(f"Intentant connectar a {self.host}:{self.port}")
        try:
            # Crear un nou socket
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(5)  # Timeout de 5 segons
            self.socket.connect((self.host, self.port))
            
            # Actualitzar estat
            self.connected = True
            self.running = True
            self.reconnect_attempts = 0
            self.last_heartbeat = time.time()
            
            # Iniciar els threads de comunicació
            self._start_threads()
            
            # Emetre senyal d'estat
            self.connection_status_changed.emit(True, f"Connectat a {self.host}:{self.port}")
            logger.info(f"Connectat a {self.host}:{self.port}")
            
            # Iniciar timer de heartbeat
            self._start_heartbeat_timer()
            
            return True
            
        except Exception as e:
            self.connected = False
            self.socket = None
            self.connection_error.emit(f"Error connectant al bridge: {e}")
            logger.error(f"Error connectant al bridge: {e}")
            
            # Iniciar reconnexió automàtica si està habilitada
            if self.auto_reconnect:
                self._schedule_reconnect()
            
            return False
    
    def disconnect(self):
        """Desconnecta del bridge i neteja recursos."""
        logger.info("Desconnectant del bridge")
        
        # Aturar threads i timers
        self.running = False
        
        if self.reconnect_timer:
            self.reconnect_timer.stop()
        
        # Tancar socket
        if self.socket:
            try:
                self.socket.close()
            except Exception as e:
                logger.error(f"Error tancant socket: {e}")
            finally:
                self.socket = None
        
        # Actualitzar estat
        self.connected = False
        
        # Emetre senyal d'estat
        self.connection_status_changed.emit(False, "Desconnectat")
        logger.info("Desconnectat del bridge")
    
    def send_command(self, command):
        """
        Envia una comanda al bridge.
        
        Args:
            command (dict): Comanda a enviar en format diccionari.
            
        Returns:
            bool: True si la comanda s'ha posat a la cua, False en cas contrari.
        """
        if not self.connected:
            logger.warning("No es pot enviar comanda: No connectat")
            return False
        
        try:
            # Convertir comanda a JSON i afegir-la a la cua
            command_json = json.dumps(command)
            self.send_queue.put(command_json)
            logger.debug(f"Comanda posada a la cua: {command_json}")
            return True
        except Exception as e:
            logger.error(f"Error preparant comanda: {e}")
            return False
    
    def cleanup(self):
        """Neteja recursos i tanca connexions."""
        self.disconnect()
        
        # Netejar cues
        while not self.send_queue.empty():
            try:
                self.send_queue.get_nowait()
                self.send_queue.task_done()
            except:
                pass
        
        while not self.receive_queue.empty():
            try:
                self.receive_queue.get_nowait()
                self.receive_queue.task_done()
            except:
                pass
        
        logger.info("Connexió netejada")
    
    def _start_threads(self):
        """Inicia els threads de comunicació."""
        # Thread per rebre dades
        self.receive_thread = threading.Thread(target=self._receive_data_thread)
        self.receive_thread.daemon = True
        self.receive_thread.start()
        
        # Thread per processar dades rebudes
        self.process_thread = threading.Thread(target=self._process_data_thread)
        self.process_thread.daemon = True
        self.process_thread.start()
        
        # Thread per enviar dades
        self.send_thread = threading.Thread(target=self._send_data_thread)
        self.send_thread.daemon = True
        self.send_thread.start()
        
        logger.debug("Threads de comunicació iniciats")
    
    def _receive_data_thread(self):
        """Thread que rep dades del bridge i les posa a la cua de recepció."""
        buffer = ""
        
        while self.running and self.connected:
            try:
                # Rebre dades
                data = self.socket.recv(8192)  # 8KB buffer
                
                if not data:
                    logger.warning("Connexió tancada pel bridge")
                    self._handle_connection_loss()
                    break
                
                # Actualitzar timestamp de l'últim heartbeat rebut
                self.last_heartbeat = time.time()
                
                # Afegir dades al buffer i processar línies completes
                buffer += data.decode('utf-8', errors='replace')
                
                # Processar totes les línies completes
                while '\n' in buffer:
                    line, buffer = buffer.split('\n', 1)
                    
                    if line:
                        # Si la cua està plena, descartar les dades més antigues
                        if self.receive_queue.full():
                            try:
                                self.receive_queue.get_nowait()
                                self.receive_queue.task_done()
                            except:
                                pass
                        
                        # Afegir nova línia a la cua
                        self.receive_queue.put(line)
                
            except socket.timeout:
                # Timeout és normal, verificar heartbeat
                self._check_heartbeat()
                continue
            except Exception as e:
                if self.running:  # Ignora errors si s'està aturant voluntàriament
                    logger.error(f"Error rebent dades: {e}")
                    self._handle_connection_loss()
                break
        
        logger.debug("Thread de recepció aturat")
    
    def _process_data_thread(self):
        """Thread que processa les dades rebudes i emet signals."""
        while self.running:
            try:
                # Obtenir dades de la cua amb timeout
                try:
                    line = self.receive_queue.get(timeout=0.5)
                except queue.Empty:
                    continue
                
                # Intentar parsejar com a JSON
                try:
                    data = json.loads(line)
                    
                    # Emetre signal amb les dades rebudes
                    self.data_received.emit(data)
                    
                    # Processar tipus específics de missatges
                    if data.get('type') == 'heartbeat':
                        self.last_heartbeat = time.time()
                    elif data.get('type') == 'error':
                        logger.warning(f"Error rebut del bridge: {data.get('message')}")
                    
                    logger.debug(f"Dades processades: {data}")
                    
                except json.JSONDecodeError:
                    # No és JSON, tractar com a text pla
                    logger.debug(f"Text rebut (no és JSON): {line}")
                
                # Marcar com a processada
                self.receive_queue.task_done()
                
            except Exception as e:
                logger.error(f"Error processant dades rebudes: {e}")
                time.sleep(0.1)
        
        logger.debug("Thread de processament aturat")
    
    def _send_data_thread(self):
        """Thread que envia dades al bridge."""
        while self.running and self.connected:
            try:
                # Obtenir dades de la cua amb timeout
                try:
                    data = self.send_queue.get(timeout=0.5)
                except queue.Empty:
                    continue
                
                # Enviar dades
                if self.connected and self.socket:
                    self.socket.sendall((data + "\n").encode('utf-8'))
                    logger.debug(f"Dades enviades: {data}")
                
                # Marcar com a enviada
                self.send_queue.task_done()
                
            except Exception as e:
                logger.error(f"Error enviant dades: {e}")
                self._handle_connection_loss()
                break
        
        logger.debug("Thread d'enviament aturat")
    
    def _handle_connection_loss(self):
        """Gestiona la pèrdua de connexió."""
        if not self.connected:
            return  # Ja s'ha gestionat
        
        logger.warning("Connexió perduda")
        
        # Actualitzar estat
        self.connected = False
        
        # Tancar socket
        if self.socket:
            try:
                self.socket.close()
            except:
                pass
            finally:
                self.socket = None
        
        # Emetre senyal d'estat
        self.connection_status_changed.emit(False, "Connexió perduda")
        
        # Iniciar reconnexió automàtica si està habilitada
        if self.auto_reconnect:
            self._schedule_reconnect()
    
    def _schedule_reconnect(self):
        """Programa un intent de reconnexió."""
        if not self.auto_reconnect or self.reconnect_attempts >= self.max_reconnect_attempts:
            if self.reconnect_attempts >= self.max_reconnect_attempts:
                logger.warning(f"S'ha arribat al màxim d'intents de reconnexió ({self.max_reconnect_attempts})")
                self.connection_status_changed.emit(False, "Error de connexió: Màxim d'intents assolit")
            return
        
        self.reconnect_attempts += 1
        
        # Calcular temps d'espera amb backoff
        wait_time = min(self.reconnect_interval * self.reconnect_attempts, 30)  # màxim 30 segons
        
        logger.info(f"Programant reconnexió en {wait_time} segons (intent {self.reconnect_attempts})")
        self.connection_status_changed.emit(False, f"Reconnectant en {wait_time}s (intent {self.reconnect_attempts})")
        
        # Utilitzar QTimer per reconnectar
        self.reconnect_timer = QTimer()
        self.reconnect_timer.setSingleShot(True)
        self.reconnect_timer.timeout.connect(self._reconnect)
        self.reconnect_timer.start(wait_time * 1000)  # convertir a mil·lisegons
    
    @pyqtSlot()
    def _reconnect(self):
        """Intent de reconnexió."""
        logger.info("Intentant reconnectar...")
        self.connect()
    
    def _start_heartbeat_timer(self):
        """Inicia el timer per verificar heartbeats."""
        self.heartbeat_timer = QTimer()
        self.heartbeat_timer.timeout.connect(self._check_heartbeat)
        self.heartbeat_timer.start(self.heartbeat_timeout * 500)  # Meitat del timeout en ms
        logger.debug("Timer de heartbeat iniciat")
    
    def _check_heartbeat(self):
        """Verifica que s'hagin rebut heartbeats recents."""
        if not self.connected:
            return
            
        time_since_last = time.time() - self.last_heartbeat
        if time_since_last > self.heartbeat_timeout:
            logger.warning(f"No s'ha rebut heartbeat en {time_since_last:.1f} segons")
            self._handle_connection_loss()
