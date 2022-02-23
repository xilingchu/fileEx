from pathlib import Path

def path(path_str:str, is_file:bool=True):
    '''
    Translate str to pathlib.path and make new directory if not exist.
    '''
    # Judge it is path or the file.
    _path = Path(path_str).expanduser().resolve()
    if is_file:
        _dir = _path.parent
    else:
        _dir = _path
    if not _dir.is_dir():
        _dir.mkdir(parents=True)
    return _path
