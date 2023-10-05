#!/bin/bash

set -e -x

# Fetch the source code for the latest release of Sqlite.
if [[ ! -d "sqlite" ]]; then
  wget https://www.sqlite.org/src/tarball/sqlite.tar.gz?r=release -O sqlite.tar.gz
  tar xzf sqlite.tar.gz
  cd sqlite/
  LIBS="-lm" ./configure --disable-tcl --enable-tempstore=always
  make sqlite3.c
  cd ../
  rm sqlite.tar.gz
fi

# Grab the pysqlite3 source code.
if [[ ! -d "./pysqlite3" ]]; then
  git clone git@github.com:coleifer/pysqlite3
fi

# Copy the sqlite3 source amalgamation into the pysqlite3 directory so we can
# create a self-contained extension module.
cp "sqlite/sqlite3.c" pysqlite3/
cp "sqlite/sqlite3.h" pysqlite3/

# Create the wheels and strip symbols to produce manylinux wheels.
docker run -it -v $(pwd):/io quay.io/pypa/manylinux2014_x86_64 /io/_build_wheels.sh

# Remove un-stripped wheels.
sudo rm ./wheelhouse/*-linux_*
