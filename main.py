import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog, messagebox
import threading
import time
import os
import json # Aunque ConfigManager ahora maneja JSON, seguimos usándolo para otras operaciones.
from PIL import Image, ImageTk
import sys

# Importar las clases y funciones de los módulos dentro de 'utils'
from utils.config_manager import ConfigManager
from utils import backup_manager # Asegúrate de que backup_manager exista y sea funcional

# === Funciones de Utilidad de Ruta (para PyInstaller) ===
def resource_path(relative_path):
    """Obtiene la ruta absoluta para el recurso, para PyInstaller."""
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

# === CONFIG INICIAL ===
# Crear una instancia de ConfigManager. El nombre del archivo ahora será "config.json" por defecto.
# Pasamos el nombre de la aplicación para que ConfigManager sepa dónde crear la carpeta de configuración.
config_manager_instance = ConfigManager(app_name="SV_REPO_Save_Manager", filename="config.json", locales_path=resource_path("locales"))

# Variables globales que almacenan los valores de configuración obtenidos del ConfigManager
# Accedemos directamente a los valores ya parseados por ConfigManager.
idioma_actual = config_manager_instance.get_setting('General', 'language')
modo_actual_ctk = config_manager_instance.get_setting('General', 'appearance_mode')

# La ruta de backup se inicializa aquí o se obtiene desde el config_manager
ruta_backup_inicial = config_manager_instance.get_setting('Backup', 'ruta_backup')
if not ruta_backup_inicial or not os.path.exists(ruta_backup_inicial):
    detected_save_path = backup_manager.obtener_ruta_saves()
    if detected_save_path:
        ruta_backup_inicial = detected_save_path
        config_manager_instance.set_setting("Backup", "ruta_backup", detected_save_path)
    else:
        ruta_backup_inicial = os.path.expanduser("~") # Fallback seguro
        config_manager_instance.set_setting("Backup", "ruta_backup", os.path.expanduser("~"))


ctk.set_appearance_mode(modo_actual_ctk)
ctk.set_default_color_theme("dark-blue")

# current_texts ahora se carga directamente desde la instancia de ConfigManager
current_texts = config_manager_instance.current_locales

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
credits_label = None # Se mantiene tu credits_label original
lbl_timer_auto_backup = None # Nueva etiqueta para el timer
timer_auto_backup_var = None # Nueva variable para el texto del timer

# Ruta global para el icono de la ventana principal y pop-ups
ICON_PATH = resource_path("icon.ico")


# --- Funciones de la UI ---

# Nueva función para mostrar mensajes temporales

_timed_message_window = None # Variable global para controlar la ventana de mensaje temporal

def show_timed_message(message, duracion_ms=7000):
    """
    Muestra una notificación discreta en la esquina superior derecha de la pantalla (área total de monitores).
    No roba el foco.
    """
    global _timed_message_window

    # Si ya existe una ventana de mensaje, la cerramos para no tener múltiples
    if _timed_message_window and _timed_message_window.winfo_exists():
        _timed_message_window.destroy()

    _timed_message_window = ctk.CTkToplevel(root)
    _timed_message_window.overrideredirect(True)  # Elimina bordes y barra de título
    _timed_message_window.attributes('-topmost', False) # Desactiva "siempre encima" por defecto

    # Configura la apariencia del mensaje
    current_appearance_mode = ctk.get_appearance_mode()
    bg_color = "#333333" if current_appearance_mode == "Dark" else "#EEEEEE"
    text_color = "#FFFFFF" if current_appearance_mode == "Dark" else "#000000"

    _timed_message_window.configure(fg_color=bg_color, corner_radius=10)
    _timed_message_window.attributes('-alpha', 0.9) # Semi-transparente

    # Contenido del mensaje
    label_mensaje = ctk.CTkLabel(
        _timed_message_window,
        text=message,
        font=ctk.CTkFont(size=14, weight="bold"),
        text_color=text_color,
        wraplength=300, # Para que el texto se ajuste
        justify="center"
    )
    label_mensaje.pack(padx=20, pady=10)

    # Posicionar en la esquina superior derecha de la PANTALLA TOTAL
    _timed_message_window.update_idletasks() # Asegúrate de que tenga sus dimensiones correctas
    notificacion_width = _timed_message_window.winfo_width()
    notificacion_height = _timed_message_window.winfo_height()

    # Obtener el ancho y alto total de la pantalla combinada
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight() # No se usa directamente para la posición Y, pero es útil

    # Margen para que no quede pegado al borde
    margin_x = 20 # Margen desde el lado derecho
    margin_y = 20 # Margen desde la parte superior

    # Calcular la posición x e y de la ventana de notificación
    # x = (ancho total de pantalla) - (ancho de notificación) - (margen)
    # y = (margen)
    x = screen_width - notificacion_width - margin_x
    y = margin_y

    _timed_message_window.geometry(f"+{x}+{y}")

    # Opcional: Asegúrate de que no tenga un ícono en la barra de tareas (solo Windows)
    if sys.platform == "win32":
        _timed_message_window.wm_attributes("-toolwindow", True)
        # Podríamos intentar hacerla siempre-encima si no roba foco, pero a veces interfiere.
        #_timed_message_window.attributes('-topmost', True)


    # Cierra la ventana automáticamente después de un tiempo
    _timed_message_window.after(duracion_ms, _timed_message_window.destroy)

