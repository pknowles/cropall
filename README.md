# cropall

A small cross-platform python script to make cropping and resizing images fast.
I'm surprised there aren't others out there. `click2crop` looks good but is not free.

This is basically a minimal GUI for an imagemagick `convert in.jpg -crop <stuff> -resize <stuff> out.jpg`
with a preview.

# Install

This needs...

-  python 2.7 (added to PATH)
   - python-pillow
   - python-pillow-tk
-  imagemagick (added to PATH)

# Instructions

1. Run the script (double click if the OS knows to open-with).

2. If there are images in the current working directory, it should start. Otherwise it will ask for a directory.

3. Click to select the region, scroll to adjust the size, click `crop` to start imagemagick and load the next image.

There are a few options at the top of the script file itself (I haven't bothered to provide GUI controls for some yet).


## Additional

Do whatever you want with it (GPL3). The usual don't-blame-me-if-it-deletes-your-stuff.

