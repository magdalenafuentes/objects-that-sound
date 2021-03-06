import os
import pprint
import random
import shutil
import stat
from operator import attrgetter, itemgetter

import math
import pandas as pd
import wget

import util.youtube as yt
from core import ops
from core.ontology import Ontology
from core.segments import SegmentsWrapper
from util.threading import fork


def init(data_dir, overwrite=False):
    dataset_files = {
        'assessments': [
            'http://storage.googleapis.com/us_audioset/youtube_corpus/v1/qa/qa_true_counts.csv',
            'http://storage.googleapis.com/us_audioset/youtube_corpus/v1/qa/rerated_video_ids.txt'
        ],
        'labels': [
            'http://storage.googleapis.com/us_audioset/youtube_corpus/v1/csv/class_labels_indices.csv',
            'https://raw.githubusercontent.com/audioset/ontology/master/ontology.json'
        ],
        'segments': [
            'http://storage.googleapis.com/us_audioset/youtube_corpus/v1/csv/eval_segments.csv',
            'http://storage.googleapis.com/us_audioset/youtube_corpus/v1/csv/balanced_train_segments.csv',
            'http://storage.googleapis.com/us_audioset/youtube_corpus/v1/csv/unbalanced_train_segments.csv'
        ]
    }

    for parent_dir, urls in dataset_files.items():
        print('\n', parent_dir, sep='')

        parent_dir = os.path.join(data_dir, parent_dir)
        os.makedirs(parent_dir, exist_ok=True)

        files = list(map(lambda x: x.split('/')[-1], urls))

        for file, url in zip(files, urls):
            filename = os.path.join(parent_dir, file)
            print(filename)

            if os.path.exists(filename):
                print('Exists.', end=' ')

                if not overwrite:
                    print('No overwrite.')
                    continue

                print('Overwriting.')
                os.chmod(filename, stat.S_IWUSR | stat.S_IREAD)
                os.remove(filename)

            wget.download(url, filename)
            os.chmod(filename, stat.S_IREAD | stat.S_IRGRP | stat.S_IROTH)
            print()

        print('Cleaning up {}.'.format(os.path.basename(parent_dir)))

        for file in os.listdir(parent_dir):
            if file not in files:
                os.remove(os.path.join(parent_dir, file))


def download(labels, data_dir, segments, ontology, limit=None, min_size=None, max_size=None, blacklist=None, seed=None):
    random.seed(seed)
    segments = SegmentsWrapper(segments, os.path.join(data_dir, 'raw'))
    ontology = Ontology(ontology, os.path.join(data_dir, 'videos'))

    if blacklist is None:
        blacklist = pd.DataFrame(columns=['YTID', 'reason'])
    else:
        blacklist = pd.read_csv(blacklist)

    def segment_in_ontology(o):
        def decorator(s):
            return any(map(o.__contains__, s.positive_labels))
        return decorator

    def filter_by_ontology(s):
        def decorator(o):
            return list(filter(segment_in_ontology(o), s))
        return decorator

    ontologies = ontology.retrieve(*labels)
    segments = list(filter(segment_in_ontology(ontologies), segments))

    ontologies = list(map(ontology.retrieve, labels))
    downloaded = list(filter(attrgetter('is_available'), segments))
    downloaded = map(filter_by_ontology(downloaded), ontologies)
    downloaded = zip(map(attrgetter('name'), ontologies), downloaded)

    counter = {name: s for name, s in downloaded}
    pprint.pprint({name: len(s) for name, s in counter.items()})

    random.shuffle(segments)

    for segment in segments:
        finished = limit is not None and all(map(limit.__le__, map(len, counter.values())))
        print(list(map(len, counter.values())))

        if finished:
            break

        if not any(map(lambda x: segment.ytid in x, counter.values())):

            if limit is not None:
                ok = True
                exceeded = list()

                for ont in ontologies:
                    if segment_in_ontology(ont)(segment) and len(counter[ont.name]) >= limit:
                        ok = False
                        exceeded.append(ont.proper_name)

                if not ok:
                    print('[{}] "{}" has reached limit.'.format(segment.ytid, exceeded))
                    continue

            blacklisted = blacklist[blacklist['YTID'] == segment.ytid]
            if not blacklisted.empty:
                print('[{}] is blacklisted. {}.'.format(*blacklisted.values[0]))
                continue

            info = yt.info(segment.ytid)
            if info == -1:
                continue

            formats = filter(lambda x: 'filesize' in x, info['formats'])
            filesizes = map(itemgetter('filesize'), formats)
            filesizes = list(filter(lambda x: x is not None, filesizes))
            filesize = int(max(filesizes) / 1024 / 1024) if filesizes else None

            if filesize is None:
                print('[{}] cannot retrieve filesize from youtube info'.format(segment.ytid))
                continue

            if min_size is not None and filesize < min_size:
                print('[{}] smaller than min_size ({} MiB).'.format(segment.ytid, filesize))
                continue

            if max_size is not None and filesize > max_size:
                print('[{}] exceeds max_size ({} MiB).'.format(segment.ytid, filesize))
                continue

            yt.dl(segment.ytid, outtmpl=segment.ydl_outtmpl)

            for ont in ontologies:
                if segment_in_ontology(ont)(segment):
                    counter[ont.name].append(segment)


