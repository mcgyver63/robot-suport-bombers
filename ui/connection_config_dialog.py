from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGridLayout, QGroupBox,
    QPushButton, QLabel, QLineEdit, QCheckBox, QSpinBox,
    QDialogButtonBox, QComboBox, QTabWidget, QWidget
)
from PyQt5.QtCore import Qt

class ConnectionConfigDialog(QDialog):
    """
    Diàleg millorat per configurar la connexió amb el robot.
    Proporciona opcions per configurar l'adreça IP, port, 
    reconnexió automàtica i altres paràmetres de comunicació.
    """
    
    def __init__(self, current_config, parent=None):
        """
        Inicialitza el diàleg amb la configuració actual.
        
        Args:
            current_config (dict): Configuració actual
            parent: Widget pare
        """
        super().__init__(parent)
        
        # Assegurar que la configuració és un diccionari
        if not isinstance(current_config, dict):
            current_config = {}
        
        self.setWindowTitle("Configuració de Connexió")
        self.setMinimumWidth(400)
        
        # Crear el layout principal amb pestanyes
        self.tab_widget = QTabWidget()
        self.main_layout = QVBoxLayout(self)
        self.main_layout.addWidget(self.tab_widget)
        
        # Crear pestanyes
        self.connection_tab = QWidget()
        self.advanced_tab = QWidget()
        self.heartbeat_tab = QWidget()
        
        self.tab_widget.addTab(self.connection_tab, "Connexió Bàsica")
        self.tab_widget.addTab(self.advanced_tab, "Opcions Avançades")
        self.tab_widget.addTab(self.heartbeat_tab, "Heartbeat")
        
        # Configurar cada pestanya
        self._setup_connection_tab(current_config)
        self._setup_advanced_tab(current_config)
        self._setup_heartbeat_tab(current_config)
        
        # Botó de desar i cancel·lar
        self.button_box = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        self.main_layout.addWidget(self.button_box)
        
        # Configurar mida
        self.resize(450, 350)
    
    def _setup_connection_tab(self, config):
        """Configura la pestanya de connexió bàsica."""
        layout = QVBoxLayout(self.connection_tab)
        
        # Grup de configuració de connexió
        connection_group = QGroupBox("Paràmetres de connexió")
        connection_layout = QGridLayout()
        
        # IP del robot
        connection_layout.addWidget(QLabel("IP del robot:"), 0, 0)
        self.ip_input = QLineEdit()
        self.ip_input.setText(config.get("host", "192.168.1.100"))
        self.ip_input.setPlaceholderText("p. ex. 192.168.1.100")
        connection_layout.addWidget(self.ip_input, 0, 1)
        
        # Port
        connection_layout.addWidget(QLabel("Port:"), 1, 0)
        self.port_input = QLineEdit()
        self.port_input.setText(str(config.get("port", 9999)))
        self.port_input.setPlaceholderText("p. ex. 9999")
        connection_layout.addWidget(self.port_input, 1, 1)
        
        # Tipus de connexió (per a futures expansions)
        connection_layout.addWidget(QLabel("Tipus de connexió:"), 2, 0)
        self.connection_type = QComboBox()
        self.connection_type.addItems(["TCP/IP", "Serial", "Bluetooth"])
        # Seleccionar el tipus actual
        current_type = config.get("connection_type", "TCP/IP")
        index = self.connection_type.findText(current_type)
        if index >= 0:
            self.connection_type.setCurrentIndex(index)
        connection_layout.addWidget(self.connection_type, 2, 1)
        
        # Temps d'espera de connexió
        connection_layout.addWidget(QLabel("Temps d'espera (segons):"), 3, 0)
        self.timeout_input = QSpinBox()
        self.timeout_input.setRange(1, 60)
        self.timeout_input.setValue(config.get("timeout", 5))
        connection_layout.addWidget(self.timeout_input, 3, 1)
        
        # Reconnexió automàtica
        connection_layout.addWidget(QLabel("Reconnexió automàtica:"), 4, 0)
        self.auto_reconnect = QCheckBox()
        self.auto_reconnect.setChecked(config.get("auto_reconnect", True))
        connection_layout.addWidget(self.auto_reconnect, 4, 1)
        
        connection_group.setLayout(connection_layout)
        layout.addWidget(connection_group)
        
        # Estat actual de connexió
        status_group = QGroupBox("Estat actual")
        status_layout = QHBoxLayout()
        
        status_text = "Desconnectat"
        status_color = "red"
        
        if hasattr(self.parent(), "connection_manager") and self.parent().connection_manager:
            if getattr(self.parent().connection_manager, "connected", False):
                status_text = f"Connectat a {config.get('host', '?')}:{config.get('port', '?')}"
                status_color = "green"
        
        status_label = QLabel(f"<span style='color: {status_color};'>{status_text}</span>")
        status_layout.addWidget(status_label)
        
        status_group.setLayout(status_layout)
        layout.addWidget(status_group)
        
        # Espai flexible
        layout.addStretch()
    
    def _setup_advanced_tab(self, config):
        """Configura la pestanya d'opcions avançades."""
        layout = QVBoxLayout(self.advanced_tab)
        
        # Grup d'opcions avançades
        advanced_group = QGroupBox("Opcions avançades")
        advanced_layout = QGridLayout()
        
        # Interval de reconnexió
        advanced_layout.addWidget(QLabel("Interval de reconnexió (segons):"), 0, 0)
        self.reconnect_interval = QSpinBox()
        self.reconnect_interval.setRange(1, 60)
        self.reconnect_interval.setValue(config.get("reconnect_interval", 5))
        advanced_layout.addWidget(self.reconnect_interval, 0, 1)
        
        # Nombre màxim d'intents
        advanced_layout.addWidget(QLabel("Màxim d'intents de reconnexió:"), 1, 0)
        self.max_reconnect_attempts = QSpinBox()
        self.max_reconnect_attempts.setRange(1, 100)
        self.max_reconnect_attempts.setValue(config.get("max_reconnect_attempts", 5))
        advanced_layout.addWidget(self.max_reconnect_attempts, 1, 1)
        
        # Mida del buffer
        advanced_layout.addWidget(QLabel("Mida del buffer (bytes):"), 2, 0)
        self.buffer_size = QSpinBox()
        self.buffer_size.setRange(1024, 65536)
        self.buffer_size.setSingleStep(1024)
        self.buffer_size.setValue(config.get("buffer_size", 8192))
        advanced_layout.addWidget(self.buffer_size, 2, 1)
        
        # Protocol d'encriptació (per a futures expansions)
        advanced_layout.addWidget(QLabel("Protocol de seguretat:"), 3, 0)
        self.security_protocol = QComboBox()
        self.security_protocol.addItems(["Cap", "SSL/TLS", "Personalitzat"])
        current_protocol = config.get("security_protocol", "Cap")
        index = self.security_protocol.findText(current_protocol)
        if index >= 0:
            self.security_protocol.setCurrentIndex(index)
        advanced_layout.addWidget(self.security_protocol, 3, 1)
        
        advanced_group.setLayout(advanced_layout)
        layout.addWidget(advanced_group)
        
        # Opcions per a logs i depuració
        debug_group = QGroupBox("Depuració i logs")
        debug_layout = QGridLayout()
        
        # Nivell de log
        debug_layout.addWidget(QLabel("Nivell de log:"), 0, 0)
        self.log_level = QComboBox()
        self.log_level.addItems(["INFO", "DEBUG", "WARNING", "ERROR"])
        current_level = config.get("log_level", "INFO")
        index = self.log_level.findText(current_level)
        if index >= 0:
            self.log_level.setCurrentIndex(index)
        debug_layout.addWidget(self.log_level, 0, 1)
        
        # Activar logs detallats de comunicació
        debug_layout.addWidget(QLabel("Logs detallats de comunicació:"), 1, 0)
        self.verbose_logging = QCheckBox()
        self.verbose_logging.setChecked(config.get("verbose_logging", False))
        debug_layout.addWidget(self.verbose_logging, 1, 1)
        
        debug_group.setLayout(debug_layout)
        layout.addWidget(debug_group)
        
        # Espai flexible
        layout.addStretch()
    
    def _setup_heartbeat_tab(self, config):
        """Configura la pestanya de heartbeat."""
        layout = QVBoxLayout(self.heartbeat_tab)
        
        # Grup de configuració de heartbeat
        heartbeat_group = QGroupBox("Configuració de Heartbeat")
        heartbeat_layout = QGridLayout()
        
        # Activar heartbeat
        heartbeat_layout.addWidget(QLabel("Activar heartbeat:"), 0, 0)
        self.enable_heartbeat = QCheckBox()
        self.enable_heartbeat.setChecked(config.get("enable_heartbeat", True))
        heartbeat_layout.addWidget(self.enable_heartbeat, 0, 1)
        
        # Interval de heartbeat
        heartbeat_layout.addWidget(QLabel("Interval (segons):"), 1, 0)
        self.heartbeat_interval = QSpinBox()
        self.heartbeat_interval.setRange(1, 60)
        self.heartbeat_interval.setValue(config.get("heartbeat_interval", 5))
        heartbeat_layout.addWidget(self.heartbeat_interval, 1, 1)
        
        # Timeout de heartbeat
        heartbeat_layout.addWidget(QLabel("Timeout (segons):"), 2, 0)
        self.heartbeat_timeout = QSpinBox()
        self.heartbeat_timeout.setRange(2, 120)
        self.heartbeat_timeout.setValue(config.get("heartbeat_timeout", 10))
        heartbeat_layout.addWidget(self.heartbeat_timeout, 2, 1)
        
        # Acció en cas de timeout
        heartbeat_layout.addWidget(QLabel("Acció en timeout:"), 3, 0)
        self.heartbeat_action = QComboBox()
        self.heartbeat_action.addItems(["Reconnectar", "Notificar", "Ignorar"])
        current_action = config.get("heartbeat_action", "Reconnectar")
        index = self.heartbeat_action.findText(current_action)
        if index >= 0:
            self.heartbeat_action.setCurrentIndex(index)
        heartbeat_layout.addWidget(self.heartbeat_action, 3, 1)
        
        heartbeat_group.setLayout(heartbeat_layout)
        layout.addWidget(heartbeat_group)
        
        # Espai flexible
        layout.addStretch()
    
    def get_config(self):
        """
        Obté la configuració actual del diàleg.
        
        Returns:
            dict: Configuració actualitzada
        """
        config = {
            # Pestanya de connexió bàsica
            "host": self.ip_input.text(),
            "port": int(self.port_input.text()),
            "connection_type": self.connection_type.currentText(),
            "timeout": self.timeout_input.value(),
            "auto_reconnect": self.auto_reconnect.isChecked(),
            
            # Pestanya d'opcions avançades
            "reconnect_interval": self.reconnect_interval.value(),
            "max_reconnect_attempts": self.max_reconnect_attempts.value(),
            "buffer_size": self.buffer_size.value(),
            "security_protocol": self.security_protocol.currentText(),
            "log_level": self.log_level.currentText(),
            "verbose_logging": self.verbose_logging.isChecked(),
            
            # Pestanya de heartbeat
            "enable_heartbeat": self.enable_heartbeat.isChecked(),
            "heartbeat_interval": self.heartbeat_interval.value(),
            "heartbeat_timeout": self.heartbeat_timeout.value(),
            "heartbeat_action": self.heartbeat_action.currentText()
        }
        
        return config
