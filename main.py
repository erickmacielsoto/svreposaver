import customtkinter as ctk
import tkinter as tk # Necesario para BooleanVar, StringVar, IntVar
from tkinter import filedialog, messagebox # messagebox también se usa en main.py
import threading
import time
import os
import json # Necesario para cargar los archivos .json de los locales
from PIL import Image, ImageTk
import sys # Para resource_path

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
# Cargar configuración y textos al inicio
config = config_manager.cargar_config()
idioma_actual = config.get("idioma", "es")
modo_actual_ctk = config.get("appearance_mode", "System") # Usar un nombre diferente para evitar conflicto

# Aplicar modo y tema ANTES de inicializar CTk
ctk.set_appearance_mode(modo_actual_ctk)
ctk.set_default_color_theme("dark-blue")

# Variables globales para textos
current_texts = {}

# Funciones de carga de textos (usando resource_path)
def load_locale_texts(code):
    """Carga los textos de un idioma específico."""
    locale_file_path = resource_path(os.path.join("locales", f"{code}.json"))
    try:
        with open(locale_file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"ERROR: Archivo de idioma no encontrado: {locale_file_path}")
        return {}
    except json.JSONDecodeError as e:
        print(f"ERROR: Error al parsear JSON para '{code}' en '{locale_file_path}': {e}")
        return {}
    except Exception as e:
        print(f"ERROR: No se pudo cargar idioma '{code}' desde '{locale_file_path}': {e}")
        return {}

# Cargar los textos iniciales de la UI
current_texts = load_locale_texts(idioma_actual)


# --- Archivos y carpetas ---
FLAGS_DIR = "flags"
IMG_DIR = "img"

# Idiomas disponibles y sus imágenes de bandera (con rutas ajustadas para resource_path)
idiomas_banderas = {
    "es": resource_path(os.path.join(FLAGS_DIR, "mx.png")), # México para español
    "en": resource_path(os.path.join(FLAGS_DIR, "en.png")),
    "pt": resource_path(os.path.join(FLAGS_DIR, "pt.png")),
    "it": resource_path(os.path.join(FLAGS_DIR, "it.png")),
    "de": resource_path(os.path.join(FLAGS_DIR, "de.png"))
}

# Cargar imágenes al inicio (usando resource_path)
img_sun = None
img_moon = None
try:
    img_sun = Image.open(resource_path(os.path.join(IMG_DIR, "lightmode.png"))).resize((24,24), Image.LANCZOS)
    img_moon = Image.open(resource_path(os.path.join(IMG_DIR, "darkmode.png"))).resize((24,24), Image.LANCZOS)
except Exception as e:
    print(f"Error al cargar imágenes de modo: {e}")

img_sun_tk = None
img_moon_tk = None
if img_sun:
    img_sun_tk = ctk.CTkImage(light_image=img_sun, dark_image=img_sun, size=(24,24))
if img_moon:
    img_moon_tk = ctk.CTkImage(light_image=img_moon, dark_image=img_moon, size=(24,24))

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

# <<< MUEVE ESTAS LÍNEAS ABAJO, DESPUÉS DE `root = ctk.CTk()` >>>
# backup_automatico_var = tk.BooleanVar(value=config.get("backup_automatico", False))
# ruta_backup_var = tk.StringVar(value=config.get("ruta_backup", backup_manager.obtener_ruta_saves()))
# intervalo_minutos_var = tk.IntVar(value=config.get("intervalo_minutos", 5))


# --- Funciones de la UI ---
# ... (rest of your UI functions, they don't need to change) ...

