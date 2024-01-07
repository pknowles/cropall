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


# README:
# this script needs
# 1.  python 3.x  https://www.python.org/downloads/
#               also python-tk and python-imaging-tk
# 2.  imagemagick http://www.imagemagick.org/script/binary-releases.php#windows
# 3.  both added to PATH http://stackoverflow.com/questions/6318156/adding-python-path-on-windows-7

# 4. If "import Image" fails below, do this...
#       install pip http://stackoverflow.com/questions/4750806/how-to-install-pip-on-windows
#       run "pip install Pillow"
#       or on linux install python-pillow and python-pillow-tk http://stackoverflow.com/questions/10630736/no-module-named-image-tk

import os
import sys
import tkinter
import logging
import box
import numpy as np
from tkinter import *
from tkinter.ttk import *
from ttkthemes import ThemedTk
import tkinter.filedialog
import shutil
import pathlib
from PIL import ImageOps
from PIL import ImageTk
from PIL import Image

logger = logging.getLogger("cropall")
logger.setLevel(logging.DEBUG)


def clamp(x, a, b):
    return min(max(x, a), b)


class App(ThemedTk):
    def getImages(self, dir):
        logger.info("Scanning {}".format(dir))
        allImages = []
        for i in os.listdir(dir):
            b, e = os.path.splitext(i)
            if e.lower() not in self.args.extensions:
                continue
            allImages += [i]
        return allImages

    def __init__(self, args, cropper):
        super().__init__(theme="breeze")

        self.args = args
        self.cropper = cropper

        if self.args.width < -1 or self.args.height < -1:
            raise ValueError("Resize value is invalid")

        self.wm_title("cropall")

        # Initial size based on screen dpi
        dpi = self.winfo_fpixels("1i")
        self.geometry("{}x{}".format(int(dpi * 16), int(dpi * 8)))

        self.inDir = self.args.input_folder[0]

        infiles = self.getImages(self.inDir)

        # If that didn't work, show a browse dialogue
        if not len(infiles):
            logger.warning(
                "No images in the current directory. Please select a different directory."
            )
            self.lift()
            self.inDir = tkinter.filedialog.askdirectory(
                parent=self, initialdir=self.inDir, title="Please select a directory"
            )
            if not len(self.inDir):
                raise ValueError("No directory selected. Exiting.")
            self.inDir = pathlib.Path(os.path.normpath(self.inDir))
            infiles = self.getImages(self.inDir)
            if not len(infiles):
                raise RuntimeError("No images found in " + self.inDir + ". Exiting.")
            logger.info("Found {} images".format(len(infiles)))
        else:
            logger.info("Found {} images in the current directory".format(len(infiles)))

        self.outDir = self.inDir / self.args.output

        if not os.path.exists(self.outDir):
            logger.info("Creating output directory, " + self.outDir)
            os.makedirs(self.outDir)

        logger.info("Initializing GUI")

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self.files = infiles

        self.image_orig = None
        self.image = None
        self.delayed_resize_id = None
        self.preview = None

        self.displayed_crop_rectangle = None
        self.verti_aux_item = None
        self.horiz_aux_item = None

        # "click-drag" selection rectangle
        self.mouse_position = box.Size2D(0, 0)
        self.mouse_selection = box.Box2D(box.Size2D(0, 0), box.Size2D(1, 1))

        # "scroll" selection center and crop index
        self.scroll_crop_width = 1
        self.current = 0

        self.shift_pressed = False

        self.controls = Frame(self)
        self.controls.grid(row=1, column=0, columnspan=2, sticky="nsew")
        self.buttons = []
        selection_mode_options = ("click-drag", "scroll")
        self.selection_mode = StringVar()
        self.selection_mode.set(self.args.select_mode)
        self.selection_mode_dropdown = OptionMenu(
            self.controls,
            self.selection_mode,
            args.select_mode,
            *selection_mode_options
        )
        self.selection_mode_dropdown.grid(row=0, column=0, sticky="nsew")

        self.inputs = []

        self.aspect_vars = (StringVar(), StringVar())
        self.aspect_vars[0].set(3)
        self.aspect_vars[1].set(2)
        self.inputs += [Entry(self.controls, textvariable=self.aspect_vars[0])]
        self.inputs[-1].grid(row=0, column=2, sticky="nsew")
        self.inputs += [Entry(self.controls, textvariable=self.aspect_vars[1])]
        self.inputs[-1].grid(row=0, column=3, sticky="nsew")

        self.buttons += [Button(self.controls, text="Prev", command=self.previous)]
        self.buttons[-1].grid(row=0, column=4, sticky="nsew")
        self.buttons += [Button(self.controls, text="Next", command=self.next)]
        self.buttons[-1].grid(row=0, column=5, sticky="nsew")
        self.buttons += [Button(self.controls, text="Copy", command=self.copy)]
        self.buttons[-1].grid(row=0, column=6, sticky="nsew")
        self.buttons += [Button(self.controls, text="Resize", command=self.resize)]
        self.buttons[-1].grid(row=0, column=7, sticky="nsew")
        self.buttons += [Button(self.controls, text="Crop", command=self.save_next)]
        self.buttons[-1].grid(row=0, column=8, sticky="nsew")

        self.menubar = Menu(self)
        self.options_menu = Menu(self.menubar)
        self.restrictRatio = IntVar()
        self.options_menu.add_checkbutton(
            label="Fix Aspect Ratio", variable=self.restrictRatio
        )
        self.restrictSizes = IntVar()
        self.options_menu.add_checkbutton(
            label="Perfect Pixel Ratio", variable=self.restrictSizes
        )
        self.showGuides = IntVar()
        self.options_menu.add_checkbutton(label="Show guides", variable=self.showGuides)
        self.menubar.add_cascade(label="Options", menu=self.options_menu)
        self.configure(relief="flat", background="gray", menu=self.menubar)

        self.imageLabel = Canvas(self, highlightthickness=0, bg="grey")
        self.imageLabel.grid(row=0, column=0, sticky="nw", padx=0, pady=0)
        self.c = self.imageLabel

        self.previewLabel = Label(self, relief=FLAT, borderwidth=0)
        self.previewLabel.grid(row=0, column=1, sticky="nw", padx=0, pady=0)

        self.restrictSizes.set(0 if self.args.allow_fractional_size else 1)
        self.restrictRatio.set(1 if self.args.fixed_aspect else 0)
        self.showGuides.set(1 if self.args.show_guides else 0)

        self.aspect_vars[0].trace("w", self.on_aspect_changed)
        self.aspect_vars[1].trace("w", self.on_aspect_changed)
        self.restrictSizes.trace("w", self.on_option_changed)
        self.restrictRatio.trace("w", self.on_aspect_changed)
        self.showGuides.trace("w", self.on_aspect_changed)
        self.selection_mode.trace("w", self.on_aspect_changed)
        self.bind("<Configure>", self.on_resize)
        self.bind("<space>", self.save_next)
        self.bind("d", self.next)
        self.bind("a", self.previous)
        self.imageLabel.bind("<ButtonPress-1>", self.on_mouse_down)
        self.imageLabel.bind("<B1-Motion>", self.on_mouse_drag)
        self.imageLabel.bind("<ButtonRelease-1>", self.on_mouse_up)
        self.bind("<KeyPress-Shift_L>", self.on_shift_press)
        self.bind("<KeyRelease-Shift_L>", self.on_shift_release)
        self.bind("<Escape>", self.remove_focus)
        self.bind("<Button-4>", self.on_mouse_scroll)
        self.bind("<Button-5>", self.on_mouse_scroll)
        self.bind("<MouseWheel>", self.on_mouse_scroll)

        logger.warning("Checking for existing crops")
        self.current = 0
        while self.current < len(self.files) and os.path.exists(
            os.path.join(self.outDir, self.files[self.current])
        ):
            logger.warning("Skipping " + self.files[self.current] + ". Already cropped.")
            self.current += 1

        # Trigger a resize to set self.display_area
        self.display_area = box.Size2D(-1, -1)
        self.update()

        # Load the first image
        self.current += 1
        self.previous()

    def aspect(self):
        try:
            return box.Size2D(
                max(1, int(self.aspect_vars[0].get())),
                max(1, int(self.aspect_vars[1].get())),
            )
        except ValueError:
            return box.Size2D(1, 1)

    def scroll_crop_size(self):
        aspect = self.aspect()
        return (
            self.scroll_crop_width,
            (self.scroll_crop_width * aspect[1]) / aspect[0],
        )

    def image_crop_box(self):
        "Returns the crop box for the original image"
        image_box = box.Box2D.scale_down(self.image_size, self.image_area)

        if self.selection_mode.get() == "click-drag":
            image_mouse_box = (self.mouse_selection - image_box).scaled(
                image_box.size, self.image_size
            )
            if self.restrictRatio.get() == 1:
                region = box.Box2D.cover(self.aspect(), image_mouse_box.size, False)
                region.offset += image_mouse_box.offset
                box.Box2D
                return region.positive_size()
            else:
                return image_mouse_box.positive_size()
        else:
            # scroll to change size
            region = box.Box2D(
                ((self.mouse_position - image_box.offset) * self.image_size)
                / image_box.size,
                self.scroll_crop_size(),
            )
            region.offset -= (region.size / 2).astype(int)
            return region.clamped(self.image_size)

    def displayed_crop_box(self):
        "Returns the crop box for the possibly-scaled displayed image, relative to the image_box area, not the whole image_area"
        image_box = box.Box2D.scale_down(self.image_size, self.image_area)
        orig_crop = self.image_crop_box()
        display_crop = orig_crop.scaled(self.image_size, image_box.size)
        return display_crop

    def previous(self, event=None):
        self.current -= 1
        self.current = (self.current + len(self.files)) % len(self.files)
        self.load_imgfile(self.files[self.current])

    def next(self, event=None):
        self.current += 1
        self.current = (self.current + len(self.files)) % len(self.files)
        self.load_imgfile(self.files[self.current])

    def copy(self):
        shutil.copy(self.inDir / self.currentName, self.outDir / self.currentName)
        self.next()

    def resize(self):
        self.cropper.resize(
            self.inDir / self.currentName, self.outDir / self.currentName
        )
        self.next()

    def save_next(self, event=None):
        box = self.image_crop_box()
        self.cropper.crop(
            self.inDir / self.currentName,
            self.outDir / self.currentName,
            box.coords().tolist(),
        )
        self.next()

    def load_imgfile(self, filename):
        self.currentName = filename
        fullFilename = os.path.join(self.inDir, filename)
        logger.info("Loading " + fullFilename)
        self.image_orig = Image.open(fullFilename)
        self.image_size = box.Size2D(self.image_orig.size[0], self.image_orig.size[1])
        logger.info(
            "Image is " + str(self.image_size[0]) + "x" + str(self.image_size[1])
        )

        # Initialize scroll cropping
        image_box = box.Box2D.scale_down(self.image_size, self.image_area)
        self.scroll_crop_width = self.image_size[0] // 2
        self.inc_scroll_crop()
        self.mouse_position = (self.image_area / 2).astype(int)
        self.mouse_selection = self.displayed_crop_box() + image_box

        self.update_image_display()
        self.update_selection_box(self.imageLabel)
        self.update_preview(self.imageLabel)

    def update_image_display(self):
        if not self.image_orig:
            return

        image_box = box.Box2D.scale_down(self.image_size, self.image_area)
        if self.args.fast_preview:
            # does NOT create a copy so self.image_orig is the same as self.image
            self.image = self.image_orig.copy()
            self.image.thumbnail(image_box.size, Image.NEAREST)
        else:
            if self.args.antialiase_slow_preview:
                self.image = self.image_orig.resize(image_box.size, Image.LANCZOS)
            else:
                self.image = self.image_orig.copy()
                self.image.thumbnail(image_box.size, Image.NEAREST)
        logger.info("Resized preview")

        self.imagePhoto = ImageTk.PhotoImage(self.image)
        self.imageLabel.configure(width=self.image_area[0], height=self.image_area[1])
        canva_image = self.imageLabel.create_image(
            image_box.offset[0], image_box.offset[1], anchor=NW, image=self.imagePhoto
        )
        self.imageLabel.tag_lower(canva_image)

    def test_fractional_size(self):
        if not self.args.allow_fractional_size:
            (w, h) = self.scroll_crop_size()
            if int(h) != h or int(w) != w:
                return False
        return True

    def update_selection_box(self, widget):
        if not self.image or self.image_area[0] == 0:
            return

        image_box = box.Box2D.scale_down(self.image_size, self.image_area)
        selection_box = self.displayed_crop_box() + image_box
        if self.displayed_crop_rectangle is None:
            self.displayed_crop_rectangle = widget.create_rectangle(
                selection_box.coords().tolist(), outline=self.args.selection_color
            )
        else:
            widget.coords(
                self.displayed_crop_rectangle, *selection_box.coords().tolist()
            )

        if self.showGuides.get() == 1:
            verti_bbox = selection_box.copy()
            verti_bbox.offset[0] += verti_bbox.size[0] / 3
            verti_bbox.size[0] /= 3
            verti_bbox = verti_bbox.coords().tolist()
            horiz_bbox = selection_box.copy()
            horiz_bbox.offset[1] += horiz_bbox.size[1] / 3
            horiz_bbox.size[1] /= 3
            horiz_bbox = horiz_bbox.coords().tolist()
            if self.horiz_aux_item is None:
                self.horiz_aux_item = widget.create_rectangle(
                    horiz_bbox, outline=self.args.selection_color
                )
            else:
                widget.coords(self.horiz_aux_item, *horiz_bbox)
            if self.verti_aux_item is None:
                self.verti_aux_item = widget.create_rectangle(
                    verti_bbox, outline=self.args.selection_color
                )
            else:
                widget.coords(self.verti_aux_item, *verti_bbox)
        else:
            if self.horiz_aux_item:
                widget.delete(self.horiz_aux_item)
                self.horiz_aux_item = None
            if self.verti_aux_item:
                widget.delete(self.verti_aux_item)
                self.verti_aux_item = None

    def update_preview(self, widget):
        if not self.image or self.image_area[0] == 0:
            return

        # get a crop for the preview
        if self.args.fast_preview:
            preview = self.image.crop(self.displayed_crop_box().coords().tolist())
        else:
            preview = self.image_orig.crop(self.image_crop_box().coords().tolist())

        # Resize and letterbox
        preview_box = box.Box2D.contain(preview.size, self.preview_area)
        preview = preview.resize(preview_box.size, Image.LANCZOS)
        preview = ImageOps.expand(
            preview, border=tuple(preview_box.offset), fill=(100, 100, 100)
        )
        self.preview = preview

        self.previewPhoto = ImageTk.PhotoImage(self.preview)
        self.previewLabel.configure(image=self.previewPhoto)

    def remove_focus(self, event=None):
        self.focus()

    def on_resize(self, event):
        new_display_area = box.Size2D(self.winfo_width(), self.winfo_height())
        if np.array_equal(self.display_area, new_display_area):
            return

        # Left/right panel sizes are computed manually based off the entire
        # window size because it was easier than figuring out tkinter. Note that
        # the height for the bottom bar of control buttons is not taken into
        # account.
        logger.info("Resize window {}x{}".format(*new_display_area))
        self.display_area = new_display_area
        self.image_area = self.display_area.copy()
        self.preview_area = self.display_area.copy()
        self.image_area[0] /= 2
        self.preview_area[0] -= self.image_area[0]
        self.update_selection_box(self.imageLabel)
        self.update_preview(self.imageLabel)

        # If the input image is huge, updating the display image can be quite
        # slow, so consolidate multiple resizes to a single delayed event.
        if self.delayed_resize_id:
            self.after_cancel(self.delayed_resize_id)
        if self.image_orig:
            self.delayed_resize_id = self.after(1000, self.update_image_display)

    def on_aspect_changed(self, event, var1, var2):
        self.update_selection_box(self.imageLabel)
        self.update_preview(self.imageLabel)

    def on_option_changed(self, event, var1, var2):
        self.args.allow_fractional_size = self.restrictSizes.get() == 0

    def inc_scroll_crop(self):
        # Scroll one pixel at a time if shift is pressed. Otherwise skip a few
        if not self.shift_pressed:
            self.scroll_crop_width = min(
                self.image_size[0], int(self.scroll_crop_width * 1.1)
            )
        while self.scroll_crop_width < self.image_size[0]:
            self.scroll_crop_width += 1
            if self.test_fractional_size():
                break
        logger.info("Crop width: {}".format(self.scroll_crop_width))

    def dec_scroll_crop(self):
        # Scroll one pixel at a time if shift is pressed. Otherwise skip a few
        if not self.shift_pressed:
            self.scroll_crop_width = max(1, int(self.scroll_crop_width * 0.9))
        while self.scroll_crop_width > 1:
            self.scroll_crop_width -= 1
            if self.test_fractional_size():
                break
        logger.info("Crop width: {}".format(self.scroll_crop_width))

    def on_mouse_scroll(self, event):
        changed = False
        if event.num == 5 or event.delta < 0:
            self.inc_scroll_crop()
            changed = True
        if event.num == 4 or event.delta > 0:
            self.dec_scroll_crop()
            changed = True
        if changed:
            self.update_selection_box(self.imageLabel)
            self.update_preview(self.imageLabel)

    def on_mouse_down(self, event):
        self.remove_focus()

        self.mouse_down_position = box.Size2D(event.x, event.y)
        self.mouse_position = box.Size2D(event.x, event.y)

        self.update_selection_box(event.widget)

    def on_mouse_drag(self, event):
        new_position = box.Size2D(event.x, event.y)
        delta = new_position - self.mouse_position
        self.mouse_position = new_position

        if self.selection_mode.get() == "click-drag":
            if self.shift_pressed:
                # Holding shift moves the current selection rather than resizes it
                self.mouse_selection = self.mouse_selection + delta
            else:
                # Note: size may be negative, which preserves the origin corner
                # as the offset
                self.mouse_selection = box.Box2D(
                    self.mouse_down_position,
                    self.mouse_position - self.mouse_down_position,
                )

        self.update_selection_box(event.widget)

    def on_mouse_up(self, event):
        self.update_preview(event.widget)

    def on_shift_press(self, event):
        self.shift_pressed = True

    def on_shift_release(self, event):
        self.shift_pressed = False
