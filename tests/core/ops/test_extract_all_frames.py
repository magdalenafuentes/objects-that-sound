import os
import shutil

import pytest

from core import ops


@pytest.fixture
def test_video_file():
    return 'tests/data/ops/test.mkv'


@pytest.fixture
def non_existing_test_video_file():
    return 'tests/data/ops/missing.mkv'


@pytest.fixture
def output_dir():
    return 'tests/.temp/ops/frames'


def test_extract_all_frames(test_video_file, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    ops.extract_all_frames(test_video_file, output_dir)
    assert os.path.exists(output_dir)
    assert len(os.listdir(output_dir)) == 184
    shutil.rmtree(os.path.dirname(output_dir))


def test_extract_all_frames_with_non_existing_video(non_existing_test_video_file, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    with pytest.raises(FileNotFoundError):
        ops.extract_all_frames(non_existing_test_video_file, output_dir)
    os.removedirs(output_dir)


def test_extract_all_frames_with_non_dir_output_dir(test_video_file, non_existing_test_video_file):
    with open(non_existing_test_video_file, 'a'):
        with pytest.raises(NotADirectoryError):
            ops.extract_all_frames(test_video_file, non_existing_test_video_file)
    os.remove(non_existing_test_video_file)


def test_extract_all_frames_should_create_output_parent_dir(test_video_file, output_dir):
    ops.extract_all_frames(test_video_file, output_dir)
    assert os.path.exists(output_dir)
    shutil.rmtree(os.path.dirname(output_dir))
