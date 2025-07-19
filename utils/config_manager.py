import json
import os
import sys

# Define el nombre del archivo de configuración
CONFIG_FILE_NAME = "config.json"
APP_FOLDER_NAME = "SV_REPO_Save_Manager" # Un nombre único para tu carpeta dentro de AppData

def get_config_path():
    if sys.platform == "win32":
        app_data_path = os.getenv('APPDATA') 
        config_dir = os.path.join(app_data_path, APP_FOLDER_NAME)
    else:
        home_dir = os.path.expanduser("~")
        config_dir = os.path.join(home_dir, f".{APP_FOLDER_NAME.lower().replace(' ', '_')}")
    
    os.makedirs(config_dir, exist_ok=True)
    
    return os.path.join(config_dir, CONFIG_FILE_NAME)

def cargar_config():
    config_path = get_config_path()
    try:
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        print(f"Error al cargar la configuración desde {config_path}: {e}")
    return {}

def guardar_config(config_data):
    config_path = get_config_path()
    try:
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config_data, f, indent=4)
    except Exception as e:
        print(f"Error al guardar la configuración en {config_path}: {e}")