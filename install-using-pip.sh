#!/bin/sh
if [ ! -f nopackage/__init__.py ]; then
    echo "Error: nopackage/__init__.py is missing. Run this from the nopackage repo."
    exit 1
fi
pip install --user `pwd`
