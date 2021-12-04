# nopackage
Install **any** software (including deb) using ONE COMMAND on **any** GNU-like OS!

Automate the installation of any source with zero configuration. The
source can be a zip or gz binary package, appimage, directory, or
executable file.

Step 1: nopackage <packagename>
- There is only one step!
- It installs in user space (~/.local, so add ~/.local/bin to your path--see the "Install" section).
- It keeps uninstall metadata in ~/.config/nopackage/

Install an archive (deb, zip, gz, bz2), binary (including appimage) or directory onto ANY GNU-like OS!
- A shortcut will **always** be created automatically.
- If there is a subdirectory in the archive, that will be detected and handled properly!
- If it is a binary (including appimage), that will be detected and handled properly!
- If there is no icon, and the icon is in `iconLinks`, that will be downloaded and used!

This software was formerly a script in https://github.com/poikilos/linux-preinstall/utilities.


## Author and license
- Author: Jake "Poikilos" Gustafson
- License: See [license.txt](license.txt).


## Automatic Downloads
This script will try to download the icon if an icon isn't known to be
included but is known to be online. You can see the list of possible
URLs that will be accessed by viewing the `iconLinks` dictionary in
[nopackage/__init__.py](nopackage/__init__.py).


## Install
```
pip install --user https://github.com/poikilos/nopackage/archive/refs/heads/main.zip
```
- Or use `venv` so that testing and packaging dependencies and knowing versions of dependencies and python are more clear.

### Install symlinks only
This install method is probably only helpful if you are a developer and
want your code changes in the repo to instantly affect the system.
```
mkdir -p ~/git
cd ~/git
git clone https://github.com/poikilos/nopackage.git ~/git/nopackage
cd ~/git/nopackage
./install-as-symlink.sh
# Change the following step if you are using a non-bash OS:
echo "PATH=\$PATH:$HOME/.local/bin" >> ~/.bashrc
```


## Metadata
The metadata for each installed or uninstalled program is stored
permanently in local_machine.json located at
~/.config/nopackage/local_machine.json. If you delete it, the next
run will try to regenerate it from
~/.config/nopackage/nopackage.log (which doesn't preserve
multi-version data, so the generated metadata will only refer to the
last version installed using nopackage) unless you delete that too.
The install or uninstall process will try to derive the version,
shortcut caption string, unique program name (called `luid` in the
code), and package name from the filename or directory name provided,
unless you specify such strings manually (they will be passed on to the
install_program_in_place function then to PackageInfo init).

### luid
The `luid` is a "locally-unique ID" that represents the program. It
adheres to the "UNIX name" scheme as much as possible. Where the
generated `luid` doesn't match the "UNIX name" of the project being
installed, the `luid` should be set to the proper UNIX name when
constructing PackageInfo. The `luid` is a primary key that is used to
connect a uniquely identifiable program to a list of packages of
different types or versions that you may have installed. If
`--multi-version` is enabled, see the "sc_name" section.

#### Uninstalling or installing using luid
If you know the `luid` (locally-unique ID) of a program and it is in the
programs object in local_machine.json, you can uninstall the program
using the `luid` (otherwise you need the full path of the source, which
may be inaccessible). You can obtain the `luid` of any installed program
by reviewing local_machine.json after the first run of the program. For
example: `nopackage --uninstall keepassxc` (See also the beginning of
[__init__.py](nopackage/__init__.py)).

### Multi-version support
You can enable `--multi-version` to install multiple copies of a program
with different versions. It will be enabled automatically if the
program is usually `--multi-version` when installed manually, such as
Blender (If you're installing Blender manually for some other reason,
there is no penalty--`--multi-version` simply makes a separate shortcut icon
that says the version in the caption after the name of the program).

#### sc_name
The `sc_name` is the package named (named `sc_name` since it is also the
shortcut filename--See 'packages' in local_machine.json, which will
only be populated in cases where `--multi-version` is enabled). The package
name will uniquely identify the program in case `--multi-version` is
enabled, but the `luid` will also remain as a way to track the package
back to a unique program (in 'programs' in local_machine.json). If
`--multi-version` is not enabled, `sc_name` will be the same as `luid`
but may have a vendor prefix also.


## Developer Notes:
### Testing
(requires nose such as the `python3-nose` package (`python3-nose2` wasn't tried here and requires several `libjs-*` packages.))
```bash
if [ -f "`command -v outputinspector`" ]; then
  nosetests3 1>out.txt 2>err.txt
  outputinspector
else
  nosetests3
fi
```
