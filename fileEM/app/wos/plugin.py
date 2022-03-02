from fileEM.app.wos.wosSQL import wosOper, artprint
from argparse import ArgumentParser as ap
from pathlib import Path
import sys

__all__ = ['plugin']

def plugin(parent_parse:ap, **kwargs):
    subparses = parent_parse.add_subparsers()
    # Add new method in wos
    # Add Method
    add       = subparses.add_parser('add', help='Add method in WOS plugin.')
    add.add_argument(
                    '-f', '--file',
                    required = True,
                    help = 'Add the path of the Article.'
                    )
    add.add_argument(
                    '-d', '--doi',
                    required = True,
                    help = 'Add the DOI of the Article.'
                    )
    # Query Method
    query     = subparses.add_parser('query', help='Query method in WOS plugin.')
    query.add_argument(
                    '-a', '--author',
                    type=str,
                    default=None,
                    help='Query author',
                    nargs='+'
                    )
    query.add_argument(
                    '-t', '--title',
                    type=str,
                    default=None,
                    help='Query author',
                    nargs='+'
                    )
    query.add_argument(
                    '-j', '--journal',
                    type=str,
                    default=None,
                    help='Query journal'
                    )
    query.add_argument(
                    '-k', '--keyword',
                    type=str,
                    default=None,
                    help='Query keyword',
                    nargs='+'
                    )
    query.add_argument(
                    '-p', '--pubyear',
                    type=int,
                    default=None,
                    nargs=2,
                    help='Query publish year'
                    )

def func(args, **kwargs):
    pdfviewer = kwargs['viewer']
    query_dict = {}
    for key, value in args.__dict__.items():
        if value is not None:
            query_dict[key] = value
    if 'sid_path' not in kwargs.keys():
        raise Exception('The SID is must in WOS client.')
    if 'sql_path' not in kwargs.keys():
        raise Exception('The SQL path is must in WOS client.')
    _wos = wosOper(**kwargs)
    if 'add' in sys.argv:
        args.file = Path(args.file).expanduser().resolve()
        if not Path.is_file(Path(args.file)):
            print('Please enter the correct file location.')
            sys.exit(2)
        _wos.insert(args.doi, args.file)
    if 'query' in sys.argv:
        _info = _wos.query(**query_dict)
        if len(_info) == 0:
            print('No match returns!')
        elif len(_info) == 1:
            artprint(_info[0])
        elif len(_info) < 5:
            for _item in _info:
                artprint(_item)
        else:
            for _item in _info:
                artprint(_item, False)
