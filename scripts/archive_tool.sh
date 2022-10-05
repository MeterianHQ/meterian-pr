#!/bin/bash

mkdir -p bin
cp README.md LICENSE dist/*/meterian-pr bin/
tar -zcf "$1" bin