import json
import os
import sys # Importar sys para detectar el sistema operativo

class ConfigManager:
    def __init__(self, app_name="SVREPO", filename="config.json", locales_path="locales"):
        self.app_name = app_name # Nombre de la aplicación para la carpeta en AppData/equivalente
        self.locales_path = locales_path
        self.config_data = {}
        self.current_locales = {}
        self._default_settings = self._get_default_settings()

        # === MODIFICACIÓN CLAVE AQUÍ: DETERMINAR LA RUTA DEL ARCHIVO DE CONFIGURACIÓN ===
        self.config_dir = self._get_config_directory()
        self.filename = os.path.join(self.config_dir, filename)
        # ==============================================================================

        self._initialize_config_file() # Asegura que el archivo exista y esté inicializado

        # Cargar el idioma desde la configuración después de que haya sido inicializada
        initial_language = self.get_setting('General', 'language')
        self.load_locales(initial_language)

    def _get_config_directory(self):
        """
        Determina la ruta del directorio de configuración de la aplicación
        basado en el sistema operativo.
        """
        if sys.platform == "win32":
            # En Windows, usar APPDATA para Roaming (configuraciones de usuario)
            # os.getenv('APPDATA') es más robusto que expanduser('~') para AppData
            config_path = os.path.join(os.getenv('APPDATA'), self.app_name)
        elif sys.platform == "darwin":
            # En macOS, usar ~/Library/Application Support/
            config_path = os.path.join(os.path.expanduser('~'), 'Library', 'Application Support', self.app_name)
        else:
            # En Linux/Unix, usar ~/.config/ (XDG Base Directory Specification)
            # Fallback a ~/.local/share si XDG_CONFIG_HOME no está definido.
            xdg_config_home = os.getenv('XDG_CONFIG_HOME')
            if xdg_config_home:
                config_path = os.path.join(xdg_config_home, self.app_name)
            else:
                config_path = os.path.join(os.path.expanduser('~'), '.config', self.app_name)

        # Asegurarse de que el directorio exista
        os.makedirs(config_path, exist_ok=True)
        print(f"Directorio de configuración: {config_path}")
        return config_path


    def _get_default_settings(self):
        """Define y retorna un diccionario con la configuración predeterminada."""
        return {
            "General": {
                "language": "es",
                "appearance_mode": "System"
            },
            "Backup": {
                "automatico": False,
                "intervalo_minutos": 5,
                "ruta_backup": os.path.expanduser("~"), # Directorio de usuario como predeterminado
                "partidas_auto_backup": [] # Lista vacía por defecto
            }
        }

    def _initialize_config_file(self):
        """
        Asegura que el archivo de configuración exista y contenga todos los valores por defecto.
        Si el archivo no existe o faltan secciones/opciones, las agrega.
        """
        if os.path.exists(self.filename):
            try:
                with open(self.filename, 'r', encoding='utf-8') as f:
                    actual_config_data = json.load(f)

                # Fusionar los valores existentes con los predeterminados
                # Esto asegura que cualquier opción nueva en _default_settings
                # se agregue al archivo existente si no está presente.
                # Las opciones existentes en el archivo sobrescribirán los valores predeterminados.
                merged_config = self._default_settings.copy() # Start with defaults
                for section, options in actual_config_data.items():
                    if section not in merged_config:
                        merged_config[section] = {}
                    merged_config[section].update(options) # Overwrite defaults with existing values
                self.config_data = merged_config

            except (json.JSONDecodeError, FileNotFoundError, Exception) as e:
                print(f"Error leyendo o parseando '{self.filename}'. Creando/reinicializando con valores por defecto. Error: {e}")
                self.config_data = self._default_settings.copy() # Si hay error, usamos los valores por defecto
        else:
            print(f"Archivo de configuración '{self.filename}' no encontrado. Creando con valores por defecto.")
            self.config_data = self._default_settings.copy() # Si no existe, usamos los valores por defecto

        self._write_config_file() # Guardar la configuración (ahora un dict JSON)
        print(f"Configuración cargada/inicializada desde {self.filename}: {self.config_data}")


    def _write_config_file(self):
        """Guarda la configuración actual en el archivo JSON."""
        try:
            # os.makedirs(os.path.dirname(self.filename) or '.', exist_ok=True) # Ya no es necesario, _get_config_directory lo hace
            with open(self.filename, 'w', encoding='utf-8') as f:
                json.dump(self.config_data, f, indent=4) # Indent para legibilidad
        except Exception as e:
            print(f"Error al escribir el archivo de configuración '{self.filename}': {e}")


    def get_setting(self, section, key):
        """Obtiene un valor de la configuración. Usa los valores por defecto si no existe."""
        # Obtener el valor predeterminado si no existe
        default_value = self._default_settings.get(section, {}).get(key)
        # Retornar el valor del config_data o el predeterminado
        return self.config_data.get(section, {}).get(key, default_value)


    def set_setting(self, section, key, value):
        """Establece un valor en la configuración y lo guarda."""
        if section not in self.config_data:
            self.config_data[section] = {}
        self.config_data[section][key] = value
        self._write_config_file()

    def load_locales(self, lang_code):
        """Carga los textos de localización para el idioma especificado."""
        locale_file = os.path.join(self.locales_path, f"{lang_code}.json")
        try:
            with open(locale_file, 'r', encoding='utf-8') as f:
                self.current_locales = json.load(f)
            print(f"Locales cargados: {lang_code}.json")
        except FileNotFoundError:
            print(f"Advertencia: Archivo de locales '{locale_file}' no encontrado. Usando inglés por defecto.")
            self.current_locales = self._get_default_locales()
        except json.JSONDecodeError as e:
            print(f"Error decodificando el archivo de locales '{locale_file}': {e}. Usando inglés por defecto.")
            self.current_locales = self._get_default_locales()

    def _get_default_locales(self):
        """Retorna un diccionario con los textos de locales por defecto (inglés)."""
        return {
            "title": "SV R.E.P.O Save Manager",
            "backup_now": "Create Backup",
            "restore": "Restore Backup",
            "select_backup_folder": "Select Backup Folder",
            "folder_selected_success": "Backup folder selected successfully!",
            "backup_success": "Backup created successfully in:",
            "backup_error": "An error occurred during backup:",
            "no_saves_found": "No saves found to backup.",
            "select_backup": "Select Saves to Backup",
            "select_backup_error": "You must select at least one save.",
            "accept": "Accept",
            "restore_success": "Backup restored to:",
            "restore_error": "An error occurred restoring backup:",
            "loading": "Processing, please wait...",
            "auto_backup_check": "Enable automatic backup",
            "auto_backup_interval": "Backup every:",
            "minutes": "minutes",
            "invalid_input": "Invalid Input",
            "interval_must_be_positive": "Interval must be a positive integer.",
            "auto_backup_warning_title": "Automatic Backup Warning",
            "invalid_interval_stop": "Invalid automatic backup interval ({0}). Stopping thread.",
            "unexpected_error_auto": "An unexpected error occurred in the automatic backup loop:",
            "auto_backup_success": "Automatic backup created in:",
            "auto_backup_error_title": "Automatic Backup Error",
            "auto_backup_error": "Automatic backup error:",
            "no_saves_selected_auto": "No saves selected for automatic backup. Please select some in settings.",
            "select_auto_backup_games": "Select Games for Automatic Backup",
            "change_auto_backup_selection_title": "Change Automatic Backup Selection",
            "change_auto_backup_selection_question": "Do you want to change the selected saves for automatic backup? (Select 'No' to use current and activate)", # <--- ESTA ES LA CLAVE FALTANTE
            "cancel": "Cancel",
            "exit_confirm_title": "Confirm Exit",
            "exit_warning_auto_backup": "Automatic backup is enabled. If you close the program, automatic backups will NOT be performed.\n\nDo you want to exit anyway?",
            "auto_backup_timer_off": "Automatic backup disabled.",
            "auto_backup_next_in": "Next backup in: {0:02d}:{1:02d} (min:sec)",
            "auto_backup_timer_running": "Performing backup...",
            "auto_backup_first_time_select": "Automatic backup is enabled, but no games are selected. Please select the games to backup.",
            "auto_backup_info_title": "Automatic Backup Information"
        }