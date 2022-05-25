#!/bin/bash
echo
. runinplace.rc
if [ $? -ne 0 ]; then
    echo "Error: runinplace.rc didn't run successfully. You must run this script from the nopackage repo (the same directory as runinplace.rc)"
    exit 1
fi

src_sc="nopackage/usr/share/applications/nopackage.desktop"
if [ ! -f "$src_sc" ]; then
    echo "Error: \"$src_sc\" is missing. You must run this script from the nopackage repo (the same directory as runinplace.rc)"
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
    elif [ "@$arg" == "@--uninstall" ]; then
        UNINSTALL=true
    else
        echo "Error: \"$arg\" is not a valid option."
        exit 1
    fi
done
verb="install"
redo_verb="reinstall"
dst_bins="$PREFIX/bin"
dst_bin="$dst_bins/nopackage"

if [ -d "$dst_bin" ]; then
    # Fix a glitch from an earlier version of this script:
    rmdir "$dst_bin"
fi

if [ "@$UNINSTALL" = "@true" ]; then
    verb="uninstall"
    redo_verb="uninstall"
elif [ ! -d "$dst_bins" ]; then
    mkdir -p "$dst_bins"
    if [ $? -ne 0 ]; then exit 1; fi
    echo "WARNING: $dst_bins didn't exist. Ensure it is in your path by adding a line such as the following to \"~/.bash_profile\":"
    echo 'PATH=$PATH:$HOME/.local/bin:$HOME/bin'
fi

if [ -f "$dst_bin" ]; then
    existing_src="`readlink $dst_bin`"
    if [ -z "$existing_src" ]; then
        rm "$dst_bin"
        if [ $? -ne 0 ]; then exit 1; fi
        echo "* removed existing $dst_bin"
    else
        if "@$FORCE" = "@true" ]; then
            rm "$dst_bin"
            if [ $? -ne 0 ]; then exit 1; fi
            echo "* removed existing $dst_bin (symlink)"
        else
            echo "Error: \"$dst_bin\" already exists and is a symlink. Use --force to delete the file and $redo_verb."
            exit 1
        fi
    fi
fi

if [ -f "$dst_bin" ]; then
    if [ ! -z "`readlink $dst_bin`" ]; then
        echo "Error: There is a logic error in $0 $@. The existing $dst_bin is a symlink but that should already have been addressed (if --force). Otherwise, an exit code should have been returned by now."
        exit 1
    fi
    echo "Error: There is a logic error in $0 $@. There is an existing $dst_bin but that should already have been addressed (if --force). Otherwise, an exit code should have been returned by now."
    exit 1
else
    if [ "@$UNINSTALL" = "@true" ]; then
        echo "* \"$dst_bin\"...OK (already uninstalled)"
    fi
fi
if [ "@$UNINSTALL" != "@true" ]; then
    printf "* writing $dst_bin..."
    cat > "$dst_bin" << END
#!/usr/bin/python3
# -*- coding: utf-8 -*-
import re
import sys
sys.path.insert(0, "$src_repo")
from nopackage import main
if __name__ == '__main__':
    sys.argv[0] = re.sub(r'(-script\.pyw|\.exe)?$', '', sys.argv[0])
    sys.exit(main())
END
    if [ $? -ne 0 ]; then exit 1; fi
    echo "OK"
    printf "* setting $dst_bin as executable..."
    chmod +x $dst_bin
    if [ $? -ne 0 ]; then exit 1; fi
    echo "OK"
fi

OLD_dst_sc="$PREFIX/share/applications/install_any.desktop"
if [ -f "$OLD_dst_sc" ]; then
    rm "$OLD_dst_sc"
    if [ $? -ne 0 ]; then exit 1; fi
    echo "* removed deprecated $OLD_dst_sc"
fi

dst_sc="$PREFIX/share/applications/nopackage.desktop"
if [ "@$UNINSTALL" = "@true" ]; then
    if [ -f "$dst_sc" ]; then
        printf "* removing \"$dst_sc\"..."
        rm "$dst_sc"
        code=$?
        if [ $code -eq 0 ]; then
            echo "OK"
        else
            echo "FAILED (line $LINENO)"
            exit $code
        fi
    else
        echo "* \"$dst_sc\"...OK (already uninstalled)"
    fi
    echo
    echo "Uninstall is complete."
    echo
    exit 0
else
    printf "* copying \"$dst_sc\"..."
    cp "$src_sc" "$dst_sc"
fi
code=$?
if [ $code -eq 0 ]; then
    echo "OK"
else
    echo "FAILED (line $LINENO)"
    exit $code
fi
# echo "Path=$HOME/.local/lib/nopackage" >> "$dst_sc"
echo "Path=$src_repo" >> "$dst_sc"
# ^ for metadata
echo "Exec=$dst_bin" >> "$dst_sc"
printf "* installing \"$dst_sc\"..."
xdg-desktop-icon install --novendor $dst_sc
code=$?
if [ $code -eq 0 ]; then
    echo "OK"
else
    echo "FAILED ($LINENO)"
    exit $code
fi

echo
echo "Install is complete."
echo
