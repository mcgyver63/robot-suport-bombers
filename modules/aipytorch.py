"""
Mòdul d'Intel·ligència Artificial (AIManager) amb PyTorch
==========================================================
Proporciona funcionalitats d'IA per al reconeixement d'objectes, 
anàlisi d'imatges, i assistència a la navegació.
"""

import logging
import numpy as np
from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot, QTimer

# Importació condicional de PyTorch
try:
    import torch
    import torch.nn as nn
    import torch.nn.functional as F
    HAS_TORCH = True
except ImportError:
    HAS_TORCH = False
    logging.warning("PyTorch no instal·lat. Funcionalitats d'IA limitades.")

# Configuració del logger
logger = logging.getLogger("AI")

class DummyModel(nn.Module):
    """
    Model de demostració (a substituir per un model real entrenat).
    """
    def __init__(self):
        super().__init__()
        self.fc = nn.Linear(224 * 224 * 3, 2)  # Exemple amb imatges RGB 224x224

    def forward(self, x):
        x = x.view(x.size(0), -1)
        return F.softmax(self.fc(x), dim=1)

class AIManager(QObject):
    """
    Gestor de les funcionalitats d'IA amb PyTorch.
    Proporciona mètodes per processar imatges i dades de sensors.
    """
    
    object_detected = pyqtSignal(str, float)
    ai_status_changed = pyqtSignal(bool, str)
    
    def __init__(self, config):
        super().__init__()

        self.has_torch = HAS_TORCH
        self.config = config
        ai_config = config.get('ai', {})

        self.enabled = ai_config.get('enabled', True)
        self.model_path = ai_config.get('model_path', '')

        self.model_loaded = False
        self.is_processing = False

        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self._load_model()
        
        logger.info("AIManager inicialitzat (PyTorch)")
    
    def _load_model(self):
        """Carrega el model PyTorch (de moment, un dummy)."""
        if not self.has_torch or not self.enabled:
            logger.warning("No es pot carregar el model: PyTorch no disponible o IA desactivada")
            return False
        
        try:
            # Aquí pots carregar el teu model real, per exemple:
            # self.model = torch.load(self.model_path)
            self.model = DummyModel().to(self.device)
            self.model.eval()
            self.model_loaded = True
            logger.info("Model PyTorch carregat")
            return True
        except Exception as e:
            logger.error(f"Error carregant model PyTorch: {e}")
            return False

    def process_image(self, image):
        """
        Processa una imatge amb el model PyTorch.

        Args:
            image: numpy.ndarray o QImage

        Returns:
            list: Resultats simulats
        """
        if not self.enabled or not self.model_loaded:
            return None

        try:
            self.is_processing = True
            
            # Conversió i pre-processament de la imatge (simulat)
            if isinstance(image, np.ndarray):
                img = image
            else:
                logger.warning("Tipus d'imatge no compatible")
                return None

            # Normalitzem i redimensionem si calgués
            img = img.astype(np.float32) / 255.0
            img_resized = np.resize(img, (224, 224, 3))
            tensor = torch.from_numpy(img_resized).permute(2, 0, 1).unsqueeze(0).to(self.device)

            # Inferència (simulada amb dummy)
            with torch.no_grad():
                output = self.model(tensor)
                confidence, pred_class = torch.max(output, 1)

            results = [
                {"class": "persona", "confidence": confidence.item(), "bbox": [10, 20, 100, 200]},
                {"class": "extintor", "confidence": 0.85, "bbox": [300, 150, 50, 100]}
            ]

            for obj in results:
                self.object_detected.emit(obj["class"], obj["confidence"])

            self.is_processing = False
            return results

        except Exception as e:
            logger.error(f"Error processant imatge (PyTorch): {e}")
            self.is_processing = False
            return None

    def analyze_lidar_data(self, lidar_data):
        return {"objects": [], "navigation_suggestion": None}

    def is_ready(self):
        return self.enabled and self.model_loaded and not self.is_processing

    def cleanup(self):
        logger.info("AIManager netejat (PyTorch)")
