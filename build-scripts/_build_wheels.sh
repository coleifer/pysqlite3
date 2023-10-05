#!/bin/bash

# Volume (cwd of build script) is mounted at /io.
# A checkout of pysqlite3 is cloned beforehand by the build.sh script.
cd /io/pysqlite3

sed -i "s|name='pysqlite3-binary'|name=PACKAGE_NAME|g" setup.py

PY36="/opt/python/cp36-cp36m/bin"
"${PY36}/python" setup.py build_static

PY37="/opt/python/cp37-cp37m/bin"
"${PY37}/python" setup.py build_static

PY38="/opt/python/cp38-cp38/bin"
"${PY38}/python" setup.py build_static

PY39="/opt/python/cp39-cp39/bin"
"${PY39}/python" setup.py build_static

PY310="/opt/python/cp310-cp310/bin"
"${PY310}/python" setup.py build_static

PY311="/opt/python/cp311-cp311/bin"
"${PY311}/python" setup.py build_static

PY312="/opt/python/cp312-cp312/bin"
"${PY312}/python" setup.py build_static

sed -i "s|name=PACKAGE_NAME|name='pysqlite3-binary'|g" setup.py

"${PY36}/pip" wheel /io/pysqlite3 -w /io/wheelhouse
"${PY37}/pip" wheel /io/pysqlite3 -w /io/wheelhouse
"${PY38}/pip" wheel /io/pysqlite3 -w /io/wheelhouse
"${PY39}/pip" wheel /io/pysqlite3 -w /io/wheelhouse
"${PY310}/pip" wheel /io/pysqlite3 -w /io/wheelhouse
"${PY311}/pip" wheel /io/pysqlite3 -w /io/wheelhouse
"${PY312}/pip" wheel /io/pysqlite3 -w /io/wheelhouse

for whl in /io/wheelhouse/*.whl; do
  auditwheel repair "$whl" -w /io/wheelhouse/
done
