#! /usr/bin/env python
#
# cropall: a tiny batch image processing app to crop pictures in less clicks
#
# Copyright (C) 2015-2024 Pyarelal Knowles
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import os
import sys
import error_handler
import argparse
import configparser
import pathlib

logger = error_handler.activate("cropall")

config_file = pathlib.Path("cropall.ini")

# config is in a subdirectory when packaged with pyinstaller
if hasattr(sys, "_MEIPASS"):
    config_file = pathlib.Path(sys._MEIPASS) / config_file

    # Add the _internal directory to PATH for wand/imagemagick on windows
    imagemagick_dir = str(pathlib.Path(sys._MEIPASS))
    os.environ["MAGICK_HOME"] = imagemagick_dir
    os.environ["MAGICK_CODER_FILTER_PATH"] = os.path.join(
        imagemagick_dir, "modules/filters"
    )
    os.environ["MAGICK_CODER_MODULE_PATH"] = os.path.join(
        imagemagick_dir, "modules/coders"
    )
    if sys.platform == "win32":
        os.environ["PATH"] += os.pathsep + sys._MEIPASS

config = configparser.ConfigParser()
config.read(config_file)

parser = argparse.ArgumentParser()
parser.add_argument(
    "input_folder",
    default="./",
    type=pathlib.Path,
    nargs="?",
    help="Directories for source photos",
)


def getImages(config, dir):
    logger.info("Scanning {}".format(dir))
    extensions = config["image_extensions"].split()
    images = []
    for filename in os.listdir(dir):
        basename, ext = os.path.splitext(filename)
        if ext.lower() in extensions:
            logger.info("  Found {}".format(filename))
            images += [filename]
    logger.info("Found {} images".format(len(images)))
    return images


if __name__ == "__main__":
    cropall_config = config["cropall"]
    args = parser.parse_args()
    if args.input_folder:
        input_folder = str(args.input_folder)
    else:
        # Ask for the input directory
        import tkinter.filedialog
        input_folder = tkinter.filedialog.askdirectory(
            initialdir=cropall_config["input_folder"], title="Please select a directory"
        )
    if not len(input_folder):
        raise ValueError("No directory selected. Exiting.")
    input_folder = pathlib.Path(os.path.normpath(input_folder))
    images = getImages(cropall_config, input_folder)
    if not len(images):
        raise SystemExit("No images found in " + input_folder + ". Exiting.")
    cropall_config["input_folder"] = str(input_folder)

    output_folder = input_folder / pathlib.Path(cropall_config["output_folder"])
    if not os.path.exists(output_folder):
        logger.info("Creating output directory, {}".format(output_folder))
        os.makedirs(output_folder)

    import cropper

    cropper = cropper.Cropper(config)

    import gui

    app = gui.App(config, cropper, input_folder, images, output_folder)
    app.mainloop()

    with open(config_file, 'w') as filehandle:
        config.write(filehandle)
