# -*- mode: python ; coding: utf-8 -*-

import os
import sys

# Get the project root directory
spec_file_path = os.path.abspath('maze_runner.spec')
PROJECT_ROOT = os.path.dirname(os.path.dirname(spec_file_path))

# Add the scripts directory to the path
scripts_dir = os.path.dirname(spec_file_path)
sys.path.insert(0, scripts_dir)

block_cipher = None

# Collect all sprite directories
sprite_dirs = [
    os.path.join(PROJECT_ROOT, 'sprites', 'Background'),
    os.path.join(PROJECT_ROOT, 'sprites', 'Decor'),
    os.path.join(PROJECT_ROOT, 'sprites', 'Items'),
    os.path.join(PROJECT_ROOT, 'sprites', 'Player'),
    os.path.join(PROJECT_ROOT, 'sprites', 'Tile'),
    os.path.join(PROJECT_ROOT, 'sprites', 'UI'),
    os.path.join(PROJECT_ROOT, 'sprites', 'questions'),
]

# Create datas list for all sprite files
datas = []
for sprite_dir in sprite_dirs:
    if os.path.exists(sprite_dir):
        for root, dirs, files in os.walk(sprite_dir):
            for file in files:
                file_path = os.path.join(root, file)
                # Calculate relative path from sprites directory
                rel_path = os.path.relpath(file_path, os.path.join(PROJECT_ROOT, 'sprites'))
                # Add to datas with destination in sprites folder
                datas.append((file_path, os.path.join('sprites', rel_path)))

# Add any other data files
data_files = [
    (os.path.join(PROJECT_ROOT, 'scripts', 'questions.xlsx'), '.'),
    (os.path.join(PROJECT_ROOT, 'scripts', 'chaser_model.h5'), '.') if os.path.exists(os.path.join(PROJECT_ROOT, 'scripts', 'chaser_model.h5')) else None,
]

# Filter out None values and add to datas
datas.extend([f for f in data_files if f is not None])

a = Analysis(
    ['main.py'],
    pathex=[scripts_dir],
    binaries=[],
    datas=datas,
    hiddenimports=[
        'pygame',
        'pandas',
        'requests',
        'tensorflow',
        'numpy',
        'json',
        'os',
        'sys',
        'traceback',
        'heapq',
        'math',
        'random',
        'pygame.locals',
        'pygame.mixer',
        'pygame.display',
        'pygame.font',
        'pygame.sprite',
        'pygame.surface',
        'pygame.transform',
        'pygame.draw',
        'pygame.event',
        'pygame.time',
        'pygame.rect',
        'pygame.image',
        'pygame.SRCALPHA',
        'pygame.BLEND_RGBA_MULT',
        'pygame.BLEND_PREMULTIPLIED',
        'pygame.USEREVENT',
        'pygame.QUIT',
        'pygame.K_LEFT',
        'pygame.K_RIGHT',
        'pygame.K_SPACE',
        'pygame.key',
        'Config',
        'GameConfig',
        'Levels',
        'Button',
        'QuestionUI',
        'llm_client',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='MazeRunner',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # Set to False for GUI application
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,  # You can add an icon file here if you have one
) 