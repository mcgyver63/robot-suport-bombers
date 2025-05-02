"""
Finestra Principal (MainWindow)
===============================
Implementa la finestra principal de l'aplicació amb totes les funcionalitats
d'interfície d'usuari per controlar el robot.
"""
import sys
import os
import time
import logging
import json
import numpy as np
from datetime import datetime
from PyQt5.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QTabWidget,
    QLabel,
    QPushButton,
    QStatusBar,
    QMessageBox,
    QSplitter,
    QGroupBox,
    QGridLayout,
    QSlider,
    QActionGroup,
    QComboBox,
    QAction,
    QFileDialog,
    QDialog,
    QLineEdit,
    QDialogButtonBox,
    QInputDialog,
    QApplication,
    QListWidget,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QAbstractItemView,
    QCheckBox,
    QStackedWidget,
    QCalendarWidget)
from PyQt5.QtGui import QIcon, QPixmap, QImage, QColor, QPalette
from PyQt5.QtCore import Qt, QSize, pyqtSlot, QTimer, QLocale, QDate, QDateTime

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Configuració de logging
logger = logging.getLogger("UI.MainWindow")

# Imports condicionals
try:
    import matplotlib
    matplotlib.use('Qt5Agg')
    from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
    from matplotlib.figure import Figure
    import matplotlib.pyplot as plt
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False
    logger.warning(
        "Matplotlib no instal·lat. Visualitzacions gràfiques limitades.")


