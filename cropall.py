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

import sys
import error_handler
import argparse
import configparser
import pathlib

error_handler.activate("cropall")

config_file = pathlib.Path("cropall.ini")

# config is in a subdirectory when packaged with pyinstaller
if hasattr(sys, "_MEIPASS"):
    config_file = pathlib.Path(sys._MEIPASS) / config_file

    # Add the _internal directory to PATH for wand/imagemagick on windows
    imagemagick_dir = str(pathlib.Path(sys._MEIPASS))
    os.environ["MAGICK_HOME"] = imagemagick_dir
    os.environ["MAGICK_CODER_FILTER_PATH"] = os.path.join(imagemagick_dir, "modules/filters")
    os.environ["MAGICK_CODER_MODULE_PATH"] = os.path.join(imagemagick_dir, "modules/coders")
    if sys.platform == "win32":
        os.environ["PATH"] += os.pathsep + sys._MEIPASS

config = configparser.ConfigParser()
config.read(config_file)

parser = argparse.ArgumentParser()
parser.add_argument(
    "input_folder",
    default="./",
    type=pathlib.Path,
    nargs="*",
    help="Directories for source photos",
)
# parser.add_argument(
#    "-r",
#    "--recursive",
#    action="store_true",
#    help="Search recursively in the source directories",
# )
parser.add_argument(
    "--output",
    default=config.get("cropall", "out_directory"),
    type=pathlib.Path,
    help="Output directory relative to input",
)
parser.add_argument(
    "--width",
    default=config.getint("cropall", "resize_width"),
    type=int,
    help="Resize to this width after cropping",
)
parser.add_argument(
    "--height",
    default=config.getint("cropall", "resize_height"),
    type=int,
    help="Resize to this height after cropping",
)
parser.add_argument(
    "--fast-preview",
    default=config.getboolean("cropall", "fast_preview"),
    type=argparse.BooleanOptionalAction,
    help="Show a low resolution preview. The final image will look better than preview.",
)
parser.add_argument(
    "--antialiase-slow-preview",
    default=config.getboolean("cropall", "antialiase_slow_preview"),
    type=argparse.BooleanOptionalAction,
    help="When not using --fast-preview, gives a better looking left hand preview image.",
)
parser.add_argument(
    "--allow-fractional-size",
    default=config.getboolean("cropall", "allow_fractional_size"),
    type=argparse.BooleanOptionalAction,
    help="ignores check to see if maintaining the apsect ratio perfectly is possible.",
)
parser.add_argument(
    "-e",
    "--extensions",
    default=config.get("cropall", "image_extensions").split(),
    nargs="+",
    help="File extensions considered to be images",
)
parser.add_argument(
    "-m",
    "--select-mode",
    default=config.get("cropall", "initial_selection_mode"),
    choices=(
        "scroll",
        "box",
    ),
    help="Method to choose the region to crop",
)
parser.add_argument(
    "--show-guides",
    default=config.getboolean("cropall", "show_rule_of_thirds"),
    type=argparse.BooleanOptionalAction,
    help="Displays rule-of-third guidelines.",
)
parser.add_argument(
    "--selection-color",
    default=config.get("cropall", "selection_box_color"),
    help="Color of the selection box",
)
parser.add_argument(
    "--fixed-aspect",
    default=config.getboolean("cropall", "default_fix_ratio"),
    type=argparse.BooleanOptionalAction,
    help="Fixes aspect ratio",
)

if __name__ == "__main__":
    args = parser.parse_args()

    import cropper

    cropper = cropper.Cropper(args)

    import gui

    app = gui.App(args, cropper)
    app.mainloop()
