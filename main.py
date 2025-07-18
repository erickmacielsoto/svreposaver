import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog, messagebox
import threading
import time
import os
import json
from PIL import Image, ImageTk
import sys

# Importar las funciones de los módulos dentro de 'utils'
from utils import config_manager
from utils import backup_manager

# === Funciones de Utilidad de Ruta (para PyInstaller) ===
def resource_path(relative_path):
    """Obtiene la ruta absoluta para el recurso, para PyInstaller."""
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

# === CONFIG INICIAL ===
config = config_manager.cargar_config()
idioma_actual = config.get("idioma", "es")

modo_actual_ctk = config.get("appearance_mode", "System")
ctk.set_appearance_mode(modo_actual_ctk)
ctk.set_default_color_theme("dark-blue")

current_texts = {}

def load_locale_texts(code):
    locale_file_path = resource_path(os.path.join("locales", f"{code}.json"))
    try:
        with open(locale_file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        messagebox.showerror("Error de Carga de Idioma", f"Archivo de idioma no encontrado: {locale_file_path}")
        return {}
    except json.JSONDecodeError as e:
        messagebox.showerror("Error de Carga de Idioma", f"Error al parsear JSON para '{code}' en '{locale_file_path}': {e}")
        return {}
    except Exception as e:
        messagebox.showerror("Error de Carga de Idioma", f"No se pudo cargar idioma '{code}' desde '{locale_file_path}': {e}")
        return {}

current_texts = load_locale_texts(idioma_actual)


# --- Archivos y carpetas ---
FLAGS_DIR = "flags"
IMG_DIR = "img" # Todas las imágenes excepto banderas aquí

# Idiomas disponibles y sus imágenes de bandera (con rutas ajustadas para resource_path)
idiomas_banderas = {
    "es": resource_path(os.path.join(FLAGS_DIR, "mx.png")),
    "en": resource_path(os.path.join(FLAGS_DIR, "en.png")),
    "pt": resource_path(os.path.join(FLAGS_DIR, "pt.png")),
    "it": resource_path(os.path.join(FLAGS_DIR, "it.png")),
    "de": resource_path(os.path.join(FLAGS_DIR, "de.png"))
}

# Cargar imágenes de MODO y BOTONES al inicio (usando resource_path)
img_sun_ctk = None
img_moon_ctk = None
folder_img_ctk = None
sync_img_ctk = None
data_recovery_img_ctk = None

# === INICIO DE CARGA DE IMÁGENES AL INICIO ===
try:
    path_light_mode = resource_path(os.path.join(IMG_DIR, "lightmode.png"))
    if os.path.exists(path_light_mode):
        img_sun_pil = Image.open(path_light_mode).resize((24,24), Image.LANCZOS)
        img_sun_ctk = ctk.CTkImage(light_image=img_sun_pil, dark_image=img_sun_pil, size=(24,24))
except Exception as e:
    messagebox.showerror("Error de Carga de Imagen", f"No se pudo cargar lightmode.png: {e}")

try:
    path_dark_mode = resource_path(os.path.join(IMG_DIR, "darkmode.png"))
    if os.path.exists(path_dark_mode):
        img_moon_pil = Image.open(path_dark_mode).resize((24,24), Image.LANCZOS)
        img_moon_ctk = ctk.CTkImage(light_image=img_moon_pil, dark_image=img_moon_pil, size=(24,24))
except Exception as e:
    messagebox.showerror("Error de Carga de Imagen", f"No se pudo cargar darkmode.png: {e}")

try:
    path_folder = resource_path(os.path.join(IMG_DIR, "folder.png"))
    if os.path.exists(path_folder):
        folder_img_pil = Image.open(path_folder).resize((24, 24), Image.LANCZOS)
        folder_img_ctk = ctk.CTkImage(light_image=folder_img_pil, dark_image=folder_img_pil, size=(24, 24))
except Exception as e:
    messagebox.showerror("Error de Carga de Imagen", f"No se pudo cargar folder.png: {e}")

try:
    path_sync = resource_path(os.path.join(IMG_DIR, "sync.png"))
    if os.path.exists(path_sync):
        sync_img_pil = Image.open(path_sync).resize((24, 24), Image.LANCZOS)
        sync_img_ctk = ctk.CTkImage(light_image=sync_img_pil, dark_image=sync_img_pil, size=(24, 24))
except Exception as e:
    messagebox.showerror("Error de Carga de Imagen", f"No se pudo cargar sync.png: {e}")

try:
    path_data_recovery = resource_path(os.path.join(IMG_DIR, "data-recovery.png"))
    if os.path.exists(path_data_recovery):
        data_recovery_img_pil = Image.open(path_data_recovery).resize((24, 24), Image.LANCZOS)
        data_recovery_img_ctk = ctk.CTkImage(light_image=data_recovery_img_pil, dark_image=data_recovery_img_pil, size=(24, 24))
except Exception as e:
    messagebox.showerror("Error de Carga de Imagen", f"No se pudo cargar data-recovery.png: {e}")
# === FIN DE CARGA DE IMÁGENES AL INICIO ===

# Variable global para la imagen de la bandera
img_bandera_ctk = None

# Variables globales para UI (declaradas aquí para asegurar existencia antes de asignación)
root = None
titulo = None
modo_btn = None
idioma_menu = None
bandera_lbl = None
btn_backup = None
btn_restaurar = None
btn_carpeta = None
lbl_ruta = None
chk_auto = None
lbl_min = None
entrada_min = None
lbl_mins = None
ventana_cargando = None
credits_label = None
lbl_timer_auto_backup = None # Nueva etiqueta para el timer
timer_auto_backup_var = None # Nueva variable para el texto del timer

# Ruta global para el icono de la ventana principal y pop-ups
ICON_PATH = resource_path("icon.ico")


# --- Funciones de la UI ---

# Nueva función para mostrar mensajes temporales
def show_timed_message(title, message, duration_ms=7000):
    """Muestra un mensaje en una ventana flotante que se cierra automáticamente."""
    
    # Si ya existe una ventana de mensaje, la cerramos para no tener múltiples
    global _timed_message_window
    if '_timed_message_window' in globals() and _timed_message_window and _timed_message_window.winfo_exists():
        _timed_message_window.destroy()

    _timed_message_window = ctk.CTkToplevel(root)
    _timed_message_window.geometry("350x150")
    _timed_message_window.title(title)
    _timed_message_window.attributes("-topmost", True) # Mantenerla siempre encima
    if os.path.exists(ICON_PATH):
        try:
            _timed_message_window.iconbitmap(ICON_PATH)
        except Exception as e:
            # Puedes cambiar esto a un print si no quieres un messagebox por cada error de icono temporal
            print(f"Error al cargar icono para ventana de mensaje temporal: {e}")

    # Centrar la ventana temporal
    root.update_idletasks() # Asegurarse de que las dimensiones de root estén actualizadas
    root_x = root.winfo_x()
    root_y = root.winfo_y()
    root_width = root.winfo_width()
    root_height = root.winfo_height()

    msg_width = 350
    msg_height = 150
    x_pos = root_x + (root_width // 2) - (msg_width // 2)
    y_pos = root_y + (root_height // 2) - (msg_height // 2)
    _timed_message_window.geometry(f"{msg_width}x{msg_height}+{x_pos}+{y_pos}")

    label_message = ctk.CTkLabel(_timed_message_window, text=message, wraplength=300, justify="center")
    label_message.pack(expand=True, fill="both", padx=20, pady=20)
    
    # Programar el cierre automático
    _timed_message_window.after(duration_ms, _timed_message_window.destroy)


def update_ui_texts():
    """Actualiza todos los textos y las imágenes de la interfaz de usuario."""
    global current_texts, idioma_actual, img_bandera_ctk
    
    root.title(current_texts.get("title", "SV R.E.P.O Save Manager"))
    titulo.configure(text=current_texts.get("title", "SV R.E.P.O Save Manager"))
    btn_backup.configure(text=current_texts.get("backup_now", "Crear Backup"))
    btn_restaurar.configure(text=current_texts.get("restore", "Restaurar Backup"))
    chk_auto.configure(text=current_texts.get("auto_backup_check", "Habilitar backup automático"))
    lbl_min.configure(text=current_texts.get("auto_backup_interval", "Backup cada:"))
    lbl_mins.configure(text=current_texts.get("minutes", "minutos"))

    # --- Lógica para el icono del botón de modo (Sol/Luna) ---
    actual_ctk_mode = ctk.get_appearance_mode() 
    
    if actual_ctk_mode == "Dark":
        if img_sun_ctk:
            modo_btn.configure(image=img_sun_ctk, text="")
        else:
            modo_btn.configure(image=None, text="☀️") 
    else: # Light (o System que se resolvió a Light)
        if img_moon_ctk:
            modo_btn.configure(image=img_moon_ctk, text="")
        else:
            modo_btn.configure(image=None, text="🌙") 
    
    # Forzar la actualización visual del botón de modo
    if modo_btn: # Asegurarse de que el botón existe antes de intentar actualizarlo
        modo_btn.update_idletasks() 

    # Configurar íconos de los botones de acción
    if sync_img_ctk:
        btn_backup.configure(image=sync_img_ctk, compound="left")
    else:
        btn_backup.configure(image=None, compound="left")

    if data_recovery_img_ctk:
        btn_restaurar.configure(image=data_recovery_img_ctk, compound="left")
    else:
        btn_restaurar.configure(image=None, compound="left")


    # --- Ajuste de color de texto para modo claro/oscuro ---
    text_color_for_current_mode = "white" if actual_ctk_mode == "Dark" else "black"
    
    titulo.configure(text_color=text_color_for_current_mode)
    btn_backup.configure(text_color=text_color_for_current_mode)
    btn_restaurar.configure(text_color=text_color_for_current_mode)
    chk_auto.configure(text_color=text_color_for_current_mode)
    lbl_min.configure(text_color=text_color_for_current_mode)
    lbl_mins.configure(text_color=text_color_for_current_mode)
    lbl_ruta.configure(text_color=text_color_for_current_mode)
    if credits_label: 
        credits_label.configure(text_color=text_color_for_current_mode)
    if lbl_timer_auto_backup: # Actualizar color del timer
        lbl_timer_auto_backup.configure(text_color=text_color_for_current_mode)
    
    # !!! IMPORTANTE: Actualizar el mensaje del timer de backup automático al cambiar de idioma
    update_auto_backup_timer_ui()

    # Actualizar la bandera con imágenes
    try:
        flag_image_path = idiomas_banderas.get(idioma_actual)
        if flag_image_path and os.path.exists(flag_image_path):
            img_flag_pil = Image.open(flag_image_path).resize((28,18), Image.LANCZOS)
            img_bandera_ctk = ctk.CTkImage(light_image=img_flag_pil, dark_image=img_flag_pil, size=(28,18))
            bandera_lbl.configure(image=img_bandera_ctk, text="")
        else:
            bandera_lbl.configure(image=None, text="") 
    except Exception as e:
        messagebox.showerror("Error de Carga de Bandera", f"Ocurrió un error al cargar la bandera para '{idioma_actual}': {e}")
        bandera_lbl.configure(image=None, text="") 

    # Actualizar el texto de la ventana de carga si está abierta
    if ventana_cargando and ventana_cargando.winfo_exists():
        for widget in ventana_cargando.winfo_children():
            if isinstance(widget, ctk.CTkLabel):
                widget.configure(text=current_texts.get("loading", "Procesando, espere..."))
        ventana_cargando.title(current_texts.get("loading", "Por favor espere"))


def select_backup_folder():
    path = filedialog.askdirectory(title=current_texts.get("select_backup_folder", "Selecciona carpeta para guardar backup"))
    if path:
        ruta_backup_var.set(path)
        config["ruta_backup"] = path
        config_manager.guardar_config(config)

def create_backup_thread_wrapper(selected_saves, destination_path):
    try:
        show_loading_window()
        backup_manager.crear_backup_zip(selected_saves, destination_path)
        root.after(0, hide_loading_window)
        # Usar la nueva función para mensajes temporales
        root.after(0, lambda: show_timed_message(current_texts.get("backup_now", "Backup"),
                                                   f"{current_texts.get('backup_success','Backup creado correctamente en:')}:\n{destination_path}"))
    except Exception as e:
        root.after(0, hide_loading_window)
        root.after(0, lambda: messagebox.showerror(current_texts.get("backup_now", "Backup"),
                                                    f"{current_texts.get('backup_error','Ocurrió un error haciendo backup:')}\n{e}"))

def create_backup_dialog():
    saves_list = backup_manager.listar_partidas()
    if not saves_list:
        messagebox.showwarning(current_texts.get("backup_now", "Backup"),
                               current_texts.get("no_saves_found", "No se encontraron partidas para respaldar."))
        return

    dialog_window = ctk.CTkToplevel(root)
    dialog_window.title(current_texts.get("select_backup", "Seleccionar partidas a respaldar"))
    dialog_window.geometry("350x460")
    dialog_window.grab_set()
    dialog_window.focus()
    dialog_window.transient(root)
    if os.path.exists(ICON_PATH):
        try:
            dialog_window.iconbitmap(ICON_PATH)
        except Exception as e:
            messagebox.showerror("Error de Icono de Diálogo", f"No se pudo cargar icon.ico para la ventana de diálogo: {e}")
    
    current_appearance_mode = ctk.get_appearance_mode()
    dialog_window.configure(fg_color="#1f1f1f" if current_appearance_mode == "Dark" else "#f0f0f0")

    checkbox_vars = []
    scrollable_frame = ctk.CTkScrollableFrame(dialog_window, width=330, height=380, fg_color="transparent") 
    scrollable_frame.pack(padx=10, pady=10, fill="both", expand=True)

    for save in saves_list:
        var = tk.BooleanVar(value=True)
        chk = ctk.CTkCheckBox(scrollable_frame, text=save, variable=var)
        chk.pack(anchor="w", pady=2, padx=10)
        checkbox_vars.append(var)

    def confirm_selection():
        selected_saves_list = [saves_list[i] for i, v in enumerate(checkbox_vars) if v.get()]
        if not selected_saves_list:
            messagebox.showwarning(current_texts.get("select_backup", "Seleccionar"),
                                   current_texts.get("select_backup_error", "Debes seleccionar al menos una partida."))
            return
        dialog_window.destroy()
        destination = ruta_backup_var.get() or backup_manager.obtener_ruta_saves()
        threading.Thread(target=create_backup_thread_wrapper, args=(selected_saves_list, destination), daemon=True).start()

    confirm_button = ctk.CTkButton(dialog_window, text=current_texts.get("accept", "Aceptar"), command=confirm_selection,
                                   fg_color=("#EAEAEA", "#333333"), hover_color=("#D5D5D5", "#444444"))
    confirm_button.pack(pady=10)

def restore_backup_ui():
    default_folder = backup_manager.obtener_ruta_saves()
    if not os.path.exists(default_folder):
        default_folder = os.path.expanduser("~")

    zip_file_path = filedialog.askopenfilename(
        title=current_texts.get("restore", "Seleccionar archivo ZIP de backup"),
        initialdir=default_folder,
        filetypes=[("Zip files", "*.zip")]
    )
    if not zip_file_path:
        return
    try:
        show_loading_window()
        restored_destination = backup_manager.restaurar_backup_zip(zip_file_path)
        root.after(0, hide_loading_window)
        # Usar la nueva función para mensajes temporales
        root.after(0, lambda: show_timed_message(current_texts.get("restore", "Restaurar"),
                                                   f"{current_texts.get('restore_success','Backup restaurado en:')}:\n{restored_destination}"))
    except Exception as e:
        root.after(0, hide_loading_window)
        root.after(0, lambda: messagebox.showerror(current_texts.get("restore", "Restaurar"),
                                                    f"{current_texts.get('restore_error','Ocurrió un error restaurando backup:')}\n{e}"))

def show_loading_window():
    global ventana_cargando
    if ventana_cargando and ventana_cargando.winfo_exists():
        return

    ventana_cargando = ctk.CTkToplevel(root)
    ventana_cargando.geometry("220x90")
    ventana_cargando.title(current_texts.get("loading", "Por favor espere"))
    ventana_cargando.grab_set()
    ventana_cargando.attributes("-topmost", True)
    if os.path.exists(ICON_PATH):
        try:
            ventana_cargando.iconbitmap(ICON_PATH)
        except Exception as e:
            messagebox.showerror("Error de Icono de Carga", f"No se pudo cargar icon.ico para la ventana de carga: {e}")

    root_x = root.winfo_x()
    root_y = root.winfo_y()
    root_width = root.winfo_width()
    root_height = root.winfo_height()

    loading_width = 220
    loading_height = 90
    x_pos = root_x + (root_width // 2) - (loading_width // 2)
    y_pos = root_y + (root_height // 2) - (loading_height // 2)
    ventana_cargando.geometry(f"{loading_width}x{loading_height}+{x_pos}+{y_pos}")

    label_loading = ctk.CTkLabel(ventana_cargando, text=current_texts.get("loading", "Procesando, espere..."))
    label_loading.pack(expand=True, fill="both", padx=20, pady=20)
    ventana_cargando.update_idletasks()

def hide_loading_window():
    global ventana_cargando
    if ventana_cargando and ventana_cargando.winfo_exists():
        ventana_cargando.grab_release()
        ventana_cargando.destroy()
        ventana_cargando = None

def change_language_optionmenu(choice):
    global idioma_actual, current_texts
    idioma_actual = choice
    config["idioma"] = idioma_actual
    config_manager.guardar_config(config)
    current_texts = load_locale_texts(idioma_actual)
    update_ui_texts() # Esta función ahora llamará a update_auto_backup_timer_ui

def toggle_appearance_mode():
    current_ctk_mode = ctk.get_appearance_mode()
    
    new_mode = ""
    if current_ctk_mode == "Light":
        new_mode = "Dark"
    elif current_ctk_mode == "Dark":
        new_mode = "Light"
    elif current_ctk_mode == "System": 
        system_actual_mode = root._get_appearance_mode() 
        new_mode = "Light" if system_actual_mode == "Dark" else "Dark"

    ctk.set_appearance_mode(new_mode)
    config["appearance_mode"] = new_mode 
    config_manager.guardar_config(config)
    update_ui_texts() 

_auto_backup_thread_instance = None
_auto_backup_running_flag = False 
_next_backup_time = 0 # Almacena el timestamp de la próxima ejecución
_timed_message_window = None # Variable global para controlar la ventana de mensaje temporal

def update_auto_backup_timer_ui():
    """Actualiza la etiqueta del timer de backup automático."""
    global _next_backup_time

    if not backup_automatico_var.get() or not _auto_backup_running_flag:
        # Aquí es donde se establece el mensaje cuando el backup automático está deshabilitado
        timer_auto_backup_var.set(current_texts.get("auto_backup_timer_off", "Backup automático deshabilitado."))
        lbl_timer_auto_backup.configure(text_color="gray") # Color más tenue cuando está inactivo
        return
    
    # Calcular tiempo restante
    time_left_seconds = max(0, int(_next_backup_time - time.time()))
    
    minutes = time_left_seconds // 60
    seconds = time_left_seconds % 60
    
    timer_text = current_texts.get("auto_backup_next_in", "Próximo backup en: {0:02d}:{1:02d} (min:seg)")
    timer_auto_backup_var.set(timer_text.format(minutes, seconds))

    # Cambiar color basado en el tiempo restante (opcional, para énfasis)
    if time_left_seconds < 60: # Menos de 1 minuto, color de advertencia
        lbl_timer_auto_backup.configure(text_color="orange")
    else:
        # Resetear al color por defecto del modo actual
        actual_ctk_mode = ctk.get_appearance_mode()
        text_color_for_current_mode = "white" if actual_ctk_mode == "Dark" else "black"
        lbl_timer_auto_backup.configure(text_color=text_color_for_current_mode)
    
    # Reprogramar la actualización
    if time_left_seconds > 0 and _auto_backup_running_flag:
        root.after(1000, update_auto_backup_timer_ui) # Actualizar cada segundo
    elif time_left_seconds == 0 and _auto_backup_running_flag:
        # Si el tiempo llegó a 0 y el backup aún debe correr, actualizar para reflejar la copia
        timer_auto_backup_var.set(current_texts.get("auto_backup_timer_running", "Realizando backup..."))
        lbl_timer_auto_backup.configure(text_color="green")


def start_auto_backup_thread():
    global _auto_backup_thread_instance, _auto_backup_running_flag, _next_backup_time

    if _auto_backup_running_flag: 
        return

    _auto_backup_running_flag = True 

    def auto_backup_loop():
        global _auto_backup_running_flag, _next_backup_time
        while _auto_backup_running_flag and backup_automatico_var.get():
            try:
                current_interval = intervalo_minutos_var.get()
                if current_interval <= 0:
                    root.after(0, lambda: messagebox.showwarning(
                        current_texts.get("auto_backup_warning_title", "Advertencia de Backup Automático"),
                        current_texts.get("invalid_interval_stop", f"Intervalo de backup automático inválido ({current_interval}). Deteniendo hilo.")
                    ))
                    break 

                _next_backup_time = time.time() + (current_interval * 60)
                root.after(0, update_auto_backup_timer_ui) 

                time.sleep(current_interval * 60)

                if _auto_backup_running_flag and backup_automatico_var.get():
                    root.after(0, internal_auto_backup_logic)
                else:
                    break 
            except Exception as e:
                root.after(0, lambda: messagebox.showerror(
                    current_texts.get("auto_backup_error_title", "Error en Backup Automático"),
                    current_texts.get("unexpected_error_auto", f"Ocurrió un error inesperado en el bucle de backup automático: {e}")
                ))
                break 
        _auto_backup_running_flag = False 
        root.after(0, update_auto_backup_timer_ui) 

    def internal_auto_backup_logic():
        saves_to_backup = backup_manager.listar_partidas()
        if not saves_to_backup:
            root.after(0, lambda: messagebox.showwarning(
                current_texts.get("auto_backup_warning_title", "Advertencia de Backup Automático"), 
                current_texts.get("no_saves_found_auto", "No se encontraron partidas para respaldo automático.")
            ))
            return

        destination = ruta_backup_var.get()
        if not destination:
            destination = backup_manager.obtener_ruta_saves()
        
        try:
            backup_manager.crear_backup_zip(saves_to_backup, destination)
            # Usar la nueva función para mensajes temporales
            root.after(0, lambda: show_timed_message(current_texts.get("auto_backup_success_title", "Backup Automático"), 
                                 f"{current_texts.get('auto_backup_success', 'Backup automático creado en:')} {destination} (a las {time.strftime('%H:%M:%S')})"))
        except Exception as e:
            root.after(0, lambda: messagebox.showerror(current_texts.get("auto_backup_error_title", "Error en Backup Automático"), 
                                 f"{current_texts.get('auto_backup_error', 'Error en backup automático:')} {e}"))

    _auto_backup_thread_instance = threading.Thread(target=auto_backup_loop, daemon=True)
    _auto_backup_thread_instance.start()
    root.after(0, update_auto_backup_timer_ui)


def toggle_auto_backup():
    global _auto_backup_running_flag

    config["backup_automatico"] = backup_automatico_var.get()
    try:
        new_interval = int(intervalo_minutos_var.get())
        if new_interval > 0:
            config["intervalo_minutos"] = new_interval
        else:
            raise ValueError("Intervalo debe ser un número positivo.")
    except ValueError:
        config["intervalo_minutos"] = 5
        intervalo_minutos_var.set(5)
        messagebox.showwarning(current_texts.get("invalid_input", "Entrada inválida"),
                               current_texts.get("interval_must_be_number", "El intervalo debe ser un número entero y positivo."))

    config["ruta_backup"] = ruta_backup_var.get()
    config_manager.guardar_config(config)
    
    if backup_automatico_var.get():
        start_auto_backup_thread()
    else:
        _auto_backup_running_flag = False 
        root.after(0, update_auto_backup_timer_ui) 


# --- Función para manejar el cierre de la ventana ---
def on_closing():
    global _auto_backup_running_flag
    if backup_automatico_var.get(): 
        if messagebox.askyesno(
            current_texts.get("exit_confirm_title", "Confirmar salida"),
            current_texts.get("exit_warning_auto_backup", "El backup automático está habilitado. Si cierras el programa, los backups automáticos NO se realizarán.\n\n¿Deseas salir de todas formas?")
        ):
            _auto_backup_running_flag = False 
            root.destroy() 
        else:
            pass 
    else:
        root.destroy() 

# --- Construcción de la UI ---
root = ctk.CTk()
root.geometry("750x500")
root.title(current_texts.get("title", "SV R.E.P.O Save Manager"))

# Asociar la función on_closing al protocolo de cierre de ventana
root.protocol("WM_DELETE_WINDOW", on_closing)


# Variables de control Tkinter
backup_automatico_var = tk.BooleanVar(master=root, value=config.get("backup_automatico", False))
ruta_backup_var = tk.StringVar(master=root, value=config.get("ruta_backup", backup_manager.obtener_ruta_saves()))
intervalo_minutos_var = tk.IntVar(master=root, value=config.get("intervalo_minutos", 5))

# === MODIFICACIÓN CLAVE AQUÍ: Inicializar timer_auto_backup_var con el texto correcto ===
if backup_automatico_var.get():
    # Si está habilitado desde el inicio (según la config), el texto inicial será el del timer corriendo/próximo
    # pero el valor exacto se establecerá en la primera llamada a update_auto_backup_timer_ui
    timer_auto_backup_var = tk.StringVar(master=root, value="") 
else:
    # Si no está habilitado, establecer el mensaje de deshabilitado desde el inicio
    timer_auto_backup_var = tk.StringVar(master=root, value=current_texts.get("auto_backup_timer_off", "Backup automático deshabilitado."))


# Configurar el icono de la ventana principal usando icon.ico
if os.path.exists(ICON_PATH):
    try:
        root.iconbitmap(ICON_PATH)
    except Exception as e:
        messagebox.showerror("Error de Icono de Ventana", f"No se pudo cargar icon.ico para el icono de la ventana principal: {e}")


top_frame = ctk.CTkFrame(root, fg_color="transparent")
top_frame.pack(pady=10, fill="x", padx=20)

titulo = ctk.CTkLabel(top_frame, text=current_texts.get("title", "SV R.E.P.O Save Manager"), font=("Arial", 22))
titulo.pack(side="left")

# --- Alineación de elementos a la derecha en top_frame ---
# El orden de pack() importa para side="right": el último se pega más a la derecha.
# 1. Botón de modo (más a la derecha)
modo_btn = ctk.CTkButton(top_frame, width=50, command=toggle_appearance_mode, 
                         fg_color="transparent", hover_color=("#EAEAEA", "#2A2D2E")) 
modo_btn.pack(side="right", padx=(10, 0))

# 2. Selector de idioma - Sin fg_color transparente para el OptionMenu principal
language_options = list(idiomas_banderas.keys())
idioma_menu = ctk.CTkOptionMenu(top_frame, values=language_options,
                                 command=change_language_optionmenu,
                                 width=40,
                                 dropdown_fg_color=("#EAEAEA", "#333333"), 
                                 )
idioma_menu.set(idioma_actual)
idioma_menu.pack(side="right", padx=5)

# 3. Etiqueta para la bandera
bandera_lbl = ctk.CTkLabel(top_frame, text="") 
bandera_lbl.pack(side="right", padx=(0, 5))


center_frame = ctk.CTkFrame(root, fg_color="transparent")
center_frame.pack(pady=10, fill="both", expand=True)

# === ESTRUCTURA DE BOTONES PARA ALINEACIÓN VERTICAL Y HORIZONTAL ===

buttons_main_frame = ctk.CTkFrame(center_frame, fg_color="transparent")
buttons_main_frame.pack(pady=(0, 10)) 

create_backup_group_frame = ctk.CTkFrame(buttons_main_frame, fg_color="transparent")
create_backup_group_frame.pack(pady=(0, 5)) 

btn_backup = ctk.CTkButton(create_backup_group_frame, text=current_texts.get("backup_now", "Crear Backup"), command=create_backup_dialog,
                           fg_color=("#EAEAEA", "#333333"), hover_color=("#D5D5D5", "#444444"), 
                           image=sync_img_ctk, compound="left") 
btn_backup.pack(side="left", padx=(0, 2))

btn_carpeta = ctk.CTkButton(create_backup_group_frame, text="", image=folder_img_ctk, width=40, command=select_backup_folder,
                           fg_color=("#EAEAEA", "#333333"), hover_color=("#D5D5D5", "#444444")) 
btn_carpeta.pack(side="left", padx=(2, 0))


restore_backup_group_frame = ctk.CTkFrame(buttons_main_frame, fg_color="transparent")
restore_backup_group_frame.pack(pady=(5, 0)) 

btn_restaurar = ctk.CTkButton(restore_backup_group_frame, text=current_texts.get("restore", "Restaurar Backup"), command=restore_backup_ui,
                              fg_color=("#EAEAEA", "#333333"), hover_color=("#D5D5D5", "#444444"),
                              image=data_recovery_img_ctk, compound="left")
btn_restaurar.pack() 


lbl_ruta = ctk.CTkLabel(center_frame, textvariable=ruta_backup_var, wraplength=700)
lbl_ruta.pack(pady=5)

chk_auto = ctk.CTkCheckBox(center_frame, text=current_texts.get("auto_backup_check", "Habilitar backup automático"), variable=backup_automatico_var, command=toggle_auto_backup)
chk_auto.pack(pady=(10, 5))

frame_min = ctk.CTkFrame(center_frame, fg_color="transparent")
frame_min.pack(pady=5)

lbl_min = ctk.CTkLabel(frame_min, text=current_texts.get("auto_backup_interval", "Backup cada:"))
lbl_min.pack(side="left", padx=(0, 5))

entrada_min = ctk.CTkEntry(frame_min, textvariable=intervalo_minutos_var, width=50)
entrada_min.pack(side="left", padx=(0, 5))

lbl_mins = ctk.CTkLabel(frame_min, text=current_texts.get("minutes", "minutos"))
lbl_mins.pack(side="left")

# Nueva etiqueta para el timer del backup automático
lbl_timer_auto_backup = ctk.CTkLabel(center_frame, textvariable=timer_auto_backup_var, font=("Arial", 12, "bold"))
lbl_timer_auto_backup.pack(pady=(10, 0))


def on_interval_entry_change(*args):
    global _auto_backup_running_flag, _auto_backup_thread_instance 
    try:
        new_val = int(intervalo_minutos_var.get())
        if new_val > 0:
            config["intervalo_minutos"] = new_val
            config_manager.guardar_config(config)
            # Si el backup automático está activo, reiniciar el timer con el nuevo intervalo
            if backup_automatico_var.get() and _auto_backup_running_flag:
                _auto_backup_running_flag = False
                if _auto_backup_thread_instance and _auto_backup_thread_instance.is_alive():
                    _auto_backup_thread_instance.join(timeout=0.1) 
                start_auto_backup_thread() # Reiniciar con el nuevo intervalo
        else:
            messagebox.showwarning(current_texts.get("invalid_input", "Entrada inválida"),
                                   current_texts.get("interval_must_be_positive", "El intervalo debe ser un número positivo."))
    except ValueError:
        pass 
intervalo_minutos_var.trace_add("write", on_interval_entry_change)


# --- Marco para los créditos en la parte inferior ---
bottom_frame = ctk.CTkFrame(root, fg_color="transparent")
bottom_frame.pack(side="bottom", fill="x", padx=10, pady=5)

credits_label = ctk.CTkLabel(bottom_frame, text="By: elerickmj | TikTok: @elerickmj | Colab: @jasontorresb | Chorestudio®", font=("Arial", 14))
credits_label.pack(side="left", padx=5)


# --- Inicio y bucle principal ---
root.update_idletasks() 

root.after(100, update_ui_texts) 

# No necesitamos esta llamada aquí, ya que update_ui_texts la hace
# root.after(0, update_auto_backup_timer_ui) 

if backup_automatico_var.get():
    start_auto_backup_thread()

root.mainloop()