def update_ui_texts():
    """Actualiza todos los textos y las imágenes de la interfaz de usuario."""
    global current_texts, idioma_actual, img_bandera_ctk

    # Recargar textos del idioma actual usando la instancia de ConfigManager
    config_manager_instance.load_locales(idioma_actual)
    current_texts = config_manager_instance.current_locales

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
    # Se mantienen tus créditos originales
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
        config_manager_instance.set_setting("Backup", "ruta_backup", path) # Guardar en el archivo config.json
        show_timed_message(current_texts.get("folder_selected_success", "Carpeta de backup seleccionada con éxito!"))


def create_backup_thread_wrapper(selected_saves, destination_path):
    try:
        show_loading_window()
        backup_manager.crear_backup_zip(selected_saves, destination_path)
        root.after(0, hide_loading_window)
        # Usar la nueva función para mensajes temporales
        root.after(0, lambda: show_timed_message(
                                                f"{current_texts.get('backup_success','Backup creado correctamente en:')}\n{destination_path}"))
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
    default_folder = ruta_backup_var.get() # Usar la carpeta de backup configurada como initialdir
    if not os.path.exists(default_folder):
        default_folder = os.path.expanduser("~") # Fallback si la ruta configurada no existe

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
        root.after(0, lambda: show_timed_message(
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
    config_manager_instance.set_setting("General", "language", idioma_actual) # Guardar en el archivo config.json
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
    config_manager_instance.set_setting("General", "appearance_mode", new_mode) # Guardar en el archivo config.json
    update_ui_texts()

_auto_backup_thread_instance = None
_auto_backup_running_flag = False
_next_backup_time = 0 # Almacena el timestamp de la próxima ejecución

def update_auto_backup_timer_ui():
    """Actualiza la etiqueta del timer de backup automático."""
    global _next_backup_time

    if not backup_automatico_var.get() or not _auto_backup_running_flag:
        timer_auto_backup_var.set(current_texts.get("auto_backup_timer_off", "Backup automático deshabilitado."))
        lbl_timer_auto_backup.configure(text_color="gray")
        return

    time_left_seconds = max(0, int(_next_backup_time - time.time()))

    minutes = time_left_seconds // 60
    seconds = time_left_seconds % 60

    timer_text = current_texts.get("auto_backup_next_in", "Próximo backup en: {0:02d}:{1:02d} (min:seg)")
    timer_auto_backup_var.set(timer_text.format(minutes, seconds))

    if time_left_seconds < 60 and time_left_seconds > 0:
        lbl_timer_auto_backup.configure(text_color="orange")
    elif time_left_seconds == 0:
        timer_auto_backup_var.set(current_texts.get("auto_backup_timer_running", "Realizando backup..."))
        lbl_timer_auto_backup.configure(text_color="green")
    else:
        actual_ctk_mode = ctk.get_appearance_mode()
        text_color_for_current_mode = "white" if actual_ctk_mode == "Dark" else "black"
        lbl_timer_auto_backup.configure(text_color=text_color_for_current_mode)

    if time_left_seconds > 0 and _auto_backup_running_flag:
        root.after(1000, update_auto_backup_timer_ui)
    elif time_left_seconds == 0 and _auto_backup_running_flag:
        pass


def start_auto_backup_thread():
    """
    Inicia el hilo de backup automático si no está ya corriendo.
    Configura _next_backup_time para el primer intervalo.
    """
    global _auto_backup_thread_instance, _auto_backup_running_flag, _next_backup_time

    if _auto_backup_running_flag:
        return

    _auto_backup_running_flag = True
    current_interval = intervalo_minutos_var.get()

    _next_backup_time = time.time() + (current_interval * 60)
    root.after(0, update_auto_backup_timer_ui)

    def auto_backup_loop_worker():
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

                time_to_sleep = max(0, _next_backup_time - time.time())
                if time_to_sleep > 0:
                    time.sleep(time_to_sleep)

                if not (_auto_backup_running_flag and backup_automatico_var.get()):
                    break

                root.after(0, internal_auto_backup_logic)

                _next_backup_time = time.time() + (current_interval * 60)
                root.after(0, update_auto_backup_timer_ui)

            except Exception as e:
                root.after(0, lambda: messagebox.showerror(
                    current_texts.get("auto_backup_error_title", "Error en Backup Automático"),
                    current_texts.get("unexpected_error_auto", f"Ocurrió un error inesperado en el bucle de backup automático: {e}")
                ))
                break

        _auto_backup_running_flag = False
        root.after(0, update_auto_backup_timer_ui)

    def internal_auto_backup_logic():
        # Retrieve saves to backup from the config_manager instance (directamente como lista)
        saves_to_backup = config_manager_instance.get_setting("Backup", "partidas_auto_backup")

        if not saves_to_backup:
            root.after(0, lambda: show_timed_message(
                current_texts.get("auto_backup_warning_title", "Advertencia de Backup Automático") + ":\n" +
                current_texts.get("no_saves_selected_auto", "No hay partidas seleccionadas para el respaldo automático. Por favor, selecciona algunas en la configuración.")
            ))
            backup_automatico_var.set(False)
            toggle_auto_backup()
            return

        destination = ruta_backup_var.get()
        if not destination or not os.path.exists(destination):
            root.after(0, lambda: messagebox.showwarning(
                current_texts.get("auto_backup_warning_title", "Advertencia de Backup Automático"),
                current_texts.get("select_backup_folder", "Debes seleccionar una carpeta de backup válida para el backup automático.")
            ))
            backup_automatico_var.set(False)
            toggle_auto_backup()
            return

        try:
            backup_manager.crear_backup_zip(saves_to_backup, destination)
            root.after(0, lambda: show_timed_message(
                                   f"{current_texts.get('auto_backup_success', 'Backup automático creado en:')} {destination} (a las {time.strftime('%H:%M:%S')})"))
        except Exception as e:
            root.after(0, lambda: messagebox.showerror(current_texts.get("auto_backup_error_title", "Error en Backup Automático"),
                                                       f"{current_texts.get('auto_backup_error', 'Error en backup automático:')} {e}"))

    _auto_backup_thread_instance = threading.Thread(target=auto_backup_loop_worker, daemon=True)
    _auto_backup_thread_instance.start()


def show_select_auto_backup_dialog():
    """Muestra un diálogo para que el usuario seleccione las partidas para el backup automático."""
    saves_list = backup_manager.listar_partidas()
    if not saves_list:
        messagebox.showwarning(current_texts.get("auto_backup_warning_title", "Advertencia de Backup Automático"),
                               current_texts.get("no_saves_found", "No se encontraron partidas para respaldar."))
        backup_automatico_var.set(False)
        toggle_auto_backup()
        return

    dialog_window = ctk.CTkToplevel(root)
    dialog_window.title(current_texts.get("select_auto_backup_games", "Seleccionar partidas para backup automático"))
    dialog_window.geometry("350x460")
    dialog_window.grab_set()
    dialog_window.focus()
    dialog_window.transient(root)
    if os.path.exists(ICON_PATH):
        try:
            dialog_window.iconbitmap(ICON_PATH)
        except Exception as e:
            print(f"Error al cargar icono para ventana de selección de auto-backup: {e}")

    current_appearance_mode = ctk.get_appearance_mode()
    dialog_window.configure(fg_color="#1f1f1f" if current_appearance_mode == "Dark" else "#f0f0f0")

    checkbox_vars = {}
    # Obtener la lista de partidas seleccionadas directamente como una lista desde el JSON
    selected_for_auto = config_manager_instance.get_setting("Backup", "partidas_auto_backup") or []

    scrollable_frame = ctk.CTkScrollableFrame(dialog_window, width=330, height=380, fg_color="transparent")
    scrollable_frame.pack(padx=10, pady=10, fill="both", expand=True)

    for save in saves_list:
        is_selected = save in selected_for_auto
        var = tk.BooleanVar(value=is_selected)
        chk = ctk.CTkCheckBox(scrollable_frame, text=save, variable=var)
        chk.pack(anchor="w", pady=2, padx=10)
        checkbox_vars[save] = var

    def confirm_selection_auto():
        selected_saves_list = [save for save, var in checkbox_vars.items() if var.get()]
        if not selected_saves_list:
            messagebox.showwarning(current_texts.get("select_auto_backup_games", "Seleccionar partidas"),
                                   current_texts.get("select_backup_error", "Debes seleccionar al menos una partida."))
            return

        # Guardar la lista directamente, ya que el JSON la maneja como lista
        config_manager_instance.set_setting("Backup", "partidas_auto_backup", selected_saves_list)
        dialog_window.destroy()

        start_auto_backup_thread()

    def cancel_selection_auto():
        backup_automatico_var.set(False)
        toggle_auto_backup()
        dialog_window.destroy()

    confirm_button = ctk.CTkButton(dialog_window, text=current_texts.get("accept", "Aceptar"), command=confirm_selection_auto,
                                   fg_color=("#EAEAEA", "#333333"), hover_color=("#D5D5D5", "#444444"))
    confirm_button.pack(side="left", padx=(10, 5), pady=10)

    cancel_button = ctk.CTkButton(dialog_window, text=current_texts.get("cancel", "Cancelar"), command=cancel_selection_auto,
                                   fg_color=("#EAEAEA", "#333333"), hover_color=("#D5D5D5", "#444444"))
    cancel_button.pack(side="right", padx=(5, 10), pady=10)

    dialog_window.protocol("WM_DELETE_WINDOW", cancel_selection_auto)


def toggle_auto_backup():
    """
    Gestiona el estado del checkbox de backup automático.
    Guarda la configuración y activa/desactiva el hilo según sea necesario.
    """
    global _auto_backup_running_flag

    # Update config.json with the current state of the checkbox (booleano directo)
    config_manager_instance.set_setting("Backup", "automatico", backup_automatico_var.get())

    try:
        new_interval = int(intervalo_minutos_var.get())
        if new_interval > 0:
            # Guardar el entero directamente
            config_manager_instance.set_setting("Backup", "intervalo_minutos", new_interval)
        else:
            raise ValueError("Intervalo debe ser un número positivo.")
    except ValueError:
        # Revert to last valid interval from config if input is invalid
        default_interval = config_manager_instance.get_setting('Backup', 'intervalo_minutos') # Leer el entero
        if default_interval is None: default_interval = 5 # Fallback si no existe en el JSON
        intervalo_minutos_var.set(default_interval)
        messagebox.showwarning(current_texts.get("invalid_input", "Entrada inválida"),
                               current_texts.get("interval_must_be_positive", "El intervalo debe ser un número entero y positivo."))
        # If interval is invalid, auto-backup cannot be active
        if backup_automatico_var.get():
            backup_automatico_var.set(False)
            config_manager_instance.set_setting("Backup", "automatico", False) # Guardar booleano
            _auto_backup_running_flag = False
            root.after(0, update_auto_backup_timer_ui)
            return

    # No need to save ruta_backup here, as select_backup_folder already handles it

    if backup_automatico_var.get():
        # Leer la lista directamente
        selected_for_auto = config_manager_instance.get_setting("Backup", "partidas_auto_backup") or []

        if not selected_for_auto:
            show_select_auto_backup_dialog()
        elif messagebox.askyesno(
            current_texts.get("change_auto_backup_selection_title", "Cambiar selección de backup automático"),
            current_texts.get("change_auto_backup_selection_question", "¿Deseas cambiar las partidas seleccionadas para el backup automático? (Selecciona 'No' para usar las actuales y activar)")
        ):
            show_select_auto_backup_dialog()
        else:
            # If the user chooses not to change the selection, just start the thread
            if _auto_backup_running_flag:
                _auto_backup_running_flag = False
                if _auto_backup_thread_instance and _auto_backup_thread_instance.is_alive():
                    _auto_backup_thread_instance.join(timeout=1)
            start_auto_backup_thread()
    else:
        _auto_backup_running_flag = False
        root.after(0, update_auto_backup_timer_ui)


# --- Función para manejar el cierre de la ventana ---
def on_closing():
    global _auto_backup_running_flag
    if backup_automatico_var.get() and _auto_backup_running_flag:
        if messagebox.askyesno(
            current_texts.get("exit_confirm_title", "Confirmar salida"),
            current_texts.get("exit_warning_auto_backup", "El backup automático está habilitado. Si cierras el programa, los backups automáticos NO se realizarán.\n\n¿Deseas salir de todas formas?")
        ):
            _auto_backup_running_flag = False
            if _auto_backup_thread_instance and _auto_backup_thread_instance.is_alive():
                _auto_backup_thread_instance.join(timeout=2)
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
backup_automatico_var = tk.BooleanVar(master=root, value=config_manager_instance.get_setting("Backup", "automatico"))
ruta_backup_var = tk.StringVar(master=root, value=ruta_backup_inicial) # Usa la ruta inicial calculada
intervalo_minutos_var = tk.IntVar(master=root, value=config_manager_instance.get_setting("Backup", "intervalo_minutos"))

# === Inicializar timer_auto_backup_var con el texto correcto ===
timer_auto_backup_var = tk.StringVar(master=root, value="")
if not backup_automatico_var.get():
    timer_auto_backup_var.set(current_texts.get("auto_backup_timer_off", "Backup automático deshabilitado."))


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
modo_btn = ctk.CTkButton(top_frame, width=50, command=toggle_appearance_mode,
                          fg_color="transparent", hover_color=("#EAEAEA", "#2A2D2E"))
modo_btn.pack(side="right", padx=(10, 0))

language_options = list(idiomas_banderas.keys())
idioma_menu = ctk.CTkOptionMenu(top_frame, values=language_options,
                                 command=change_language_optionmenu,
                                 width=40,
                                 dropdown_fg_color=("#EAEAEA", "#333333"),
                                 )
idioma_menu.set(idioma_actual)
idioma_menu.pack(side="right", padx=5)

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

lbl_timer_auto_backup = ctk.CTkLabel(center_frame, textvariable=timer_auto_backup_var, font=("Arial", 12, "bold"))
lbl_timer_auto_backup.pack(pady=(10, 0))


def on_interval_entry_change(*args):
    global _auto_backup_running_flag, _auto_backup_thread_instance
    try:
        new_val = int(intervalo_minutos_var.get())
        if new_val > 0:
            config_manager_instance.set_setting("Backup", "intervalo_minutos", new_val) # Guardar entero
            if backup_automatico_var.get() and _auto_backup_running_flag:
                # Si el backup auto está activo y el intervalo cambia, reinicia el hilo
                _auto_backup_running_flag = False
                if _auto_backup_thread_instance and _auto_backup_thread_instance.is_alive():
                    _auto_backup_thread_instance.join(timeout=0.1) # Espera un poco para que termine limpiamente
                start_auto_backup_thread() # Inicia uno nuevo con el nuevo intervalo
        else:
            messagebox.showwarning(current_texts.get("invalid_input", "Entrada inválida"),
                                   current_texts.get("interval_must_be_positive", "El intervalo debe ser un número positivo."))
            default_interval = config_manager_instance.get_setting('Backup', 'intervalo_minutos')
            if default_interval is None: default_interval = 5 # Fallback si no existe en el JSON
            intervalo_minutos_var.set(default_interval)
    except ValueError:
        pass # Ignora si el usuario está escribiendo un valor no numérico temporalmente
intervalo_minutos_var.trace_add("write", on_interval_entry_change)


# --- Marco para los créditos en la parte inferior ---
bottom_frame = ctk.CTkFrame(root, fg_color="transparent")
bottom_frame.pack(side="bottom", fill="x", padx=10, pady=5)

credits_label = ctk.CTkLabel(bottom_frame, text="By: elerickmj | TikTok: @elerickmj | Colab: @jasontorresb | Chorestudio®", font=("Arial", 14))
credits_label.pack(side="left", padx=5)


# --- Inicio y bucle principal ---
root.update_idletasks()

# Llamar a update_ui_texts una vez al inicio para establecer todos los textos y el estado inicial del modo.
# Esto es importante porque algunas configuraciones como el modo de apariencia pueden afectar los colores iniciales.
root.after(100, update_ui_texts)

# Después de que la UI se haya inicializado y los textos estén cargados,
# verificar si el backup automático debe iniciar.
if backup_automatico_var.get():
    # Leer la lista directamente
    selected_for_auto = config_manager_instance.get_setting("Backup", "partidas_auto_backup") or []

    if selected_for_auto:
        start_auto_backup_thread()
    else:
        # Puesto que auto_backup_var ya es True, necesitamos mostrar el diálogo
        # para que el usuario seleccione las partidas.
        messagebox.showinfo(current_texts.get("auto_backup_info_title", "Información de Backup Automático"),
                             current_texts.get("auto_backup_first_time_select", "El backup automático está habilitado, pero no hay partidas seleccionadas. Por favor, selecciona las partidas para respaldar."))
        show_select_auto_backup_dialog()


root.mainloop()