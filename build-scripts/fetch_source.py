"""Download the SQLite amalgamation this fork builds against.

The version is pinned below rather than discovered, so two builds of the same
commit always contain the same SQLite. Bumping it is a deliberate edit: run
`--check` to see what upstream currently offers, then update all three
constants together and commit.
"""
from urllib.request import urlopen
import argparse
import hashlib
import os
import re
import shutil
import tempfile
import zipfile


# --- The pin. Update these three together; see --check. ----------------------
SQLITE_VERSION = '3.53.4'
SQLITE_YEAR = '2026'      # the release-year path segment on sqlite.org
# SHA3-256 as published on https://sqlite.org/download.html for the
# sqlite-amalgamation-<encoded>.zip of the version above.
SQLITE_SHA3_256 = '628a44cfe82c66aed1ccbbe85a562d2e33ebe64b3288981ed76285612227934e'
# ---------------------------------------------------------------------------

CUR_DIR = os.path.dirname(os.path.abspath(__file__))
DEST_DIR = os.path.join(CUR_DIR, '..')
DOWNLOAD_PAGE = 'https://sqlite.org/download.html'


def encode_version(version):
    """3.53.4 -> 3530400, the form used in sqlite.org filenames."""
    parts = [int(p) for p in version.split('.')]
    if len(parts) == 3:
        parts.append(0)
    major, minor, patch, build = parts
    return '%d%02d%02d%02d' % (major, minor, patch, build)


def amalgamation_url(version=SQLITE_VERSION, year=SQLITE_YEAR):
    return 'https://sqlite.org/%s/sqlite-amalgamation-%s.zip' % (
        year, encode_version(version))


def latest_upstream():
    """Report the newest amalgamation on the download page (version, year, sha3)."""
    try:
        with urlopen(DOWNLOAD_PAGE) as fh:
            html = fh.read().decode('utf8')
    except Exception as exc:
        raise RuntimeError('Could not reach the SQLite download page: %s' % exc)

    match = re.search(
        r"sqlite-amalgamation-(\d+)\.zip</a></nobr>.*?"
        r"amalgamation</a>, version ([\d.]+?)\.<br>.*?"
        r"SHA3-256:\s*([0-9a-f]{64})",
        html, re.DOTALL)
    if match is None:
        raise RuntimeError('Could not parse the amalgamation entry; the page '
                           'layout may have changed. Check %s' % DOWNLOAD_PAGE)
    encoded, version, sha3 = match.groups()

    year_match = re.search(r'(\d{4})/sqlite-amalgamation-%s\.zip' % encoded, html)
    year = year_match.group(1) if year_match else '?'
    return version.rstrip('.'), year, sha3


def download(version=SQLITE_VERSION, year=SQLITE_YEAR, sha3=SQLITE_SHA3_256):
    url = amalgamation_url(version, year)
    with tempfile.NamedTemporaryFile(suffix='.zip') as tmp:
        print('Downloading SQLite %s: %s' % (version, url))
        with urlopen(url) as fh:
            shutil.copyfileobj(fh, tmp)

        tmp.seek(0)
        digest = hashlib.sha3_256(tmp.read()).hexdigest()
        if digest != sha3:
            raise RuntimeError(
                'SHA3-256 mismatch for %s\n  expected: %s\n  got:      %s\n'
                'Refusing to build against unverified sources.'
                % (os.path.basename(url), sha3, digest))
        print('Verified SHA3-256: %s' % digest)

        tmp.seek(0)
        written = []
        with zipfile.ZipFile(tmp) as zf:
            for path in zf.namelist():
                filename = os.path.basename(path)
                if filename not in ('sqlite3.c', 'sqlite3.h'):
                    continue

                dest_filename = os.path.join(DEST_DIR, filename)
                with zf.open(path) as src, open(dest_filename, 'wb') as dest:
                    shutil.copyfileobj(src, dest)
                written.append(filename)

    missing = {'sqlite3.c', 'sqlite3.h'} - set(written)
    if missing:
        raise RuntimeError('Archive did not contain %s' % ', '.join(sorted(missing)))
    print('Wrote %s to %s' % (', '.join(written), os.path.realpath(DEST_DIR)))


def check():
    version, year, sha3 = latest_upstream()
    print('pinned here:    %s (%s)' % (SQLITE_VERSION, SQLITE_YEAR))
    print('latest upstream: %s (%s)' % (version, year))
    if version == SQLITE_VERSION:
        print('\nUp to date.')
        return 0

    print('\nA newer release exists. To adopt it, set in %s:' % __file__)
    print("    SQLITE_VERSION = '%s'" % version)
    print("    SQLITE_YEAR = '%s'" % year)
    print("    SQLITE_SHA3_256 = '%s'" % sha3)
    return 1


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true',
                        help='report the latest upstream release without '
                             'downloading; exits 1 if the pin is behind')
    args = parser.parse_args()
    if args.check:
        raise SystemExit(check())
    download()


if __name__ == '__main__':
    main()
