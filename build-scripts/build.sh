#!/bin/bash

set -e -x

if [[ ! -d "sqlite" ]]; then
  wget https://www.sqlite.org/src/tarball/sqlite.tar.gz?r=release -O sqlite.tar.gz
  tar xzf sqlite.tar.gz
  cd sqlite/
  LIBS="-lm" ./configure --disable-tcl --enable-tempstore=always
  make sqlite3.c
  cd ../
  rm sqlite.tar.gz
fi

if [[ ! -d "./pysqlite3" ]]; then
  git clone git@github.com:coleifer/pysqlite3
fi

cp "sqlite/sqlite3.c" pysqlite3/
cp "sqlite/sqlite3.h" pysqlite3/

docker run -it -v $(pwd):/io quay.io/pypa/manylinux1_x86_64 /io/_build_wheels.sh
