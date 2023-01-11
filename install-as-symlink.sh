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
if [ "@$UNINSTALL" = "@true" ]; then
    verb="uninstall"
    redo_verb="uninstall"
# elif [ ! -d "$dst_libs" ]; then
    # mkdir -p "$dst_libs"
    # if [ $? -ne 0 ]; then exit 1; fi
fi

if [ -d "$dst_lib" ]; then
    # dst_lib is deprecated, so the logic here changed to cleanup only
    # existing_src="`readlink $dst_lib`"
    # if [ -z "$existing_src" ]; then
    if [ ! -L "$dst_lib" ]; then
        # ^ If we are really, really sure it isn't a symlink, then:
        # if [ "@$FORCE" = "@true" ]; then
            rm -Rf "$dst_lib"
            if [ $? -ne 0 ]; then exit 1; fi
            echo "* removed existing $dst_lib (real directory, not symlink)"
        # else
        #     echo "Error: \"$dst_lib\" already exists and isn't a symlink. Use --force to delete the entire directory and $redo_verb."
        #     exit 1
        # fi
    elif [ -L "$dst_lib" ]; then
        rm "$dst_lib"
    fi
fi

# src_bin="$src_lib/__init__.py"
# src_bin=$src_exe
dst_bin="$PREFIX/bin/nopackage"

# existing_src_bin="`readlink $dst_bin`"
if [ -f "$dst_bin" ]; then
    rm "$dst_bin"
fi
if [ "@$UNINSTALL" != "@true" ]; then
    # if [ "$existing_src_bin" != "$src_bin" ]; then
        printf "* installing $dst_bin..."
        ln -s "$src_exe" "$dst_bin"
        code=$?
        if [ $code -eq 0 ]; then
            echo "OK"
        else
            echo "FAILED (line $LINENO)"
            exit $code
        fi
    # fi
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
echo "Exec=$HOME/.local/bin/nopackage" >> "$dst_sc"
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
