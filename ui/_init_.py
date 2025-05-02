"""
Paquet d'interfície d'usuari per al Sistema de Control de Robot per a Bombers.
Conté els components visuals per a la interfície gràfica, incloent la finestra principal
i tots els widgets especialitzats.
"""

__version__ = '1.0.0'

# Importar els mòduls per facilitar l'accés
from . import main_window

# Exportar classes principals per accés directe
from .main_window import MainWindow

__all__ = [
    'MainWindow',
    'main_window',
]
