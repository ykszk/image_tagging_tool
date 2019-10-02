import os
from flask import Flask, render_template, request
import utils
app = Flask(__name__)
app.jinja_env.globals.update(zip=zip)
from collections import Counter

@app.route('/')
def index():
    return render_template('index.html', tags=settings['tags'])

@app.route('/list')
def list_page():
    checked_tags = [set(utils.load_tags(filename)) for filename in tag_filenames]
    title = "Image Tagging - " + settings['img_dir']
    return render_template('list.html',title=title,
                           tags=settings['tags'],
                           image_names=image_names,
                           image_paths=image_paths,
                           checked_tags=checked_tags)

@app.route('/query')
def query():
    include_tags = set([k for k, v in request.args.items() if v=='in'])
    exclude_tags = set([k for k, v in request.args.items() if v=='ex'])
    queried_tags = include_tags | exclude_tags
    checked_tags = [set(utils.load_tags(filename)) for filename in tag_filenames]
    all_tags = sorted(settings['tags'])
    checked_tags_vectors = [[t in ct for t in all_tags if t in queried_tags] for ct in checked_tags]
    queried_tags_vector = [qt in include_tags for qt in sorted(queried_tags)]
    title = 'Query result for "{}"'.format(' & '.join([str(t)  if t in include_tags else ('-'+str(t)) for t in sorted(queried_tags)]))
    matches = [ctv==queried_tags_vector for ctv in checked_tags_vectors]
    title += ', {} images found'.format(sum(matches))
    return render_template('query.html',title=title,
                           tags=settings['tags'],
                           image_names=[e for m,e in zip(matches, image_names) if m],
                           image_paths=[e for m,e in zip(matches, image_paths) if m],
                           checked_tags=[e for m,e in zip(matches, checked_tags) if m]
    )

@app.route('/stats')
def stats():
    checked_tags = [set(utils.load_tags(filename)) for filename in tag_filenames]
    delim = ' & '
    keys = [delim.join([str(t) for t in ct]) for ct in checked_tags]
    counts = Counter(keys)
    stats = []
    for k, v in counts.items():
        if k:
            queries = k.split(delim)
        else:
            queries = []
        url = '/query?' + '&'.join(
            ['{}=in'.format(q) for q in queries]+
            ['{}=ex'.format(q) for q in set(settings['tags'])-set(queries)]
        )
        stats.append((k,v,url))
    stats = sorted(stats, key=lambda s:-s[1])
    return render_template('stats.html', title='Statistics',
                           stats=stats)

@app.route('/put', methods=["PUT"])
def put():
    tags = sorted([k for k, v in request.form.items() if v=='on'])
    image_filename = os.path.join(settings['tag_dir'],request.args['name'])
    tag_filename = os.path.splitext(image_filename)[0] + '.txt'
    utils.save_tags(tag_filename, tags)
    return '', 200

import argparse
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Image tagging application.')
    parser.add_argument('-s','--settings', help="Setting file. (default: %(default)s)",metavar='<filename>',default='settings.toml')
    args = parser.parse_args()

    settings = utils.load_settings(args.settings)

    img_dir = settings['img_dir']
    image_paths = utils.list_images(img_dir)
    image_names = [image[len(img_dir)+1:] for image in image_paths]
    image_dirs = set([os.path.dirname(name) for name in image_names])
    for d in image_dirs: # create directories
        os.makedirs(os.path.join(settings['tag_dir'],d), exist_ok=True)

    tag_filenames = [os.path.splitext(os.path.join(settings['tag_dir'],image_name))[0] + '.txt' for image_name in image_names]

    app.run(**settings['server'])
