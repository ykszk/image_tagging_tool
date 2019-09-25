import os
from flask import Flask, render_template, request
import utils
app = Flask(__name__)
app.jinja_env.globals.update(zip=zip)

@app.route('/')
def index():
    checked_tags = []
    for image_name in image_names:
        try:
            filename = os.path.splitext(os.path.join(settings['tag_dir'],image_name))[0] + '.txt'
            checked_tags.append(set(utils.load_tags(filename)))
        except:
            checked_tags.append(set())

    title = "Image Tagging - " + settings['img_dir']
    return render_template('index.html',title=title,
                           tags=settings['tags'],
                           image_names=image_names,
                           image_paths=image_paths,
                           checked_tags=checked_tags)

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

    app.run(debug=True)