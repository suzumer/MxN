import argparse
import mimetypes
import glob
import re
from pathlib import Path
from tempfile import TemporaryDirectory
from PIL import Image
from PIL import ImageColor
import ffmpeg

pillowdict = {'neighbor':Image.NEAREST,'bilinear':Image.BILINEAR,'bicubic':Image.BICUBIC,'lanczos':Image.LANCZOS}

def regex_size(arg, pat=re.compile(r'(\d+)(:|x)(\d+)')):
    match = pat.match(arg)
    if not match:
        raise argparse.ArgumentTypeError(arg + ' is incorrectly formatted, must be wxh or w:h')
    return (int(match.group(1)),int(match.group(3)))
def regex_color(arg, pat=re.compile(r'#[0-9A-Fa-f]{6}')):
    match = pat.match(arg)
    if not match:
        raise argparse.ArgumentTypeError(arg + ' is incorrectly formatted, must be wxh or w:h')
    return arg
def file_type(file):
    return mimetypes.guess_type(file)[0].split('/')[0]
def stretch(image, width, height,resample):
    return image.resize((width,height),resample=pillowdict[resample])    
def fit(image, width,height,resample,color):
    size = image.size
    newsize = None
    newpos = None
    newimage = Image.new(image.mode,(width,height),color)
    if size[0]/size[1] > width/height:
        newsize = (width, (width*size[1])//size[0])
        newpos = (0,(height-newsize[1])//2)
        image = image.resize(newsize,resample=pillowdict[resample])
    else:
        newsize = ((height*size[0])//size[1],height)
        newpos = ((width-newsize[0])//2,0)
        image = image.resize(newsize,resample=pillowdict[resample])
    newimage.paste(image,newpos)
    return newimage
def scale(image,width,height,resample):
    size = image.size
    newsize = None
    crop = None
    if size[0]/size[1] > width/height:
        newsize = ((height*size[0])//size[1],height)
        crop = ((newsize[0]-width)//2,0,((newsize[0]-width)//2) + width,height)
    else:
        newsize = (width, (width*size[1])//size[0])
        crop = (0,(newsize[1] - height)//2,width,((newsize[1] - height)//2) + height)
    image = image.resize(newsize,resample=pillowdict[resample])
    image = image.crop(crop)
    return image
def native(image,width,height,color):
    newimage = Image.new(image.mode,(width,height),color)
    size = image.size
    newimage.paste(image,((width-size[0])//2,(height-size[1])//2))
    return newimage
def compile_grid(images,size,tile,inborder,outborder,color):
    newimage = Image.new('RGB',
        ((size[0]*tile[1] + inborder*(tile[1]-1) + 2*outborder),
         (size[1]*tile[0] + inborder*(tile[0]-1) + 2*outborder)),color=ImageColor.getrgb(color))
    count = 0
    for row in range(tile[0]):
        for col in range(tile[1]):
            newimage.paste(images[count],(outborder+(inborder + size[0])*col,outborder+(inborder+size[1])*row))
            count += 1
    return newimage
def get_type(file):
    return mimetypes.guess_type(file)[0].split('/')[0]
def get_id(path):
    path = Path(path)
    noext = path.name.split('.')[0]
    id = noext.split('-')[0]
    return id
def audio_key(file):
    type_ = get_type(file)
    if type_ == 'video':
        return -1
    else:
        return 0
def video_key(file):
    type_ = get_type(file)
    if type_ == 'video':
        return -1
    elif type_ == 'image':
        return 0
    else:
        return 1
def format_files(files):
    types = ['Audio','Video']
    files = [f for f in files if get_type(f) in ['video','audio','image']]
    keys = set([get_id(file) for file in files])
    filedict = {key:{type_:[] for type_ in types} for key in keys}
    for file in files:
        streams = ffmpeg.get_streams(file)
        if 'Video' in streams:
            filedict[get_id(file)]['Video'].append(file)
        if 'Audio' in streams:
            filedict[get_id(file)]['Audio'].append(file)
    for id in filedict:
        filedict[id]['Audio'].sort(key=lambda x: audio_key(x))
        filedict[id]['Video'].sort(key=lambda x: video_key(x))
    sortedkeys = sorted(list(filedict.keys()))
    audiofiles = [filedict[id]['Audio'][0] if len(filedict[id]['Audio']) > 0 else None for id in sortedkeys]
    videofiles = [filedict[id]['Video'][0] if len(filedict[id]['Video']) > 0 else None for id in sortedkeys]
    return audiofiles,videofiles






parser = argparse.ArgumentParser(
    usage="MxN", description="A program to generate tiled displays for sites like 4chan")
parser.add_argument('--no-image', help='Disable all visual output',action='store_true')
parser.add_argument('--no-audio', help='Disable all audio output',action='store_true')
parser.add_argument('--move', help='If input files are videos, will display video rather than image',action='store_true')
parser.add_argument('--simul', help='Whether to play input simultaneously or not',action='store_true')
parser.add_argument('--fps', help='Framerate of the video if input is video and still isn\'t selected',type=int,default=30)
parser.add_argument('--length', help='Default media length that will be used if none supplied',type=int,default=6)
parser.add_argument('--seek', help='How will ffmpeg extract the frame if still selected',choices=['exact','thumbnail','keyframe'],default='thumbnail')
parser.add_argument('--ffmpeg-args', help='Arguments to be passed into FFMPEG if audio or video is used',default='')
parser.add_argument('--size',help='Size of each tile in the grid, formatted as widthxheight or width:height',type=regex_size,default= (300,300))
parser.add_argument('--tile',help='How to arrange the tiles, formatted as  rowsxcolumns or rows:columns',type=regex_size,default=(3,3))
parser.add_argument('--outborder',help='Size of the outer border in pixels',type=int,default=0)
parser.add_argument('--inborder',help='Size of the borders between tiles in pixels',type=int,default=0)
parser.add_argument('--color',help='The color of the background',type=regex_color,default='#000000')
parser.add_argument('--resample',help='How to resample the image when scaling',choices=['neighbor','bilinear','bicubic','lanczos'],default='bilinear')
parser.add_argument('--fit',help='How will each image be fitted into its respective tile',choices=['stretch','scale','fit','native'],default='scale')
parser.add_argument('output', help='Name of the output file')
args = parser.parse_args()

extension = get_type(args.output)

#flags to determine which files to use
useimages = ((extension == 'video' and not args.move) or extension == 'image') and not args.no_image
useaudio = (extension in ['video','image']) and not args.no_audio
usevideo = (extension == 'video' and args.move)

#scan image,audio,and video directories
files = glob.glob('input/*.*')
audiofiles,imagefiles = format_files(files)

tiles = args.tile[0] * args.tile[1]


if useimages:
    images = []
    for f in imagefiles:
        type_ = get_type(f)
        if type_ == 'image':
            images.append(Image.open(f))
        if type_ == 'video':
            images.append(ffmpeg.media_to_pillow(f,args.seek))
        if type_ == 'audio':
            images.append(ffmpeg.media_to_pillow(f,'audio'))
    if args.size == None:
        width = max(images,key=lambda x:x.size[0]).size[0]
        height = max(images,key=lambda x:x.size[1]).size[1]
        args.size = (width,height)
    count = 0
    
    if args.fit == 'scale':
        images = [scale(image,args.size[0],args.size[1],args.resample) for image in images]
    if args.fit == 'fit':
        images = [fit(image,args.size[0],args.size[1],args.resample,args.color) for image in images]
    if args.fit == 'native':
        images = [native(image,args.size[0],args.size[1],args.color) for image in images]
    if args.fit == 'stretch':
        images = [stretch(image,args.size[0],args.size[1],args.resample) for image in images]
    finalimage = compile_grid(images[0:tiles],args.size,args.tile,args.inborder,args.outborder,args.color)

    tempdir = TemporaryDirectory()
    outputfile = args.output if extension == 'image' else str(Path(tempdir.name) / "temp.png")
    finalimage.save(outputfile)

    if extension == 'video':
        ffmpeg.create_still_video(outputfile,audiofiles,args)

if usevideo:
    ffmpeg.create_moving_video(imagefiles,audiofiles,args)
    
