import os
import functools
import toml

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
    with open(filename) as f:
        settings = toml.load(f)
        return settings

def list_images(root_dir, exts = ['.png','.jpg','.jpeg'], recursive=True):
    items = [os.path.join(root_dir,item) for item in os.listdir(root_dir)]
    images = [item for item in items if os.path.splitext(item)[1] in exts]
    if recursive:
        dirs = [item for item in items if os.path.isdir(item)]
        images.extend(sum([list_images(d) for d in dirs], []))
    return images

if __name__ == "__main__":
    print(list_images('static/img')) # debug
