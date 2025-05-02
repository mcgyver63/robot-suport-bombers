#!/usr/bin/env python3
"""
Mòdul d'Utilitats (utils.py)
============================
Proporciona funcions i classes d'utilitat comunes per als altres mòduls del sistema.
"""

import os
import sys
import json
import logging
import time
from datetime import datetime

# Configuració de logging
logger = logging.getLogger("Utils")

def setup_logging(log_dir="logs", level=logging.INFO, log_to_console=True):
    """
    Configura el sistema de logging global.
    
    Args:
        log_dir (str): Directori on desar els fitxers de log
        level (int): Nivell de logging (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_to_console (bool): Si cal mostrar logs a la consola
        
    Returns:
        logging.Logger: Logger principal
    """
    # Crear directori de logs si no existeix
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    # Nom del fitxer de log amb timestamp
    log_file = os.path.join(
        log_dir, 
        f"robot_control_{datetime.now().strftime('%Y%m%d-%H%M%S')}.log"
    )
    
    # Configuració bàsica
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    
    # Format del log
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Handler per fitxer
    file_handler = logging.FileHandler(log_file)
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)
    
    # Handler per consola (opcional)
    if log_to_console:
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)
    
    logger.info(f"Logging configurat. Fitxer de log: {log_file}")
    return root_logger

def format_time(timestamp=None):
    """
    Formata un timestamp a string llegible.
    
    Args:
        timestamp (float, optional): Timestamp unix. Si None, s'utilitza el temps actual.
        
    Returns:
        str: Timestamp formatat
    """
    if timestamp is None:
        timestamp = time.time()
    
    return datetime.fromtimestamp(timestamp).strftime('%H:%M:%S')

def parse_json_safe(json_str, default=None):
    """
    Analitza una cadena JSON de forma segura.
    
    Args:
        json_str (str): Cadena JSON a analitzar
        default: Valor a retornar en cas d'error
        
    Returns:
        dict/list/value: El resultat de l'anàlisi o el valor per defecte
    """
    try:
        return json.loads(json_str)
    except json.JSONDecodeError:
        logger.warning(f"Error analitzant JSON: {json_str[:50]}...")
        return default
    except Exception as e:
        logger.error(f"Error desconegut analitzant JSON: {e}")
        return default

def get_app_dir():
    """
    Obté el directori de l'aplicació.
    
    Returns:
        str: Ruta al directori de l'aplicació
    """
    if getattr(sys, 'frozen', False):
        # Si s'executa com a executable
        return os.path.dirname(sys.executable)
    else:
        # Si s'executa com a script
        return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def get_resource_path(relative_path):
    """
    Obté la ruta absoluta a un recurs relatiu.
    
    Args:
        relative_path (str): Ruta relativa al recurs
        
    Returns:
        str: Ruta absoluta al recurs
    """
    base_dir = get_app_dir()
    return os.path.join(base_dir, relative_path)

class Debouncer:
    """Classe per a debouncing de funcions (evitar crides excessives)."""
    
    def __init__(self, wait_time):
        """
        Inicialitza el debouncer.
        
        Args:
            wait_time (float): Temps mínim entre crides (segons)
        """
        self.wait_time = wait_time
        self.last_call = 0
    
    def should_call(self):
        """
        Comprova si ha passat prou temps des de l'última crida.
        
        Returns:
            bool: True si ha passat més temps que wait_time
        """
        current_time = time.time()
        if current_time - self.last_call > self.wait_time:
            self.last_call = current_time
            return True
        return False
    
    def reset(self):
        """Reinicia el comptador de temps."""
        self.last_call = 0

class RateLimiter:
    """Classe per limitar la freqüència de crides a funcions."""
    
    def __init__(self, max_calls, period):
        """
        Inicialitza el rate limiter.
        
        Args:
            max_calls (int): Nombre màxim de crides
            period (float): Període de temps en segons
        """
        self.max_calls = max_calls
        self.period = period
        self.calls = []
    
    def can_call(self):
        """
        Comprova si es pot fer una nova crida.
        
        Returns:
            bool: True si es pot fer la crida
        """
        current_time = time.time()
        
        # Eliminar crides antigues
        self.calls = [t for t in self.calls if current_time - t < self.period]
        
        # Comprovar si es pot fer una nova crida
        if len(self.calls) < self.max_calls:
            self.calls.append(current_time)
            return True
        
        return False
    
    def reset(self):
        """Reinicia el comptador de crides."""
        self.calls = []
