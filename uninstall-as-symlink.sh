#!/bin/bash

if [ ! -f "install-as-symlink.sh" ]; then
    echo "You must run this script from the nopackage repo (the same directory as runinplace.rc)"
    exit 1
fi

if [ -z "$FORCE" ]; then
    FORCE=false
fi

UNINSTALL=false

for arg in "$@"
do
    if [ "@$arg" == "@--force" ]; then
        FORCE=true
    else
        echo "Error: \"$arg\" is not a valid uninstall option."
        exit 1
    fi
done
MORE_ARGS=
if [ "@$FORCE" = "@true" ]; then
    MORE_ARGS="$MORE_ARGS --force"
fi
./install-as-symlink.sh --uninstall $MORE_ARGS
