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
import logging
import traceback
from tkinter.messagebox import showerror
from functools import partial


def handle_exception(logger, exc_type, exc_value, exc_traceback):
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return

    logger.critical("Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback))

    # Error popup for windows, where the console is just closed immediately
    if sys.platform == "win32":
        showerror(
            "Uncaught exception",
            "\n".join(traceback.format_exception(exc_type, exc_value, exc_traceback)),
        )


def activate(logger_name):
    logging.basicConfig(
        filename="{}_log.txt".format(logger_name),
        format="%(asctime)s %(levelname)-8s %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    logger = logging.getLogger(logger_name)
    handler = logging.StreamHandler(stream=sys.stdout)
    logger.addHandler(handler)
    sys.excepthook = partial(handle_exception, logger)
    return logger
