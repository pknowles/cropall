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
import wand.image

logger = logging.getLogger("cropall")


class Cropper:
    def __init__(self, config):
        self.config = config

    def resize(self, src_file, dst_file):
        with wand.image.Image(filename=src_file) as img:
            img.transform(
                resize="{}x{}>".format(
                    self.config["cropper"]["resize_width"],
                    self.config["cropper"]["resize_height"],
                )
            )
            img.save(filename=dst_file)

    def crop(self, src_file, dst_file, box):
        with wand.image.Image(filename=src_file) as img:
            crop = "{}x{}+{}+{}".format(
                box[2] - box[0], box[3] - box[1], box[0], box[1]
            )
            img.transform(crop=crop)
            resize = "no resize"
            if self.config.getboolean("cropper", "resize"):
                resize = "{}x{}>".format(
                    self.config["cropper"]["resize_width"],
                    self.config["cropper"]["resize_height"],
                )
                img.transform(resize=resize)
            logger.info(f"Writing {dst_file}, crop {crop} {resize}")
            img.save(filename=dst_file)
