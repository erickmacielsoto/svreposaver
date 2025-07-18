# -*- mode: python ; coding: utf-8 -*-

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('locales', 'locales'),          # Mantiene la carpeta 'locales' con archivos .json
        ('img', 'img'),                  # Añade toda la carpeta 'img'
        ('flags', 'flags'),              # Mantiene la carpeta 'flags' para las banderas
        ('icon.ico', '.'),               # El icono principal para la ventana y el .exe (a la raíz del bundle)
    ],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='SV_REPO_Save_Manager', # Cambié el nombre para que sea más descriptivo en el .exe
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,                   # 'True' si quieres una consola CMD abierta junto a la GUI
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['icon.ico'],               # Esto es para el icono del .exe en el explorador de archivos
)

# Esto solo es necesario si estás creando un instalador o algo más complejo,
# o si necesitas acceso directo a la carpeta 'dist' para ver estos archivos.
# No es estrictamente necesario para el funcionamiento del .exe si 'img' y 'flags'
# ya están en 'datas'.
# coll = COLLECT(
#     exe,
#     a.binaries,
#     a.datas,
#     strip=False,
#     upx=True,
#     upx_exclude=[],
#     name='SV_REPO_Save_Manager'
# )