class MainWindow(QMainWindow):
    """
    Finestra principal de l'aplicació.
    Integra tots els components i gestiona la interacció amb l'usuari.
    """

    def __init__(
            self,
            config,
            connection_manager,
            sensor_manager,
            lidar_manager,
            camera_manager,
            navigation_manager,
            db_manager,
            config_manager,
            ai_manager=None):
        """
        Inicialitza la finestra principal.

        Args:
            config (dict): Configuració general
            connection_manager: Gestor de connexió
            sensor_manager: Gestor de sensors
            lidar_manager: Gestor de LiDAR
            camera_manager: Gestor de càmera
            navigation_manager: Gestor de navegació
            db_manager: Gestor de base de dades
            config_manager: Gestor de configuració
            ai_manager: Gestor d'IA
        """
        super().__init__()

        # Guardar referències als gestors
        self.config = config
        self.connection_manager = connection_manager
        self.sensor_manager = sensor_manager
        self.lidar_manager = lidar_manager
        self.camera_manager = camera_manager
        self.navigation_manager = navigation_manager
        self.db_manager = db_manager
        self.config_manager = config_manager
        self.ai_manager = ai_manager

        # Configurar interdependències entre gestors
        self.navigation_manager.setup_components(
            connection_manager, lidar_manager)

        # Inicialitzar la interfície
        self._init_ui()

        # Connectar signals i slots
        self._connect_signals()

        # Timer per a actualitzacions periòdiques
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self._periodic_update)
        self.update_timer.start(1000)  # 1 segon

        # Emmagatzemar l'última lectura del LiDAR
        self.last_lidar_data = None

        logger.info("MainWindow inicialitzada")

    def _init_ui(self):
        """Inicialitza la interfície d'usuari."""
        # Configuració bàsica de la finestra
        self.setWindowTitle("Sistema de Control de Robot per a Bombers")
        self.resize(1200, 800)

        # Icona de l'aplicació
        icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                 "../resources/icons/robot_icon.png")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        # Barra d'estat
        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)

        # Widget central
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Layout principal
        main_layout = QVBoxLayout(central_widget)

        # Splitter per dividir la pantalla
        self.main_splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(self.main_splitter)

        # Panel esquerre (controls)
        left_panel = self._create_left_panel()
        self.main_splitter.addWidget(left_panel)

        # Panell dret (visualització)
        right_panel = self._create_right_panel()
        self.main_splitter.addWidget(right_panel)

        # Inicialitzar mides del splitter
        self.main_splitter.setSizes([400, 800])

        # Crear menú
        self._create_menu()

        # Actualitzar estat inicial de la interfície
        self._update_ui_state()

        # Crear pestanya d'IA
        ai_panel = self._create_ai_panel()
        right_panel.addTab(ai_panel, "Intel·ligència Artificial")

    def _create_menu(self):
        """Crea la barra de menú."""
        # Menú Arxiu
        file_menu = self.menuBar().addMenu("&Arxiu")

        # Acció Projectes
        projects_action = QAction("&Projectes", self)
        projects_action.setShortcut("Ctrl+P")
        projects_action.triggered.connect(self._manage_projects)
        file_menu.addAction(projects_action)

        # Acció Guardar configuració
        save_config_action = QAction("&Guardar configuració", self)
        save_config_action.setShortcut("Ctrl+S")
        save_config_action.triggered.connect(self._save_config)
        file_menu.addAction(save_config_action)

        # Acció Carregar configuració
        load_config_action = QAction("&Carregar configuració", self)
        load_config_action.setShortcut("Ctrl+L")
        load_config_action.triggered.connect(self._load_config)
        file_menu.addAction(load_config_action)

        file_menu.addSeparator()

        # Acció Sortir
        exit_action = QAction("&Sortir", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # Menú Eines
        tools_menu = self.menuBar().addMenu("&Eines")

        # Acció Calibrar sensors
        calibrate_action = QAction("&Calibrar sensors", self)
        calibrate_action.triggered.connect(self._calibrate_sensors)
        tools_menu.addAction(calibrate_action)

        # Acció Reiniciar connexió
        reconnect_action = QAction("&Reiniciar connexió", self)
        reconnect_action.triggered.connect(self._reconnect)
        tools_menu.addAction(reconnect_action)

        # Acció Captures de pantalla
        screenshot_action = QAction("&Capturar pantalla", self)
        screenshot_action.setShortcut("F12")
        screenshot_action.triggered.connect(self._take_screenshot)
        tools_menu.addAction(screenshot_action)

        tools_menu.addSeparator()

        # Acció Preferències
        preferences_action = QAction("&Preferències", self)
        preferences_action.triggered.connect(self._show_preferences)
        tools_menu.addAction(preferences_action)

        # Menú Visualització
        view_menu = self.menuBar().addMenu("&Visualització")

        # Acció Tema clar/fosc
        self.toggle_theme_action = QAction("Tema &fosc", self)
        self.toggle_theme_action.setCheckable(True)
        self.toggle_theme_action.triggered.connect(self._toggle_theme)
        view_menu.addAction(self.toggle_theme_action)

        # Acció Vista LiDAR (selector de vista)
        lidar_view_menu = view_menu.addMenu("Vista &LiDAR")

        self.lidar_cartesian_action = QAction("&Cartesiana", self)
        self.lidar_cartesian_action.setCheckable(True)
        self.lidar_cartesian_action.setChecked(True)
        self.lidar_cartesian_action.triggered.connect(
            lambda: self._set_lidar_view(0))
        lidar_view_menu.addAction(self.lidar_cartesian_action)

        self.lidar_polar_action = QAction("&Polar", self)
        self.lidar_polar_action.setCheckable(True)
        self.lidar_polar_action.triggered.connect(
            lambda: self._set_lidar_view(1))
        lidar_view_menu.addAction(self.lidar_polar_action)

        self.lidar_combined_action = QAction("&Combinada", self)
        self.lidar_combined_action.setCheckable(True)
        self.lidar_combined_action.triggered.connect(
            lambda: self._set_lidar_view(2))
        lidar_view_menu.addAction(self.lidar_combined_action)

        # Grup d'accions per al tipus de vista
        self.lidar_view_group = QActionGroup(self)
        self.lidar_view_group.addAction(self.lidar_cartesian_action)
        self.lidar_view_group.addAction(self.lidar_polar_action)
        self.lidar_view_group.addAction(self.lidar_combined_action)
        self.lidar_view_group.setExclusive(True)

        # Menú Ajuda
        help_menu = self.menuBar().addMenu("A&juda")

        # Acció Manual d'usuari
        manual_action = QAction("&Manual d'usuari", self)
        manual_action.triggered.connect(self._show_manual)
        help_menu.addAction(manual_action)

        # Acció Sobre
        about_action = QAction("&Sobre", self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)

        # I implementar:
    def _create_ai_panel(self):
        """Crea el panell d'IA."""
        ai_panel = QWidget()
        layout = QVBoxLayout(ai_panel)
    
        # Controls d'IA
        controls_layout = QHBoxLayout()
    
        self.ai_enabled_checkbox = QCheckBox("Activar IA")
        self.ai_enabled_checkbox.setChecked(self.ai_manager.enabled)
        self.ai_enabled_checkbox.toggled.connect(self._toggle_ai)
        controls_layout.addWidget(self.ai_enabled_checkbox)
    
        # Selector de model
        controls_layout.addWidget(QLabel("Model:"))
        self.model_combo = QComboBox()
        self.model_combo.addItems(["Detecció d'objectes", "Reconeixement facial", "Personalitzat"])
        self.model_combo.currentIndexChanged.connect(self._change_ai_model)
        controls_layout.addWidget(self.model_combo)
    
        controls_layout.addStretch()
    
        layout.addLayout(controls_layout)
    
        # Visualització de deteccions
        self.detection_view = QLabel("Esperant deteccions...")
        self.detection_view.setAlignment(Qt.AlignCenter)
        self.detection_view.setMinimumSize(640, 480)
        self.detection_view.setStyleSheet("border: 1px solid #999; background-color: #111;")
        layout.addWidget(self.detection_view)
    
        # Llista d'objectes detectats
        detections_group = QGroupBox("Objectes detectats")
        detections_layout = QVBoxLayout(detections_group)
    
        self.detections_list = QTableWidget(0, 3)
        self.detections_list.setHorizontalHeaderLabels(["Objecte", "Confiança", "Posició"])
        self.detections_list.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        detections_layout.addWidget(self.detections_list)
    
        layout.addWidget(detections_group)
    
        return ai_panel

    def _toggle_ai(self, enabled):
        """Activa o desactiva la IA."""
        if hasattr(self.ai_manager, 'enabled'):
            self.ai_manager.enabled = enabled
        
        # Actualitzar interfície
            self.model_combo.setEnabled(enabled)
        
        # Mostrar estat
            if enabled:
                self.statusBar.showMessage("IA activada")
            else:
                self.statusBar.showMessage("IA desactivada")

    def _change_ai_model(self, index):
        """Canvia el model d'IA."""
        # Implementació bàsica
        model_names = ["object_detection", "face_recognition", "custom"]
        if hasattr(self.ai_manager, 'model_path'):
        # Crear ruta al model
            model_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                 "../models", model_names[index])
        
        # Aquí caldria implementar la recàrrega del model
        # Per ara, només mostrem un missatge
        self.statusBar.showMessage(f"Canviant a model: {model_names[index]}")

    def _create_right_panel(self):
        """Crea el panell dret amb visualitzacions."""
        right_panel = QTabWidget()

        # Pestanya LiDAR
        if HAS_MATPLOTLIB:
            lidar_panel = self._create_lidar_panel()
            right_panel.addTab(lidar_panel, "LiDAR")
        else:
            lidar_panel = QWidget()
            lidar_layout = QVBoxLayout(lidar_panel)
            lidar_layout.addWidget(
                QLabel("Matplotlib no disponible. Visualització LiDAR limitada."))
            right_panel.addTab(lidar_panel, "LiDAR (No disponible)")

        # Pestanya Càmera
        camera_panel = self._create_camera_panel()
        right_panel.addTab(camera_panel, "Càmera")

        # Pestanya Sensors
        sensors_panel = self._create_sensors_panel()
        right_panel.addTab(sensors_panel, "Sensors")

        # Pestanya Configuració
        config_panel = self._create_config_panel()
        right_panel.addTab(config_panel, "Configuració")

        # Pestanya Informes (nova)
        reports_panel = self._create_reports_panel()
        right_panel.addTab(reports_panel, "Informes")

        return right_panel

    def _create_left_panel(self):
        """Crea el panell esquerre amb controls."""
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)

        # Grup de Connexió
        connection_box = QGroupBox("Connexió")
        connection_layout = QVBoxLayout()

        # Indicador d'estat
        self.connection_status_label = QLabel("Estat: Desconnectat")
        connection_layout.addWidget(self.connection_status_label)

        # Botó de connexió
        self.connect_button = QPushButton("Connectar")
        self.connect_button.clicked.connect(self._toggle_connection)
        connection_layout.addWidget(self.connect_button)

        connection_box.setLayout(connection_layout)
        left_layout.addWidget(connection_box)

        # Grup de Control de Navegació
        navigation_box = QGroupBox("Control de Navegació")
        navigation_layout = QGridLayout()

        # Botons de direcció
        self.up_button = QPushButton("Endavant")
        self.up_button.clicked.connect(
            lambda: self.navigation_manager.move("forward"))

        self.down_button = QPushButton("Endarrere")
        self.down_button.clicked.connect(
            lambda: self.navigation_manager.move("backward"))

        self.left_button = QPushButton("Esquerra")
        self.left_button.clicked.connect(
            lambda: self.navigation_manager.move("left"))

        self.right_button = QPushButton("Dreta")
        self.right_button.clicked.connect(
            lambda: self.navigation_manager.move("right"))

        self.stop_button = QPushButton("Aturar")
        self.stop_button.clicked.connect(self.navigation_manager.stop)

        # Col·locar els botons en una graella
        navigation_layout.addWidget(self.up_button, 0, 1)
        navigation_layout.addWidget(self.left_button, 1, 0)
        navigation_layout.addWidget(self.stop_button, 1, 1)
        navigation_layout.addWidget(self.right_button, 1, 2)
        navigation_layout.addWidget(self.down_button, 2, 1)

        # Control de velocitat
        speed_layout = QHBoxLayout()
        speed_layout.addWidget(QLabel("Velocitat:"))

        self.speed_slider = QSlider(Qt.Horizontal)
        self.speed_slider.setRange(0, 100)
        self.speed_slider.setValue(50)
        self.speed_slider.valueChanged.connect(self._update_speed)
        speed_layout.addWidget(self.speed_slider)

        self.speed_label = QLabel("50%")
        speed_layout.addWidget(self.speed_label)

        navigation_layout.addLayout(speed_layout, 3, 0, 1, 3)

        # Selector de mode
        mode_layout = QHBoxLayout()
        mode_layout.addWidget(QLabel("Mode:"))

        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["Manual", "Assistit", "Autònom"])
        self.mode_combo.currentIndexChanged.connect(self._change_mode)
        mode_layout.addWidget(self.mode_combo)

        navigation_layout.addLayout(mode_layout, 4, 0, 1, 3)

        navigation_box.setLayout(navigation_layout)
        left_layout.addWidget(navigation_box)

        # Grup d'Alertes
        alerts_box = QGroupBox("Alertes")
        alerts_layout = QVBoxLayout()

        self.alerts_label = QLabel("Cap alerta activa")
        alerts_layout.addWidget(self.alerts_label)

        self.clear_alerts_button = QPushButton("Netejar Alertes")
        self.clear_alerts_button.clicked.connect(self._clear_alerts)
        alerts_layout.addWidget(self.clear_alerts_button)

        alerts_box.setLayout(alerts_layout)
        left_layout.addWidget(alerts_box)

        # Afegir espai elàstic al final
        left_layout.addStretch()

        return left_panel

    def _create_lidar_panel(self):
        """Crea el panell de visualització del LiDAR amb modes múltiples."""
        lidar_panel = QWidget()
        layout = QVBoxLayout(lidar_panel)

        # Opcions de visualització
        options_layout = QHBoxLayout()
        options_layout.addWidget(QLabel("Visualització:"))

        self.lidar_view_combo = QComboBox()
        self.lidar_view_combo.addItems(["Cartesiana", "Polar", "Combinada"])
        self.lidar_view_combo.currentIndexChanged.connect(
            self._switch_lidar_view)
        options_layout.addWidget(self.lidar_view_combo)

        options_layout.addStretch()

        # Opcions addicionals
        self.show_obstacles_check = QCheckBox("Mostrar obstacles")
        self.show_obstacles_check.setChecked(True)
        options_layout.addWidget(self.show_obstacles_check)

        layout.addLayout(options_layout)

        # Contenidor per les visualitzacions
        self.lidar_view_stack = QStackedWidget()

        # Vista cartesiana
        self.cartesian_view = QWidget()
        cartesian_layout = QVBoxLayout(self.cartesian_view)

        if HAS_MATPLOTLIB:
            self.cartesian_figure = Figure(figsize=(5, 5), dpi=100)
            self.cartesian_axes = self.cartesian_figure.add_subplot(111)
            self.cartesian_canvas = FigureCanvas(self.cartesian_figure)
            cartesian_layout.addWidget(self.cartesian_canvas)
        else:
            cartesian_layout.addWidget(QLabel("Matplotlib no disponible"))

        self.lidar_view_stack.addWidget(self.cartesian_view)

        # Vista polar
        self.polar_view = QWidget()
        polar_layout = QVBoxLayout(self.polar_view)

        if HAS_MATPLOTLIB:
            self.polar_figure = Figure(figsize=(5, 5), dpi=100)
            self.polar_axes = self.polar_figure.add_subplot(
                111, projection='polar')
            self.polar_canvas = FigureCanvas(self.polar_figure)
            polar_layout.addWidget(self.polar_canvas)
        else:
            polar_layout.addWidget(QLabel("Matplotlib no disponible"))

        self.lidar_view_stack.addWidget(self.polar_view)

        # Vista combinada
        self.combined_view = QWidget()
        combined_layout = QHBoxLayout(self.combined_view)

        if HAS_MATPLOTLIB:
            # Vista cartesiana
            self.combined_cartesian_figure = Figure(figsize=(5, 5), dpi=100)
            self.combined_cartesian_axes = self.combined_cartesian_figure.add_subplot(
                111)
            self.combined_cartesian_canvas = FigureCanvas(
                self.combined_cartesian_figure)
            combined_layout.addWidget(self.combined_cartesian_canvas)

            # Vista polar
            self.combined_polar_figure = Figure(figsize=(5, 5), dpi=100)
            self.combined_polar_axes = self.combined_polar_figure.add_subplot(
                111, projection='polar')
            self.combined_polar_canvas = FigureCanvas(
                self.combined_polar_figure)
            combined_layout.addWidget(self.combined_polar_canvas)
        else:
            combined_layout.addWidget(QLabel("Matplotlib no disponible"))

        self.lidar_view_stack.addWidget(self.combined_view)

        layout.addWidget(self.lidar_view_stack)

        # Informació de distàncies
        info_layout = QHBoxLayout()

        info_layout.addWidget(QLabel("Distància mínima:"))
        self.min_distance_label = QLabel("--")
        info_layout.addWidget(self.min_distance_label)

        info_layout.addSpacing(20)

        info_layout.addWidget(QLabel("Direcció:"))
        self.direction_label = QLabel("--")
        info_layout.addWidget(self.direction_label)

        info_layout.addStretch()

        self.capture_lidar_btn = QPushButton("Capturar vista")
        self.capture_lidar_btn.clicked.connect(self._capture_lidar_view)
        info_layout.addWidget(self.capture_lidar_btn)

        layout.addLayout(info_layout)

        return lidar_panel

    def _create_camera_panel(self):
        """Crea el panell de visualització de la càmera."""
        camera_panel = QWidget()
        layout = QVBoxLayout(camera_panel)

        # Controls de càmera
        controls_layout = QHBoxLayout()

        # Botons d'streaming
        self.start_stream_btn = QPushButton("Iniciar streaming")
        self.start_stream_btn.clicked.connect(self._start_camera_stream)
        controls_layout.addWidget(self.start_stream_btn)

        self.stop_stream_btn = QPushButton("Aturar streaming")
        self.stop_stream_btn.clicked.connect(self._stop_camera_stream)
        self.stop_stream_btn.setEnabled(False)
        controls_layout.addWidget(self.stop_stream_btn)

        # Botons de captura
        self.snapshot_btn = QPushButton("Capturar imatge")
        self.snapshot_btn.clicked.connect(self._take_camera_snapshot)
        controls_layout.addWidget(self.snapshot_btn)

        controls_layout.addStretch()

        # Selector de mode de processament
        controls_layout.addWidget(QLabel("Processament:"))
        self.processing_combo = QComboBox()
        self.processing_combo.addItems(["Cap", "Vores", "Moviment", "Tèrmic"])
        self.processing_combo.currentIndexChanged.connect(
            self._change_camera_processing)
        controls_layout.addWidget(self.processing_combo)

        layout.addLayout(controls_layout)

        # Visualització de càmera
        self.camera_label = QLabel("Flux de càmera no disponible")
        self.camera_label.setAlignment(Qt.AlignCenter)
        self.camera_label.setMinimumSize(640, 480)
        self.camera_label.setStyleSheet(
            "border: 1px solid #999; background-color: #111;")
        layout.addWidget(self.camera_label)

        # Informació de FPS i estat
        info_layout = QHBoxLayout()

        info_layout.addWidget(QLabel("FPS:"))
        self.fps_label = QLabel("--")
        info_layout.addWidget(self.fps_label)

        info_layout.addSpacing(20)

        info_layout.addWidget(QLabel("Estat:"))
        self.camera_status_label = QLabel("Inactiu")
        info_layout.addWidget(self.camera_status_label)

        info_layout.addStretch()

        layout.addLayout(info_layout)

        return camera_panel

    def _create_sensors_panel(self):
        """Crea el panell de visualització de dades dels sensors."""
        sensors_panel = QWidget()
        layout = QVBoxLayout(sensors_panel)

        # Controls de sensors
        controls_layout = QHBoxLayout()

        self.simulate_sensors_btn = QPushButton("Simular sensors")
        self.simulate_sensors_btn.setCheckable(True)
        self.simulate_sensors_btn.clicked.connect(
            self._toggle_sensor_simulation)
        controls_layout.addWidget(self.simulate_sensors_btn)

        controls_layout.addStretch()

        layout.addLayout(controls_layout)

        # Crear una graella per als sensors
        sensors_grid = QGridLayout()

        # Definir estils per als diferents tipus de sensors
        sensor_styles = {
            'temperature': "background-color: #ffe0e0; border: 1px solid #ffb0b0; border-radius: 5px;",
            'humidity': "background-color: #e0f0ff; border: 1px solid #b0d0ff; border-radius: 5px;",
            'gas': "background-color: #e0ffe0; border: 1px solid #b0ffb0; border-radius: 5px;",
            'co': "background-color: #fff0e0; border: 1px solid #ffd0b0; border-radius: 5px;",
            'smoke': "background-color: #f0e0ff; border: 1px solid #d0b0ff; border-radius: 5px;",
            'battery': "background-color: #e0ffff; border: 1px solid #b0ffff; border-radius: 5px;"
        }

        # Crear widgets per a cada sensor
        self.sensor_panels = {}
        self.sensor_data_labels = {}
        self.sensor_alert_labels = {}

        row = 0
        col = 0
        max_cols = 2

        for sensor_type, properties in self.sensor_manager.SENSOR_TYPES.items():
            # Crear un grup per al sensor
            sensor_group = QGroupBox(properties['name'])
            sensor_group.setStyleSheet(sensor_styles.get(sensor_type, ""))

            sensor_layout = QVBoxLayout(sensor_group)

            # Valor actual
            data_label = QLabel(f"-- {properties['unit']}")
            data_label.setStyleSheet("font-size: 18px; font-weight: bold;")
            data_label.setAlignment(Qt.AlignCenter)
            sensor_layout.addWidget(data_label)
            self.sensor_data_labels[sensor_type] = data_label

            # Estat d'alerta
            alert_label = QLabel("Normal")
            alert_label.setStyleSheet("color: green;")
            alert_label.setAlignment(Qt.AlignCenter)
            sensor_layout.addWidget(alert_label)
            self.sensor_alert_labels[sensor_type] = alert_label

            # Afegir a la graella
            sensors_grid.addWidget(sensor_group, row, col)

            # Actualitzar fila i columna
            col += 1
            if col >= max_cols:
                col = 0
                row += 1

            # Guardar referència
            self.sensor_panels[sensor_type] = sensor_group

        layout.addLayout(sensors_grid)

        # Historial de lectures (gràfic)
        history_group = QGroupBox("Historial de lectures")
        history_layout = QVBoxLayout(history_group)

        if HAS_MATPLOTLIB:
            self.sensor_history_figure = Figure(figsize=(5, 3), dpi=100)
            self.sensor_history_axes = self.sensor_history_figure.add_subplot(
                111)
            self.sensor_history_canvas = FigureCanvas(
                self.sensor_history_figure)
            history_layout.addWidget(self.sensor_history_canvas)

            # Dropdown per seleccionar sensor
            history_controls = QHBoxLayout()
            history_controls.addWidget(QLabel("Sensor:"))

            self.history_sensor_combo = QComboBox()
            self.history_sensor_combo.addItems(
                [self.sensor_manager.SENSOR_TYPES[s]['name'] for s in self.sensor_manager.SENSOR_TYPES])
            self.history_sensor_combo.currentIndexChanged.connect(
                self._update_sensor_history)
            history_controls.addWidget(self.history_sensor_combo)

            history_controls.addStretch()

            history_layout.addLayout(history_controls)
        else:
            history_layout.addWidget(QLabel("Matplotlib no disponible"))

        history_group.setLayout(history_layout)
        layout.addWidget(history_group)

        return sensors_panel

    def _create_config_panel(self):
        """Crea el panell de configuració."""
        config_panel = QWidget()
        config_layout = QVBoxLayout(config_panel)

        # Connexió
        connection_box = QGroupBox("Configuració de Connexió")
        connection_layout = QGridLayout()

        connection_layout.addWidget(QLabel("IP Raspberry Pi:"), 0, 0)
        self.config_host_input = QLabel(
            self.config.get(
                'connection',
                {}).get(
                'host',
                '192.168.1.100'))
        connection_layout.addWidget(self.config_host_input, 0, 1)

        connection_layout.addWidget(QLabel("Port:"), 1, 0)
        self.config_port_input = QLabel(
            str(self.config.get('connection', {}).get('port', 9999)))
        connection_layout.addWidget(self.config_port_input, 1, 1)

        # Botó per obrir diàleg de configuració
        self.edit_connection_btn = QPushButton("Editar")
        self.edit_connection_btn.clicked.connect(self._edit_connection_config)
        connection_layout.addWidget(self.edit_connection_btn, 2, 0, 1, 2)

        connection_box.setLayout(connection_layout)
        config_layout.addWidget(connection_box)

        # Configuració de LiDAR
        lidar_box = QGroupBox("Configuració de LiDAR")
        lidar_layout = QGridLayout()

        # Llindar de detecció d'obstacles
        lidar_layout.addWidget(QLabel("Llindar d'obstacles (mm):"), 0, 0)

        # Assegurar que 'lidar' és un diccionari
        lidar_config = self.config.get('lidar', {})
        if not isinstance(lidar_config, dict):
            lidar_config = {}

        obstacle_threshold = lidar_config.get('obstacle_threshold', 500)
        self.lidar_threshold_label = QLabel(str(obstacle_threshold))
        lidar_layout.addWidget(self.lidar_threshold_label, 0, 1)

        # Botó per editar el llindar
        self.edit_lidar_btn = QPushButton("Editar")
        self.edit_lidar_btn.clicked.connect(self._edit_lidar_threshold)
        lidar_layout.addWidget(self.edit_lidar_btn, 0, 2)

        lidar_box.setLayout(lidar_layout)
        config_layout.addWidget(lidar_box)

        # Configuració de sensors
        sensors_box = QGroupBox("Configuració de Sensors")
        sensors_layout = QGridLayout()

        # Títols de columnes
        sensors_layout.addWidget(QLabel("<b>Sensor</b>"), 0, 0)
        sensors_layout.addWidget(QLabel("<b>Llindar</b>"), 0, 1)
        sensors_layout.addWidget(QLabel("<b>Editar</b>"), 0, 2)

        # Diccionari de sensors disponibles amb els seus noms amigables
        available_sensors = {
            'mq2': "MQ-002 (Gas)",
            'mq135': "MQ-135 (Qualitat aire)",
            'k001': "K-001 (Temperatura)",
            'k026': "K-026 (Flama)",
            'k36': "K-36 (So)",
            'gy521': "GY-521 (MPU6050)"
        }

        # Assegurar que 'sensors' és un diccionari
        sensors_config = self.config.get('sensors', {})
        if not isinstance(sensors_config, dict):
            sensors_config = {}

        # Afegir només els sensors disponibles
        row = 1
        self.threshold_widgets = {}

        for sensor_key, sensor_name in available_sensors.items():
            # Buscar el sensor a la configuració actual o a SENSOR_TYPES
            if sensor_key in self.sensor_manager.SENSOR_TYPES or sensor_key in sensors_config:
                # Nom del sensor
                name_label = QLabel(sensor_name)
                sensors_layout.addWidget(name_label, row, 0)

                # Obtenir llindar o valor per defecte
                sensor_config = sensors_config.get(sensor_key, {})
                if not isinstance(sensor_config, dict):
                    sensor_config = {}

                threshold = sensor_config.get('threshold', 0)

                # Unitat (depenent del sensor)
                unit = ""
                if "temperatura" in sensor_name.lower():
                    unit = "°C"
                elif "gas" in sensor_name.lower() or "aire" in sensor_name.lower():
                    unit = "ppm"
                elif "so" in sensor_name.lower():
                    unit = "dB"

                # Llindar actual
                threshold_label = QLabel(f"{threshold} {unit}")
                sensors_layout.addWidget(threshold_label, row, 1)

                # Botó per editar
                edit_btn = QPushButton("Editar")
                edit_btn.clicked.connect(
                    lambda checked,
                    sk=sensor_key,
                    sn=sensor_name,
                    u=unit: self._edit_sensor_threshold(
                        sk,
                        sn,
                        u))
                sensors_layout.addWidget(edit_btn, row, 2)

                # Desar referències
                self.threshold_widgets[sensor_key] = threshold_label

                row += 1

        # Afegir calibració dels sensors de gas
        sensors_layout.addWidget(
            QLabel("<b>Calibració Sensors Gas</b>"), row, 0, 1, 3)
        row += 1

        # MQ-002 Calibració
        if 'mq2' in available_sensors:
            sensors_layout.addWidget(QLabel("Calibració MQ-002:"), row, 0)
            mq2_config = sensors_config.get('mq2', {})
            if not isinstance(mq2_config, dict):
                mq2_config = {}

            calib_mq2 = mq2_config.get('calibration', "No calibrat")
            self.calib_mq2_label = QLabel(str(calib_mq2))
            sensors_layout.addWidget(self.calib_mq2_label, row, 1)

            # Botó per calibrar
            self.calib_mq2_btn = QPushButton("Calibrar")
            self.calib_mq2_btn.clicked.connect(
                lambda: self._calibrate_gas_sensor(
                    'mq2', "MQ-002"))
            sensors_layout.addWidget(self.calib_mq2_btn, row, 2)
            row += 1

        # MQ-135 Calibració
        if 'mq135' in available_sensors:
            sensors_layout.addWidget(QLabel("Calibració MQ-135:"), row, 0)
            mq135_config = sensors_config.get('mq135', {})
            if not isinstance(mq135_config, dict):
                mq135_config = {}

            calib_mq135 = mq135_config.get('calibration', "No calibrat")
            self.calib_mq135_label = QLabel(str(calib_mq135))
            sensors_layout.addWidget(self.calib_mq135_label, row, 1)

            # Botó per calibrar
            self.calib_mq135_btn = QPushButton("Calibrar")
            self.calib_mq135_btn.clicked.connect(
                lambda: self._calibrate_gas_sensor(
                    'mq135', "MQ-135"))
            sensors_layout.addWidget(self.calib_mq135_btn, row, 2)
            row += 1

        sensors_box.setLayout(sensors_layout)
        config_layout.addWidget(sensors_box)

        # Afegim espai al final
        config_layout.addStretch()

        # Afegeix opcions per a perfils de configuració
        profiles_box = QGroupBox("Perfils de Configuració")
        profiles_layout = QHBoxLayout()

        profiles_layout.addWidget(QLabel("Perfil:"))

        self.profiles_combo = QComboBox()
        self._update_profiles_combo()
        profiles_layout.addWidget(self.profiles_combo)

        self.load_profile_btn = QPushButton("Carregar")
        self.load_profile_btn.clicked.connect(self._load_profile)
        profiles_layout.addWidget(self.load_profile_btn)

        self.save_profile_btn = QPushButton("Desar com...")
        self.save_profile_btn.clicked.connect(self._save_profile)
        profiles_layout.addWidget(self.save_profile_btn)

        self.delete_profile_btn = QPushButton("Eliminar")
        self.delete_profile_btn.clicked.connect(self._delete_profile)
        profiles_layout.addWidget(self.delete_profile_btn)

        profiles_box.setLayout(profiles_layout)
        config_layout.addWidget(profiles_box)

        return config_panel

    def _create_reports_panel(self):
        """Crea el panell d'informes i estadístiques."""
        reports_panel = QWidget()
        layout = QVBoxLayout(reports_panel)

        # Controls de dates
        date_layout = QHBoxLayout()

        date_layout.addWidget(QLabel("Data inici:"))
        self.start_date = QCalendarWidget()
        self.start_date.setMaximumHeight(200)
        date_layout.addWidget(self.start_date)

        date_layout.addWidget(QLabel("Data fi:"))
        self.end_date = QCalendarWidget()
        self.end_date.setMaximumHeight(200)
        self.end_date.setSelectedDate(QDate.currentDate())
        date_layout.addWidget(self.end_date)

        layout.addLayout(date_layout)

        # Tipus d'informe
        report_type_layout = QHBoxLayout()

        report_type_layout.addWidget(QLabel("Tipus d'informe:"))

        self.report_type_combo = QComboBox()
        self.report_type_combo.addItems(
            ["Resum general", "Sensors", "LiDAR", "Navegació", "Esdeveniments", "Personalitzat"])
        report_type_layout.addWidget(self.report_type_combo)

        report_type_layout.addStretch()

        self.generate_report_btn = QPushButton("Generar informe")
        self.generate_report_btn.clicked.connect(self._generate_report)
        report_type_layout.addWidget(self.generate_report_btn)

        layout.addLayout(report_type_layout)

        # Vista prèvia de l'informe
        preview_group = QGroupBox("Vista prèvia de l'informe")
        preview_layout = QVBoxLayout(preview_group)

        self.report_preview = QLabel(
            "Seleccioneu dates i tipus d'informe, i premeu 'Generar informe'")
        self.report_preview.setAlignment(Qt.AlignCenter)
        self.report_preview.setStyleSheet(
            "border: 1px solid #999; padding: 10px; background-color: white;")
        self.report_preview.setMinimumHeight(300)
        preview_layout.addWidget(self.report_preview)

        layout.addWidget(preview_group)

        # Opcions d'exportació
        export_layout = QHBoxLayout()

        export_layout.addStretch()

        self.export_pdf_btn = QPushButton("Exportar PDF")
        self.export_pdf_btn.clicked.connect(lambda: self._export_report("pdf"))
        export_layout.addWidget(self.export_pdf_btn)

        self.export_csv_btn = QPushButton("Exportar CSV")
        self.export_csv_btn.clicked.connect(lambda: self._export_report("csv"))
        export_layout.addWidget(self.export_csv_btn)

        layout.addLayout(export_layout)

        return reports_panel

    def _update_profiles_combo(self):
        """Actualitza el combo box de perfils amb els perfils disponibles."""
        try:
            self.profiles_combo.clear()

            # Afegir perfil per defecte
            self.profiles_combo.addItem("Perfil per defecte")

            # Obtenir perfils disponibles del config_manager
            if hasattr(self.config_manager, 'get_available_profiles'):
                profiles = self.config_manager.get_available_profiles()

                if profiles:
                    for profile in profiles:
                        self.profiles_combo.addItem(profile)
        except Exception as e:
            logger.error(f"Error actualitzant combo de perfils: {e}")

    def _toggle_connection(self):
        """Commuta l'estat de connexió."""
        if hasattr(
                self.connection_manager,
                'connected') and self.connection_manager.connected:
            self.connection_manager.disconnect()
        else:
            self.connection_manager.connect()

    def _update_speed(self, value):
        """Actualitza la velocitat del robot."""
        self.speed_label.setText(f"{value}%")

        # Adaptar el valor al rang necessari
        adjusted_value = int(value * 2.55)  # Convertir de 0-100 a 0-255
        self.navigation_manager.set_speed(adjusted_value)

    def _change_mode(self, index):
        """Canvia el mode de navegació."""
        mode_map = {
            0: "manual",
            1: "assisted",
            2: "autonomous"
        }
        if index in mode_map:
            self.navigation_manager.set_mode(mode_map[index])

    def _switch_lidar_view(self, index):
        """Canvia entre les diferents vistes del LiDAR."""
        self.lidar_view_stack.setCurrentIndex(index)

        # Actualitzar les accions del menú
        if index == 0:
            self.lidar_cartesian_action.setChecked(True)
        elif index == 1:
            self.lidar_polar_action.setChecked(True)
        elif index == 2:
            self.lidar_combined_action.setChecked(True)

        # Si hi ha dades disponibles, actualitzar la visualització
        if self.last_lidar_data:
            self.update_lidar_view(self.last_lidar_data)

    def _set_lidar_view(self, index):
        """Estableix la vista del LiDAR des de les accions del menú."""
        self.lidar_view_combo.setCurrentIndex(index)

    def _load_profile(self):
        """Carrega un perfil de configuració seleccionat."""
        profile_name = self.profiles_combo.currentText()

        if profile_name == "Perfil per defecte":
            # Carregar configuració per defecte
            if hasattr(self.config_manager, 'reset_to_defaults'):
                success = self.config_manager.reset_to_defaults()

                if success:
                    QMessageBox.information(
                        self,
                        "Perfil carregat",
                        "S'ha restaurat la configuració per defecte")

                    # Actualitzar configuració local
                    self.config = self.config_manager.load_config()

                    # Actualitzar interfície
                    self._update_ui_state()
                else:
                    QMessageBox.warning(
                        self, "Error", "No s'ha pogut restaurar la configuració per defecte")
        else:
            # Carregar perfil específic
            if hasattr(self.config_manager, 'load_profile'):
                success = self.config_manager.load_profile(profile_name)

                if success:
                    QMessageBox.information(
                        self,
                        "Perfil carregat",
                        f"S'ha carregat el perfil '{profile_name}'")

                    # Actualitzar configuració local
                    self.config = self.config_manager.load_config()

                    # Actualitzar interfície
                    self._update_ui_state()
                else:
                    QMessageBox.warning(
                        self, "Error", f"No s'ha pogut carregar el perfil '{profile_name}'")

    def _save_profile(self):
        """Desa la configuració actual com a nou perfil."""
        # Demanar nom del perfil
        name, ok = QInputDialog.getText(
            self, "Desar perfil", "Nom del perfil:")

        if ok and name:
            if hasattr(self.config_manager, 'save_profile'):
                success = self.config_manager.save_profile(name)

                if success:
                    QMessageBox.information(
                        self, "Perfil desat", f"S'ha desat el perfil '{name}'")

                    # Actualitzar combo
                    self._update_profiles_combo()

                    # Seleccionar el nou perfil
                    index = self.profiles_combo.findText(name)
                    if index >= 0:
                        self.profiles_combo.setCurrentIndex(index)
                else:
                    QMessageBox.warning(
                        self, "Error", f"No s'ha pogut desar el perfil '{name}'")

    def _delete_profile(self):
        """Elimina el perfil seleccionat."""
        profile_name = self.profiles_combo.currentText()

        if profile_name == "Perfil per defecte":
            QMessageBox.warning(
                self,
                "No es pot eliminar",
                "No es pot eliminar el perfil per defecte")
            return

        reply = QMessageBox.question(
            self,
            "Eliminar perfil",
            f"Estàs segur que vols eliminar el perfil '{profile_name}'?\nAquesta acció no es pot desfer.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No)

        if reply != QMessageBox.Yes:
            return

        try:
            # Obtenir ID del projecte
            if hasattr(self.config_manager, 'delete_profile'):
                success = self.config_manager.delete_profile(profile_name)

                if success:
                    QMessageBox.information(
                        self,
                        "Perfil eliminat",
                        f"S'ha eliminat el perfil '{profile_name}'")

                    # Actualitzar combo i seleccionar el perfil per defecte
                    self._update_profiles_combo()
                    self.profiles_combo.setCurrentIndex(0)
                else:
                    QMessageBox.warning(
                        self, "Error", f"No s'ha pogut eliminar el perfil '{profile_name}'")
            else:
                QMessageBox.information(
                    self, "Funció no implementada", "La funció d'eliminar perfils no està implementada.")

        except Exception as e:
            logger.error(f"Error eliminant perfil: {e}")
            QMessageBox.critical(self, "Error", f"Error eliminant perfil: {e}")

    def _capture_lidar_view(self):
        """Captura la vista actual del LiDAR i la desa com a imatge."""
        if not HAS_MATPLOTLIB:
            QMessageBox.warning(
                self,
                "Captura no disponible",
                "Matplotlib no està instal·lat. No es pot capturar la vista.")
            return

        try:
            # Determinar quina figura capturar
            current_view = self.lidar_view_stack.currentIndex()

            if current_view == 0:  # Cartesiana
                figure = self.cartesian_figure
            elif current_view == 1:  # Polar
                figure = self.polar_figure
            else:  # Combinada
                # Crear una nova figura combinant les dues
                figure = Figure(figsize=(10, 5), dpi=100)

                # Còpia de la vista cartesiana
                ax1 = figure.add_subplot(121)
                for line in self.combined_cartesian_axes.get_lines():
                    ax1.plot(line.get_xdata(), line.get_ydata(),
                             color=line.get_color(),
                             marker=line.get_marker(),
                             linestyle=line.get_linestyle())
                ax1.set_title("Vista Cartesiana")
                ax1.grid(True)

                # Còpia de la vista polar
                ax2 = figure.add_subplot(122, projection='polar')
                for line in self.combined_polar_axes.get_lines():
                    ax2.plot(line.get_xdata(), line.get_ydata(),
                             color=line.get_color(),
                             marker=line.get_marker(),
                             linestyle=line.get_linestyle())
                ax2.set_title("Vista Polar")
                ax2.grid(True)

                figure.tight_layout()

            # Demanar on guardar la imatge
            filepath, _ = QFileDialog.getSaveFileName(
                self,
                "Desar captura del LiDAR",
                os.path.expanduser("~/captura_lidar.png"),
                "Imatges (*.png *.jpg)"
            )

            if not filepath:
                return

            # Desar la figura
            figure.savefig(filepath, dpi=150, bbox_inches='tight')

            QMessageBox.information(
                self,
                "Captura desada",
                f"La captura s'ha desat a {filepath}")

        except Exception as e:
            logger.error(f"Error capturant vista del LiDAR: {e}")
            QMessageBox.critical(
                self, "Error", f"No s'ha pogut capturar la vista: {e}")

    def _start_camera_stream(self):
        """Inicia l'streaming de la càmera."""
        if hasattr(self.camera_manager, 'start_stream'):
            success = self.camera_manager.start_stream(self.connection_manager)

            if success:
                self.start_stream_btn.setEnabled(False)
                self.stop_stream_btn.setEnabled(True)
                self.camera_status_label.setText("Streaming actiu")
            else:
                QMessageBox.warning(
                    self, "Error", "No s'ha pogut iniciar l'streaming de la càmera")

    def _stop_camera_stream(self):
        """Atura l'streaming de la càmera."""
        if hasattr(self.camera_manager, 'stop_stream'):
            success = self.camera_manager.stop_stream(self.connection_manager)

            if success:
                self.start_stream_btn.setEnabled(True)
                self.stop_stream_btn.setEnabled(False)
                self.camera_status_label.setText("Streaming aturat")
            else:
                QMessageBox.warning(
                    self, "Error", "No s'ha pogut aturar l'streaming de la càmera")

    def _take_camera_snapshot(self):
        """Captura i desa una instantània de la càmera."""
        if hasattr(self.camera_manager, 'capture_snapshot'):
            snapshot = self.camera_manager.capture_snapshot()

            if snapshot:
                # Demanar on guardar la imatge
                filepath, _ = QFileDialog.getSaveFileName(
                    self,
                    "Desar instantània",
                    os.path.expanduser("~/instantania_camera.png"),
                    "Imatges (*.png *.jpg)"
                )

                if filepath:
                    try:
                        success = self.camera_manager.save_snapshot(filepath)

                        if success:
                            QMessageBox.information(
                                self, "Instantània desada", f"La instantània s'ha desat a {filepath}")
                        else:
                            QMessageBox.warning(
                                self, "Error", "No s'ha pogut desar la instantània")
                    except Exception as e:
                        logger.error(f"Error desant instantània: {e}")
                        QMessageBox.critical(
                            self, "Error", f"Error desant instantània: {e}")
            else:
                QMessageBox.warning(
                    self,
                    "Instantània no disponible",
                    "No hi ha cap imatge disponible per capturar")

    def _change_camera_processing(self, index):
        """Canvia el mode de processament de la càmera."""
        if hasattr(self.camera_manager, 'enable_processing'):
            processing_modes = {
                0: None,  # Cap
                1: "edge",  # Vores
                2: "motion",  # Moviment
                3: "thermal"  # Tèrmic
            }

            mode = processing_modes.get(index)

            if index == 0:
                # Desactivar processament
                self.camera_manager.enable_processing(False)
            else:
                # Activar processament i configurar mode
                self.camera_manager.enable_processing(True)

                if mode == "edge":
                    self.camera_manager.toggle_edge_detection(True)
                    self.camera_manager.toggle_motion_detection(False)
                elif mode == "motion":
                    self.camera_manager.toggle_edge_detection(False)
                    self.camera_manager.toggle_motion_detection(True)
                elif mode == "thermal":
                    # Suposem que hi ha una funció per a mode tèrmic
                    if hasattr(self.camera_manager, 'toggle_thermal_mode'):
                        self.camera_manager.toggle_thermal_mode(True)
                    else:
                        QMessageBox.warning(
                            self,
                            "Mode no disponible",
                            "El mode tèrmic no està implementat")
                        self.processing_combo.setCurrentIndex(0)

    def _toggle_sensor_simulation(self, checked):
        """Activa o desactiva la simulació de sensors."""
        if hasattr(
                self.sensor_manager,
                'start_simulation') and hasattr(
                self.sensor_manager,
                'stop_simulation'):
            if checked:
                self.sensor_manager.start_simulation()
                self.simulate_sensors_btn.setText("Aturar simulació")
            else:
                self.sensor_manager.stop_simulation()
                self.simulate_sensors_btn.setText("Simular sensors")

    def _update_sensor_history(self, index):
        """Actualitza el gràfic d'historial de sensors."""
        if not HAS_MATPLOTLIB:
            return

        # Obtenir el tipus de sensor seleccionat (segons l'ordre d'afegit al
        # combo)
        sensor_types = list(self.sensor_manager.SENSOR_TYPES.keys())

        if index < 0 or index >= len(sensor_types):
            return

        selected_sensor = sensor_types[index]

        # Actualitzar gràfic amb dades simulades (en un cas real s'usarien
        # dades reals)
        try:
            self.sensor_history_axes.clear()

            # En un cas real, obtindríem l'historial de dades
            # Per ara simulem algunes dades
            import numpy as np

            x = np.arange(20)

            # Generar dades segons el tipus de sensor
            if selected_sensor == 'temperature':
                y = 25 + 5 * np.sin(x / 3) + np.random.normal(0, 0.5, 20)
                label = 'Temperatura (°C)'
                color = 'red'
            elif selected_sensor == 'humidity':
                y = 60 + 15 * np.sin(x / 5) + np.random.normal(0, 2, 20)
                label = 'Humitat (%)'
                color = 'blue'
            elif selected_sensor == 'gas':
                y = 800 + 200 * np.sin(x / 4) + np.random.normal(0, 50, 20)
                label = 'Gas (ppm)'
                color = 'green'
            else:
                # Valors aleatoris per altres sensors
                y = 50 + 20 * np.sin(x / 3) + np.random.normal(0, 5, 20)
                label = 'Valor'
                color = 'purple'

            # Dibuixar dades
            self.sensor_history_axes.plot(
                x, y, marker='o', color=color, label=label)

            # Configurar eixos
            self.sensor_history_axes.set_xlabel('Temps (minuts)')
            self.sensor_history_axes.set_ylabel(label)
            self.sensor_history_axes.grid(True)
            self.sensor_history_axes.legend()

            # Actualitzar el gràfic
            self.sensor_history_canvas.draw()

        except Exception as e:
            logger.error(f"Error actualitzant l'historial de sensors: {e}")

    def _manage_projects(self):
        """Obre el diàleg de gestió de projectes."""
        if not self.db_manager:
            QMessageBox.warning(self, "Base de dades no disponible",
                                "El gestor de base de dades no està disponible")
            return

        try:
            from ui.project_dialog import ProjectDialog
            dialog = ProjectDialog(self.db_manager, self)
            dialog.exec_()
        except Exception as e:
            logger.error(f"Error obrint diàleg de projectes: {e}")
            QMessageBox.critical(
                self, "Error", f"Error obrint diàleg de projectes: {e}")

    def _clear_alerts(self):
        """Neteja les alertes actives."""
        self.alerts_label.setText("Cap alerta activa")
        self.alerts_label.setStyleSheet("")

        # Reiniciar els estats d'alerta dels sensors
        for sensor_type in self.sensor_alert_labels:
            self.sensor_alert_labels[sensor_type].setText("Normal")
            self.sensor_alert_labels[sensor_type].setStyleSheet(
                "color: green;")

    def _edit_lidar_threshold(self):
        """Edita el llindar d'obstacles del LiDAR."""
        # Obtenir valor actual
        lidar_config = self.config.get('lidar', {})
        if not isinstance(lidar_config, dict):
            lidar_config = {}

        current_value = lidar_config.get('obstacle_threshold', 500)

        # Mostrar diàleg d'edició
        new_value, ok = QInputDialog.getInt(
            self,
            "Editar llindar d'obstacles",
            "Distància (mm):",
            current_value,
            100,  # Mínim: 10 cm
            5000,  # Màxim: 5 metres
            100   # Pas: 10 cm
        )

        if ok:
            # Actualitzar valor al ConfigManager
            if not isinstance(self.config.get('lidar', {}), dict):
                self.config['lidar'] = {}

            self.config['lidar']['obstacle_threshold'] = new_value
            self.config_manager.update_section('lidar', self.config['lidar'])

            # Actualitzar etiqueta
            self.lidar_threshold_label.setText(str(new_value))

            # Actualitzar el NavigationManager si és necessari
            if hasattr(self.navigation_manager, 'obstacle_threshold'):
                self.navigation_manager.obstacle_threshold = new_value

            # Mostrar confirmació
            QMessageBox.information(
                self,
                "Configuració",
                "Llindar d'obstacles actualitzat correctament")

    def _calibrate_gas_sensor(self, sensor_key, sensor_name):
        """Inicia el procés de calibració d'un sensor de gas."""
        reply = QMessageBox.question(
            self,
            f"Calibrar {sensor_name}",
            f"Vols iniciar la calibració del sensor {sensor_name}?\n\n"
            "Assegura't que el sensor estigui en aire net i estable durant la calibració.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            # Simulem que s'envia una comanda de calibració
            # En un entorn real, això s'hauria d'enviar al bridge i esperar
            # resposta
            if hasattr(
                    self.connection_manager,
                    'send_command') and self.connection_manager.connected:
                # Enviar comanda de calibració
                calibration_cmd = {
                    "type": "sensor_control",
                    "action": "calibrate",
                    "sensor": sensor_key
                }
                success = self.connection_manager.send_command(calibration_cmd)

                if success:
                    # Actualitzar la configuració
                    if not isinstance(self.config.get('sensors', {}), dict):
                        self.config['sensors'] = {}
                    if not isinstance(
                        self.config['sensors'].get(
                            sensor_key, {}), dict):
                        self.config['sensors'][sensor_key] = {}

                    # Guardar la data de calibració
                    import datetime
                    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
                    self.config['sensors'][sensor_key]['calibration'] = now
                    self.config_manager.update_section(
                        'sensors', self.config['sensors'])

                    # Actualitzar etiqueta
                    if hasattr(self, f"calib_{sensor_key}_label"):
                        getattr(self, f"calib_{sensor_key}_label").setText(now)

                    QMessageBox.information(
                        self,
                        "Calibració",
                        f"Calibració del sensor {sensor_name} completada correctament."
                    )
                else:
                    QMessageBox.warning(
                        self,
                        "Error",
                        f"No s'ha pogut enviar la comanda de calibració del sensor {sensor_name}."
                    )
            else:
                QMessageBox.warning(
                    self,
                    "Error",
                    "No es pot calibrar el sensor: Robot no connectat."
                )

    def _edit_sensor_threshold(self, sensor_key, sensor_name="", unit=""):
        """Edita el llindar d'alerta per a un sensor específic."""
        # Obtenir valor actual
        sensors_config = self.config.get('sensors', {})
        if not isinstance(sensors_config, dict):
            sensors_config = {}

        sensor_config = sensors_config.get(sensor_key, {})
        if not isinstance(sensor_config, dict):
            sensor_config = {}

        current_value = sensor_config.get('threshold', 0)

        # Mostrar diàleg d'edició
        new_value, ok = QInputDialog.getDouble(
            self,
            f"Editar llindar per a {sensor_name}",
            f"Llindar ({unit}):",
            current_value,
            0.0,
            10000.0,
            2
        )

        if ok:
            # Actualitzar valor al ConfigManager
            if not isinstance(self.config.get('sensors', {}), dict):
                self.config['sensors'] = {}
            if not isinstance(
    self.config['sensors'].get(
        sensor_key, {}), dict):
                self.config['sensors'][sensor_key] = {}

            self.config['sensors'][sensor_key]['threshold'] = new_value
            self.config_manager.update_section(
                'sensors', self.config['sensors'])

            # Actualitzar etiqueta
            if sensor_key in self.threshold_widgets:
                self.threshold_widgets[sensor_key].setText(
                    f"{new_value} {unit}")

            # Mostrar confirmació
            QMessageBox.information(
                self,
                "Configuració",
                f"Llindar de {sensor_name} actualitzat correctament")

    def _toggle_theme(self, checked):
        """Canvia entre el tema clar i fosc."""
        if checked:
            # Tema fosc
            app = QApplication.instance()

            dark_palette = QPalette()
            dark_palette.setColor(QPalette.Window, QColor(53, 53, 53))
            dark_palette.setColor(QPalette.WindowText, Qt.white)
            dark_palette.setColor(QPalette.Base, QColor(35, 35, 35))
            dark_palette.setColor(QPalette.AlternateBase, QColor(53, 53, 53))
            dark_palette.setColor(QPalette.ToolTipBase, QColor(25, 25, 25))
            dark_palette.setColor(QPalette.ToolTipText, Qt.white)
            dark_palette.setColor(QPalette.Text, Qt.white)
            dark_palette.setColor(QPalette.Button, QColor(53, 53, 53))
            dark_palette.setColor(QPalette.ButtonText, Qt.white)
            dark_palette.setColor(QPalette.BrightText, Qt.red)
            dark_palette.setColor(QPalette.Link, QColor(42, 130, 218))
            dark_palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
            dark_palette.setColor(QPalette.HighlightedText, Qt.black)

            app.setPalette(dark_palette)

            # Actualitzar text del botó
            self.toggle_theme_action.setText("Tema &clar")
        else:
            # Tema clar (per defecte)
            app = QApplication.instance()
            app.setPalette(app.style().standardPalette())

            # Actualitzar text del botó
            self.toggle_theme_action.setText("Tema &fosc")

    def _take_screenshot(self):
        """Captura la pantalla actual i la desa com a imatge."""
        try:
            # Capturar la pantalla
            screen = QApplication.primaryScreen()
            screenshot = screen.grabWindow(self.winId())

            # Demanar on guardar la imatge
            filepath, _ = QFileDialog.getSaveFileName(
                self,
                "Desar captura de pantalla",
                os.path.expanduser("~/captura_pantalla.png"),
                "Imatges (*.png *.jpg)"
            )

            if not filepath:
                return

            # Desar la imatge
            screenshot.save(filepath)

            QMessageBox.information(
                self,
                "Captura desada",
                f"La captura de pantalla s'ha desat a {filepath}")

        except Exception as e:
            logger.error(f"Error capturant pantalla: {e}")
            QMessageBox.critical(
                self, "Error", f"No s'ha pogut capturar la pantalla: {e}")

    def _show_preferences(self):
        """Mostra el diàleg de preferències."""
        # En una aplicació real, s'implementaria un diàleg de preferències
        # complet
        QMessageBox.information(
            self,
            "Preferències",
            "Aquí s'implementaria un diàleg de preferències")

    def _show_manual(self):
        """Mostra el manual d'usuari."""
        try:
            # Comprovar si existeix el manual
            manual_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                       "../docs/manual.pdf")

            if os.path.exists(manual_path):
                # Obrir el manual amb l'aplicació predeterminada
                import subprocess
                import platform

                if platform.system() == 'Windows':
                    os.startfile(manual_path)
                elif platform.system() == 'Darwin':  # macOS
                    subprocess.call(('open', manual_path))
                else:  # Linux i altres
                    subprocess.call(('xdg-open', manual_path))
            else:
                # Si no existeix, mostrar missatge
                QMessageBox.information(
                    self,
                    "Manual d'usuari",
                    "El manual d'usuari encara no està disponible.\n\n"
                    "Aquí es mostraria la documentació completa del sistema."
                )
        except Exception as e:
            logger.error(f"Error mostrant manual: {e}")
            QMessageBox.critical(
                self, "Error", f"No s'ha pogut mostrar el manual: {e}")

    def _edit_connection_config(self):
        """Obre el diàleg per editar la configuració de connexió."""
        try:
            # Obtenir la configuració actual
            current_config = self.config.get('connection', {})
            if not isinstance(current_config, dict):
                current_config = {}

            from ui.connection_config_dialog import ConnectionConfigDialog
            dialog = ConnectionConfigDialog(current_config, self)

            if dialog.exec_() == QDialog.Accepted:
                # Obtenir nova configuració
                new_config = dialog.get_config()

                # Actualitzar configuració
                self.config_manager.update_section('connection', new_config)

                # Actualitzar visualització
                self.config_host_input.setText(
                    new_config.get('host', '192.168.1.100'))
                self.config_port_input.setText(
                    str(new_config.get('port', 9999)))

                # Actualitzar ConnectionManager si cal
                if hasattr(self.connection_manager, 'host'):
                    self.connection_manager.host = new_config.get(
                        'host', '192.168.1.100')
                if hasattr(self.connection_manager, 'port'):
                    self.connection_manager.port = new_config.get('port', 9999)
                if hasattr(self.connection_manager, 'auto_reconnect'):
                    self.connection_manager.auto_reconnect = new_config.get(
                        'auto_reconnect', True)
                if hasattr(self.connection_manager, 'reconnect_interval'):
                    self.connection_manager.reconnect_interval = new_config.get(
                        'reconnect_interval', 5)

                QMessageBox.information(
                    self,
                    "Configuració de connexió",
                    "Configuració desada correctament. Els canvis s'aplicaran en la propera connexió."
                )
        except Exception as e:
            QMessageBox.critical(
                self,
                "Error",
                f"No s'ha pogut obrir el diàleg de configuració: {str(e)}"
            )
            logger.error(f"Error obrint diàleg de configuració: {e}")

    def _save_config(self):
        """Guarda la configuració actual en un fitxer."""
        filepath, _ = QFileDialog.getSaveFileName(
            self,
            "Guardar Configuració",
            os.path.expanduser("~"),
            "Fitxers de configuració (*.json *.yaml);;Tots els fitxers (*)"
        )

        if filepath:
            try:
                success = self.config_manager.save_config()

                if success:
                    QMessageBox.information(
                        self, "Configuració", "Configuració guardada correctament")
                else:
                    QMessageBox.critical(
                        self, "Error", "No s'ha pogut guardar la configuració")
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Error",
                    f"Error en guardar la configuració: {str(e)}")
                logger.error(f"Error en guardar configuració: {e}")

    def _load_config(self):
        """Carrega la configuració des d'un fitxer."""
        filepath, _ = QFileDialog.getOpenFileName(
            self,
            "Carregar Configuració",
            os.path.expanduser("~"),
            "Fitxers de configuració (*.json *.yaml);;Tots els fitxers (*)"
        )

        if filepath:
            try:
                # Aquesta funció no està implementada al ConfigManager original
                # Seria una bona millora per afegir
                # self.config_manager.load_from_file(filepath)

                # Per ara, simplement mostrem un missatge
                QMessageBox.information(
                    self,
                    "Funció no implementada",
                    "La càrrega de configuració des d'un fitxer extern no està implementada.\n"
                    "Aquesta funcionalitat s'implementarà en una propera versió.")
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Error",
                    f"Error en carregar la configuració: {str(e)}")
                logger.error(f"Error en carregar configuració: {e}")

    def _calibrate_sensors(self):
        """Inicia el procés de calibració de sensors."""
        reply = QMessageBox.question(
            self,
            "Calibrar Sensors",
            "Iniciar calibració de sensors? El robot ha d'estar en una posició segura.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No)

        if reply == QMessageBox.Yes:
            try:
                # Comprovar si tenim la funció de calibració
                if hasattr(self.sensor_manager, 'calibrate'):
                    success = self.sensor_manager.calibrate()

                    if success:
                        QMessageBox.information(
                            self, "Calibració", "Calibració completada correctament")
                    else:
                        QMessageBox.warning(
                            self, "Error", "No s'ha pogut completar la calibració")
                else:
                    # Simulem l'enviament d'una comanda de calibració
                    if hasattr(
                            self.connection_manager,
                            'send_command') and self.connection_manager.connected:
                        calibration_cmd = {
                            "type": "sensor_control",
                            "action": "calibrate_all"
                        }
                        success = self.connection_manager.send_command(
                            calibration_cmd)

                        if success:
                            QMessageBox.information(
                                self, "Calibració", "Comanda de calibració enviada correctament")
                        else:
                            QMessageBox.warning(
                                self, "Error", "No s'ha pogut enviar la comanda de calibració")
                    else:
                        QMessageBox.warning(
                            self, "Error", "Robot no connectat")
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Error",
                    f"Error durant la calibració: {str(e)}")
                logger.error(f"Error en calibrar sensors: {e}")

    def _reconnect(self):
        """Reinicia la connexió amb el robot."""
        try:
            self.connection_manager.disconnect()
            time.sleep(1)  # Espera breu
            self.connection_manager.connect()
        except Exception as e:
            QMessageBox.critical(
                self, "Error", f"Error al reconnectar: {str(e)}")
            logger.error(f"Error al reconnectar: {e}")

    def _show_about(self):
        """Mostra informació sobre l'aplicació."""
        QMessageBox.about(
            self,
            "Sobre Sistema de Control",
            "Sistema de Control de Robot per a Bombers\n"
            "Versió 1.0\n\n"
            "Desenvolupat per al Cos de Bombers de Catalunya\n"
            "© 2025 Generalitat de Catalunya"
        )

    def _generate_report(self):
        """Genera un informe segons els paràmetres seleccionats."""
        try:
            # Obtenir dates seleccionades
            start_date = self.start_date.selectedDate().toString("yyyy-MM-dd")
            end_date = self.end_date.selectedDate().toString("yyyy-MM-dd")

            # Obtenir tipus d'informe
            report_type = self.report_type_combo.currentText()

            # Simulem la generació d'un informe
            report_html = f"""
                <html>
                <head>
                    <style>
                        body {{ font-family: Arial, sans-serif; margin: 20px; }}
                        h1 {{ color: #2a82da; }}
                        table {{ border-collapse: collapse; width: 100%; margin-top: 20px; }}
                        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                        th {{ background-color: #f2f2f2; }}
                        tr:hover {{ background-color: #f5f5f5; }}
                    </style>
                </head>
                <body>
                    <h1>Informe: {report_type}</h1>
                    <p><b>Període:</b> {start_date} - {end_date}</p>
                    <p><b>Generat:</b> {datetime.now().strftime('%Y-%m-%d %H:%M')}</p>

                    <h2>Resum</h2>
                    <p>Aquest informe proporciona una visió general del rendiment del sistema durant el període especificat.</p>

                    <table>
                        <tr>
                            <th>Mètrica</th>
                            <th>Valor</th>
                        </tr>
                        <tr>
                            <td>Temps total d'operació</td>
                            <td>23.5 hores</td>
                        </tr>
                        <tr>
                            <td>Distància recorreguda</td>
                            <td>1.2 km</td>
                        </tr>
                        <tr>
                            <td>Nombre d'alertes</td>
                            <td>12</td>
                        </tr>
                        <tr>
                            <td>Nivell mitjà de bateria</td>
                            <td>78%</td>
                        </tr>
                    </table>

                    <h2>Detalls addicionals</h2>
                    <p>Aquí s'inclourien més detalls específics basats en el tipus d'informe seleccionat.</p>
                </body>
                </html>
                """

            # Mostrar l'informe a la vista prèvia
            self.report_preview.setText(report_html)

            # Activar botons d'exportació
            self.export_pdf_btn.setEnabled(True)
            self.export_csv_btn.setEnabled(True)

        except Exception as e:
            logger.error(f"Error generant informe: {e}")
            QMessageBox.critical(
                self, "Error", f"No s'ha pogut generar l'informe: {e}")

    def _export_report(self, format_type):
        """
        Exporta l'informe generat al format especificat.

        Args:
            format_type (str): Format d'exportació ('pdf' o 'csv')
        """
        try:
            # Determinar tipus de fitxer i extension
            if format_type == 'pdf':
                file_filter = "Documents PDF (*.pdf)"
                extension = "pdf"
            elif format_type == 'csv':
                file_filter = "Arxius CSV (*.csv)"
                extension = "csv"
            else:
                QMessageBox.warning(
                    self,
                    "Format no suportat",
                    f"El format '{format_type}' no està suportat")
                return

            # Demanar on guardar l'informe
            filepath, _ = QFileDialog.getSaveFileName(
                self,
                f"Exportar informe a {format_type.upper()}",
                os.path.expanduser(f"~/informe.{extension}"),
                file_filter
            )

            if not filepath:
                return

            # En una aplicació real, aquí s'utilitzaria una biblioteca per convertir
            # el contingut a PDF o CSV. Per ara, simulem que ho fem
            # correctament.

            if format_type == 'pdf':
                # Aquí s'utilitzaria una biblioteca com reportlab o weasyprint
                # per convertir l'HTML a PDF
                try:
                    # Simulem la creació d'un PDF
                    with open(filepath, 'w') as f:
                        f.write("Contingut simulat d'un PDF")

                    QMessageBox.information(
                        self,
                        "Exportació completada",
                        f"L'informe s'ha exportat correctament a {filepath}"
                    )
                except Exception as e:
                    raise Exception(f"Error creant el PDF: {e}")

            elif format_type == 'csv':
                # Aquí s'utilitzaria una biblioteca com csv o pandas
                # per generar un CSV amb les dades
                try:
                    # Simulem la creació d'un CSV
                    with open(filepath, 'w') as f:
                        f.write("Mètrica,Valor\n")
                        f.write("Temps total d'operació,23.5 hores\n")
                        f.write("Distància recorreguda,1.2 km\n")
                        f.write("Nombre d'alertes,12\n")
                        f.write("Nivell mitjà de bateria,78%\n")

                    QMessageBox.information(
                        self,
                        "Exportació completada",
                        f"L'informe s'ha exportat correctament a {filepath}"
                    )
                except Exception as e:
                    raise Exception(f"Error creant el CSV: {e}")

        except Exception as e:
            logger.error(f"Error exportant informe: {e}")
            QMessageBox.critical(
                self, "Error", f"No s'ha pogut exportar l'informe: {e}")

    def _update_ui_state(self):
        """Actualitza l'estat de la interfície segons l'estat actual del sistema."""
        # Actualitzar estat de connexió
        is_connected = hasattr(self.connection_manager,
                               'connected') and self.connection_manager.connected
        self.connection_status_label.setText(
            f"Estat: {'Connectat' if is_connected else 'Desconnectat'}")
        self.connect_button.setText(
            "Desconnectar" if is_connected else "Connectar")

        # Activar/desactivar controls de navegació segons l'estat de connexió
        self.up_button.setEnabled(is_connected)
        self.down_button.setEnabled(is_connected)
        self.left_button.setEnabled(is_connected)
        self.right_button.setEnabled(is_connected)
        self.stop_button.setEnabled(is_connected)
        self.speed_slider.setEnabled(is_connected)
        self.mode_combo.setEnabled(is_connected)

        # Actualitzar botons de càmera
        self.start_stream_btn.setEnabled(is_connected)
        self.stop_stream_btn.setEnabled(False)  # Inicialment desactivat
        self.snapshot_btn.setEnabled(
            is_connected and hasattr(
                self.camera_manager,
                'get_current_frame') and self.camera_manager.get_current_frame() is not None)

        # Actualitzar visualització de configuració
        connection_config = self.config.get('connection', {})
        self.config_host_input.setText(
            connection_config.get(
                'host', '192.168.1.100'))

        self.config_port_input.setText(
            str(connection_config.get('port', 9999)))

        # Actualitzar llindars de sensors
        for sensor_type, properties in self.sensor_manager.SENSOR_TYPES.items():
            if sensor_type in self.threshold_widgets:
                self.threshold_widgets[sensor_type].setText(
                    f"{properties['threshold']} {properties['unit']}")

    def _periodic_update(self):
        """Realitza actualitzacions periòdiques de la interfície."""
        # Actualitzar estat de connexió
        is_connected = hasattr(self.connection_manager,
                               'connected') and self.connection_manager.connected
        self.connection_status_label.setText(
            f"Estat: {'Connectat' if is_connected else 'Desconnectat'}")

        # Actualitzar dades de sensors
        if is_connected:
            # Simular una actualització dels sensors
            if hasattr(self.sensor_manager, 'request_update'):
                self.sensor_manager.request_update()

        # Actualitzar FPS de càmera
        if hasattr(self.camera_manager, 'get_fps'):
            fps = self.camera_manager.get_fps()
            self.fps_label.setText(str(fps))

        # Comprovar si cal activar el botó de snapshot
        if hasattr(self.camera_manager, 'get_current_frame'):
            has_frame = self.camera_manager.get_current_frame() is not None
            self.snapshot_btn.setEnabled(is_connected and has_frame)

    def _connect_signals(self):
        """Connecta els signals i slots."""
        # Connexió
        if hasattr(self.connection_manager, 'connection_status_changed'):
            self.connection_manager.connection_status_changed.connect(
                self.update_connection_status)

        # Sensors
        if hasattr(self.sensor_manager, 'sensor_data_updated'):
            self.sensor_manager.sensor_data_updated.connect(
                self.update_sensor_data)

        if hasattr(self.sensor_manager, 'sensor_alert'):
            self.sensor_manager.sensor_alert.connect(self.show_sensor_alert)

        if hasattr(self.sensor_manager, 'sensors_status_updated'):
            self.sensor_manager.sensors_status_updated.connect(
                self.update_all_sensors_data)

        # LiDAR
        if self.lidar_manager:
            if hasattr(self.lidar_manager, 'lidar_data_updated'):
                self.lidar_manager.lidar_data_updated.connect(
                    self.update_lidar_view)

            if hasattr(self.lidar_manager, 'obstacle_detected'):
                self.lidar_manager.obstacle_detected.connect(
                    self.show_obstacle_alert)

        # Càmera
        if self.camera_manager:
            if hasattr(self.camera_manager, 'camera_frame_ready'):
                self.camera_manager.camera_frame_ready.connect(
                    self.update_camera_view)

            if hasattr(self.camera_manager, 'camera_status_changed'):
                self.camera_manager.camera_status_changed.connect(
                    self.update_camera_status)

        # Navegació
        if hasattr(self.navigation_manager, 'navigation_status_changed'):
            self.navigation_manager.navigation_status_changed.connect(
                self.update_navigation_status)

        if hasattr(self.navigation_manager, 'obstacle_alert'):
            self.navigation_manager.obstacle_alert.connect(
                self.show_navigation_alert)

        # Configuració
        if hasattr(self.config_manager, 'config_updated'):
            self.config_manager.config_updated.connect(self.update_config_view)

        # AI

        if hasattr(self.ai_manager, 'object_detected'):
            self.ai_manager.object_detected.connect(self.update_detection_list)

        if hasattr(self.ai_manager, 'ai_status_changed'):
            self.ai_manager.ai_status_changed.connect(self.update_ai_status)  

    def show_obstacle_alert(self, angle, distance):
        """
        Mostra una alerta quan es detecta un obstacle.

        Args:
            angle (float): Angle on s'ha detectat l'obstacle (radiants)
            distance (float): Distància a l'obstacle (mm)
        """
        # Convertir angle a graus per mostrar-lo
        angle_degrees = round(angle * 180 / 3.14159, 1)
        
        # Convertir distància a metres per mostrar-la
        distance_meters = round(distance / 1000, 2)
        
        # Determinar la posició aproximada
        position = "davant"
        if angle > 0.5:
            position = "esquerra"
        elif angle < -0.5:
            position = "dreta"
        
        # Mostrar l'alerta a la interfície
        self.alerts_label.setText(f"ALERTA: Obstacle detectat a {position} ({distance_meters} m)")
        self.alerts_label.setStyleSheet("color: red; font-weight: bold;")
        
        # Actualitzar les etiquetes de distància i direcció si existeixen
        if hasattr(self, 'min_distance_label'):
            self.min_distance_label.setText(f"{distance_meters} m")
        
        if hasattr(self, 'direction_label'):
            self.direction_label.setText(f"{angle_degrees}°")
        
        # Registrar a log
        logger.warning(f"Obstacle detectat: angle={angle_degrees}°, distància={distance_meters}m, posició={position}")

    def update_lidar_view(self, lidar_data):
        """
        Actualitza la visualització del LiDAR amb noves dades.

        Args:
            lidar_data: Objecte LidarData amb les dades del LiDAR
        """
        # Guardar les dades més recents
        self.last_lidar_data = lidar_data
        
        # Comprovar que tenim matplotlib disponible
        if not HAS_MATPLOTLIB:
            return
        
        # Obtenir les dades
        current_view = self.lidar_view_stack.currentIndex()
        
        try:
            if current_view == 0:  # Vista cartesiana
                self._update_cartesian_view(lidar_data)
            elif current_view == 1:  # Vista polar
                self._update_polar_view(lidar_data)
            else:  # Vista combinada
                self._update_combined_view(lidar_data)
            
            # Actualitzar informació de distància mínima
            min_angle, min_distance = lidar_data.get_nearest_obstacle()
            if min_angle is not None and min_distance is not None:
                self.min_distance_label.setText(f"{min_distance/1000:.2f} m")
                self.direction_label.setText(f"{min_angle*180/3.14159:.1f}°")
        
        except Exception as e:
            logger.error(f"Error actualitzant visualització del LiDAR: {e}")

    def update_camera_view(self, frame):
        """
        Actualitza la visualització de la càmera amb un nou fotograma.
        
        Args:
            frame (QImage): Imatge rebuda de la càmera
        """
        if frame is None:
            return
            
        try:
            # Convertir a QPixmap
            pixmap = QPixmap.fromImage(frame)
            
            # Ajustar al tamany del label mantenint la proporció
            if hasattr(self, 'camera_label'):
                pixmap = pixmap.scaled(
                    self.camera_label.size(),
                    Qt.KeepAspectRatio,
                    Qt.SmoothTransformation
                )
                
                # Mostrar el frame
                self.camera_label.setPixmap(pixmap)
                
            # Actualitzar FPS i estat si correspon
            if hasattr(self.camera_manager, 'get_fps'):
                fps = self.camera_manager.get_fps()
                if hasattr(self, 'fps_label'):
                    self.fps_label.setText(str(fps))
                    
            # Actualitzar estat de streaming
            if hasattr(self, 'camera_status_label'):
                self.camera_status_label.setText("Streaming actiu")
                
            # Activar/desactivar botons
            if hasattr(self, 'start_stream_btn'):
                self.start_stream_btn.setEnabled(False)
            if hasattr(self, 'stop_stream_btn'):
                self.stop_stream_btn.setEnabled(True)
            if hasattr(self, 'snapshot_btn'):
                self.snapshot_btn.setEnabled(True)
                
        except Exception as e:
            logger.error(f"Error actualitzant visualització de càmera: {e}")

    def update_camera_status(self, is_active, message=""):
        """
        Actualitza l'estat de la càmera a la interfície.
        
        Args:
            is_active (bool): Si la càmera està activa
            message (str): Missatge d'estat
        """
        try:
            # Actualitzar etiqueta d'estat
            if hasattr(self, 'camera_status_label'):
                self.camera_status_label.setText(message)
            
            # Actualitzar estat dels botons
            if hasattr(self, 'start_stream_btn'):
                self.start_stream_btn.setEnabled(not is_active)
            
            if hasattr(self, 'stop_stream_btn'):
                self.stop_stream_btn.setEnabled(is_active)
            
            # Actualitzar barra d'estat amb informació de la càmera
            self.statusBar.showMessage(f"Càmera: {message}")
            
            # Registrar l'estat
            if is_active:
                logger.info(f"Càmera activa: {message}")
            else:
                logger.info(f"Càmera inactiva: {message}")
                
        except Exception as e:
            logger.error(f"Error actualitzant estat de càmera: {e}")

    def update_navigation_status(self, mode, state_info):
        """
        Actualitza l'estat de navegació a la interfície.
        
        Args:
            mode (str): Mode de navegació actual ("manual", "assisted", "autonomous")
            state_info (dict): Informació d'estat addicional
        """
        try:
            # Actualitzar combo de mode si existeix
            if hasattr(self, 'mode_combo'):
                if mode == "manual":
                    self.mode_combo.setCurrentIndex(0)
                elif mode == "assisted":
                    self.mode_combo.setCurrentIndex(1)
                elif mode == "autonomous":
                    self.mode_combo.setCurrentIndex(2)
            
            # Actualitzar slider de velocitat si existeix
            if 'speed' in state_info and hasattr(self, 'speed_slider'):
                speed_percent = min(100, max(0, int(state_info['speed'] / 2.55)))
                self.speed_slider.setValue(speed_percent)
                if hasattr(self, 'speed_label'):
                    self.speed_label.setText(f"{speed_percent}%")
            
            # Actualitzar estat dels botons de direcció segons el mode
            is_manual = mode == "manual"
            if hasattr(self, 'up_button'):
                self.up_button.setEnabled(is_manual)
            if hasattr(self, 'down_button'):
                self.down_button.setEnabled(is_manual)
            if hasattr(self, 'left_button'):
                self.left_button.setEnabled(is_manual)
            if hasattr(self, 'right_button'):
                self.right_button.setEnabled(is_manual)
            
            # Mostrar informació a la barra d'estat
            moving_status = "en moviment" if state_info.get('is_moving', False) else "aturat"
            direction = state_info.get('direction', 'stop')
            
            self.statusBar.showMessage(f"Navegació: Mode {mode}, {moving_status}, direcció {direction}")
            
            # Registrar canvi d'estat
            logger.info(f"Estat navegació actualitzat: mode={mode}, {state_info}")
                
        except Exception as e:
            logger.error(f"Error actualitzant estat de navegació: {e}")


    def show_navigation_alert(self, direction, angle, distance):
        """
        Mostra una alerta de navegació a la interfície.
        
        Args:
            direction (str): Direcció de l'alerta ("frontal", "esquerra", "dreta")
            angle (float): Angle de l'obstacle (radiants)
            distance (float): Distància a l'obstacle (mm)
        """
        try:
            # Convertir distància a metres per mostrar-la
            distance_meters = round(distance / 1000, 2)
            
            # Convertir angle a graus
            angle_degrees = round(angle * 180 / 3.14159, 1)
            
            # Missatge d'alerta
            alert_message = f"ALERTA DE NAVEGACIÓ: Obstacle a {direction} ({distance_meters}m, {angle_degrees}°)"
            
            # Mostrar alerta a la interfície
            if hasattr(self, 'alerts_label'):
                self.alerts_label.setText(alert_message)
                self.alerts_label.setStyleSheet("color: red; font-weight: bold;")
            
            # Actualitzar barra d'estat
            self.statusBar.showMessage(alert_message)
            
            # Registrar alerta
            logger.warning(f"Alerta navegació: {alert_message}")
            
        except Exception as e:
            logger.error(f"Error mostrant alerta de navegació: {e}")

    def update_config_view(self, config):
        """
        Actualitza la visualització de configuració quan canvia la configuració.
        
        Args:
            config (dict): La configuració actualitzada
        """
        try:
            # Actualitzar visualització de config de connexió
            connection_config = config.get('connection', {})
            if hasattr(self, 'config_host_input'):
                self.config_host_input.setText(
                    connection_config.get('host', '192.168.1.100'))
            
            if hasattr(self, 'config_port_input'):
                self.config_port_input.setText(
                    str(connection_config.get('port', 9999)))
            
            # Actualitzar llindars de sensors
            sensors_config = config.get('sensors', {})
            for sensor_type, properties in self.sensor_manager.SENSOR_TYPES.items():
                if sensor_type in self.threshold_widgets:
                    sensor_config = sensors_config.get(sensor_type, {})
                    threshold = sensor_config.get('threshold', properties['threshold'])
                    unit = properties.get('unit', '')
                    self.threshold_widgets[sensor_type].setText(f"{threshold} {unit}")
            
            # Actualitzar llindar de LiDAR
            lidar_config = config.get('lidar', {})
            if hasattr(self, 'lidar_threshold_label'):
                self.lidar_threshold_label.setText(
                    str(lidar_config.get('obstacle_threshold', 500)))
            
            # Registrar l'actualització
            logger.info("Visualització de configuració actualitzada")
            
        except Exception as e:
            logger.error(f"Error actualitzant visualització de configuració: {e}")         
                    
    @pyqtSlot(bool, str)
    def update_connection_status(self, is_connected, message=""):
        """Actualitza l'estat de connexió a la interfície."""
        self.connection_status_label.setText(f"Estat: {message}")
        self.connect_button.setText(
            "Desconnectar" if is_connected else "Connectar")

        # Guardar l'estat de connexió al connection_manager si no té l'atribut
        # 'connected'
        if not hasattr(self.connection_manager, 'connected'):
            setattr(self.connection_manager, 'connected', is_connected)

        # Activar/desactivar controls segons estat de connexió
        self._update_ui_state()

        # Actualitzar barra d'estat
        self.statusBar.showMessage(f"Connexió: {message}")
      

    @pyqtSlot(str, float)
    def update_sensor_data(self, sensor_type, value):
        """Actualitza les dades d'un sensor específic."""
        if sensor_type in self.sensor_data_labels:
            properties = self.sensor_manager.SENSOR_TYPES.get(sensor_type, {})
            self.sensor_data_labels[sensor_type].setText(
                f"{value:.1f} {properties.get('unit', '')}"
            )

    @pyqtSlot(dict)
    def update_all_sensors_data(self, sensor_data):
        """Actualitza les dades de tots els sensors."""
        for sensor_type, value in sensor_data.items():
            if sensor_type in self.sensor_data_labels:
                properties = self.sensor_manager.SENSOR_TYPES.get(sensor_type, {})
                self.sensor_data_labels[sensor_type].setText(
                    f"{value:.1f} {properties.get('unit', '')}"
                )

    @pyqtSlot(str, str)
    def show_sensor_alert(self, sensor_type, message):
        """Mostra una alerta per a un sensor específic."""
        # Actualitzar etiqueta d'alerta general
        self.alerts_label.setText(f"ALERTA: {message}")
        self.alerts_label.setStyleSheet("color: red; font-weight: bold;")

        # Actualitzar etiqueta d'alerta del sensor específic
        if sensor_type in self.sensor_alert_labels:
            self.sensor_alert_labels[sensor_type].setText("ALERTA")
            self.sensor_alert_labels[sensor_type].setStyleSheet(
                "color: red; font-weight: bold;")
   
     
    @pyqtSlot(str, float)
    def update_detection_list(self, object_type, confidence):
        """Actualitza la llista d'objectes detectats."""
        row_count = self.detections_list.rowCount()
        self.detections_list.insertRow(row_count)
    
        # Afegir tipus d'objecte
        self.detections_list.setItem(row_count, 0, QTableWidgetItem(object_type))
    
        # Afegir confiança
        self.detections_list.setItem(row_count, 1, 
                                QTableWidgetItem(f"{confidence:.2f}"))
    
        # Posició (simulada per ara)
        self.detections_list.setItem(row_count, 2, 
                                QTableWidgetItem("Centre"))
    
        # Limitar a 10 files màxim
        if self.detections_list.rowCount() > 10:
            self.detections_list.removeRow(0)

    @pyqtSlot(bool, str)
    def update_ai_status(self, is_active, message):
        """Actualitza l'estat de la IA."""
        # Implementació bàsica
        self.ai_enabled_checkbox.setChecked(is_active)
        self.statusBar.showMessage(f"IA: {message}")

    def closeEvent(self, event):
        """S'executa quan es tanca la finestra principal."""
        try:
            # Aturar timers i threads
            if hasattr(
                    self,
                    'update_timer') and self.update_timer.isActive():
                self.update_timer.stop()

            # Netejar recursos de la connexió
            if hasattr(self, 'connection_manager'):
                self.connection_manager.cleanup()
                logger.info("ConnectionManager netejat")

            # Netejar recursos del LiDAR
            if hasattr(self, 'lidar_manager'):
                self.lidar_manager.cleanup()
                logger.info("LidarManager netejat")

            # Netejar recursos de la càmera
            if hasattr(self, 'camera_manager'):
                self.camera_manager.cleanup()
                logger.info("CameraManager netejat")

            # Netejar recursos dels sensors
            if hasattr(self, 'sensor_manager'):
                self.sensor_manager.cleanup()
                logger.info("SensorManager netejat")

            # Acceptar l'event de tancament
            event.accept()
        except Exception as e:
            logger.error(f"Error tancant l'aplicació: {e}")
            event.accept()