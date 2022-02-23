#! /usr/bin/python
import yaml
from argparse import ArgumentParser as ap
from fileEx import app
from fileEx.utils.path import path
import sys

config_path = path('/home/xlc/.config/fileEx/config.yaml')

def main():
    config    = open(config_path, 'r')
    config    = yaml.load(config, Loader=yaml.FullLoader)
    parse     = ap(prog='fileEx', description='API of fileEx.')
    subparses = parse.add_subparsers(help='Plugin in fileEx.')
    # Import the app and add the keys.
    for key in config.keys():
        _plugin = getattr(app, key).plugin.plugin
        _method = subparses.add_parser(key, help='The method of %s'%key)
        _plugin(_method)
    
    _main_args = parse.parse_args()

    for key in config.keys():
        _args_fun  = getattr(app, key).plugin.func
        if key in sys.argv:
            kwargs  = config[key]
            _args_fun(_main_args, **kwargs)
    
if __name__ == '__main__':
    main()