def preprocess(data_dir, segments, workers=1):
    if not isinstance(workers, int):
        raise TypeError('WORKERS can\'t be of type {}'.format(type(workers).__name__))

    if workers < 0:
        raise ValueError('WORKERS must be positive (not {}).'.format(workers))

    def thread_print_function(thread_id):
        def decorator(*args, wait=False, **kwargs):
            end = '\r' if wait and workers == 1 else '\n'
            if workers > 1:
                args = ('[Thread {}]'.format(thread_id),) + args
            print(*args, **kwargs, end=end)
        return decorator

    def thread_function(thread_id, thread_segments):
        print_function = thread_print_function(thread_id)

        for i, segment in enumerate(thread_segments):
            print_function('{}: ({} / {})'.format(segment.ytid, i+1, len(thread_segments)))
            print_function('{}: Extracting frames'.format(segment.ytid), wait=True)

            ops.extract_frames(segment.raw, segment.frames_dir, segment.start_seconds)

            print_function('{}: Extracting frames (finished)'.format(segment.ytid))
            print_function('{}: Computing spectrograms'.format(segment.ytid), wait=True)

            waveform, sr = segment.waveform
            for j in range(segment.start_frames, min(segment.end_frames, len(segment))):
                if workers == 1:
                    print_function('{}: Computing spectrograms ({})'.format(segment.ytid, j), wait=True)

                if not os.path.exists(segment.spectrogram(j)):
                    start_samples = segment.get_sample_index(j)
                    samples_slice = slice(start_samples, start_samples+segment.sample_rate)
                    ops.compute_spectrogram(waveform[samples_slice], segment.spectrogram(j))

            print_function('{}: Computing spectrograms (finished)'.format(segment.ytid))

    segments = SegmentsWrapper(segments, os.path.join(data_dir, 'raw'))
    segments = list(filter(attrgetter('is_available'), segments))

    thread_args = list()

    for idx in range(workers):
        thread_size = math.ceil(len(segments) / workers)
        thread_start = idx * thread_size
        thread_args.append((idx, segments[thread_start:thread_start + thread_size]))

    fork(workers, thread_function, *thread_args)


def cleanup(data_dir, segments, audio, frames, spectrograms):
    segments = SegmentsWrapper(segments, os.path.join(data_dir, 'raw'))
    segments = list(filter(attrgetter('is_available'), segments))

    for s in segments:
        if os.path.exists(s.wav) and audio:
            print(f'{s.ytid}: Deleting audio...', end='\r')
            os.remove(s.wav)
            print(f'{s.ytid}: Deleting audio OK')

        if os.path.exists(s.frames_dir) and frames:
            print(f'{s.ytid}: Deleting frames...', end='\r')
            shutil.rmtree(s.frames_dir)
            print(f'{s.ytid}: Deleting frames OK')

        if os.path.exists(s.spectrograms_dir) and spectrograms:
            print(f'{s.ytid}: Deleting spectrograms...', end='\r')
            shutil.rmtree(s.spectrograms_dir)
            print(f'{s.ytid}: Deleting spectrograms OK')


def compress_segments(data_dir, segments, ontology, labels, output_file):
    raw_dir = os.path.join(data_dir, 'raw')
    segments = SegmentsWrapper(segments, raw_dir)
    ontology = Ontology(ontology, os.path.join(data_dir, 'videos'))

    def transform_segment(s):
        return (s.ytid,
                str(float(s.start_seconds)),
                str(float(s.end_seconds)),
                '"{}"'.format(','.join(s.positive_labels)))

    def segment_in_ontology(o):
        def decorator(s):
            return any(map(o.__contains__, s.positive_labels))
        return decorator

    ontologies = ontology.retrieve(*labels)

    available_segments = os.listdir(raw_dir)
    available_segments = filter(segments.__contains__, available_segments)
    available_segments = map(segments.__getitem__, available_segments)
    available_segments = filter(attrgetter('is_available'), available_segments)
    available_segments = filter(segment_in_ontology(ontologies), available_segments)
    available_segments = map(transform_segment, available_segments)
    available_segments = map(', '.join, available_segments)
    available_segments = '\n'.join(available_segments)

    with open(output_file, 'w') as outfile:
        outfile.write(available_segments)

    print('Segments file saved to', output_file)
