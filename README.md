# MxN

## Requirements:
- python >= 3.8
- ffmpeg
- Pillow

To get Pillow, run:
```
pip install Pillow
```
## Overview
This is a simple command tool to create a grid of images or videos.
Simply create a folder named 'input',place the input files in the folder, and then call:
```
python mxn.py output.mp4
``` 
If you are uploading to a site like 4chan, you must specify the following arguments:
```
python mxn.py --ffmpeg-args "-c:v libvpx -c:a libvorbis -auto-alt-ref 0" output.webm
```  
Command line arguments an input file name formats are documented in the DOCS.md file.
