#!/bin/bash
echo
. runinplace.rc
if [ $? -ne 0 ]; then
    echo "Error: runinplace.rc didn't run successfully. You must run this script from the nopackage repo (the same directory as runinplace.rc)"
    exit 1
fi

src_sc="nopackage/dist/share/applications/nopackage.desktop"
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
elif [ ! -d "$dst_libs" ]; then
    mkdir -p "$dst_libs"
    if [ $? -ne 0 ]; then exit 1; fi
fi

if [ -d "$dst_lib" ]; then
    existing_src="`readlink $dst_lib`"
    if [ -z "$existing_src" ]; then
        # ^ If we are really, really sure it isn't a symlink, then:
        if [ "@$FORCE" = "@true" ]; then
            rm -Rf "$dst_lib"
            if [ $? -ne 0 ]; then exit 1; fi
            echo "* removed existing $dst_lib (real directory, not symlink)"
        else
            echo "Error: \"$dst_lib\" already exists and isn't a symlink. Use --force to delete the entire directory and $redo_verb."
            exit 1
        fi
    fi
fi

if [ -f "$dst_lib/__init__.py" ]; then
    existing_src="`readlink $dst_lib`"
    if [ -z "$existing_src" ]; then
        echo "Error: There is a logic error in $0 $@. The existing src is not a symlink but that should already have been addressed (if --force). Otherwise, an exit code should have been returned by now."
        exit 1
    fi
    if [ "@$UNINSTALL" = "@true" ]; then
        printf "* removing $dst_lib (pointed to $existing_src)..."
        rm "$dst_lib"
        if [ $? -ne 0 ]; then exit 1; fi
        echo "OK"
    else
        if [ "$existing_src" != "$src_lib" ]; then
            if [ "@$FORCE" = "@true" ]; then
                printf "* removing $dst_lib (pointed to different source: $existing_src)..."
                rm "$dst_lib"
                # ^ rm shouldn't be recursive here because it is a symlink to a directory not a directory.
                if [ $? -ne 0 ]; then exit 1; fi
                echo "OK"
            else
                echo "Error: \"$dst_lib\" already exists but points to \"$existing_src\". Use --force to change the symlink to point to \"$src_lib\" and $redo_verb."
                exit 1
            fi
        fi
    fi
else
    if [ "@$UNINSTALL" = "@true" ]; then
        echo "* \"$dst_lib\"...OK (already uninstalled)"
    fi
fi
if [ "@$UNINSTALL" != "@true" ]; then
    if [ ! -f "$dst_lib/__init__.py" ]; then
        printf "* installing $dst_lib..."
        ln -s "$src_lib" "$dst_lib"
        if [ $? -ne 0 ]; then exit 1; fi
        echo "OK"
    else
        existing_src="`readlink $dst_lib`"
        if [ "$existing_src" != "$src_lib" ]; then
            echo "Error: There is a logic error in the script. The existing \"$dst_lib\" is a symlink that points to the some other source (\"$existing_src\") instead of \"$src_lib\"but that should have been addressed above (if --force). Otherwise, an exit code should have been returned by now."
            exit 1
        fi
        echo "* using existing symlink \"dst_lib\" since it already points to \"$src_lib\""
    fi
fi

src_bin="$src_lib/__init__.py"
dst_bin="$PREFIX/bin/nopackage"

existing_src_bin=
if [ -f "$dst_bin" ]; then
    existing_src_bin="`readlink $dst_bin`"
    if [ -z "$existing_src_bin" ]; then
        if [ "@$FORCE" = "@true" ]; then
            rm "$dst_bin"
            if [ $? -ne 0 ]; then exit 1; fi
            echo "* removed existing \"$dst_bin\""
        else
            if [ "@$UNINSTALL" = "@true" ]; then
                echo "Error: The existing \"$dst_bin\" is not a symlink. Use --force to remove it anyway to completely $verb."
            else
                echo "Error: The existing \"$dst_bin\" is not a symlink. Use --force to remove it and make it a link to $src_bin."
            fi
            exit 1
        fi
    elif [ "$existing_src_bin" != "$src_bin" ]; then
        rm "$dst_bin"
        if [ $? -ne 0 ]; then exit 1; fi
        echo "* removed \"$dst_bin\" (It was linked to a different binary: \"$existing_src_bin\")"
    else
        if [ "@$UNINSTALL" = "@true" ]; then
            rm "$dst_bin"
            if [ $? -ne 0 ]; then exit 1; fi
            echo "* removed \"$dst_bin\""
        else
            echo "* using existing $dst_bin since it already points to \"$src_bin\""
        fi
    fi
fi
if [ "@$UNINSTALL" != "@true" ]; then
    if [ "$existing_src_bin" != "$src_bin" ]; then
        printf "* installing $dst_bin..."
        ln -s "$src_bin" "$dst_bin"
        code=$?
        if [ $code -eq 0 ]; then
            echo "OK"
        else
            echo "FAILED (line $LINENO)"
            exit $code
        fi
    fi
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
echo "Exec=$HOME/.local/lib/nopackage/__init__.py" >> "$dst_sc"
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
