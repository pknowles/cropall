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
import subprocess
from distutils import spawn

logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler(stream=sys.stdout))


class Cropper:
    def __init__(self, args):
        self.args = args
        self.convert_path = spawn.find_executable("convert")
        if self.convert_path:
            logger.info('Found ImageMagick\'s "convert" at', self.convert_path)
        else:
            raise EnvironmentError(
                'Could not find ImageMagick\'s "convert". Is it installed and in PATH?'
            )

    def resize(self, src_file, dst_file):
        if not (self.args.width > 0):
            logger.error("Error: no resize specified. Not resizing")
            return
        c = 'convert "' + src_file + '"'
        c += ' -resize "' + str(self.args.width) + "x" + str(self.args.height) + '>"'
        c += ' "' + dst_file + '"'
        logger.info(c)
        subprocess.Popen(c, shell=True)
        logger.info("Running")
        # os.system(c)

    def crop(self, src_file, dst_file, box):
        c = 'convert "' + src_file + '"'
        c += (
            " -crop "
            + str(box[2] - box[0])
            + "x"
            + str(box[3] - box[1])
            + "+"
            + str(box[0])
            + "+"
            + str(box[1])
        )
        if self.args.width > 0:
            c += (
                ' -resize "' + str(self.args.width) + "x" + str(self.args.height) + '>"'
            )
        c += ' "' + dst_file + '"'
        logger.info(c)
        subprocess.Popen(c, shell=True)
        logger.info("Running")
