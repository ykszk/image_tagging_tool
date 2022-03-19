from pathlib import Path
from flask import Flask, Blueprint, render_template, request
import utils
app = Flask(__name__)
app.jinja_env.globals.update(zip=zip)
from collections import Counter


from abc import ABCMeta, abstractmethod


class DBBase(metaclass=ABCMeta):
    @abstractmethod
    def checked_tags(self):
        pass
    @abstractmethod
    def save_tags(self, key, tags):
        pass

    def query(self, include_tags, exclude_tags):
        queried_tags = include_tags | exclude_tags
        checked_tags = self.checked_tags()
        all_tags = sorted(settings['tags'])
        checked_tags_vectors = [[t in ct for t in all_tags if t in queried_tags] for ct in checked_tags]
        queried_tags_vector = [qt in include_tags for qt in sorted(queried_tags)]
        matches = [ctv==queried_tags_vector for ctv in checked_tags_vectors]
        return matches

class TXTDB(DBBase):
    def __init__(self, tag_filenames):
        self.tag_filenames = tag_filenames
    def checked_tags(self):
        return [set(utils.load_tags(filename)) for filename in self.tag_filenames]
    def save_tags(self, key, tags):
        image_filename = Path(settings['tag_dir']) / key
        tag_filename = Path(image_filename).with_suffix('.txt')
        utils.save_tags(tag_filename, tags)

import sqlalchemy
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, String
from sqlalchemy.orm import Session
Base = declarative_base()
class SQLite3DB(DBBase):
    class Record(Base):
        __tablename__ = "records"
        key = Column(String(length=1024), primary_key=True)
        data = Column(String(length=1024))
        def __init__(self, key, data):
            self.key = key
            self.data = data
        def tags(self):
            return set(self.data.split(','))
    def __init__(self, filename, keys, echo):
        self.engine = sqlalchemy.create_engine(filename, echo=echo)
        Base.metadata.create_all(bind=self.engine)

        self.keys = keys
        with Session(self.engine) as session:
            existing_keys = set((r.key for r in session.query(self.Record).all()))
            for key in keys:
                if key not in existing_keys:
                    record = self.Record(key, '')
                    session.add(record)
            session.commit()

    def checked_tags(self):
        with Session(self.engine) as session:
            ctags = [r.tags() for r in session.query(self.Record).all()]
        return ctags

    def save_tags(self, key, tags):
        with Session(self.engine) as session:
            record = session.query(self.Record).get(key)  
            record.data = ','.join(tags)
            session.commit()


@app.route('/')
def index():
    return render_template('index.html', tags=settings['tags'])

@app.route('/list')
def list_page():
    checked_tags = db.checked_tags()
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
    checked_tags = db.checked_tags()
    title = 'Query result for "{}"'.format(' & '.join([str(t)  if t in include_tags else ('-'+str(t)) for t in sorted(queried_tags)]))
    matches = db.query(include_tags, exclude_tags)
    title += ', {} images found'.format(sum(matches))
    return render_template('query.html',title=title,
                           tags=settings['tags'],
                           image_names=[e for m,e in zip(matches, image_names) if m],
                           image_paths=[e for m,e in zip(matches, image_paths) if m],
                           checked_tags=[e for m,e in zip(matches, checked_tags) if m]
    )

@app.route('/stats')
def stats():
    checked_tags = db.checked_tags()
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
    db.save_tags(request.args['name'], tags)
    return '', 200

import argparse
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Image tagging application.')
    parser.add_argument('-s','--settings', help="Setting file. (default: %(default)s)",metavar='<filename>',default='settings.toml')
    parser.add_argument('--debug',
                        help='Run in debug mode',
                        action='store_true')
    args = parser.parse_args()

    settings = utils.load_settings(args.settings)

    img_dir = Path(settings['img_dir'])
    IMAGE_URL = 'images'
    blueprint = Blueprint(IMAGE_URL, __name__, static_url_path='/images', static_folder=img_dir)
    app.register_blueprint(blueprint)
    image_paths = sorted(img_dir.glob("**/*['.png','.jpg','.jpeg']"))
    image_names = [str(image.relative_to(img_dir)) for image in image_paths]
    image_paths = [str(Path(IMAGE_URL) / p) for p in image_names]


    tag_dir = settings['tag_dir']
    if tag_dir.endswith('.sqlite3') or tag_dir.endswith('.db'):
        db = SQLite3DB('sqlite:///{}'.format(settings['tag_dir']), image_names, args.debug)
    else:
        tag_dir = Path(tag_dir)
        image_dirs = set([Path(name).parent for name in image_names])
        for d in image_dirs:
            (tag_dir / d).mkdir(parents=True, exist_ok=True)
        tag_filenames = [(tag_dir / image_name).with_suffix('.txt') for image_name in image_names]
        db = TXTDB(tag_filenames)
    if args.debug:
        settings.pop('threads', None)
        app.run(**settings['server'])
    else:
        print(settings['server'])
        from waitress import serve
        serve(app, **settings['server'])
