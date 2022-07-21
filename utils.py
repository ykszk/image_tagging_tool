import os
import functools
import toml
from pathlib import Path

def exception_handler(default_value=None):
    '''
    Wrap function with try and except. 'default_value' is returned on exception.
    '''
    def d(f):
        @functools.wraps(f)
        def wrapper(*args, **kwargs):
            try:
                return f(*args, **kwargs)
            except:
                return default_value
        return wrapper
    return d

def save_tags(filename, tags):
    with open(filename,'w') as f:
        f.write('\n'.join(tags))

@exception_handler([])
def load_tags(filename):
    with open(filename) as f:
        return f.read().split()

def load_settings(filename):
    filename = Path(filename)
    settings = {"server":{"threads": 10}, "multilabel": True}
    with open(filename) as f:
        settings.update(toml.load(f))
    if not Path(settings['tag_dir']).is_absolute():
        settings['tag_dir'] = str(filename.parent / settings['tag_dir'])
        settings['img_dir'] = str(filename.parent / settings['img_dir'])
    return settings
