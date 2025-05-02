"""
Diàleg de Gestió de Projectes
=============================
Proporciona una interfície per crear, editar i gestionar projectes.
"""

import os
import logging
from datetime import datetime
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGridLayout, QGroupBox,
    QLabel, QLineEdit, QTextEdit, QPushButton, QDialogButtonBox,
    QListWidget, QAbstractItemView, QTableWidget, QTableWidgetItem,
    QHeaderView, QMessageBox, QInputDialog, QComboBox, QFileDialog
)
from PyQt5.QtCore import Qt

# Configuració de logging
logger = logging.getLogger("UI.ProjectDialog")

class ProjectDialog(QDialog):
    """Diàleg per gestionar projectes."""
    
    def __init__(self, db_manager, parent=None):
        """
        Inicialitza el diàleg de projectes.
        
        Args:
            db_manager: Gestor de base de dades
            parent: Widget pare (opcional)
        """
        super().__init__(parent)
        
        self.db_manager = db_manager
        self.setWindowTitle("Gestió de Projectes")
        self.setMinimumWidth(600)
        self.setMinimumHeight(500)
        
        # Layout principal
        layout = QVBoxLayout(self)
        
        # Llista de projectes
        self.projects_group = QGroupBox("Projectes disponibles")
        projects_layout = QVBoxLayout()
        
        self.projects_list = QListWidget()
        self.projects_list.setSelectionMode(QAbstractItemView.SingleSelection)
        self.projects_list.currentRowChanged.connect(self._project_selected)
        projects_layout.addWidget(self.projects_list)
        
        # Botons per a projectes
        projects_buttons = QHBoxLayout()
        
        self.new_project_btn = QPushButton("Nou projecte")
        self.new_project_btn.clicked.connect(self._create_new_project)
        projects_buttons.addWidget(self.new_project_btn)
        
        self.edit_project_btn = QPushButton("Editar")
        self.edit_project_btn.clicked.connect(self._edit_project)
        self.edit_project_btn.setEnabled(False)
        projects_buttons.addWidget(self.edit_project_btn)
        
        self.delete_project_btn = QPushButton("Eliminar")
        self.delete_project_btn.clicked.connect(self._delete_project)
        self.delete_project_btn.setEnabled(False)
        projects_buttons.addWidget(self.delete_project_btn)
        
        projects_layout.addLayout(projects_buttons)
        self.projects_group.setLayout(projects_layout)
        layout.addWidget(self.projects_group)
        
        # Detalls del projecte
        self.details_group = QGroupBox("Detalls del projecte")
        details_layout = QGridLayout()
        
        details_layout.addWidget(QLabel("Nom:"), 0, 0)
        self.project_name_label = QLabel("")
        details_layout.addWidget(self.project_name_label, 0, 1)
        
        details_layout.addWidget(QLabel("Descripció:"), 1, 0)
        self.project_description_label = QLabel("")
        self.project_description_label.setWordWrap(True)
        details_layout.addWidget(self.project_description_label, 1, 1)
        
        details_layout.addWidget(QLabel("Creat:"), 2, 0)
        self.project_created_label = QLabel("")
        details_layout.addWidget(self.project_created_label, 2, 1)
        
        details_layout.addWidget(QLabel("Última modificació:"), 3, 0)
        self.project_updated_label = QLabel("")
        details_layout.addWidget(self.project_updated_label, 3, 1)
        
        self.details_group.setLayout(details_layout)
        layout.addWidget(self.details_group)
        
        # Configuracions del projecte
        self.configs_group = QGroupBox("Configuracions del projecte")
        configs_layout = QVBoxLayout()
        
        # Llista de configuracions
        self.configs_table = QTableWidget(0, 4)
        self.configs_table.setHorizontalHeaderLabels(["Nom", "Data creació", "Tipus", "Aplicar"])
        self.configs_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.configs_table.verticalHeader().setVisible(False)
        configs_layout.addWidget(self.configs_table)
        
        # Botons per a configuracions
        configs_buttons = QHBoxLayout()
        
        self.new_config_btn = QPushButton("Nova configuració")
        self.new_config_btn.clicked.connect(self._create_new_config)
        self.new_config_btn.setEnabled(False)
        configs_buttons.addWidget(self.new_config_btn)
        
        self.export_config_btn = QPushButton("Exportar")
        self.export_config_btn.clicked.connect(self._export_config)
        self.export_config_btn.setEnabled(False)
        configs_buttons.addWidget(self.export_config_btn)
        
        self.import_config_btn = QPushButton("Importar")
        self.import_config_btn.clicked.connect(self._import_config)
        self.import_config_btn.setEnabled(False)
        configs_buttons.addWidget(self.import_config_btn)
        
        configs_layout.addLayout(configs_buttons)
        self.configs_group.setLayout(configs_layout)
        layout.addWidget(self.configs_group)
        
        # Historial de sessions
        self.sessions_group = QGroupBox("Historial de sessions")
        sessions_layout = QVBoxLayout()
        
        self.sessions_table = QTableWidget(0, 4)
        self.sessions_table.setHorizontalHeaderLabels(["Data", "Hora inici", "Durada", "Notes"])
        self.sessions_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.sessions_table.verticalHeader().setVisible(False)
        sessions_layout.addWidget(self.sessions_table)
        
        self.sessions_group.setLayout(sessions_layout)
        layout.addWidget(self.sessions_group)
        
        # Botons finals
        buttons = QDialogButtonBox(QDialogButtonBox.Close)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        
        # Carregar projectes
        self.load_projects()
    
    def load_projects(self):
        """Carrega la llista de projectes des de la base de dades."""
        try:
            self.projects_list.clear()
            projects = self.db_manager.get_projects()
            
            if projects:
                for project in projects:
                    self.projects_list.addItem(f"{project['name']}")
                    
                # Seleccionar el primer projecte
                self.projects_list.setCurrentRow(0)
            else:
                # Botons que requereixen un projecte
                self.edit_project_btn.setEnabled(False)
                self.delete_project_btn.setEnabled(False)
                self.new_config_btn.setEnabled(False)
                self.export_config_btn.setEnabled(False)
                self.import_config_btn.setEnabled(False)
                
                # Netejar detalls
                self._clear_project_details()
                
        except Exception as e:
            logger.error(f"Error carregant projectes: {e}")
            QMessageBox.critical(self, "Error", f"Error carregant projectes: {e}")
    
    def _clear_project_details(self):
        """Neteja la informació de detalls del projecte."""
        self.project_name_label.setText("")
        self.project_description_label.setText("")
        self.project_created_label.setText("")
        self.project_updated_label.setText("")
        self.configs_table.setRowCount(0)
        self.sessions_table.setRowCount(0)
    
    def _project_selected(self, row):
        """
        Actualitza la informació detallada quan es selecciona un projecte.
        
        Args:
            row (int): Índex del projecte seleccionat
        """
        if row < 0:
            # No hi ha cap projecte seleccionat
            self.edit_project_btn.setEnabled(False)
            self.delete_project_btn.setEnabled(False)
            self.new_config_btn.setEnabled(False)
            self.export_config_btn.setEnabled(False)
            self.import_config_btn.setEnabled(False)
            
            self._clear_project_details()
            return
        
        # Activar botons
        self.edit_project_btn.setEnabled(True)
        self.delete_project_btn.setEnabled(True)
        self.new_config_btn.setEnabled(True)
        self.export_config_btn.setEnabled(True)
        self.import_config_btn.setEnabled(True)
        
        try:
            # Obtenir projecte seleccionat
            projects = self.db_manager.get_projects()
            if not projects or row >= len(projects):
                return
            
            project = projects[row]
            
            # Mostrar detalls
            self.project_name_label.setText(project['name'])
            self.project_description_label.setText(project['description'] or "Sense descripció")
            
            created_date = datetime.fromisoformat(project['created_at'])
            self.project_created_label.setText(created_date.strftime("%d/%m/%Y %H:%M"))
            
            updated_date = datetime.fromisoformat(project.get('updated_at', project['created_at']))
            self.project_updated_label.setText(updated_date.strftime("%d/%m/%Y %H:%M"))
            
            # Carregar configuracions
            # Si existeix un mètode get_configurations al DBManager
            if hasattr(self.db_manager, 'get_configurations'):
                try:
                    configurations = self.db_manager.get_configurations(project['id'])
                    
                    self.configs_table.setRowCount(len(configurations))
                    for i, config in enumerate(configurations):
                        # Nom
                        self.configs_table.setItem(i, 0, QTableWidgetItem(config['name']))
                        
                        # Data creació
                        created_at = datetime.fromisoformat(config['created_at'])
                        self.configs_table.setItem(i, 1, QTableWidgetItem(created_at.strftime("%d/%m/%Y %H:%M")))
                        
                        # Tipus (suposem que es pot determinar per alguna propietat)
                        config_type = "Estàndard"
                        self.configs_table.setItem(i, 2, QTableWidgetItem(config_type))
                        
                        # Botó d'aplicar
                        apply_btn = QPushButton("Aplicar")
                        apply_btn.setProperty("config_id", config['id'])
                        apply_btn.clicked.connect(self._apply_config)
                        self.configs_table.setCellWidget(i, 3, apply_btn)
                except Exception as e:
                    logger.error(f"Error carregant configuracions: {e}")
                    self.configs_table.setRowCount(0)
            else:
                # Si no hi ha mètode, mostrar un missatge
                self.configs_table.setRowCount(1)
                self.configs_table.setSpan(0, 0, 1, 4)
                self.configs_table.setItem(0, 0, QTableWidgetItem("Funcionalitat no implementada"))
            
            # Carregar sessions
            # Si existeix un mètode get_sessions al DBManager
            if hasattr(self.db_manager, 'get_sessions'):
                try:
                    sessions = self.db_manager.get_sessions(project['id'])
                    
                    self.sessions_table.setRowCount(len(sessions))
                    for i, session in enumerate(sessions):
                        # Data
                        started_at = datetime.fromisoformat(session['started_at'])
                        self.sessions_table.setItem(i, 0, QTableWidgetItem(started_at.strftime("%d/%m/%Y")))
                        
                        # Hora inici
                        self.sessions_table.setItem(i, 1, QTableWidgetItem(started_at.strftime("%H:%M:%S")))
                        
                        # Durada
                        duration = session.get('duration_seconds', 0)
                        hours, remainder = divmod(duration, 3600)
                        minutes, seconds = divmod(remainder, 60)
                        duration_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
                        self.sessions_table.setItem(i, 2, QTableWidgetItem(duration_str))
                        
                        # Notes
                        self.sessions_table.setItem(i, 3, QTableWidgetItem(session.get('notes', '')))
                except Exception as e:
                    logger.error(f"Error carregant sessions: {e}")
                    self.sessions_table.setRowCount(0)
            else:
                # Si no hi ha mètode, mostrar un missatge
                self.sessions_table.setRowCount(1)
                self.sessions_table.setSpan(0, 0, 1, 4)
                self.sessions_table.setItem(0, 0, QTableWidgetItem("Funcionalitat no implementada"))
            
        except Exception as e:
            logger.error(f"Error mostrant detalls del projecte: {e}")
            QMessageBox.critical(self, "Error", f"Error mostrant detalls del projecte: {e}")
    
    def _create_new_project(self):
        """Crea un nou projecte."""
        # Crear un subdiàleg per introduir dades
        dialog = QDialog(self)
        dialog.setWindowTitle("Nou projecte")
        dialog.setMinimumWidth(400)
        
        layout = QVBoxLayout(dialog)
        
        form_layout = QGridLayout()
        
        form_layout.addWidget(QLabel("Nom:"), 0, 0)
        name_input = QLineEdit()
        form_layout.addWidget(name_input, 0, 1)
        
        form_layout.addWidget(QLabel("Descripció:"), 1, 0)
        description_input = QTextEdit()
        description_input.setFixedHeight(100)
        form_layout.addWidget(description_input, 1, 1)
        
        layout.addLayout(form_layout)
        
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)
        
        # Mostrar diàleg
        result = dialog.exec_()
        
        if result == QDialog.Accepted:
            name = name_input.text().strip()
            description = description_input.toPlainText().strip()
            
            if not name:
                QMessageBox.warning(self, "Nom requerit", "Cal especificar un nom per al projecte.")
                return
            
            try:
                # Crear projecte
                project_id = self.db_manager.save_project(name, description)
                
                if project_id:
                    # Actualitzar llista
                    self.load_projects()
                    
                    # Seleccionar el nou projecte
                    for i in range(self.projects_list.count()):
                        if self.projects_list.item(i).text() == name:
                            self.projects_list.setCurrentRow(i)
                            break
                    
                    QMessageBox.information(self, "Projecte creat", f"El projecte '{name}' s'ha creat correctament.")
                else:
                    QMessageBox.warning(self, "Error", "No s'ha pogut crear el projecte.")
            
            except Exception as e:
                logger.error(f"Error creant projecte: {e}")
                QMessageBox.critical(self, "Error", f"Error creant projecte: {e}")
    
    def _edit_project(self):
        """Edita el projecte seleccionat."""
        row = self.projects_list.currentRow()
        if row < 0:
            return
        
        try:
            # Obtenir projecte seleccionat
            projects = self.db_manager.get_projects()
            if not projects or row >= len(projects):
                return
            
            project = projects[row]
            
            # Crear un subdiàleg per editar dades
            dialog = QDialog(self)
            dialog.setWindowTitle("Editar projecte")
            dialog.setMinimumWidth(400)
            
            layout = QVBoxLayout(dialog)
            
            form_layout = QGridLayout()
            
            form_layout.addWidget(QLabel("Nom:"), 0, 0)
            name_input = QLineEdit(project['name'])
            form_layout.addWidget(name_input, 0, 1)
            
            form_layout.addWidget(QLabel("Descripció:"), 1, 0)
            description_input = QTextEdit(project['description'] or "")
            description_input.setFixedHeight(100)
            form_layout.addWidget(description_input, 1, 1)
            
            layout.addLayout(form_layout)
            
            buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
            buttons.accepted.connect(dialog.accept)
            buttons.rejected.connect(dialog.reject)
            layout.addWidget(buttons)
            
            # Mostrar diàleg
            result = dialog.exec_()
            
            if result == QDialog.Accepted:
                name = name_input.text().strip()
                description = description_input.toPlainText().strip()
                
                if not name:
                    QMessageBox.warning(self, "Nom requerit", "Cal especificar un nom per al projecte.")
                    return
                
                # Actualitzar projecte (aquesta funció hauria d'existir al DBManager)
                if hasattr(self.db_manager, 'update_project'):
                    success = self.db_manager.update_project(project['id'], name, description)
                    
                    if success:
                        # Actualitzar llista
                        self.load_projects()
                        
                        # Seleccionar el projecte editat
                        for i in range(self.projects_list.count()):
                            if self.projects_list.item(i).text() == name:
                                self.projects_list.setCurrentRow(i)
                                break
                        
                        QMessageBox.information(self, "Projecte actualitzat", f"El projecte '{name}' s'ha actualitzat correctament.")
                    else:
                        QMessageBox.warning(self, "Error", "No s'ha pogut actualitzar el projecte.")
                else:
                    QMessageBox.information(self, "Funció no implementada", "La funció d'actualitzar projectes no està implementada.")
            
        except Exception as e:
            logger.error(f"Error editant projecte: {e}")
            QMessageBox.critical(self, "Error", f"Error editant projecte: {e}")
    
    def _delete_project(self):
        """Elimina el projecte seleccionat."""
        row = self.projects_list.currentRow()
        if row < 0:
            return
        
        project_name = self.projects_list.item(row).text()
        
        # Confirmar eliminació
        reply = QMessageBox.question(
            self, 
            "Eliminar projecte", 
            f"Estàs segur que vols eliminar el projecte '{project_name}'?\nAquesta acció no es pot desfer.",
            QMessageBox.Yes | QMessageBox.No, 
            QMessageBox.No
        )
        
        if reply != QMessageBox.Yes:
            return
        
        try:
            # Obtenir ID del projecte
            projects = self.db_manager.get_projects()
            if not projects or row >= len(projects):
                return
            
            project_id = projects[row]['id']
            
            # Eliminar projecte (aquesta funció hauria d'existir al DBManager)
            if hasattr(self.db_manager, 'delete_project'):
                success = self.db_manager.delete_project(project_id)
                
                if success:
                    # Actualitzar llista
                    self.load_projects()
                    
                    QMessageBox.information(self, "Projecte eliminat", f"El projecte '{project_name}' s'ha eliminat correctament.")
                else:
                    QMessageBox.warning(self, "Error", f"No s'ha pogut eliminar el projecte '{project_name}'.")
            else:
                QMessageBox.information(self, "Funció no implementada", "La funció d'eliminar projectes no està implementada.")
            
        except Exception as e:
            logger.error(f"Error eliminant projecte: {e}")
            QMessageBox.critical(self, "Error", f"Error eliminant projecte: {e}")
    
    def _create_new_config(self):
        """Crea una nova configuració per al projecte seleccionat."""
        row = self.projects_list.currentRow()
        if row < 0:
            return
        
        try:
            # Obtenir projecte seleccionat
            projects = self.db_manager.get_projects()
            if not projects or row >= len(projects):
                return
            
            project_id = projects[row]['id']
            project_name = projects[row]['name']
            
            # Demanar nom de la configuració
            name, ok = QInputDialog.getText(self, "Nova configuració", "Nom de la configuració:")
            
            if not ok or not name:
                return
            
            # Comprovar si existeix la funció necessària
            if hasattr(self.db_manager, 'save_configuration'):
                # Obtenir configuració actual des del pare (MainWindow)
                current_config = None
                
                if self.parent() and hasattr(self.parent(), 'config_manager'):
                    config_manager = self.parent().config_manager
                    if hasattr(config_manager, 'load_config'):
                        current_config = config_manager.load_config()
                
                if current_config:
                    # Desar configuració
                    config_id = self.db_manager.save_configuration(project_id, name, current_config)
                    
                    if config_id:
                        # Actualitzar vista
                        self._project_selected(row)
                        
                        QMessageBox.information(self, "Configuració desada", f"S'ha desat la configuració '{name}' per al projecte '{project_name}'.")
                    else:
                        QMessageBox.warning(self, "Error", "No s'ha pogut desar la configuració.")
                else:
                    QMessageBox.warning(self, "Configuració no disponible", "No s'ha pogut obtenir la configuració actual.")
            else:
                QMessageBox.information(self, "Funció no implementada", "La funció de desar configuracions no està implementada.")
            
        except Exception as e:
            logger.error(f"Error creant configuració: {e}")
            QMessageBox.critical(self, "Error", f"Error creant configuració: {e}")
    
    def _apply_config(self):
        """Aplica la configuració seleccionada."""
        # Obtenir el botó que ha triggerat l'acció
        sender = self.sender()
        if not sender or not hasattr(sender, 'property'):
            return
        
        # Obtenir l'ID de la configuració
        config_id = sender.property('config_id')
        if not config_id:
            return
        
        try:
            # Comprovar si existeix la funció necessària
            if hasattr(self.db_manager, 'get_configuration'):
                # Obtenir configuració
                config = self.db_manager.get_configuration(config_id)
                
                if config and 'config_data' in config:
                    # Aplicar configuració a través del ConfigManager
                    if self.parent() and hasattr(self.parent(), 'config_manager'):
                        config_manager = self.parent().config_manager
                        
                        # Actualitzar configuració
                        if hasattr(config_manager, 'update_config_all'):
                            success = config_manager.update_config_all(config['config_data'])
                            
                            if success:
                                QMessageBox.information(self, "Configuració aplicada", f"S'ha aplicat la configuració '{config['name']}'.")
                            else:
                                QMessageBox.warning(self, "Error", "No s'ha pogut aplicar la configuració.")
                        else:
                            QMessageBox.information(self, "Funció no implementada", "La funció d'aplicar configuracions no està implementada.")
                    else:
                        QMessageBox.warning(self, "ConfigManager no disponible", "No s'ha pogut accedir al gestor de configuració.")
                else:
                    QMessageBox.warning(self, "Configuració no disponible", "No s'ha pogut obtenir la configuració.")
            else:
                QMessageBox.information(self, "Funció no implementada", "La funció d'obtenir configuracions no està implementada.")
            
        except Exception as e:
            logger.error(f"Error aplicant configuració: {e}")
            QMessageBox.critical(self, "Error", f"Error aplicant configuració: {e}")
    
    def _export_config(self):
        """Exporta la configuració del projecte a un fitxer."""
        row = self.projects_list.currentRow()
        if row < 0:
            return
        
        try:
            # Obtenir projecte seleccionat
            projects = self.db_manager.get_projects()
            if not projects or row >= len(projects):
                return
            
            project_id = projects[row]['id']
            project_name = projects[row]['name']
            
            # Comprovar si hi ha configuracions
            if hasattr(self.db_manager, 'get_configurations'):
                configs = self.db_manager.get_configurations(project_id)
                
                if not configs:
                    QMessageBox.warning(self, "Sense configuracions", "Aquest projecte no té configuracions per exportar.")
                    return
                
                # Seleccionar configuració si n'hi ha més d'una
                config_to_export = None
                
                if len(configs) == 1:
                    config_to_export = configs[0]
                else:
                    # Crear diàleg per seleccionar
                    dialog = QDialog(self)
                    dialog.setWindowTitle("Seleccionar configuració")
                    
                    layout = QVBoxLayout(dialog)
                    
                    layout.addWidget(QLabel("Selecciona la configuració a exportar:"))
                    
                    config_combo = QComboBox()
                    for config in configs:
                        config_combo.addItem(config['name'], config['id'])
                    layout.addWidget(config_combo)
                    
                    buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
                    buttons.accepted.connect(dialog.accept)
                    buttons.rejected.connect(dialog.reject)
                    layout.addWidget(buttons)
                    
                    if dialog.exec_() == QDialog.Accepted:
                        selected_id = config_combo.currentData()
                        for config in configs:
                            if config['id'] == selected_id:
                                config_to_export = config
                                break
                    else:
                        return
                
                if not config_to_export:
                    return
                
                # Demanar on guardar
                filepath, _ = QFileDialog.getSaveFileName(
                    self,
                    "Exportar configuració",
                    os.path.expanduser(f"~/{project_name}_{config_to_export['name']}.json"),
                    "Arxius JSON (*.json)"
                )
                
                if not filepath:
                    return
                
                # Exportar
                try:
                    import json
                    
                    with open(filepath, 'w', encoding='utf-8') as f:
                        json.dump(config_to_export['config_data'], f, indent=4)
                    
                    QMessageBox.information(
                        self, 
                        "Configuració exportada", 
                        f"S'ha exportat la configuració '{config_to_export['name']}' a {filepath}"
                    )
                except Exception as e:
                    raise Exception(f"Error exportant configuració: {e}")
            else:
                QMessageBox.information(self, "Funció no implementada", "La funció d'exportar configuracions no està implementada.")
            
        except Exception as e:
            logger.error(f"Error exportant configuració: {e}")
            QMessageBox.critical(self, "Error", f"Error exportant configuració: {e}")
    
    def _import_config(self):
        """Importa una configuració des d'un fitxer al projecte seleccionat."""
        row = self.projects_list.currentRow()
        if row < 0:
            return
        
        try:
            # Obtenir projecte seleccionat
            projects = self.db_manager.get_projects()
            if not projects or row >= len(projects):
                return
            
            project_id = projects[row]['id']
            project_name = projects[row]['name']
            
            # Demanar fitxer a importar
            filepath, _ = QFileDialog.getOpenFileName(
                self,
                "Importar configuració",
                os.path.expanduser("~"),
                "Arxius JSON (*.json)"
            )
            
            if not filepath:
                return
            
            # Llegir configuració
            try:
                import json
                
                with open(filepath, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
                
                # Demanar nom per a la configuració
                config_name, ok = QInputDialog.getText(
                    self, 
                    "Nom de la configuració", 
                    "Introdueix un nom per a la configuració importada:",
                    text=os.path.splitext(os.path.basename(filepath))[0]
                )
                
                if not ok or not config_name:
                    return
                
                # Desar configuració
                if hasattr(self.db_manager, 'save_configuration'):
                    config_id = self.db_manager.save_configuration(project_id, config_name, config_data)
                    
                    if config_id:
                        # Actualitzar vista
                        self._project_selected(row)
                        
                        QMessageBox.information(
                            self, 
                            "Configuració importada", 
                            f"S'ha importat la configuració '{config_name}' per al projecte '{project_name}'."
                        )
                    else:
                        QMessageBox.warning(self, "Error", "No s'ha pogut importar la configuració.")
                else:
                    QMessageBox.information(self, "Funció no implementada", "La funció d'importar configuracions no està implementada.")
                    
            except Exception as e:
                raise Exception(f"Error important configuració: {e}")
            
        except Exception as e:
            logger.error(f"Error important configuració: {e}")
            QMessageBox.critical(self, "Error", f"Error important configuració: {e}")
            
