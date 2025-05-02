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