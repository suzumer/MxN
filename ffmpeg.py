#take in video and return Pillow file with keyframe
from tempfile import TemporaryDirectory
from PIL import Image
from pathlib import Path
import subprocess
import re
import mimetypes
import string

def get_type(file):
    return mimetypes.guess_type(file)[0].split('/')[0]

def loop_parse(start, before, after, args,code):
    return (f"loop=loop={before*args.fps}:size=1:start=0,loop=loop={after*args.fps}:size=1:start={start*args.fps}," if not args.simul else "" ) + f"setpts=N/FRAME_RATE/TB[{code}];"
def stretch(files,args):
    lengths = [get_length(file,args.length) for file in files]
    befores = [sum(lengths[:x]) for x in range(len(lengths))]
    starts = [sum(lengths[:x+1]) for x in range(len(lengths))]
    afters = [sum(lengths[x+1:]) for x in range(len(lengths))]
    filtergraph = ''
    count = 1
    code = new_code()
    codes = []
    for before,after,start in zip(befores,afters,starts):
        filtergraph += f"[{count}:v]scale={args.size[0]}:{args.size[1]},framerate=fps={args.fps}," + loop_parse(start, before, after, args,code)
        codes.append(code)
        code = new_code(code)
        count += 1
    grid,code = create_grid(codes,args)
    filtergraph += grid
    return filtergraph, code
def native(files,args):
    lengths = [get_length(file,args.length) for file in files]
    befores = [sum(lengths[:x]) for x in range(len(lengths))]
    starts = [sum(lengths[:x+1]) for x in range(len(lengths))]
    afters = [sum(lengths[x+1:]) for x in range(len(lengths))]
    filtergraph = ''
    count = 1
    code = new_code()
    codes = []
    for before,after,start in zip(befores,afters,starts):
        filtergraph += f"color=color={args.color}:r={args.fps}:size={args.size[0]}x{args.size[1]}[{code}];[{code}][{count}:v]overlay=(W-w)/2:(H-h)/2," + loop_parse(start, before, after, args,code)
        codes.append(code)
        code = new_code(code)
        count += 1
    grid,code = create_grid(codes,args)
    filtergraph += grid
    return filtergraph, code

def scale(files,args):
    lengths = [get_length(file,args.length) for file in files]
    befores = [sum(lengths[:x]) for x in range(len(lengths))]
    starts = [sum(lengths[:x+1]) for x in range(len(lengths))]
    afters = [sum(lengths[x+1:]) for x in range(len(lengths))]
    filtergraph = ''
    count = 1
    code = new_code()
    codes = []
    for before,after,start in zip(befores,afters,starts):
        filtergraph += f"[{count}:v]scale='if(gt(iw/ih,{args.size[0]}/{args.size[1]}),-1,{args.size[0]})':'if(gt(iw/ih,{args.size[0]}/{args.size[1]}),{args.size[1]},-1)',crop={args.size[0]}:{args.size[1]},framerate=fps={args.fps}," + loop_parse(start, before, after, args,code)
        codes.append(code)
        code = new_code(code)
        count += 1
    grid,code = create_grid(codes,args)
    filtergraph += grid
    return filtergraph, code
def fit(files,args):
    lengths = [get_length(file,args.legnth) for file in files]
    befores = [sum(lengths[:x]) for x in range(len(lengths))]
    starts = [sum(lengths[:x+1]) for x in range(len(lengths))]
    afters = [sum(lengths[x+1:]) for x in range(len(lengths))]
    filtergraph = ''
    count = 1
    code = new_code()
    othercode = new_code('fff')
    codes = []
    for before,after,start in zip(befores,afters,starts):
        filtergraph += f"color=color={args.color}:r={args.fps}:size={args.size[0]}x{args.size[1]}[{code}];[{count}:v]scale='if(gt(iw/ih,{args.size[0]}/{args.size[1]}),{args.size[0]},-1)':'if(gt(iw/ih,{args.size[0]}/{args.size[1]}),-1,{args.size[1]})'[{othercode}];[{code}][{othercode}]overlay=(W-w)/2:(H-h)/2," + loop_parse(start, before, after, args,code)
        codes.append(code)
        code = new_code(code)
        count += 1
    grid, code = create_grid(codes,args)
    filtergraph += grid
    return filtergraph,code
methoddict = {'native':native,'scale':scale,'fit':fit,'stretch':stretch}
def get_timestamp(path):
    path = Path(path)
    noext = path.name.split('.')[0]
    if '-' in noext:
        noext = noext.split('-')[1].replace('_',':')
    else:
        noext = '00:00'
    return noext
def get_length(path,default):
    path = Path(path)
    noext = path.name.split('.')[0]
    if noext.count('-') == 2:
        noext = noext.split('-')[2]
    else:
        noext = default
    return int(noext)

