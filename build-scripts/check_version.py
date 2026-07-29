"""Check that the version, the SQLite pin, and the git tag all agree.

Three things have to say the same thing and nothing previously connected them:

  pyproject.toml    version = "0.6.1+sqlite.3.53.4"
  fetch_source.py   SQLITE_VERSION = '3.53.4'      -> must match the local segment
  the git tag       0.6.1  (or v0.6.1)             -> must match the base version

A mismatch is not a build failure, so without this the release just ships
confusingly-named assets: a release titled 0.6.1 full of 0.6.0 wheels, or a
`+sqlite.3.53.4` filename around a different SQLite.

Usage:
    python build-scripts/check_version.py            # version vs SQLite pin
    python build-scripts/check_version.py <tag>      # ...and vs the tag
"""
import os
import sys
import tomllib

CUR_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, CUR_DIR)
from fetch_source import SQLITE_VERSION  # noqa: E402

PYPROJECT = os.path.join(CUR_DIR, '..', 'pyproject.toml')


def split_version(version):
    """'0.6.1+sqlite.3.53.4' -> ('0.6.1', 'sqlite.3.53.4')"""
    base, _, local = version.partition('+')
    return base, local


def main(argv):
    with open(PYPROJECT, 'rb') as fh:
        version = tomllib.load(fh)['project']['version']
    base, local = split_version(version)

    print('pyproject version: %s' % version)
    print('  base:            %s' % base)
    print('  local segment:   %s' % (local or '<none>'))
    print('SQLite pin:        %s' % SQLITE_VERSION)

    errors = []

    expected_local = 'sqlite.%s' % SQLITE_VERSION
    if local != expected_local:
        errors.append(
            "Local version segment is '+%s' but the SQLite pin is %s.\n"
            "  Set version = \"%s+%s\" in pyproject.toml, or correct "
            "SQLITE_VERSION in build-scripts/fetch_source.py."
            % (local, SQLITE_VERSION, base, expected_local))

    if len(argv) > 1:
        tag = argv[1]
        # A leading 'v' is accepted in tags; the version itself never has one.
        normalized = tag[1:] if tag.startswith('v') else tag
        print('git tag:           %s' % tag)
        if normalized != base:
            errors.append(
                "Tag '%s' does not match the version in pyproject.toml (%s).\n"
                "  Either tag %s, or bump version to \"%s+%s\" and re-tag.\n"
                "  Note the tag carries only the base version -- the "
                "'+%s' segment is not part of it."
                % (tag, base, base, normalized, expected_local, expected_local))

    if errors:
        print('\n'.join(['', 'FAILED:'] + ['  * %s' % e for e in errors]),
              file=sys.stderr)
        return 1

    print('\nOK: version, SQLite pin%s agree.'
          % (' and tag' if len(argv) > 1 else ''))
    return 0


if __name__ == '__main__':
    raise SystemExit(main(sys.argv))