def update_ui_texts():
    """Actualiza todos los textos de la interfaz de usuario."""
    global current_texts, idioma_actual, img_bandera_tk
    
    root.title(current_texts.get("title", "SV R.E.P.O Save Manager"))
    titulo.configure(text=current_texts.get("title", "SV R.E.P.O Save Manager"))
    btn_backup.configure(text=current_texts.get("backup_now", "Crear Backup"))
    btn_restaurar.configure(text=current_texts.get("restore", "Restaurar Backup"))
    chk_auto.configure(text=current_texts.get("auto_backup_check", "Habilitar backup automático"))
    lbl_min.configure(text=current_texts.get("auto_backup_interval", "Backup cada:"))
    lbl_mins.configure(text=current_texts.get("minutes", "minutos"))
    # El label_ruta ya usa textvariable, así que se actualiza solo si cambia ruta_backup_var

    # Actualizar la imagen/texto del botón de modo
    current_mode_check = ctk.get_appearance_mode()
    if current_mode_check == "Dark":
        modo_btn.configure(image=img_sun_tk, text="") if img_sun_tk else modo_btn.configure(text="🌞")
    else:
        modo_btn.configure(image=img_moon_tk, text="") if img_moon_tk else modo_btn.configure(text="🌚")

    # Actualizar la bandera
    try:
        flag_image_path = idiomas_banderas.get(idioma_actual)
        if flag_image_path:
            img_flag_pil = Image.open(flag_image_path).resize((28,18), Image.LANCZOS)
            img_bandera_tk = ctk.CTkImage(light_image=img_flag_pil, dark_image=img_flag_pil, size=(28,18))
            bandera_lbl.configure(image=img_bandera_tk, text="")
        else:
            bandera_lbl.configure(text="🌐", image=None)
    except Exception as e:
        print(f"Error al cargar bandera en update_ui_texts para {idioma_actual}: {e}")
        bandera_lbl.configure(text="🌐", image=None)

    # También actualizar el texto de la ventana de carga si está abierta
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
        root.after(0, lambda: messagebox.showinfo(current_texts.get("backup_now", "Backup"),
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
    dialog_window.transient(root) # Hacerla transitoria para que esté sobre la ventana principal

    # Ajustar color de fondo
    current_appearance_mode = ctk.get_appearance_mode()
    dialog_window.configure(fg_color="#1f1f1f" if current_appearance_mode == "Dark" else "#f0f0f0")

    checkbox_vars = []
    scrollable_frame = ctk.CTkScrollableFrame(dialog_window, width=330, height=380)
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

    confirm_button = ctk.CTkButton(dialog_window, text=current_texts.get("accept", "Aceptar"), command=confirm_selection)
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
        root.after(0, lambda: messagebox.showinfo(current_texts.get("restore", "Restaurar"),
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
    global idioma_actual, current_texts # Asegurarse de que se actualice la global
    idioma_actual = choice
    config["idioma"] = idioma_actual
    config_manager.guardar_config(config)
    current_texts = load_locale_texts(idioma_actual) # Recargar los textos con el nuevo idioma
    update_ui_texts() # Actualizar la interfaz con los nuevos textos

def toggle_appearance_mode():
    current_mode = ctk.get_appearance_mode()
    new_mode = "Dark" if current_mode == "Light" else "Light"
    ctk.set_appearance_mode(new_mode)
    config["appearance_mode"] = new_mode
    config_manager.guardar_config(config)
    update_ui_texts() # Actualizar el botón de modo

# Variables de estado del hilo de backup automático
_auto_backup_thread_instance = None
_auto_backup_running_flag = False

def start_auto_backup_thread():
    global _auto_backup_thread_instance, _auto_backup_running_flag

    if _auto_backup_running_flag:
        print("El hilo de backup automático ya está corriendo.")
        return

    def auto_backup_loop():
        global _auto_backup_running_flag
        _auto_backup_running_flag = True

        while _auto_backup_running_flag and backup_automatico_var.get():
            try:
                current_interval = intervalo_minutos_var.get()
                if current_interval <= 0:
                    print(f"Intervalo de backup automático inválido ({current_interval}). Deteniendo hilo.")
                    break

                time.sleep(current_interval * 60)

                if _auto_backup_running_flag and backup_automatico_var.get():
                    root.after(0, internal_auto_backup_logic)
            except Exception as e:
                print(f"Error inesperado en el bucle de backup automático: {e}")
        _auto_backup_running_flag = False

    def internal_auto_backup_logic():
        saves_to_backup = backup_manager.listar_partidas()
        if not saves_to_backup:
            print(current_texts.get("no_saves_found_auto", "No se encontraron partidas para respaldo automático."))
            return

        destination = ruta_backup_var.get() or backup_manager.obtener_ruta_saves()
        try:
            backup_manager.crear_backup_zip(saves_to_backup, destination)
            print(f"{current_texts.get('auto_backup_success', 'Backup automático creado en:')} {destination} (a las {time.strftime('%H:%M:%S')})")
        except Exception as e:
            print(f"{current_texts.get('auto_backup_error', 'Error en backup automático:')} {e}")

    _auto_backup_thread_instance = threading.Thread(target=auto_backup_loop, daemon=True)
    _auto_backup_thread_instance.start()

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
        config["intervalo_minutos"] = 5 # Default on error
        intervalo_minutos_var.set(5)
        messagebox.showwarning(current_texts.get("invalid_input", "Entrada inválida"),
                               current_texts.get("interval_must_be_number", "El intervalo debe ser un número entero y positivo."))

    config["ruta_backup"] = ruta_backup_var.get()
    config_manager.guardar_config(config)

    if backup_automatico_var.get():
        start_auto_backup_thread()
    else:
        _auto_backup_running_flag = False # Signal thread to stop


# --- Construcción de la UI ---
# CREAR LA VENTANA PRINCIPAL PRIMERO
root = ctk.CTk()
root.geometry("750x500")
root.title(current_texts.get("title", "SV R.E.P.O Save Manager"))

# AHORA SÍ, CREAR LAS VARIABLES DE CONTROL CON 'master=root'
backup_automatico_var = tk.BooleanVar(master=root, value=config.get("backup_automatico", False))
ruta_backup_var = tk.StringVar(master=root, value=config.get("ruta_backup", backup_manager.obtener_ruta_saves()))
intervalo_minutos_var = tk.IntVar(master=root, value=config.get("intervalo_minutos", 5))


if os.path.exists(resource_path("icon.ico")):
    try:
        root.iconbitmap(resource_path("icon.ico"))
    except Exception as e:
        print(f"Error al cargar icon.ico: {e}")


top_frame = ctk.CTkFrame(root, fg_color="transparent")
top_frame.pack(pady=10, fill="x", padx=20)

titulo = ctk.CTkLabel(top_frame, text=current_texts.get("title", "SV R.E.P.O Save Manager"), font=("Arial", 22))
titulo.pack(side="left")

modo_btn = ctk.CTkButton(top_frame, width=50, command=toggle_appearance_mode)
modo_btn.pack(side="right", padx=10)

# Selector idioma desplegable
language_options = list(idiomas_banderas.keys())
idioma_menu = ctk.CTkOptionMenu(top_frame, values=language_options,
                                 command=change_language_optionmenu,
                                 width=80)
idioma_menu.set(idioma_actual)
idioma_menu.pack(side="right", padx=10)

# Cargar la imagen de la bandera inicial para el label
img_bandera_tk = None
try:
    initial_flag_path = idiomas_banderas.get(idioma_actual)
    if initial_flag_path:
        initial_flag_pil = Image.open(initial_flag_path).resize((28,18), Image.LANCZOS)
        img_bandera_tk = ctk.CTkImage(light_image=initial_flag_pil, dark_image=initial_flag_pil, size=(28,18))
except Exception as e:
    print(f"Error al cargar bandera inicial para {idioma_actual}: {e}")

bandera_lbl = ctk.CTkLabel(top_frame, image=img_bandera_tk if img_bandera_tk else None)
bandera_lbl.pack(side="right")
if not img_bandera_tk:
    bandera_lbl.configure(text="🌐")


center_frame = ctk.CTkFrame(root, fg_color="transparent")
center_frame.pack(pady=10, fill="both", expand=True)

fila1 = ctk.CTkFrame(center_frame, fg_color="transparent")
fila1.pack(pady=10)

btn_backup = ctk.CTkButton(fila1, text=current_texts.get("backup_now", "Crear Backup"), command=create_backup_dialog)
btn_backup.pack(side="left", padx=10)

btn_restaurar = ctk.CTkButton(fila1, text=current_texts.get("restore", "Restaurar Backup"), command=restore_backup_ui)
btn_restaurar.pack(side="left", padx=10)

btn_carpeta = ctk.CTkButton(fila1, text="📁", width=40, command=select_backup_folder)
btn_carpeta.pack(side="left", padx=10)

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

def on_interval_entry_change(*args):
    try:
        new_val = int(intervalo_minutos_var.get())
        if new_val > 0:
            config["intervalo_minutos"] = new_val
            config_manager.guardar_config(config)
    except ValueError:
        pass
intervalo_minutos_var.trace_add("write", on_interval_entry_change)


# --- Inicio y bucle principal ---
update_ui_texts() # Asegurar que todos los textos estén en el idioma correcto al inicio
if backup_automatico_var.get():
    start_auto_backup_thread()

root.mainloop()