def get_streams(file):
    pat=re.compile(r'Stream #\d+:\d+(?:\(\w+\))?: (\w+):')
    run = subprocess.run(['ffprobe','-hide_banner',file],capture_output=True)
    streams = pat.findall(run.stderr.decode('UTF-8'))
    return streams

def media_to_pillow(file,seek):
    tempdir = TemporaryDirectory()
    path = Path(file)
    imagepath = str(Path(tempdir.name) / 'output.png')
    time = get_timestamp(path)
    if seek == 'audio':
        subprocess.run(["ffmpeg", '-i',file,'-frames:v','1', imagepath])
    if seek == 'exact':
        subprocess.run(["ffmpeg","-ss", time, '-i',file,'-frames:v','1', imagepath])
    if seek == 'keyframe':
        subprocess.run(["ffmpeg","-ss", time, '-skip_frame',"nokey", '-i',file, '-frames:v','1', imagepath])
    if seek == 'thumbnail':
        subprocess.run(["ffmpeg","-ss", time, '-i',file,'-frames:v','1','-vf','thumbnail', imagepath])
    image = Image.open(imagepath)
    imagecopy = image.copy()
    image.close()
    tempdir.cleanup()
    return imagecopy

def new_code(old_code='_'):
    if old_code == '_':
        return 'a'
    code = int(''.join([str(string.ascii_lowercase.find(letter)) for letter in old_code]))
    code += 1
    newcode = ''.join([string.ascii_lowercase[int(number)] for number in str(code)])
    return newcode
def create_audio(files,directory,deflength):
    lengths = [get_length(file,deflength) for file in files]
    codes = []
    for i in range(len(lengths)):
        if i == 0:
            codes.append(new_code())
        else:
            codes.append(new_code(codes[-1]))
    directory = Path(directory)
    array = ['ffmpeg','-y']
    for file in files:
        array.append('-ss')
        array.append(get_timestamp(file))
        array.append('-i')
        array.append(file)
    array.append('-filter_complex')
    filtergraph = [f"[{count}:a]atrim=0:{length}[{code}];" for length,count,code in zip(lengths,range(len(lengths)),codes)]
    filtergraph +=  [f'[{code}]' for code in codes] + [f'concat=n={len(lengths)}:v=0:a=1[{new_code(codes[-1])}]']
    filtergraph = ''.join(filtergraph)
    array.append(filtergraph)
    array += ['-map',f'[{new_code(codes[-1])}]','-vn','-ac','2']
    array.append(str(directory / 'output.wav'))
    print(' '.join(array))
    subprocess.run(array)
    return str(directory / 'output.wav')
def create_still_video(imagefile,audiofiles,args):
    audiodirectory = TemporaryDirectory()
    audiofiles = audiofiles[:args.tile[0]*args.tile[1]]
    audiofile = create_audio(audiofiles,audiodirectory.name,args.length)
    array = ['ffmpeg','-y','-i',audiofile,'-i',imagefile]
    array += args.ffmpeg_args.split()
    array.append(args.output)
    subprocess.run(array)
    audiodirectory.cleanup()
    return
    
def create_moving_video(imagefiles,audiofiles,args):
    audiodirectory = TemporaryDirectory()
    audiofile = create_audio(audiofiles,audiodirectory.name,args.length)
    imagefiles = imagefiles[:args.tile[0]*args.tile[1]]
    lengths = [get_length(file,args.length) for file in imagefiles]
    array = ['ffmpeg','-y','-i',audiofile]
    for file in imagefiles:
        type_ = get_type(file)
        if type_ not in ['audio','image']:
            array.append('-ss')
            array.append(get_timestamp(file))
        array.append('-i')
        array.append(file)
    array.append('-sws_flags')
    array.append(args.resample)
    array.append('-filter_complex')
    filter_graph,code = methoddict[args.fit](imagefiles,args)
    array.append(filter_graph)
    array += ['-map',f'[{code}]','-map','0:a:0','-t',f'{sum(lengths)}']
    array += args.ffmpeg_args.split()
    array.append(args.output)
    print(' '.join(array))
    subprocess.run(array)
    audiodirectory.cleanup()
    return

def create_grid(codes,args):
    code = 'ffffff'
    filtergraph = f'color=color={args.color}:size={args.size[0]*args.tile[1] + args.inborder*(args.tile[1]-1) + args.outborder*2}x{args.size[1]*args.tile[0] + args.inborder*(args.tile[0]-1) + args.outborder*2}:r={args.fps}[{code}];'
    count = 0
    for row in range(args.tile[0]):
        for col in range(args.tile[1]):
            filtergraph += f'[{code}][{codes[count]}]overlay={args.outborder+(args.inborder + args.size[0])*col}:{args.outborder+(args.inborder+args.size[1])*row}[{(code:=new_code(code))}];'
            count += 1
    filtergraph += f'[{code}]setpts=N/FRAME_RATE/TB[{(code:=new_code(code))}]'
    return filtergraph, code

