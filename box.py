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

import numpy as np


class Size2D(np.ndarray):
    def __new__(cls, width, height):
        obj = np.asarray([width, height], dtype="int").view(cls)
        return obj

    @staticmethod
    def center(source_size, destination_size):
        remaining_size = destination_size - source_size
        return remaining_size / 2


class Box2D:
    "A rectangle with an offset and size"

    def __init__(self, offset, size):
        self.offset = offset.astype(int)
        self.size = np.ceil(size).astype(int)

    def copy(self):
        return Box2D(self.offset, self.size)

    def clamped(self, size):
        "Returns a box with the same size moved such that it's within size"
        delta_over = np.maximum(self.offset + self.size, size) - size
        delta_under = np.minimum(self.offset, [0, 0])
        return Box2D(self.offset - delta_over - delta_under, self.size)

    def min_max(self):
        return (
            np.minimum(self.offset, self.offset + self.size),
            np.maximum(self.offset, self.offset + self.size),
        )

    @staticmethod
    def from_min_max(coord_min, coord_max):
        return Box2D(coord_min, coord_max - coord_min)

    def positive_size(self):
        return Box2D.from_min_max(*self.min_max())

    def coords(self):
        "Returns [left, upper, right, lower] coordinates that can be passed to Image.crop()"
        return np.concatenate((self.offset, self.offset + self.size))

    def scaled(self, source_size, destination_size):
        "Returns the box transformed from coordinates of source_size to destination_size, e.g. to find the same relative box in different units"
        return Box2D(
            (self.offset * destination_size) / source_size,
            (self.size * destination_size) / source_size,
        )

    def __sub__(self, other):
        "Subtracts the other box's offset"
        offset = other.offset if isinstance(other, Box2D) else other
        return Box2D(
            self.offset - offset,
            self.size,
        )

    def __add__(self, other):
        "Adds the other box's offset"
        offset = other.offset if isinstance(other, Box2D) else other
        return Box2D(
            self.offset + offset,
            self.size,
        )

    @staticmethod
    def fill(source_size, destination_size):
        "Like CSS - the image is resized to fill the given dimension. If necessary, the image will be stretched or squished to fit"
        return Box2D(Size2D(0, 0), destination_size)

    @staticmethod
    def contain(source_size, destination_size, center=True):
        assert source_size[0] > 0 and source_size[1] > 0
        "Like CSS - the image keeps its aspect ratio, but is resized to fit within the given dimension"
        scale = min(
            abs(destination_size[0] / source_size[0]),
            abs(destination_size[1] / source_size[1]),
        )
        box_size = np.array(source_size) * np.sign(destination_size) * scale
        box_offset = (
            Size2D.center(box_size, destination_size) if center else Size2D(0, 0)
        )
        return Box2D(box_offset, box_size)

    @staticmethod
    def cover(source_size, destination_size, center=True):
        assert source_size[0] > 0 and source_size[1] > 0
        "Like CSS - the image keeps its aspect ratio and fills the given dimension. The image will be clipped to fit"
        scale = max(
            abs(destination_size[0] / source_size[0]),
            abs(destination_size[1] / source_size[1]),
        )
        box_size = np.array(source_size) * np.sign(destination_size) * scale
        box_offset = (
            Size2D.center(box_size, destination_size) if center else Size2D(0, 0)
        )
        return Box2D(box_offset, box_size)

    @staticmethod
    def scale_down(source_size, destination_size, center=True):
        assert source_size[0] > 0 and source_size[1] > 0
        "Like CSS - the image is scaled down to the smallest version of none or contain"
        scale = min(
            abs(destination_size[0] / source_size[0]),
            abs(destination_size[1] / source_size[1]),
        )
        scale = min(1, scale)
        box_size = np.array(source_size) * np.sign(destination_size) * scale
        box_offset = (
            Size2D.center(box_size, destination_size) if center else Size2D(0, 0)
        )
        return Box2D(box_offset, box_size)
