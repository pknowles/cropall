# cropall

![gui preview](doc/preview.jpg "GUI preview")

A small cross-platform python script to interactively crop and resize lots of
images images quickly. Image editors like gimp take way too long to start, open
an image, crop it, export it. A batch job/script can automate it but everything
gets cropped at the same positions. This app sits in the middle, automating
loading/clicking crop/save/next so your amazing human vision can be used to
quickly select what needs to be cropped and not wasted on navigating clunky GUI
hierarchies.

This is really a minimal GUI and preview for the following imagemagick command:

    convert in.jpg -crop <region> -resize <fit> out.jpg

This script actually uses imagemagick under the hood for its fast and high
quality resampling algorithms. The GUI shows a quick and low quality preview.

## Usage

Download a pre-built from the
[releases](https://github.com/pknowles/cropall/releases) section on github.
These are self contained packages created with pyinstaller.

Alternatively, grab the source and dependencies. I hope it's simple enough that
people with a little python experience can adapt it as needed.

```
git clone https://github.com/pknowles/cropall.git
cd cropall
python -m venv .venv
.venv/bin/activate
pip install -r requirements.txt
python cropall.py
```

Feel free to report issues and pull requests are most welcome, thank you! I
can't promise I'll get to them immediately sorry.

## Forks and alternatives

- [@rystraum](https://github.com/rystraum/cropall) has added a number of
  features such as rotation and keyboard shortcuts. See
  [#2](https://github.com/pknowles/cropall/issues/2).
- There's a great list of alternatives here:
  https://askubuntu.com/questions/97695/is-there-a-lightweight-tool-to-crop-images-quickly
- E.g.: https://github.com/weclaw1/inbac

## Additional

Do whatever you want with it, within GPL3. The usual
don't-blame-me-if-it-deletes-your-stuff.

