import os
import zipfile
from datetime import datetime
import shutil
from getpass import getuser # Mover la importación aquí para mejor práctica

def obtener_ruta_saves():
    usuario = getuser()
    ruta = os.path.join("C:/Users", usuario, "AppData", "LocalLow", "semiwork", "Repo", "saves")
    return ruta

def listar_partidas():
    ruta = obtener_ruta_saves()
    if not os.path.exists(ruta):
        return []
    return [d for d in os.listdir(ruta) if os.path.isdir(os.path.join(ruta, d))]

def crear_backup_zip(partidas_seleccionadas, destino):
    if not os.path.exists(destino):
        os.makedirs(destino)
    ruta_saves = obtener_ruta_saves()
    for partida in partidas_seleccionadas:
        carpeta_origen = os.path.join(ruta_saves, partida)
        timestamp = datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
        nombre_zip = f"{partida}_{timestamp}.zip"
        ruta_zip = os.path.join(destino, nombre_zip)
        with zipfile.ZipFile(ruta_zip, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, _, files in os.walk(carpeta_origen):
                for file in files:
                    ruta_completa = os.path.join(root, file)
                    arcname = os.path.relpath(ruta_completa, carpeta_origen)
                    zipf.write(ruta_completa, arcname)

def restaurar_backup_zip(ruta_zip):
    ruta_saves = obtener_ruta_saves()
    with zipfile.ZipFile(ruta_zip, 'r') as zipf:
        nombre_zip = os.path.basename(ruta_zip)
        # La lógica para extraer el nombre de la carpeta del ZIP es un poco frágil.
        # Si el nombre del ZIP no sigue el patrón esperado (e.g., "partida_YYYY_MM_DD_HH_MM_SS.zip"),
        # esto podría fallar. Podríamos necesitar un método más robusto o confiar en que el nombre
        # del ZIP siempre será consistente.
        # Por ahora, mantendré tu lógica, pero es un punto a considerar si hay problemas.
        partes = nombre_zip.rsplit('_', 6) # Intenta dividir por 6 guiones bajos desde la derecha
        if len(partes) >= 2:
            nombre_carpeta = partes[0]
            # Reconstruir el nombre de la carpeta si tiene guiones bajos en el nombre original
            for i in range(1, len(partes) - 6): # Iterar hasta justo antes de las partes de fecha/hora
                nombre_carpeta += "_" + partes[i]
        else:
            # Si no se puede dividir como se espera, toma el nombre antes de la extensión
            nombre_carpeta = os.path.splitext(nombre_zip)[0]

        destino = os.path.join(ruta_saves, nombre_carpeta)
        if os.path.exists(destino):
            shutil.rmtree(destino) # Elimina la carpeta existente para asegurar una restauración limpia
        os.makedirs(destino, exist_ok=True)
        zipf.extractall(destino)
    return destino