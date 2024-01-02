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
from tkinter import *
import tkinter.filedialog
import shutil
import pathlib
from PIL import ImageOps
from PIL import ImageTk
from PIL import Image

logger = logging.getLogger("cropall")
logger.addHandler(logging.StreamHandler(stream=sys.stdout))

def clamp(x, a, b):
	return min(max(x, a), b)

class App(Tk):
	def getImages(self, dir):
		print("Scanning ", dir)
		allImages = []
		for i in os.listdir(dir):
			b, e = os.path.splitext(i)
			if e.lower() not in self.args.extensions: continue
			allImages += [i]
		return allImages

	def __init__(self, args, cropper):
		super().__init__()
		self.args = args
		self.cropper = cropper

		if self.args.width < -1 or self.args.height < -1:
			raise ValueError("Resize value is invalid")

		self.wm_title("cropall")

		self.inDir = self.args.input_folder[0]

		infiles = self.getImages(self.inDir)

		# If that didn't work, show a browse dialogue
		if not len(infiles):
			print("No images in the current directory. Please select a different directory.")
			self.inDir = tkinter.filedialog.askdirectory(parent=self, initialdir=self.inDir,title='Please select a directory')
			if not len(self.inDir):
				raise ValueError("No directory selected. Exiting.")
			self.inDir = pathlib.Path(os.path.normpath(self.inDir))
			infiles = self.getImages(self.inDir)
			if not len(infiles):
				raise RuntimeError("No images found in " + self.inDir + ". Exiting.")
			print("Found", len(infiles), "images")
		else:
			print("Found", len(infiles), "images in the current directory")

		self.outDir = self.inDir / self.args.output

		if not os.path.exists(self.outDir):
			print("Creating output directory, " + self.outDir)
			os.makedirs(self.outDir)

		print("Initializing GUI")

		self.grid_rowconfigure(0, weight=1)
		self.grid_columnconfigure(0, weight=1)
		self.geometry("1024x512")
		#self.resizable(0,0)

		self.files = infiles

		self.preview = None

		self.item = None

		# "click-drag" selection corners
		self.opposite_corner_coord = (0, 0)
		self.this_corner_coord = (0, 0)

		# "scroll" selection center and crop index
		self.cropIndex = 2
		self.x = 0
		self.y = 0
		self.current = 0

		self.shift_pressed = False

		self.controls = Frame(self)
		self.controls.grid(row=1, column=0, columnspan=2, sticky="nsew")
		self.buttons = []
		selection_mode_options = ('click-drag', 'scroll')
		self.selection_mode = StringVar()
		self.selection_mode.set(self.args.select_mode)
		self.selection_mode_dropdown = OptionMenu(self.controls, self.selection_mode, args.select_mode, *selection_mode_options)
		self.selection_mode_dropdown.grid(row=0, column=0, sticky="nsew")

		self.inputs = []

		self.restrictRatio = IntVar()
		self.inputs += [Checkbutton(self.controls, text="Fix Aspect Ratio", variable=self.restrictRatio)]
		self.inputs[-1].grid(row=0, column=1, sticky="nsew")

		self.aspect = (StringVar(), StringVar())
		self.aspect[0].set("RatioX")
		self.aspect[1].set("RatioY")
		self.inputs += [Entry(self.controls, textvariable=self.aspect[0])]
		self.inputs[-1].grid(row=0, column=2, sticky="nsew")
		self.inputs += [Entry(self.controls, textvariable=self.aspect[1])]
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

		self.restrictSizes = IntVar()
		self.inputs += [Checkbutton(self.controls, text="Perfect Pixel Ratio", variable=self.restrictSizes)]
		self.inputs[-1].grid(row=0, column=9, sticky="nsew")

		self.imageLabel = Canvas(self, highlightthickness=0)
		self.imageLabel.grid(row=0, column=9, sticky='nw', padx=0, pady=0)
		self.c = self.imageLabel

		self.previewLabel = Label(self, relief=FLAT, borderwidth=0)
		self.previewLabel.grid(row=0, column=1, sticky='nw', padx=0, pady=0)

		self.restrictSizes.set(0 if self.args.allow_fractional_size else 1)
		self.restrictRatio.set(1 if self.args.fixed_aspect else 0)

		self.aspect[0].trace("w", self.on_aspect_changed)
		self.aspect[1].trace("w", self.on_aspect_changed)
		self.restrictSizes.trace("w", self.on_option_changed)
		self.restrictRatio.trace("w", self.on_aspect_changed)
		self.bind('<space>', self.save_next)
		self.bind('d', self.next)
		self.bind('a', self.previous)
		self.c.bind('<ButtonPress-1>', self.on_mouse_down)
		self.c.bind('<B1-Motion>', self.on_mouse_drag)
		self.c.bind('<ButtonRelease-1>', self.on_mouse_up)
		#self.c.bind('<Button-3>', self.on_right_click)
		self.bind('<KeyPress-Shift_L>', self.on_shift_press)
		self.bind('<KeyRelease-Shift_L>', self.on_shift_release)
		self.bind('<Escape>', self.remove_focus)
		self.bind('<Button-4>', self.on_mouse_scroll)
		self.bind('<Button-5>', self.on_mouse_scroll)
		self.bind('<MouseWheel>', self.on_mouse_scroll)

		print("Checking for existing crops")
		#self.load_imgfile(allImages[0])
		self.current = 0
		while self.current < len(self.files) and os.path.exists(os.path.join(self.outDir, self.files[self.current])):
			print("Skipping " + self.files[self.current] + ". Already cropped.")
			self.current += 1
		self.current += 1
		self.previous()

	def updateCropSize(self):
		if self.cropIndex <= 4:
			self.cropdiv = 8.0 / (9.0 - self.cropIndex)
		else:
			self.cropdiv = (1 + (self.cropIndex - 1) * 0.25)

	def getCropSize(self):
		self.updateCropSize()
		h = int(self.imageOrigSize[1] / self.cropdiv)
		w = int(self.imageOrigSize[1] * self.aspectRatio / self.cropdiv)
		if w > self.imageOrigSize[0]:
			w = int(self.imageOrigSize[0] / self.cropdiv)
			h = int(self.imageOrigSize[0] / (self.cropdiv * self.aspectRatio))
		#w = int(self.imageOrigSize[0] / self.cropdiv)
		return w, h

	def correct_ar(self, this_corner_image, opposite_corner_image):
		w = this_corner_image[0] - opposite_corner_image[0]
		h = this_corner_image[1] - opposite_corner_image[1]
		aspect_sign = -1 if (w*h < 0) else 1 # to determine whether this corner's x and y are on the same side of the other corner's x and y or not

		# aspect ratio correction
		if (abs(float(w)/float(h)) > self.aspectRatio): # box is too wide -> increase height to match aspect
			this_corner_image = (this_corner_image[0], opposite_corner_image[1] + aspect_sign * w / self.aspectRatio)
		if (abs(float(w)/float(h)) < self.aspectRatio): # box is too high -> increase width to match aspect
			this_corner_image = (opposite_corner_image[0] + aspect_sign * h * self.aspectRatio, this_corner_image[1])
		return this_corner_image, opposite_corner_image


	def getRealBox(self):
		imw = self.imageOrigSize[0]
		imh = self.imageOrigSize[1]
		prevw = self.imagePhoto.width()
		prevh = self.imagePhoto.height()

		if (self.selection_mode.get() == 'click-drag'):
			this_corner_image = (self.this_corner_coord[0] * imw / prevw, self.this_corner_coord[1] * imh / prevh)
			opposite_corner_image = (self.opposite_corner_coord[0] * imw / prevw, self.opposite_corner_coord[1] * imh / prevh)
			
			w = this_corner_image[0] - opposite_corner_image[0]
			h = this_corner_image[1] - opposite_corner_image[1]

			if (self.restrictRatio.get() == 1):

				if (self.shift_pressed): # never resize box when shift is pressed. only force it inside bounds.

					this_corner_image, opposite_corner_image = self.correct_ar(this_corner_image, opposite_corner_image)
					w = this_corner_image[0] - opposite_corner_image[0]
					h = this_corner_image[1] - opposite_corner_image[1]

					move_toright = 0 - min(this_corner_image[0], opposite_corner_image[0]) 
					move_toleft =  max(this_corner_image[0], opposite_corner_image[0]) - imw
					move_x = move_toright if (move_toright > 0) else (-move_toleft if (move_toleft > 0) else 0)

					move_down = 0 - min(this_corner_image[1], opposite_corner_image[1]) 
					move_up =  max(this_corner_image[1], opposite_corner_image[1]) - imh
					move_y = move_down if (move_down > 0) else (-move_up if (move_up > 0) else 0)

					this_corner_image = (this_corner_image[0] + move_x, this_corner_image[1] + move_y)
					opposite_corner_image = (opposite_corner_image[0] + move_x, opposite_corner_image[1] + move_y)


				else: # shift is not pressed, check AR

					opposite_corner_image = ( max(min(opposite_corner_image[0], imw), 0), max(min(opposite_corner_image[1], imh), 0) )
					self.opposite_corner_coord = ( max(min(self.opposite_corner_coord[0], prevw), 0), max(min(self.opposite_corner_coord[1], prevh), 0) )

					this_corner_image, opposite_corner_image = self.correct_ar(this_corner_image, opposite_corner_image)
					w = this_corner_image[0] - opposite_corner_image[0]
					h = this_corner_image[1] - opposite_corner_image[1]

					# bounds correction
					# left
					if (this_corner_image[0] < 0):
						correction = opposite_corner_image[0] / float(-w)
						h = h * correction
						this_corner_image = (0, opposite_corner_image[1] + h)
						w = this_corner_image[0] - opposite_corner_image[0]

					# top
					if (this_corner_image[1] < 0):
						correction = opposite_corner_image[1] / float(-h)
						w = w * correction
						this_corner_image = (opposite_corner_image[0] + w, 0)
						h = this_corner_image[1] - opposite_corner_image[1]

					# bottom
					if (this_corner_image[1] > imh):
						correction = (imh - opposite_corner_image[1]) / float(h)
						w = w * correction
						this_corner_image = (opposite_corner_image[0] + w, imh)
						h = this_corner_image[1] - opposite_corner_image[1]

					# right
					if (this_corner_image[0] > imw):
						correction = (imw - opposite_corner_image[0]) / float(w)
						h = h * correction
						this_corner_image = (imw, opposite_corner_image[1] + h)
						w = this_corner_image[0] - opposite_corner_image[0]

					this_corner_image = (int(round(this_corner_image[0])), int(round(this_corner_image[1])))

			else: # no fixed AR
				# bounds check
				this_corner_image = ( max(min(this_corner_image[0], imw), 0.0), max(min(this_corner_image[1], imh), 0.0))
			
			box = ( min(this_corner_image[0], opposite_corner_image[0]), min(this_corner_image[1], opposite_corner_image[1]), max(this_corner_image[0], opposite_corner_image[0]), max(this_corner_image[1], opposite_corner_image[1]) )

		else: # traditional (scroll) selection
			w, h = self.getCropSize()
			box = (int(round(self.x*imw/prevw))-w//2, int(round(self.y*imh/prevh))-h//2)
			box = (max(box[0], 0), max(box[1], 0))
			box = (min(box[0]+w, imw)-w, min(box[1]+h, imh)-h)
			box = (box[0], box[1], box[0]+w, box[1]+h)

		return box

	def getPreviewBox(self):
		imw = self.imageOrigSize[0]
		imh = self.imageOrigSize[1]
		prevw = self.imagePhoto.width()
		prevh = self.imagePhoto.height()
		bbox = self.getRealBox()
		bbox = (bbox[0]*prevw/imw, bbox[1]*prevh/imh, bbox[2]*prevw/imw, bbox[3]*prevh/imh)
		return (int(bbox[0]), int(bbox[1]), int(bbox[2]), int(bbox[3]))


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
		self.cropper.resize(self.inDir / self.currentName, self.outDir / self.currentName)
		self.next()

	def save_next(self, event=None):
		box = self.getRealBox()
		self.cropper.crop(self.inDir / self.currentName, self.outDir / self.currentName, box)
		self.next()

	def load_imgfile(self, filename):
		self.currentName = filename
		fullFilename = os.path.join(self.inDir, filename)
		logger.info("Loading " + fullFilename)
		img = Image.open(fullFilename)

		self.imageOrig = img
		self.imageOrigSize = (img.size[0], img.size[1])
		logger.info("Image is " + str(self.imageOrigSize[0]) + "x" + str(self.imageOrigSize[1]))

		basewidth = 512
		wpercent = (basewidth/float(img.size[0]))
		hsize = int((float(img.size[1])*float(wpercent)))
		if self.args.fast_preview:
			#does NOT create a copy so self.imageOrig is the same as self.image
			img.thumbnail((basewidth,hsize), Image.NEAREST)
		else:
			if self.args.antialiase_slow_preview:
				img = img.resize((basewidth,hsize), Image.LANCZOS)
			else:
				img = img.copy()
				img.thumbnail((basewidth,hsize), Image.NEAREST)
		self.image = img
		logger.info("Resized preview")

		#self.geometry("1024x"+str(hsize + 100))
		self.configure(relief='flat', background='gray')

		self.imagePhoto = ImageTk.PhotoImage(self.image)
		self.imageLabel.configure(width=self.imagePhoto.width(), height=self.imagePhoto.height())
		self.imageLabel.create_image(0, 0, anchor=NW, image=self.imagePhoto)

		self.previewPhoto = ImageTk.PhotoImage(self.image)
		self.previewLabel.configure(image=self.previewPhoto)

		self.item = None

		self.verti_aux_item = None
		self.horiz_aux_item = None

		self.on_aspect_changed(None, None, None) #update aspect ratio with new image size

		#self.imageLabel.pack(side = "left", fill = "both", expand = "yes")
		#self.previewLabel.pack(side = "left", fill = "both", expand = "yes")
		#self.c.pack(side = "bottom", fill = "both", expand = "yes")

		#self.c.xview_moveto(0)
		#self.c.yview_moveto(0)
		#self.c.config(scrollregion=self.c.bbox('all'))

	def test(self):
		if not self.args.allow_fractional_size:
			self.updateCropSize()
			if int(self.cropdiv) != self.cropdiv: return False
			w, h = self.getCropSize()
			if int(h) != h or int(w) != w: return False
			#if self.imageOrigSize[1] % int(self.cropdiv) != 0: return False
			#if self.imageOrigSize[0] % int(self.cropdiv) != 0: return False
		return True

	def update_box(self, widget):
		bbox = self.getPreviewBox()
		#bbox = (widget.canvasx(bbox[0]), widget.canvasy(bbox[1]), widget.canvasx(bbox[2]), widget.canvasy(bbox[3]))

		if self.item is None:
			self.item = widget.create_rectangle(bbox, outline=self.args.selection_color)
		else:
			widget.coords(self.item, *bbox)

		if (self.args.show_guides):
			horiz_bbox = (bbox[0], bbox[1] + (bbox[3] - bbox[1]) / 3, bbox[2], bbox[3] - (bbox[3] - bbox[1]) / 3)
			verti_bbox = (bbox[0] + (bbox[2] - bbox[0]) / 3, bbox[1], bbox[2] - (bbox[2] - bbox[0]) / 3, bbox[3])
			if self.horiz_aux_item is None:
					self.horiz_aux_item = widget.create_rectangle(horiz_bbox, outline=self.args.selection_color)
			else:
					widget.coords(self.horiz_aux_item, *horiz_bbox)
			if self.verti_aux_item is None:
					self.verti_aux_item = widget.create_rectangle(verti_bbox, outline=self.args.selection_color)
			else:
					widget.coords(self.verti_aux_item, *verti_bbox)

	def update_preview(self, widget):
		if self.item:
			#get a crop for the preview
			#box = tuple((int(round(v)) for v in widget.coords(self.item)))
			box = self.getRealBox()
			pbox = self.getPreviewBox()
			if self.args.fast_preview:
				preview = self.image.crop(pbox) # region of interest
			else:
				preview = self.imageOrig.crop(box) # region of interest

			#add black borders for correct aspect ratio
			#if preview.size[0] > 512:
			preview.thumbnail(self.image.size, Image.LANCZOS) #downscale to preview rez
			paspect = preview.size[0]/float(preview.size[1])
			aspect = self.image.size[0]/float(self.image.size[1])
			if paspect < aspect:
				bbox = (0, 0, int(preview.size[1] * aspect), preview.size[1])
			else:
				bbox = (0, 0, preview.size[0], int(preview.size[0] / aspect))
			preview = ImageOps.expand(preview, border=((bbox[2]-preview.size[0])//2, (bbox[3]-preview.size[1])//2))
			#preview = ImageOps.fit(preview, size=self.image.size, method=Image.LANCZOS, bleed=-10.0)

			#resize to preview rez (if too small)
			self.preview = preview.resize(self.image.size, Image.LANCZOS)
			self.previewPhoto = ImageTk.PhotoImage(self.preview)
			self.previewLabel.configure(image=self.previewPhoto)

			logger.info(str(box[2]-box[0])+"x"+str(box[3]-box[1])+"+"+str(box[0])+"+"+str(box[1]))

	def remove_focus(self, event=None):
			self.focus()

	def on_aspect_changed(self, event, var1, var2):
		if (self.restrictRatio.get() == 1):
			try:
				x = float(self.aspect[0].get())
				y = float(self.aspect[1].get())
				if x < 0 or y < 1:
					raise ZeroDivisionError()
				self.aspectRatio = x / y
			except (ZeroDivisionError, ValueError) as e:
				self.aspectRatio = float(self.imageOrigSize[0])/float(self.imageOrigSize[1])
		else:
			self.aspectRatio = float(self.imageOrigSize[0])/float(self.imageOrigSize[1])
		self.update_box(self.imageLabel)
		self.update_preview(self.imageLabel)

	def on_option_changed(self, event, var1, var2):
		self.args.allow_fractional_size = (self.restrictSizes.get() == 0)

	def on_mouse_scroll(self, event):
		if event.num == 5 or event.delta < 0:
			dir = -1
		if event.num == 4 or event.delta > 0:
			dir = 1

		if dir == 1:
			while self.cropIndex < self.imagePhoto.width():
				self.cropIndex += 1
				if self.test(): break
		if dir == -1:
			if self.cropIndex == 1:
				logger.info("At maximum")
				return
			while self.cropIndex > 1:
				self.cropIndex -= 1
				if self.test(): break

		logger.info(self.cropIndex)

		self.update_box(self.imageLabel)
		self.update_preview(self.imageLabel)

	def on_mouse_down(self, event):
		self.remove_focus()

		self.opposite_corner_coord = (event.x, event.y)
		self.this_corner_coord = (event.x, event.y)

		self.x = event.x
		self.y = event.y

		self.update_box(event.widget)

	def on_mouse_drag(self, event):

		delta = (event.x - self.this_corner_coord[0], event.y - self.this_corner_coord[1])
		self.this_corner_coord = (event.x, event.y)

		prevw = self.imagePhoto.width()
		prevh = self.imagePhoto.height()

		#click-drag selection
		if self.shift_pressed:
			self.opposite_corner_coord = (self.opposite_corner_coord[0] + delta[0], self.opposite_corner_coord[1] + delta[1])

		self.x = event.x
		self.y = event.y

		self.update_box(event.widget)

	def on_mouse_up(self, event):
		self.update_preview(event.widget)

	def on_shift_press(self, event):
		self.shift_pressed = True

	def on_shift_release(self, event):
		self.shift_pressed = False
