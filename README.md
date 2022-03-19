# Image Tagging Application #
![screenshot](static/demo/screenshot.png "screenshot")

## Prepare ##
1. Install packages

    pip install flask waitress toml sqlalchemy

2. Put image files in `static/imgs`
3. Edit config file `settings.toml`

## Run ##
```sh
python app.py
```
Open localhost:5000 in a web browser.

## Demo ##
```sh
python app.py --settings static/demo/settings.toml
# or below to use sqlite
python app.py --settings static/demo/settings.toml