#!/bin/bash
if [ "@$PREFIX" = "@" ]; then
    PREFIX="$HOME/.local"
fi
src_repo="`pwd`"
src_lib="$src_repo/nopackage"
dst_libs="$HOME/.local/lib"
dst_lib="$dst_libs/nopackage"
src_exe="$src_lib/__init__.py"
if [ ! -f "$src_exe" ]; then
    printf "Error: $src_exe is missing. Run this script from the nopackage repo"
    if [ -f "__init__.py" ]; then
        printf " not the nopackage/nopackage module directory"
    fi
    echo "."
    exit 1
fi

if [ -z "$FORCE" ]; then
    FORCE=false
fi

for arg in "$@"
do
    if [ "@$arg" == "@--force" ]; then
        FORCE=true
    else
        echo "Error: \"$arg\" is not a valid option."
        exit 1
    fi
done

if [ ! -d "$dst_libs" ]; then
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
        else
            echo "Error: \"$dst_lib\" already exists and isn't a symlink. Use --force to delete the entire directory and reinstall."
            exit 1
        fi
    fi
fi

if [ -f "$dst_lib/__init__.py" ]; then
    existing_src="`readlink $dst_lib`"
    if [ -z "$existing_src" ]; then
        echo "Error: There is a logic error in the install script. The existing src is not a symlink but that should already have been addressed (if --force) or returned an exit code."
        exit 1
    fi
    if [ "$existing_src" != "$src_lib" ]; then
        if [ "@$FORCE" = "@true" ]; then
            rm "$dst_lib"
            # ^ rm shouldn't be recursive here because it is a symlink to a directory not a directory.
            if [ $? -ne 0 ]; then exit 1; fi
        else
            echo "Error: \"$dst_lib\" already exists but points to \"$existing_src\". Use --force to change the symlink to point to \"$src_lib\" and reinstall."
            exit 1
        fi
    fi
fi

if [ ! -f "$dst_lib/__init__.py" ]; then
    ln -s "$src_lib" "$dst_lib"
    if [ $? -ne 0 ]; then exit 1; fi
else
    existing_src="`readlink $dst_lib`"
    if [ "$existing_src" != "$src_lib" ]; then
        echo "Error: There is a logic error in the script. The existing \"$dst_lib\" is a symlink that points to the some other source (\"$existing_src\") instead of \"$src_lib\"but that should have been addressed above (if --force) or returned an exit code."
        exit 1
    fi
    echo "* using existing symlink \"dst_lib\" since it already points to \"$src_lib\""
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
            echo "* removed old \"$dst_bin\""
        else
            echo "Error: The existing \"$dst_bin\" is not a symlink. Use --force to remove it and make it a link to $src_bin."
            exit 1
        fi
    elif [ "$existing_src_bin" != "$src_bin" ]; then
        rm "$dst_bin"
        if [ $? -ne 0 ]; then exit 1; fi
        echo "* removed old \"$dst_bin\""
    else
        echo "* using existing $dst_bin since it already points to \"$src_bin\""
    fi
fi
if [ "$existing_src_bin" != "$src_bin" ]; then
    printf "* installing $dst_bin..."
    ln -s "$src_bin" "$dst_bin"
    code=$?
    if [ $code -eq 0 ]; then
        echo "OK"
    else
        echo "FAILED"
        exit $code
    fi
fi

OLD_dst_sc="$PREFIX/share/applications/install_any.desktop"
if [ -f "$OLD_dst_sc" ]; then
    rm "$OLD_dst_sc"
    if [ $? -ne 0 ]; then exit 1; fi
    echo "* removed deprecated $OLD_dst_sc"
fi

src_sc="dist/share/applications/nopackage.desktop"
dst_sc="$PREFIX/share/applications/nopackage.desktop"
printf "* copying \"$dst_sc\"..."
cp "$src_sc" "$dst_sc"
code=$?
if [ $code -eq 0 ]; then
    echo "OK"
else
    echo "FAILED"
    exit $code
fi
echo "Path=$HOME/.local/lib/nopackage" >> "$dst_sc"
echo "Path=$src_repo" >> "$dst_sc"
# ^ for metadata
echo "Exec=$HOME/.local/lib/nopackage/__init__.py" >> "$dst_sc"
printf "* installing \"$dst_sc\"..."
xdg-desktop-icon install --novendor $dst_sc
code=$?
if [ $code -eq 0 ]; then
    echo "OK"
else
    echo "FAILED"
    exit $code
fi
