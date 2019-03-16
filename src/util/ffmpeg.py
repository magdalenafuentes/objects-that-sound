import os
import shutil
import subprocess


def ffmpeg(infile, outfile, *flags, **options):
    if not shutil.which('ffmpeg'):
        raise AssertionError('ffmpeg not available')

    if not os.path.exists(infile):
        raise FileNotFoundError('INFILE ({})'.format(infile))

    if not os.path.exists(os.path.dirname(outfile)):
        os.makedirs(os.path.dirname(outfile))

    command = 'ffmpeg -i {infile} {flags} {options} -loglevel panic -hide_banner -y {outfile}'.format(
        infile=infile,
        outfile=outfile,
        flags=' '.join(map(lambda flag: '-' + flag, flags)),
        options=' '.join(map(lambda item: '-{} {}'.format(*item), options.items())))

    try:
        output = subprocess.check_output(command.split())
        return output.decode()
    except subprocess.SubprocessError:
        raise RuntimeError('FFMPEG ({})'.format(command))


def ffprobe(input_file, *flags, **options):
    if not shutil.which('ffprobe'):
        raise AssertionError('ffprobe not available')

    if not os.path.exists(input_file):
        raise FileNotFoundError('INFILE ({})'.format(input_file))

    command = 'ffprobe {flags} {options} -hide_banner {input_file}'.format(
        input_file=input_file,
        flags=' '.join(map(lambda flag: '-' + flag, flags)),
        options=' '.join(map(lambda item: '-{} {}'.format(*item), options.items())))

    try:
        output = subprocess.check_output(command.split())
        return output.decode()
    except subprocess.SubprocessError:
        raise RuntimeError('FFPROBE ({})'.format(command))
