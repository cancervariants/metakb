"""This module tests ioutils."""

import os
import uuid
import metakb.utils.ioutils as ioutils
import pytest
import gzip
import hashlib
import io


def test_ensure_directory():
    """Should create a directory."""
    dirname = str(uuid.uuid1())
    path = _path(_dir(), 'test', dirname)
    ioutils.ensure_directory(path)
    directory_created = os.path.isdir(path)
    if directory_created:
        os.rmdir(path)
    assert directory_created, 'Should have created new directory {}'.format(path)


def test_ensure_directoryraises_error():
    """Should raise an error if passed a file."""
    path = os.path.realpath(__file__)
    with pytest.raises(Exception):
        ioutils.ensure_directory(path)
        assert False, 'Should have raised an exception'


def test_gzip_emitter():
    """Should create a gz json file with gz by default."""
    path = _path(_dir(), 'test', 'anything.json')
    with ioutils.JSONEmitter(path) as emitter:
        emitter.write({'foo': 'bar'})
    assert os.path.isfile(path + '.gz'), 'Should create .gz'
    os.remove(path + '.gz')


def test_gzip_emitter_suffix():
    """Should create a gz json file with gz already appended."""
    path = _path(_dir(), 'test', 'anything.json.gz')
    with ioutils.JSONEmitter(path) as emitter:
        emitter.write({'foo': 'bar'})
    assert not os.path.isfile(path + '.gz'), 'Should not create .gz.gz'
    try:
        with gzip.open(path, 'rb') as f:
            file_content = f.read()
            assert file_content, 'Should have content'
    except Exception as e:
        assert False, 'should be return a gzip {}'.format(str(e))
    os.remove(path)


def test_plain_emitter():
    """Should create a json file."""
    path = _path(_dir(), 'test', 'anything.json')
    with ioutils.JSONEmitter(path, compresslevel=0) as emitter:
        emitter.write({'foo': 'bar'})
    assert os.path.isfile(path), 'Should create .json'
    os.remove(path)


def test_GzipBufferedTextReader():
    """Should read plain text zip file."""
    path = _path(_dir(), 'fixtures', 'test.txt.gz')
    with ioutils.GzipBufferedTextReader(path) as ins:
        for line in ins:
            assert line == 'any text ....\n', 'Should return expected text'


def test_GzipBufferedDictReader():
    """Should read csv or tsv zip file."""
    path = _path(_dir(), 'fixtures', 'test.csv.gz')
    ins = ioutils.GzipBufferedDictReader(path)
    for line in ins:
        assert isinstance(line, dict), 'Should return dict'
    path = _path(_dir(), 'fixtures', 'test.tsv.gz')
    ins = ioutils.GzipBufferedDictReader(path)
    for line in ins:
        assert isinstance(line, dict), 'Should return dict'
    # should support 'with'
    with ioutils.GzipBufferedDictReader(path) as ins:
        for line in ins:
            assert isinstance(line, dict), 'Should return dict'


def test_CsvReader():
    """Should read tsv or csv files."""
    path = _path(_dir(), 'fixtures', 'test.tsv')
    ins = ioutils.CsvReader(path)
    for line in ins:
        assert isinstance(line, dict), 'Should return dict'
    path = _path(_dir(), 'fixtures', 'test.csv')
    ins = ioutils.CsvReader(path)
    for line in ins:
        assert isinstance(line, dict), 'Should return dict'
    # should support 'with'
    with ioutils.CsvReader(path) as ins:
        for line in ins:
            assert isinstance(line, dict), 'Should return dict'


def test_JsonReader():
    """Should read tsv or csv files."""
    path = _path(_dir(), 'fixtures', 'test.json')
    ins = ioutils.JsonReader(path)
    for line in ins:
        assert isinstance(line, dict), 'Should return dict'
    path = _path(_dir(), 'fixtures', 'test.json.gz')
    ins = ioutils.JsonReader(path)
    for line in ins:
        assert isinstance(line, dict), 'Should return dict'
    # should support 'with'
    with ioutils.JsonReader(path) as ins:
        for line in ins:
            assert isinstance(line, dict), 'Should return dict'


