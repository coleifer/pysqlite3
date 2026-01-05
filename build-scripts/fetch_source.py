from urllib.request import urlopen
import os
import re
import shutil
import tempfile
import zipfile


CUR_DIR = os.path.dirname(__file__)

def download():
    try:
        with urlopen('https://sqlite.org/download.html') as fh:
            html = fh.read().decode('utf8')
    except Exception as exc:
        raise RuntimeError('Could not download Sqlite amalgamation: %s' % exc)

    match = re.search(r'(\d{4}/sqlite-amalgamation-(\d+)\.zip)', html)
    if match is None:
        raise RuntimeError('Could not find Sqlite amalgamation on download page.')

    link, version = match.groups()
    url = 'https://sqlite.org/%s' % link
    with tempfile.NamedTemporaryFile(suffix='.zip') as tmp:
        print('Downloading sqlite source code: %s' % url)
        with urlopen(url) as fh:
            shutil.copyfileobj(fh, tmp)
        tmp.seek(0)
        with zipfile.ZipFile(tmp) as zf:
            for path in zf.namelist():
                filename = os.path.basename(path)
                if filename not in ('sqlite3.c', 'sqlite3.h'):
                    continue

                dest_filename = os.path.join(CUR_DIR, '../', filename)
                with zf.open(path) as src, open(dest_filename, 'wb') as dest:
                    shutil.copyfileobj(src, dest)


if __name__ == '__main__':
    download()
