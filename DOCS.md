## Input file info
Input files must be placed in the 'input' folder
The name can be formatted in the following ways:
- id.mp4
- id-00_30.mp4
- id-00_30-7.mp4

The id is simply an identifier. Media will be displayed in the grid in id order.
The file name can also contain the time that the media should start at.
This should be in the same format as ffmpeg, except the ':' is replaced with '\_'
If time is supplied, then you can also supply a length specifier.
This is simply the length of the media expressed in seconds.

## Command line info
There are several command-line options that can be used with MxN. To get an overview, run:
```
python mxn.py -h
```
## Info not presented by the above command:

--resample accepts three options: 'neighbor','bilinear','bicubic', and 'lanczos'
Info for each option can be found on the following pages:
- [Pillow](https://pillow.readthedocs.io/en/stable/handbook/concepts.html#filters)
- [FFMPEG](https://ffmpeg.org/ffmpeg-scaler.html)

--fit accepts four options: 'stretch', 'scale', 'fit', and 'native'
- stretch simply stretches the input into the output shape
- scale resizes the input so that no padding is required, and crops it to the right size
- fit resizes the input to be large enough to fill the tile and then pads the rest
- native does not resize the input image and either pads or crops the image accordingly

--color should accept a color expressed in th format #ffffff

--no-audio hasn't been tested, and probably doesn't work
