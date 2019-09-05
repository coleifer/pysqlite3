#!/bin/bash

cleanup="sqlite pysqlite3 wheelhouse"
for p in $cleanup; do
  if [[ -d "$p" ]]; then
    rm -rf "$p"
  fi
done
