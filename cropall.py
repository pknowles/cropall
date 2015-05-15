#! /usr/bin/env python2

#README:
#this script needs
#1.  python 2.7 (or at least < 3) https://www.python.org/downloads/release/python-278/
#        also python-tk and python-imaging-tk
#2.  imagemagick http://www.imagemagick.org/script/binary-releases.php#windows
#3.  both added to PATH http://stackoverflow.com/questions/6318156/adding-python-path-on-windows-7

#4. If "import Image" fails below, do this...
#    install pip http://stackoverflow.com/questions/4750806/how-to-install-pip-on-windows
#    run "pip install Pillow"
#    or on linux install python-pillow and python-pillow-tk http://stackoverflow.com/questions/10630736/no-module-named-image-tk

#you may change the below self-explanatory variables

#select input images from current directory
image_extensions = [".jpg", ".png", ".bmp"]

#directory to put output images (created automatically in current directory)
out_directory = "crops"

#after cropping, will resize down until the image firs in these dimensions. set to 0 to disable
resize_width = 1920
resize_height = 1080

#uses low resolution to show crop (real image will look better than preview)
fast_preview = True

#if the above is False, this controls how accurate the left hand preview image is
antialiase_original_preview = True

#ignores check to see if maintaining the apsect ratio perfectly is possible
allow_fractional_size = False





def pause():
	raw_input("Press Enter to continue...")

try:
	import os, sys
	print sys.version

	from distutils import spawn
	convert_path = spawn.find_executable("convert")
	if convert_path:
		print "Found 'convert' at", convert_path
	else:
		raise EnvironmentError("Could not find ImageMagick's 'convert'. Is it installed and in PATH?")

	print "Importing libraries..."
	
	print "> Tkinter"
	import Tkinter
	from Tkinter import *
	from Tkinter import Frame
	print "> subprocess"
	import subprocess
	print "> tkFileDialog"
	import tkFileDialog
	print "> shutil"
	import shutil
	print "> Image"
	try:
		from PIL import Image
	except ImportError:
		import Image
	print "> ImageOps"
	try:
		from PIL import ImageOps
	except ImportError:
		import ImageOps
	print "> ImageTk"
	try:
		from PIL import ImageTk
	except ImportError:
		import ImageTk
	print "Done"
except Exception as e:
	#because windows closes the window
	print e
	pause()
	raise e

if resize_height == 0:
	resize_width = 0
if resize_width < -1 or resize_height < -1:
	print "Note: resize is invalid. Not resizing."
	pause()
	resize_width = 0

# open a SPIDER image and convert to byte format
#im = Image.open(allImages[0])
#im = im.resize((250, 250), Image.ANTIALIAS)

#root = Tkinter.Tk()
# A root window for displaying objects

# Convert the Image object into a TkPhoto object
#tkimage = ImageTk.PhotoImage(im)

#Tkinter.Label(root, image=tkimage).pack()
# Put it in the display window

