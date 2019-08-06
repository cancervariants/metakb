"""Useful io utilities."""

import json
import gzip
import os
import csv
import io
import sys
from datetime import datetime


def ensure_directory(*args):
    """Create a directory."""
    path = os.path.join(*args)
    if os.path.isfile(path):
        raise Exception(
            "Output directory %s is a regular file", path)

    os.makedirs(path, exist_ok=True)


class JsonReader:
    def __init__(self, path):
        if path.endswith(".json.gz"):
            self.fp = io.TextIOWrapper(io.BufferedReader(gzip.GzipFile(path)))
        else:
            self.fp = open(path, "r", encoding='utf-8')

    def __iter__(self):
        return self

    def __next__(self):
        try:
            line = self.fp.readline()
            if len(line) < 1:
                raise IndexError()
            return json.loads(line)
        except IndexError:
            raise StopIteration()

    def __enter__(self):
        # create logic, already opened
        return self

    def __exit__(self, type, value, traceback):
        # ensure file closed
        self.fp.close()


class GzipBufferedTextReader(io.TextIOWrapper):
    """Wraps TextIOWrapper with buffered GzipFile reader."""
    def __init__(self, file, **kwargs):
        super().__init__(io.BufferedReader(gzip.GzipFile(file)), **kwargs)


class CsvReader(csv.DictReader):
    """Wraps csv.DictReader with tsv options."""
    def __init__(self, file, **kwargs):
        self.fp = open(file, "r")
        if file.endswith('.tsv'):
            super().__init__(self.fp, delimiter="\t", **kwargs)
        else:
            super().__init__(self.fp, **kwargs)

    def __enter__(self):
        # create logic, already opened
        return self

    def __exit__(self, type, value, traceback):
        # ensure file closed
        self.fp.close()


class GzipBufferedDictReader(csv.DictReader):
    """Wraps csv.DictReader with buffered GzipFile reader."""
    def __init__(self, file, **kwargs):
        if '.tsv' in file and 'delimiter' not in kwargs:
            kwargs['delimiter'] = '\t'
        self.fp = GzipBufferedTextReader(file)
        super().__init__(self.fp, **kwargs)

    def __enter__(self):
        # create logic, already opened
        return self

    def __exit__(self, type, value, traceback):
        # ensure file closed
        self.fp.close()


def recommended_reader(path):
    """Deduces a recommended reader class based on path."""
    if path.endswith(".csv.gz") or path.endswith(".tsv.gz"):
        return GzipBufferedDictReader
    if path.endswith(".json.gz") or path.endswith(".json"):
        return JsonReader
    if path.endswith(".gz"):
        return GzipBufferedTextReader
    if path.endswith(".tsv") or path.endswith(".csv"):
        return CsvReader
    return None


def reader(path, reader_class=None, **kwargs):
    """Construct a file reader object from file specified by path,
    or a DictReader object if the file is a .tsv, .csv, .json.
    Automatically handles gz
    """
    # no preference for reader specified, look up one of ours
    if not reader_class:
        reader_class = recommended_reader(path)
    # no reader, open in text mode
    if not reader_class:
        return open(path, "r")
    return reader_class(path, **kwargs)


class Rate:
    """Writes progress to stderr."""

    def __init__(self):
        """Initialize class vars."""
        self.i = 0
        self.start = None
        self.first = None

    def close(self):
        """Write final stats."""
        if self.i == 0:
            return

        self.log()
        dt = datetime.now() - self.first
        m = "\ntotal: {0:,} in {1:,d} seconds".format(self.i,
                                                      int(dt.total_seconds()))
        print(m, file=sys.stderr)

    def log(self):
        """Write stats."""
        if self.i == 0:
            return

        dt = datetime.now() - self.start
        self.start = datetime.now()
        rate = 1000 / dt.total_seconds()
        m = "rate: {0:,} emitted ({1:,d}/sec)".format(self.i, int(rate))
        print("\r" + m, end='', file=sys.stderr)

    def tick(self):
        """Increment stats."""
        if self.start is None:
            self.start = datetime.now()
            self.first = self.start

        self.i += 1

        if self.i % 1000 == 0:
            self.log()


class JSONEmitter():
    """Writes objects to disk as json, defaults to gz."""

    def __init__(self, path, compresslevel=9):
        """Ensure path exists, set compresslevel=0 or path contains gz to skip compression."""
        self.path = path
        self.compresslevel = compresslevel
        self.rate = Rate()

        ensure_directory(os.path.dirname(path))
        if compresslevel == 0 and not path.endswith('.gz'):
            self.fh = open(path, mode='wt')
        else:

            if 'gz' not in path:
                self.path = path + '.gz'
            # write with 0 mtime (ensures identical file each run)
            # in turn ensures md5 hash identical
            self.fh = gzip.GzipFile(
                filename='',
                compresslevel=self.compresslevel,
                fileobj=open(self.path, mode='wb'),
                mtime=0
            )

    def write(self, obj):
        """Write object as json + newline."""
        if self.compresslevel > 0:
            self.fh.write(json.dumps(obj).encode())
            self.fh.write('\n'.encode())
        else:
            self.fh.write(json.dumps(obj))
            self.fh.write('\n')
        self.rate.tick()

    def close(self):
        """Close the file."""
        self.fh.close()
        self.rate.close()

    # support 'with...'
    def __enter__(self):
        """Set things up."""
        return self

    def __exit__(self, type, value, traceback):
        """Tear things down."""
        self.close()
