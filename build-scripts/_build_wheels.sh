#!/bin/bash

# Volume (cwd of build script) is mounted at /io.
# A checkout of pysqlite3 is cloned beforehand by the build.sh script.
cd /io/pysqlite3

sed -i "s|name='pysqlite3-binary'|name=PACKAGE_NAME|g" setup.py

PY36="/opt/python/cp36-cp36m/bin"
"${PY36}/python" setup.py build_static

PY37="/opt/python/cp37-cp37m/bin"
"${PY37}/python" setup.py build_static

sed -i "s|name=PACKAGE_NAME|name='pysqlite3-binary'|g" setup.py

"${PY36}/pip" wheel /io/pysqlite3 -w /io/wheelhouse
"${PY37}/pip" wheel /io/pysqlite3 -w /io/wheelhouse

for whl in /io/wheelhouse/*.whl; do
  auditwheel repair "$whl" -w /io/wheelhouse/
done
