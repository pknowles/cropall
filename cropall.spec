# -*- mode: python ; coding: utf-8 -*-

# Reach into the privates of wand/api.py and grab the DLLs it finds
print("Find ImageMagick libraries")
imagemagic_dlls=set()
import os
import sys
import wand.api
from wand.api import library_paths
old_path = os.environ['PATH']
for libwand_path, libmagick_path in library_paths():
    if libwand_path and os.path.exists(libwand_path):
        imagemagic_dlls.add(libwand_path)
    if libmagick_path and os.path.exists(libmagick_path):
        imagemagic_dlls.add(libmagick_path)
path_extra = os.environ['PATH'][len(old_path):]
if sys.platform == "win32":
    for dir in path_extra.split(os.pathsep):
        if "filters" in dir or "coders" in dir:
            for file in os.listdir(dir):
                imagemagic_dlls.add(os.path.join(dir, file))
                
print("Find 3rd party dependency license files")
matches = ["LICENSE.txt","METADATA","PKG-INFO"]
licenses = []
import sysconfig
for root, dir, files in os.walk(sysconfig.get_paths()["purelib"]):
    for file in files:
            if file in matches:
               src = f"{root}/{file}"
               dest = f"PACKAGE_LICENSES/{os.path.basename(root)}"
               licenses.append((src, dest))
               print(f"\tLicense file: {root}/{file}")

# Find the ImageMagick license file, typically next to the dll
for dir in map(os.path.dirname, imagemagic_dlls):
    imagemagick_license = os.path.join(dir, "LICENSE.txt")
    if os.path.exists(imagemagick_license):
        print(f"\tLicense file: {imagemagick_license}")
        licenses += [(imagemagick_license, "PACKAGE_LICENSES/ImageMagick")]
        break

print(f"{len(licenses)} dependency licenses found. Copying to PACKAGE_LICENSES folder in distribution")

a = Analysis(
    ['cropall.py'],
    pathex=[],
    binaries=list((src, ".") for src in imagemagic_dlls),
    datas=[('cropall.ini', '.')] + licenses,
    hiddenimports=['PIL._tkinter_finder'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='cropall',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='cropall',
)
