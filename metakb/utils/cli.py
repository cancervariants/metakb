"""Utility, sets common arguments."""
import argparse
import logging


def default_argument_parser(output_dir=None, description='A VICC metakb command line utility.'):
    """Construct a parser with common parameters."""
    parser = argparse.ArgumentParser(
        description=description,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--output_dir', type=str,
                        default=output_dir,
                        help='Path for output files.')
    parser.add_argument(
        '-d', '--debug',
        help="Print lots of debugging statements.",
        action="store_const", dest="loglevel", const=logging.DEBUG,
        default=logging.WARNING,
    )
    parser.add_argument(
        '-v', '--verbose',
        help="Be verbose.",
        action="store_const", dest="loglevel", const=logging.INFO,
    )
    return parser