def test_reader():
    """Should return appropriate reader."""
    path = _path(_dir(), 'fixtures', 'test.txt')
    assert str(ioutils.reader(path).__class__.__name__) == 'TextIOWrapper'
    path = _path(_dir(), 'fixtures', 'test.csv')
    assert str(ioutils.reader(path).__class__.__name__) == 'CsvReader'
    path = _path(_dir(), 'fixtures', 'test.tsv')
    assert str(ioutils.reader(path).__class__.__name__) == 'CsvReader'
    path = _path(_dir(), 'fixtures', 'test.txt.gz')
    assert str(ioutils.reader(path).__class__.__name__) == 'GzipBufferedTextReader'
    path = _path(_dir(), 'fixtures', 'test.csv.gz')
    assert str(ioutils.reader(path).__class__.__name__) == 'GzipBufferedDictReader'
    path = _path(_dir(), 'fixtures', 'test.tsv.gz')
    assert str(ioutils.reader(path).__class__.__name__) == 'GzipBufferedDictReader'
    path = _path(_dir(), 'fixtures', 'test.json')
    assert str(ioutils.reader(path).__class__.__name__) == 'JsonReader'
    path = _path(_dir(), 'fixtures', 'test.json.gz')
    assert str(ioutils.reader(path).__class__.__name__) == 'JsonReader'
    path = _path(_dir(), 'fixtures', 'test.unknown_type')
    assert str(ioutils.reader(path).__class__.__name__) == 'TextIOWrapper'


def test_reader_reader_class():
    """Should return specified reader."""
    path = _path(_dir(), 'fixtures', 'test.txt')
    assert str(ioutils.reader(path, reader_class=io.TextIOBase).__class__.__name__) == 'TextIOBase'
    path = _path(_dir(), 'fixtures', 'test.csv')
    assert str(ioutils.reader(path, reader_class=io.TextIOBase).__class__.__name__) == 'TextIOBase'
    path = _path(_dir(), 'fixtures', 'test.tsv')
    assert str(ioutils.reader(path, reader_class=io.TextIOBase).__class__.__name__) == 'TextIOBase'
    path = _path(_dir(), 'fixtures', 'test.txt.gz')
    assert str(ioutils.reader(path, reader_class=io.TextIOBase).__class__.__name__) == 'TextIOBase'
    path = _path(_dir(), 'fixtures', 'test.csv.gz')
    assert str(ioutils.reader(path, reader_class=io.TextIOBase).__class__.__name__) == 'TextIOBase'
    path = _path(_dir(), 'fixtures', 'test.tsv.gz')
    assert str(ioutils.reader(path, reader_class=io.TextIOBase).__class__.__name__) == 'TextIOBase'
    path = _path(_dir(), 'fixtures', 'test.json')
    assert str(ioutils.reader(path, reader_class=io.TextIOBase).__class__.__name__) == 'TextIOBase'
    path = _path(_dir(), 'fixtures', 'test.json.gz')
    assert str(ioutils.reader(path, reader_class=io.TextIOBase).__class__.__name__) == 'TextIOBase'
    path = _path(_dir(), 'fixtures', 'test.unknown_type')
    assert str(ioutils.reader(path, reader_class=io.TextIOBase).__class__.__name__) == 'TextIOBase'


def test_gzip_emitter_read():
    """Should create a gz file, and reader should be able to read it."""
    path = _path(_dir(), 'test', 'anything.json.gz')
    with ioutils.JSONEmitter(path) as emitter:
        emitter.write({'foo': 'bar'})
    try:
        input = ioutils.reader(path)
        for line in input:
            assert line['foo'] == 'bar'
    except Exception as e:
        assert False, 'should be able to read gzip {}'.format(str(e))

    os.remove(path)


def test_gzip_emitter_md5():
    """Two different files, with same content, should have same hash."""
    path1 = _path(_dir(), 'test', 'anything.json.gz')
    with ioutils.JSONEmitter(path1) as emitter:
        emitter.write({'foo': 'bar'})
    path2 = _path(_dir(), 'test', 'anything2.json.gz')
    with ioutils.JSONEmitter(path2) as emitter:
        emitter.write({'foo': 'bar'})
    h1 = hashlib.md5()
    h2 = hashlib.md5()
    with open(path1, mode='rb') as input:
        h1.update(input.read())
    with open(path2, mode='rb') as input:
        h2.update(input.read())
    assert h1.hexdigest() == h2.hexdigest(), 'Should have the same hash'
    os.remove(path1)
    os.remove(path2)


def _dir():
    """Return the directory of this file."""
    return os.path.dirname(os.path.realpath(__file__))


def _path(*args):
    """Join args as path."""
    return os.path.join(*args)
