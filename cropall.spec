# -*- mode: python ; coding: utf-8 -*-

# Reach into the privates of wand/api.py and grab the DLLs it finds
print("Find ImageMagick libraries")
libraries=[]
import os
import sys
import wand.api
from wand.api import library_paths
old_path = os.environ['PATH']
for libwand_path, libmagick_path in library_paths():
    if sys.platform != "win32" and (libwand_path or libmagick_path):
        print("Warning: searching hard coded path /lib64")
        libwand_path = os.path.join("/lib64", libwand_path) if libwand_path else None
        libmagick_path = os.path.join("/lib64", libmagick_path) if libmagick_path else None
    if libwand_path and os.path.exists(libwand_path):
        libraries += [(libwand_path, ".")]
    if libmagick_path and os.path.exists(libmagick_path):
        libraries += [(libmagick_path, ".")]
libraries = list(set(libraries))
path_extra = os.environ['PATH'][len(old_path):]
if sys.platform == "win32":
    for dir in set(path_extra.split(os.pathsep)):
        if "filters" in dir:
            for file in os.listdir(dir):
                libraries += [(os.path.join(dir, file), "modules/filters")]
        if "coders" in dir:
            for file in os.listdir(dir):
                libraries += [(os.path.join(dir, file), "modules/coders")]
else:
    import wand.version
    options = wand.version.configure_options()
    for file in os.listdir(options['FILTER_PATH']):
        libraries += [(os.path.join(options['FILTER_PATH'], file), "modules/filters")]
    for file in os.listdir(options['CODER_PATH']):
        libraries += [(os.path.join(options['CODER_PATH'], file), "modules/coders")]

for lib, dst in libraries:
    print(f"\tLibrary: {lib}")

print("Find 3rd party dependency license files")
matches = ["LICENSE", "LICENSE.txt", "NOTICE", "NOTICE.txt", "AUTHORS.txt","METADATA","PKG-INFO"]
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
imagemagick_dirs = ["/usr/share/doc/ImageMagick-libs", "/usr/share/licenses/ImageMagick-libs"]
if sys.platform == "win32":
    imagemagick_dirs = set(map(os.path.dirname, libraries))
for dir in imagemagick_dirs:
    for file in matches:
        imagemagick_license = os.path.join(dir, file)
        if os.path.exists(imagemagick_license):
            print(f"\tLicense file: {imagemagick_license}")
            licenses += [(imagemagick_license, "PACKAGE_LICENSES/ImageMagick")]

print(f"{len(licenses)} dependency licenses found. Copying to PACKAGE_LICENSES folder in distribution")

a = Analysis(
    ['cropall.py'],
    pathex=[],
    binaries=libraries,
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
