"""This module tests requests cli."""
from metakb.utils.cli import default_argument_parser


def test_default_argument_parser():
    """Should create a parser with a cache file."""
    parser = default_argument_parser(output_dir='foo')
    args = parser.parse_args()
    assert args.output_dir == 'foo', 'Should have my output_dir'