class MyApp(Tk):
	def getImages(self, dir):
		print "Scanning " + dir
		allImages = []
		for i in os.listdir(dir):
			b, e = os.path.splitext(i)
			if e.lower() not in image_extensions: continue
			allImages += [i]
		return allImages

	def __init__(self):
		Tk.__init__(self)
		
		self.inDir = os.getcwd()
		
		infiles = self.getImages(self.inDir)
		
		if not len(infiles):
			print "No images in the current directory. Please select a different directory."
			self.inDir = tkFileDialog.askdirectory(parent=self, initialdir="/",title='Please select a directory')
			if not len(self.inDir):
				print "No directory selected. Exiting."
				pause()
				raise SystemExit()
			self.inDir = os.path.normpath(self.inDir)
			infiles = self.getImages(self.inDir)
			if not len(infiles):
				print "No images found in " + self.inDir + ". Exiting."
				pause()
				raise SystemExit()
			print "Found", len(infiles), "images"
		else:
			print "Found", len(infiles), "images in the current directory"
		
		self.outDir = os.path.join(self.inDir, out_directory)

		if not os.path.exists(self.outDir):
			print "Creating output directory, " + self.outDir
			os.makedirs(self.outDir)
		
		print "Initializing GUI"
	
		self.grid_rowconfigure(0, weight=1)
		self.grid_columnconfigure(0, weight=1)
		self.geometry("1024x512")
		#self.resizable(0,0)
		
		self.files = infiles
		
		self.preview = None
		
		self.item = None
		self.cropIndex = 2
		self.x = 0
		self.y = 0
		self.current = 0

		#self.main = ScrolledCanvas(self)
		#self.main.grid(row=0, column=0, sticky='nsew')
		#self.c = self.main.canv
		
		#self.frame = Frame(self)
		#self.frame.grid(row=0, column=0, sticky='nsew')
		#self.frame.grid_rowconfigure(0, weight=1)
		#self.frame.grid_columnconfigure(0, weight=1)
		#self.c = Canvas(self.frame, bd=0, highlightthickness=0, background='black')
		#self.c.grid(row=0, column=0, sticky='nsew', padx=4, pady=4)
		
		self.controls = Frame(self)
		self.controls.grid(row=1, column=0, columnspan=2, sticky="nsew")
		self.buttons = []
		self.info = Label(self.controls, text="Pyar's Cropper")
		self.info.grid(row=0, column=0, sticky="nsew")
		
		self.inputs = []
		self.aspect = (StringVar(), StringVar())
		self.aspect[0].set("Ratio X")
		self.aspect[1].set("Ratio Y")
		self.inputs += [Entry(self.controls, textvariable=self.aspect[0])]
		self.inputs[-1].grid(row=0, column=1, sticky="nsew")
		self.inputs += [Entry(self.controls, textvariable=self.aspect[1])]
		self.inputs[-1].grid(row=0, column=2, sticky="nsew")
		
		self.buttons += [Button(self.controls, text="Prev", command=self.previous)]
		self.buttons[-1].grid(row=0, column=3, sticky="nsew")
		self.buttons += [Button(self.controls, text="Next", command=self.next)]
		self.buttons[-1].grid(row=0, column=4, sticky="nsew")
		self.buttons += [Button(self.controls, text="Copy", command=self.copy)]
		self.buttons[-1].grid(row=0, column=5, sticky="nsew")
		self.buttons += [Button(self.controls, text="Resize", command=self.resize)]
		self.buttons[-1].grid(row=0, column=6, sticky="nsew")
		self.buttons += [Button(self.controls, text="Crop", command=self.save_next)]
		self.buttons[-1].grid(row=0, column=7, sticky="nsew")
		
		self.restrictSizes = IntVar()
		self.inputs += [Checkbutton(self.controls, text="Perfect Pixel Ratio", variable=self.restrictSizes)]
		self.inputs[-1].grid(row=0, column=8, sticky="nsew")

		self.imageLabel = Canvas(self, highlightthickness=0)
		self.imageLabel.grid(row=0, column=0, sticky='nw', padx=0, pady=0)
		self.c = self.imageLabel
		
		self.previewLabel = Label(self, relief=FLAT, borderwidth=0)
		self.previewLabel.grid(row=0, column=1, sticky='nw', padx=0, pady=0)
		
		self.restrictSizes.set(0 if allow_fractional_size else 1)

		self.aspect[0].trace("w", self.on_aspect_changed)
		self.aspect[1].trace("w", self.on_aspect_changed)
		self.restrictSizes.trace("w", self.on_option_changed)
		self.bind('<space>', self.save_next)
		self.c.bind('<ButtonPress-1>', self.on_mouse_down)
		self.c.bind('<B1-Motion>', self.on_mouse_drag)
		self.c.bind('<ButtonRelease-1>', self.on_mouse_up)
		#self.c.bind('<Button-3>', self.on_right_click)
		self.bind('<Button-4>', self.on_mouse_scroll)
		self.bind('<Button-5>', self.on_mouse_scroll)
		self.bind('<MouseWheel>', self.on_mouse_scroll)
		
		print "Checking for existing crops"
		#self.load_imgfile(allImages[0])
		self.current = 0
		while self.current < len(self.files) and os.path.exists(os.path.join(self.outDir, self.files[self.current])):
			print "Skipping " + self.files[self.current] + ". Already cropped."
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

	def getRealBox(self):
		w, h = self.getCropSize()
		imw = self.imageOrigSize[0]
		imh = self.imageOrigSize[1]
		prevw = self.imagePhoto.width()
		prevh = self.imagePhoto.height()
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
		
	
	def previous(self):
		self.current -= 1
		self.current = (self.current + len(self.files)) % len(self.files)
		self.load_imgfile(self.files[self.current])
	
	def next(self):
		self.current += 1
		self.current = (self.current + len(self.files)) % len(self.files)
		self.load_imgfile(self.files[self.current])
		
	def copy(self):
		c = "copy \"" + os.path.join(self.inDir, self.currentName) + "\" \"" + os.path.join(self.outDir, self.currentName) + "\""
		print c
		shutil.copy(os.path.join(self.inDir, self.currentName), os.path.join(self.outDir, self.currentName))
		#subprocess.Popen(c, shell=True)
		#os.system(c)
		self.next()
	
	def resize(self):
		if not (resize_width > 0):
			print "Error: no resize specified. Not resizing"
			return
		c = "convert \"" + os.path.join(self.inDir, self.currentName) + "\""
		c += " -resize \"" + str(resize_width) + "x" + str(resize_height) + ">\""
		c += " \"" + os.path.join(self.outDir, self.currentName) + "\""
		print c
		subprocess.Popen(c, shell=True)
		print "Running"
		#os.system(c)
		self.next()
	
	def save_next(self, event=None):
		box = self.getRealBox()
		c = "convert \"" + os.path.join(self.inDir, self.currentName) + "\""
		c += " -crop " + str(box[2]-box[0]) + "x" + str(box[3]-box[1]) + "+" + str(box[0]) + "+" + str(box[1])
		if (resize_width > 0):
			c += " -resize \"" + str(resize_width) + "x" + str(resize_height) + ">\""
		c += " \"" + os.path.join(self.outDir, self.currentName) + "\""
		print c
		subprocess.Popen(c, shell=True)
		print "Running"
		#os.system(c)
		self.next()
		
	def load_imgfile(self, filename):		
		self.currentName = filename
		fullFilename = os.path.join(self.inDir, filename)
		print "Loading " + fullFilename
		img = Image.open(fullFilename)
		
		self.imageOrig = img
		self.imageOrigSize = (img.size[0], img.size[1])
		print "Image is " + str(self.imageOrigSize[0]) + "x" + str(self.imageOrigSize[1])
		
		basewidth = 512
		wpercent = (basewidth/float(img.size[0]))
		hsize = int((float(img.size[1])*float(wpercent)))
		if fast_preview:
			#does NOT create a copy so self.imageOrig is the same as self.image
			img.thumbnail((basewidth,hsize), Image.NEAREST)
		else:
			if antialiase_original_preview:
				img = img.resize((basewidth,hsize), Image.ANTIALIAS)
			else:
				img = img.copy()
				img.thumbnail((basewidth,hsize), Image.NEAREST)
		self.image = img
		print "Resized preview"
		
		#self.geometry("1024x"+str(hsize + 100))
		self.configure(relief='flat', background='red')

		self.imagePhoto = ImageTk.PhotoImage(self.image)
		self.imageLabel.configure(width=self.imagePhoto.width(), height=self.imagePhoto.height())
		self.imageLabel.create_image(0, 0, anchor=NW, image=self.imagePhoto)

		self.previewPhoto = ImageTk.PhotoImage(self.image)
		self.previewLabel.configure(image=self.previewPhoto)
		
		self.item = None
		
		self.on_aspect_changed(None, None, None) #update aspect ratio with new image size
		
		#self.imageLabel.pack(side = "left", fill = "both", expand = "yes")
		#self.previewLabel.pack(side = "left", fill = "both", expand = "yes")
		#self.c.pack(side = "bottom", fill = "both", expand = "yes")
		
		#self.c.xview_moveto(0)
		#self.c.yview_moveto(0)
		#self.c.config(scrollregion=self.c.bbox('all'))
	
	def test(self):
		if not allow_fractional_size:
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
			self.item = widget.create_rectangle(bbox, outline="yellow")
		else:
			widget.coords(self.item, *bbox)
			
	def update_preview(self, widget):
		if self.item:
			#get a crop for the preview
			#box = tuple((int(round(v)) for v in widget.coords(self.item)))
			box = self.getRealBox()
			pbox = self.getPreviewBox()
			if fast_preview:
				preview = self.image.crop(pbox) # region of interest
			else:
				preview = self.imageOrig.crop(box) # region of interest
			
			#add black borders for correct aspect ratio
			#if preview.size[0] > 512:
			preview.thumbnail(self.image.size, Image.ANTIALIAS) #downscale to preview rez
			paspect = preview.size[0]/float(preview.size[1])
			aspect = self.image.size[0]/float(self.image.size[1])
			if paspect < aspect:
				bbox = (0, 0, int(preview.size[1] * aspect), preview.size[1])
			else:
				bbox = (0, 0, preview.size[0], int(preview.size[0] / aspect))
			preview = ImageOps.expand(preview, border=(bbox[2]-preview.size[0], bbox[3]-preview.size[1]))
			#preview = ImageOps.fit(preview, size=self.image.size, method=Image.ANTIALIAS, bleed=-10.0)
			
			#resize to preview rez (if too small)
			self.preview = preview.resize(self.image.size, Image.ANTIALIAS)
			self.previewPhoto = ImageTk.PhotoImage(self.preview)
			self.previewLabel.configure(image=self.previewPhoto)
			
			print str(box[2]-box[0])+"x"+str(box[3]-box[1])+"+"+str(box[0])+"+"+str(box[1])
	
	def on_aspect_changed(self, event, var1, var2):
		try:
			x = float(self.aspect[0].get())
			y = float(self.aspect[1].get())
			if x < 0 or y < y:
				raise ZeroDivisionError()
			self.aspectRatio = x / y
		except:
			self.aspectRatio = float(self.imageOrigSize[0])/float(self.imageOrigSize[1])
		self.update_box(self.imageLabel)
		self.update_preview(self.imageLabel)
		
	def on_option_changed(self, event, var1, var2):
		global allow_fractional_size
		allow_fractional_size = (self.restrictSizes.get() == 0)
	
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
				print "At maximum"
				return
			while self.cropIndex > 1:
				self.cropIndex -= 1
				if self.test(): break
				
		print self.cropIndex
		
		self.update_box(self.imageLabel)
		self.update_preview(self.imageLabel)
	
	def on_mouse_down(self, event):
		self.x = event.x
		self.y = event.y
		self.update_box(event.widget)

	def on_mouse_drag(self, event):
		self.x = event.x
		self.y = event.y
		self.update_box(event.widget)

	def on_mouse_up(self, event):
		self.update_preview(event.widget)


app =  MyApp()
app.mainloop()

