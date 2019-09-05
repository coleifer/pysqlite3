#!/bin/bash

cleanup="sqlite pysqlite3 wheelhouse"
for p in $cleanup; do
  if [[ -d "$p" ]]; then
    sudo rm -rf "$p"
  fi
done
