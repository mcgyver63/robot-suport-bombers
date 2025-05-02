"""
Mòdul de Gestió de Base de Dades
================================
Proporciona funcionalitats per gestionar projectes, configuracions i sessions.
"""

import os
import sqlite3
import logging
import json
from datetime import datetime

# Configuració de logging
logger = logging.getLogger("DB")

class DBManager:
    """Gestor de base de dades per a projectes, configuracions i sessions."""
    
    def __init__(self, db_file=None):
        """
        Inicialitza el gestor de base de dades.
        
        Args:
            db_file: Ruta al fitxer de base de dades (opcional)
        """
        # Si no s'especifica un fitxer, utilitzar un per defecte
        if db_file is None:
            base_dir = os.path.abspath(os.path.dirname(__file__))
            parent_dir = os.path.dirname(base_dir)
            db_dir = os.path.join(parent_dir, "db")
            os.makedirs(db_dir, exist_ok=True)
            self.db_file = os.path.join(db_dir, "projects.db")
        else:
            self.db_file = db_file
    
    def connect(self):
        """
        Estableix una connexió amb la base de dades.
        
        Returns:
            tuple: (connexió, cursor)
        """
        conn = sqlite3.connect(self.db_file)
        conn.row_factory = sqlite3.Row  # Per obtenir els resultats com a diccionaris
        cursor = conn.cursor()
        return conn, cursor
    
    def init_db(self):
        """Inicialitza l'estructura de la base de dades."""
        try:
            conn, cursor = self.connect()
            
            # Crear taula de projectes
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS projects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            ''')
            
            # Crear taula de configuracions
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS configurations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                config_data TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (project_id) REFERENCES projects (id) ON DELETE CASCADE
            )
            ''')
            
            # Crear taula de sessions
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id INTEGER NOT NULL,
                started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                ended_at TIMESTAMP,
                duration_seconds REAL,
                notes TEXT,
                FOREIGN KEY (project_id) REFERENCES projects (id) ON DELETE CASCADE
            )
            ''')
            
            conn.commit()
            conn.close()
            
            logger.info("Base de dades inicialitzada correctament")
            return True
        except Exception as e:
            logger.error(f"Error inicialitzant base de dades: {e}")
            return False
    
    # ========== Gestió de Projectes ==========
    
    def get_projects(self):
        """
        Obté tots els projectes.
        
        Returns:
            list: Llista de projectes
        """
        try:
            conn, cursor = self.connect()
            cursor.execute("SELECT * FROM projects ORDER BY name")
            projects = [dict(row) for row in cursor.fetchall()]
            conn.close()
            return projects
        except Exception as e:
            logger.error(f"Error obtenint projectes: {e}")
            return []
    
    def get_project(self, project_id):
        """
        Obté un projecte pel seu ID.
        
        Args:
            project_id: ID del projecte
        
        Returns:
            dict: Dades del projecte o None si no existeix
        """
        try:
            conn, cursor = self.connect()
            cursor.execute("SELECT * FROM projects WHERE id = ?", (project_id,))
            project = cursor.fetchone()
            conn.close()
            
            if project:
                return dict(project)
            return None
        except Exception as e:
            logger.error(f"Error obtenint projecte {project_id}: {e}")
            return None
    
    def save_project(self, name, description=""):
        """
        Crea un nou projecte.
        
        Args:
            name: Nom del projecte
            description: Descripció del projecte (opcional)
        
        Returns:
            int: ID del projecte creat o None si hi ha error
        """
        try:
            conn, cursor = self.connect()
            
            # Comprovar si ja existeix un projecte amb aquest nom
            cursor.execute("SELECT id FROM projects WHERE name = ?", (name,))
            existing = cursor.fetchone()
            
            if existing:
                logger.warning(f"Ja existeix un projecte amb el nom '{name}'")
                conn.close()
                return existing[0]
            
            # Inserir nou projecte
            cursor.execute(
                "INSERT INTO projects (name, description) VALUES (?, ?)",
                (name, description)
            )
            
            project_id = cursor.lastrowid
            conn.commit()
            conn.close()
            
            logger.info(f"Projecte creat: {name} (ID: {project_id})")
            return project_id
        except Exception as e:
            logger.error(f"Error creant projecte: {e}")
            return None
    
    def update_project(self, project_id, name, description=""):
        """
        Actualitza un projecte existent.
        
        Args:
            project_id: ID del projecte
            name: Nou nom del projecte
            description: Nova descripció del projecte
        
        Returns:
            bool: True si s'ha actualitzat correctament
        """
        try:
            conn, cursor = self.connect()
            
            # Actualitzar projecte
            cursor.execute(
                "UPDATE projects SET name = ?, description = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                (name, description, project_id)
            )
            
            success = cursor.rowcount > 0
            conn.commit()
            conn.close()
            
            if success:
                logger.info(f"Projecte actualitzat: {name} (ID: {project_id})")
            else:
                logger.warning(f"No s'ha pogut actualitzar el projecte {project_id}")
            
            return success
        except Exception as e:
            logger.error(f"Error actualitzant projecte {project_id}: {e}")
            return False
    
    def delete_project(self, project_id):
        """
        Elimina un projecte.
        
        Args:
            project_id: ID del projecte
        
        Returns:
            bool: True si s'ha eliminat correctament
        """
        try:
            conn, cursor = self.connect()
            
            # Obtenir nom del projecte abans d'eliminar-lo
            cursor.execute("SELECT name FROM projects WHERE id = ?", (project_id,))
            project = cursor.fetchone()
            
            if not project:
                logger.warning(f"No s'ha trobat el projecte {project_id}")
                conn.close()
                return False
            
            project_name = project[0]
            
            # Eliminar projecte (les configuracions i sessions s'eliminaran en cascada)
            cursor.execute("DELETE FROM projects WHERE id = ?", (project_id,))
            
            success = cursor.rowcount > 0
            conn.commit()
            conn.close()
            
            if success:
                logger.info(f"Projecte eliminat: {project_name} (ID: {project_id})")
            else:
                logger.warning(f"No s'ha pogut eliminar el projecte {project_id}")
            
            return success
        except Exception as e:
            logger.error(f"Error eliminant projecte {project_id}: {e}")
            return False
    
    # ========== Gestió de Configuracions ==========
    
    def get_configurations(self, project_id):
        """
        Obté totes les configuracions d'un projecte.
        
        Args:
            project_id: ID del projecte
        
        Returns:
            list: Llista de configuracions
        """
        try:
            conn, cursor = self.connect()
            cursor.execute(
                "SELECT * FROM configurations WHERE project_id = ? ORDER BY created_at DESC",
                (project_id,)
            )
            
            configurations = []
            for row in cursor.fetchall():
                config = dict(row)
                # Convertir el JSON de configuració a diccionari
                config['config_data'] = json.loads(config['config_data'])
                configurations.append(config)
            
            conn.close()
            return configurations
        except Exception as e:
            logger.error(f"Error obtenint configuracions per al projecte {project_id}: {e}")
            return []
    
    def get_configuration(self, config_id):
        """
        Obté una configuració pel seu ID.
        
        Args:
            config_id: ID de la configuració
        
        Returns:
            dict: Dades de la configuració o None si no existeix
        """
        try:
            conn, cursor = self.connect()
            cursor.execute("SELECT * FROM configurations WHERE id = ?", (config_id,))
            config = cursor.fetchone()
            conn.close()
            
            if config:
                config_dict = dict(config)
                # Convertir el JSON de configuració a diccionari
                config_dict['config_data'] = json.loads(config_dict['config_data'])
                return config_dict
            return None
        except Exception as e:
            logger.error(f"Error obtenint configuració {config_id}: {e}")
            return None
    
    def save_configuration(self, project_id, name, config_data):
        """
        Desa una configuració per a un projecte.
        
        Args:
            project_id: ID del projecte
            name: Nom de la configuració
            config_data: Dades de configuració (diccionari)
        
        Returns:
            int: ID de la configuració creada o None si hi ha error
        """
        try:
            # Convertir configuració a JSON
            config_json = json.dumps(config_data)
            
            conn, cursor = self.connect()
            
            # Inserir configuració
            cursor.execute(
                "INSERT INTO configurations (project_id, name, config_data) VALUES (?, ?, ?)",
                (project_id, name, config_json)
            )
            
            config_id = cursor.lastrowid
            conn.commit()
            conn.close()
            
            logger.info(f"Configuració desada: {name} per al projecte {project_id} (ID: {config_id})")
            return config_id
        except Exception as e:
            logger.error(f"Error desant configuració per al projecte {project_id}: {e}")
            return None
    
    def delete_configuration(self, config_id):
        """
        Elimina una configuració.
        
        Args:
            config_id: ID de la configuració
        
        Returns:
            bool: True si s'ha eliminat correctament
        """
        try:
            conn, cursor = self.connect()
            
            # Eliminar configuració
            cursor.execute("DELETE FROM configurations WHERE id = ?", (config_id,))
            
            success = cursor.rowcount > 0
            conn.commit()
            conn.close()
            
            if success:
                logger.info(f"Configuració eliminada: {config_id}")
            else:
                logger.warning(f"No s'ha pogut eliminar la configuració {config_id}")
            
            return success
        except Exception as e:
            logger.error(f"Error eliminant configuració {config_id}: {e}")
            return False
    
    # ========== Gestió de Sessions ==========
    
    def get_sessions(self, project_id):
        """
        Obté totes les sessions d'un projecte.
        
        Args:
            project_id: ID del projecte
        
        Returns:
            list: Llista de sessions
        """
        try:
            conn, cursor = self.connect()
            cursor.execute(
                "SELECT * FROM sessions WHERE project_id = ? ORDER BY started_at DESC",
                (project_id,)
            )
            
            sessions = [dict(row) for row in cursor.fetchall()]
            conn.close()
            return sessions
        except Exception as e:
            logger.error(f"Error obtenint sessions per al projecte {project_id}: {e}")
            return []
    
    def start_session(self, project_id):
        """
        Inicia una nova sessió per a un projecte.
        
        Args:
            project_id: ID del projecte
        
        Returns:
            int: ID de la sessió creada o None si hi ha error
        """
        try:
            conn, cursor = self.connect()
            
            # Inserir sessió
            cursor.execute(
                "INSERT INTO sessions (project_id) VALUES (?)",
                (project_id,)
            )
            
            session_id = cursor.lastrowid
            conn.commit()
            conn.close()
            
            logger.info(f"Sessió iniciada: {session_id} (Projecte: {project_id})")
            return session_id
        except Exception as e:
            logger.error(f"Error iniciant sessió per al projecte {project_id}: {e}")
            return None
    
    def end_session(self, session_id, duration_seconds=None, notes=""):
        """
        Finalitza una sessió.
        
        Args:
            session_id: ID de la sessió
            duration_seconds: Durada de la sessió en segons (opcional)
            notes: Notes de la sessió (opcional)
        
        Returns:
            bool: True si s'ha finalitzat correctament
        """
        try:
            conn, cursor = self.connect()
            
            # Actualitzar sessió
            if duration_seconds is not None:
                cursor.execute(
                    "UPDATE sessions SET ended_at = CURRENT_TIMESTAMP, duration_seconds = ?, notes = ? WHERE id = ?",
                    (duration_seconds, notes, session_id)
                )
            else:
                cursor.execute(
                    "UPDATE sessions SET ended_at = CURRENT_TIMESTAMP, notes = ? WHERE id = ?",
                    (notes, session_id)
                )
            
            success = cursor.rowcount > 0
            conn.commit()
            conn.close()
            
            if success:
                logger.info(f"Sessió finalitzada: {session_id}")
            else:
                logger.warning(f"No s'ha pogut finalitzar la sessió {session_id}")
            
            return success
        except Exception as e:
            logger.error(f"Error finalitzant sessió {session_id}: {e}")
            return False
    
    def add_session_notes(self, session_id, notes):
        """
        Afegeix notes a una sessió.
        
        Args:
            session_id: ID de la sessió
            notes: Notes a afegir
        
        Returns:
            bool: True si s'han afegit correctament
        """
        try:
            conn, cursor = self.connect()
            
            # Actualitzar notes de la sessió
            cursor.execute(
                "UPDATE sessions SET notes = ? WHERE id = ?",
                (notes, session_id)
            )
            
            success = cursor.rowcount > 0
            conn.commit()
            conn.close()
            
            if success:
                logger.info(f"Notes afegides a la sessió {session_id}")
            else:
                logger.warning(f"No s'han pogut afegir notes a la sessió {session_id}")
            
            return success
        except Exception as e:
            logger.error(f"Error afegint notes a la sessió {session_id}: {e}")
            return False

# Exemple d'ús
if __name__ == "__main__":
    # Configurar logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Crear instància
    db_manager = DBManager()
    
    # Inicialitzar base de dades
    db_manager.init_db()
    
    # Crear projecte de prova
    project_id = db_manager.save_project(
        "Projecte de prova",
        "Projecte creat per a proves del gestor de base de dades."
    )
    
    # Obtenir projectes
    projects = db_manager.get_projects()
    print(f"Projectes: {len(projects)}")
    
    # Crear configuració de prova
    if project_id:
        config_id = db_manager.save_configuration(
            project_id,
            "Configuració de prova",
            {
                "connection": {
                    "host": "localhost",
                    "port": 9000
                },
                "sensors": {
                    "temperature_threshold": 40.0,
                    "humidity_threshold": 85.0
                }
            }
        )
        
        # Obtenir configuracions
        configs = db_manager.get_configurations(project_id)
        print(f"Configuracions: {len(configs)}")
        
        # Iniciar sessió de prova
        session_id = db_manager.start_session(project_id)
        
        # Finalitzar sessió
        if session_id:
            db_manager.end_session(session_id, 300.0, "Sessió de prova completada correctament.")
            
            # Obtenir sessions
            sessions = db_manager.get_sessions(project_id)
            print(f"Sessions: {len(sessions)}")
