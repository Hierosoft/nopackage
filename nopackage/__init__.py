#!/usr/bin/env python
'''
Install any program such as a zip or gz binary package, AppImage,
directory, or other file. The filename or extracted content, whichever
has the name of the program, is used to determine the "UNIX name" (as
the term is used elsewhere such as SourceForge) which nopackage calls a
"LUID" (Locally-unique Identifier). A "UNIX name" or luid is a
lowercase string without spaces that uniquely identifies any project.
It is used as:
- The destination directory where the program will be installed (always
  in the same directory scheme to match the behavior of Unix-like
  operating systems)
- The icon filename (if a fully qualified XDG program ID with vendor is
  not present).

Author: Jake Gustafson
License: GPLv3 or later (https://www.gnu.org/licenses/)

Internet use: See iconLinks variable for what will be attempted when.

USAGE:
nopackage <command> [path|luid]
nopackage install        <Program Name_version.AppImage>
nopackage install        <file.AppImage> <Icon Caption>
nopackage install        <file.deb> <Icon Caption>
nopackage install <path> --move
                         ^ moves the directory to $HOME/.local/lib64
nopackage remove <path>
                 ^ removes it from $HOME/.local/lib64
                   and tries to recover the data to the original path
                   from which it was installed (using
                   local_machine.json).
nopackage remove keepassxc
                 ^ Use a known luid from local_machine.json
                   or reinstall the same version (if you didn't
                   delete the source after remove, which
                   remove had tried to recover) like:
                   nopackage --install keepassxc
nopackage reinstall <path>
                    ^ removes it from $HOME/.local/lib64 first

nopackage help
          ^ Show this help screen.


'''
from __future__ import print_function
import sys
import stat
import os
import shutil
import tarfile
import tempfile
from zipfile import ZipFile
import platform
import json
from datetime import datetime
import inspect

'''
nopackage tries to install any folder or archived binary package.
Copyright (C) 2019  Jake "Poikilos" Gustafson

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
'''

from nopackage.find_hierosoft import hierosoft

from hierosoft.moreweb import (
    request,
    download,
)

from hierosoft import (
    CompletedProcess,
    subprocess,
    echo0,
    echo1,
    echo2,
    get_unique_path,
    PREFIX,  # ~/.local, formerly defined below and named PREFIX
    SHARE, # formerly defined below and called share_path
    PIXMAPS, # formerly defined below and named PIXMAPS
)

from hierosoft.ggrep import (
    contains_any,
    any_contains,
    contains,
)

lib64 = os.path.join(PREFIX, "lib64")
lib = os.path.join(PREFIX, "lib")

MODULE_DIR = os.path.dirname(os.path.realpath(__file__))

meta_dir = os.path.join(MODULE_DIR, "shortcut-metadata")

digits = "0123456789"
# me = os.path.split(sys.argv[0])[-1]
# ^ doesn't work correctly if used as a module
me = "nopackage"

repoDir = os.path.dirname(MODULE_DIR)
distPath = os.path.join(MODULE_DIR, "usr")
distGoodFlag = os.path.join(distPath, "share", "applications",
                            "nopackage.desktop")
if not os.path.isfile(distGoodFlag):
    raise RuntimeError("The file {} is missing. Make sure nopackage is"
                       " installed correctly."
                       "".format(distGoodFlag))
else:
    pass
    # echo0("* Checking for {}...OK".format(distGoodFlag))
bad_id_flag = ("you must use the id from"
               " the list of known installed programs")

version_chars = digits + "."

# The following dictionaries contain information that can't be derived
# from the installer file's name.
icons = {}  # A list of preferred icon file names indexed by LUID
icons["freecad"] = "org.freecadweb.FreeCAD"
icons["ultimaker.cura"] = "cura"
iconLinks = {}  # A list URLs to icon graphics indexed by LUID
iconLinks["ultimaker.cura"] = "https://github.com/Ultimaker/Cura/raw/master/icons/cura-48.png"
iconLinks["prusaslicer"] = "https://github.com/prusa3d/PrusaSlicer/raw/master/resources/icons/PrusaSlicer.png"
iconLinks["pycharm.community"] = "https://github.com/JetBrains/intellij-community/raw/master/python/resources/PyCharmCore128.png"
iconLinks["keepassxc"] = "https://github.com/keepassxreboot/keepassxc/raw/develop/share/icons/application/scalable/apps/keepassxc.svg"
iconLinks["unityhub"] = "https://img.icons8.com/ios-filled/50/000000/unity.png"
iconLinks["godot"] = "https://github.com/godotengine/godot/raw/master/main/app_icon.png"
iconLinks["ninja-ide"] = "https://github.com/ninja-ide/ninja-ide/raw/develop/icon.png"
iconLinks["olive"] = "https://upload.wikimedia.org/wikipedia/commons/c/c7/Olive_Video_Editor_Logo.png"
# pronterface.py and pronsole.py are installed to bin by pip via
#    mkdir -p cd ~/Downloads/git/kliment && cd ~/Downloads/git/kliment && git clone https://github.com/kliment/Printrun
#    cd Printrun && git pull && cd .. && python3 -m pip install --user --upgrade Printrun
iconLinks['pronterface'] = "https://raw.githubusercontent.com/kliment/Printrun/master/pronterface.png"
iconLinks['pronsole'] = "https://raw.githubusercontent.com/kliment/Printrun/master/pronsole.png"
iconLinks['plater'] = "https://raw.githubusercontent.com/kliment/Printrun/master/plater.png"
iconLinks['balenaetcher'] = "https://github.com/balena-io/etcher/blob/master/assets/icon.png"
iconLinks['pcsx2'] = "https://github.com/PCSX2/pcsx2/raw/master/bin/resources/icons/AppIconLarge.png"
if platform.system() == "Windows":
    iconLinks['pronterface'] = "https://raw.githubusercontent.com/kliment/Printrun/master/pronterface.ico"
    iconLinks['pronsole'] = "https://raw.githubusercontent.com/kliment/Printrun/master/pronsole.ico"
    iconLinks['plater'] = "https://raw.githubusercontent.com/kliment/Printrun/master/plater.ico"
    iconLinks['balenaetcher'] = "https://github.com/balena-io/etcher/blob/master/assets/icon.ico"
elif platform.system() == "Darwin":
    iconLinks['balenaetcher'] = "https://github.com/balena-io/etcher/blob/master/assets/icon.icns"
# iconLinks["mirage"] = "mirage.png" # None since in "shortcut-metadata"

iconNames = {
    'godot': "godot",  # since the file is named "app_icon.png"
    'ninja-ide': "ninja-ide",  # since the file is named "icon.png"
    'balenaetcher': "balenaetcher",  # since the file is named "icon.png"
    'pcsx2': "pcsx2",  # since the icon is called "AppIconLarge.png"
}
# ^ A list of icon names where the downloaded file should be renamed.
minimumUniquePartOfLuid = {
    'unityhub': "unity",
}
hyphenate_names = [
    "ninja-ide",
]
# Store desktop file values (execpt Icon--see iconLinks above):
shortcutMetas = {
    'argouml': {
        'Keywords': "Development;IDE;",
        'Categories': "Development;IDE;",
    },
    'godot': {
        'Keywords': "Development;IDE;",
        'Categories': "Development;IDE;",
    },
    'mirage': {
        'Categories': "Network;InstantMessaging;",
    },
    'ninja-ide': {
        'Keywords': "Qt;Development;IDE;TextEditor;",
        'Categories': "Text;Editor;",
    },
    'olive': {
        'Categories': "AudioVideo;Video;AudioVideoEditing;",
    },
    'pycharm': {
        'Keywords': "Development;IDE;",
        'Categories': "Development;IDE;",
    },
    'staruml': {
        'Keywords': "Development;IDE;",
        'Categories': "Development;IDE;",
    },
    'unityhub': {
        'Keywords': "Development;IDE;",
        'Categories': "Development;IDE;",
    },
    'pronterface': {
        # See <https://github.com/kliment/Printrun/blob/master/
        #   pronterface.desktop>
        'GenericName': "Printer Interface",
        'Comment': "Controls your 3D printer",
        'StartupNotify': "true",
        'Categories': "GNOME;GTK;Utility;Graphics;3DGraphics;",
        'Mimetype': "MimeType=application/sla;model/x.stl-binary;model/x.stl-ascii;text/x.gcode;",
    },
    'pronsole': {
        # See <https://github.com/kliment/Printrun/blob/master/
        #   pronsole.desktop>
        'GenericName': "Printer console",
        'Comment': "Controls your 3D printer form console",
        'StartupNotify': "true",
        'Terminal': "true",
        'Categories': "Utility;Graphics;3DGraphics;ConsoleOnly;",
    },
    'pronsole': {
        # See <https://github.com/kliment/Printrun/blob/master/
        #   plater.desktop>
        'GenericName': "Printer building tool",
        'Comment': "Prepares plates for 3D printing",
        'StartupNotify': "true",
        'Categories': "Utility;Graphics;3DGraphics;ConsoleOnly;",
    },
}

luid = None
for rawLuid, url in iconLinks.items():
    lastSlashI = url.rfind("/")
    fileName = url[lastSlashI+1:]
    luid = rawLuid
    # gotLuid = hyphenate_names_lookup.get(luid)
    # if gotLuid is not None:
    #     luid = gotLuid
    gotName = iconNames.get(luid)
    if gotName is not None:
        fileName = gotName
    any_part_of_luid_in_name = False
    luidParts = luid.split(".")
    notDividedPart = minimumUniquePartOfLuid.get(luid)
    if notDividedPart is not None:
        luidParts.append(notDividedPart)
    for luidPart in luidParts:
        if luidPart in fileName.lower():
            any_part_of_luid_in_name = True
            break
    if not any_part_of_luid_in_name:
        print()
        msg = (" None of {luidParts} are in {fileName} (end of {url})."
               " Add an icon name containing {luid} (case insensitive,"
               " no extension) as iconNames['{luid}']"
               " to make the generated filename unique."
               "".format(luid=luid, fileName=fileName, url=url,
                         luidParts=luidParts))
        raise AssertionError(msg)
del luid
casedNames = {  # A list of correct icon captions indexed by LUID
    'umlet': "UMLet Standalone",  # as opposed to a plugin/web ver
    'freecad': "FreeCAD",
    'android.studio.ide': "Android Studio IDE",
    'flashprint': "FlashPrint",
    'argouml': "ArgoUML",
    'ninja-ide': "Ninja-IDE",
}
annotations = {  # Add a parenthetical to the shortcut caption.
    '.deb': "deb",
    '.appimage': "AppImage",
}


known_binaries = ["RunAwesomeBump.sh"]
# ^ Allows finding the name in edge cases
#   (The version and name aren't separable in
#   AwesomeBumpV5.Bin64Linux.tar.gz)
# ^ TODO: Add multi-shortcut capability:
#   - Using only RunAwesomeBump.sh skips a shortcut to the second mode
#     run via RunAwesomeBumpGL330.sh


noCmdMsg = "Error: You must specify a directory or binary file."
OLD_NO_CMD_MSG = "You must specify a directory or binary file."
# ^ For compatibility with older versions, don't change OLD_NO_CMD_MSG.


def usage():
    print(__doc__)


shortcut_data_template = """[Desktop Entry]
Name={Name}
Exec={Exec}
Icon={Icon}
Terminal=false
Type=Application
"""


def format_shortcut(shortcut_data, meta, path=None, add_all=True):
    '''
    Change or add data to the XDG desktop format data.

    Sequential arguments:
    shortcut_data -- Provide the raw data from an XDG desktop file
        or generate such data. If None, you must set path. Only data
        that is in a section such as [Desktop Entry] will be touched.

    Keyword arguments:
    path -- If not None, the data is loaded from here instead of the
        shortcut_data being used.
    add_all -- Add keys and values from meta even if the keys are not in
        the shortcut data.
    '''
    result = ""
    marks = {}
    for k, v in meta.items():
        marks[k] = False
    if shortcut_data is None:
        if path is None:
            raise ValueError(
                "You must set shortcut_data or path."
            )
    if path is not None:
        if shortcut_data is not None:
            raise ValueError(
                'shortcut_data should be None'
                ' if path is specified, but both were specified:'
                ' (packageShortcutData={}, path={})'
                ''.format(shortcut_data, path)
            )
        with open(path, 'r') as ins:
            shortcut_data = ""
            for rawL in ins:
                line = rawL.strip()
                shortcut_data += line + "\n"
    if "\r\n" in shortcut_data:
        echo0("* Warning: converting \\r\\n newlines")
    lines = shortcut_data.split("\n")
    lineN = 0
    section = None
    for line in lines:
        lineN += 1
        line = line.strip()
        if (len(line) == 0) or line.startswith("#"):
            result += line + "\n"
            continue
        if line.startswith("[") and line.endswith("]"):
            section = line[1:-1]
            result += line + "\n"
        elif section is not None:
            signI = line.find("=")
            if signI < 1:
                echo0("{}:{}: unknown format (no assignment): {}"
                      "".format(path, lineN, line))
                result += line + "\n"
                continue
            name = line[:signI].strip()
            value = line[signI+1:].strip()
            newValue = meta.get(name)
            if newValue is not None:
                value = newValue
                marks[name] = True
            result += "{}={}\n".format(name, value)
        else:
            echo0("{}:{}: unknown format (no section): {}"
                  "".format(path, lineN, line))
            result += line + "\n"
    if add_all:
        for name, value in meta.items():
            if not marks[name]:
                result += "{}={}\n".format(name, value)
                marks[name] = True
    return result

LUID_IS_FINALIZED = False
LUID = None

def finalize_luid():
    global LUID_IS_FINALIZED
    LUID_IS_FINALIZED = True

def unfinalize_luid():
    global LUID_IS_FINALIZED
    LUID_IS_FINALIZED = False

def set_luid(luid):
    global LUID
    LUID = luid

def luid_finalized():
    return LUID_IS_FINALIZED

def get_luid():
    if not luid_finalized():
        echo0("Warning: luid {} was accessed before finalized."
              " That means it may be ambiguous and not calculated fully.")
    return LUID

def getProgramIDs():
    results = []
    programs = localMachine.get("programs")
    if programs is None:
        return None
    results = list(programs.keys())
    return results


def encode_py_val(v):
    '''
    Convert the value to Python code.
    '''
    # a.k.a. toPy
    # formerly getSymbolFromValue
    '''
    # This can also be done by converting to an ast tree using the
    # ast (abstract syntax tree) module, then back to python using
    # astor, but astor is not prepackaged with Python.
    if v is True:
        return "True"
    if v is False:
        return "False"
    if v is None:
        return "None"
    if isinstance(v, str):
        return '"' + v.replace('"', "\\\"") + '"'
    return str(v)
    '''
    # def getSymbolFromValue(v):
    if isinstance(v, str):
        return '"{}"'.format(v.replace("\"", "\\\""))
    if isinstance(v, datetime):
        return '"' + datetime.strftime(v, giteaSanitizedDtFmt) + '"'
    return str(v)


def decode_py_val(valueStr, lineN=-1, path="(generated)"):
    '''
    Convert a symbolic value such as `"\"hello\""` or `"\"True\""` to a
    real value such as `"hello"` or `True`.
    This simplistic compared to str_to_value in enissue.py in
    https://github.com/Poikilos/EnlivenMinetest.

    Keyword arguments:
    path -- The file (used for error reporting only).
    lineN -- The line number in the file (used for error reporting
        only).
    '''
    # formerly getValueFromSymbol
    # def getValueFromSymbol(valueStr, lineN=-1, path="(generated)"):
    # valueL = None
    # if valueStr is not None:
    #    valueL = valueStr.lower()
    if valueStr == "None":
        return None
    if valueStr == "True":
        return True
    if valueStr == "False":
        return False
    try:
        return int(valueStr)
    except ValueError:
        pass
    try:
        return float(valueStr)
    except ValueError:
        pass
    if valueStr.startswith("'") and valueStr.endswith("'"):
        return valueStr[1:-1].replace('\\\'', '\'')
    if valueStr.startswith('"') and valueStr.endswith('"'):
        return valueStr[1:-1].replace("\\\"", "\"")
    try:
        return datetime.strptime(valueStr, giteaSanitizedDtFmt)
    except ValueError as ex:
        if "does not match format" not in str(ex):
            echo0("{}:{}: WARNING: \"{}\" doesn't seem to be a date but"
                  " the error when trying to parse it is not clear: {}"
                  "".format(path, lineN, valueStr, str(ex)))
    return valueStr


def setDeepValue(category, luid, key, value):
    if localMachine.get(category) is None:
        localMachine[category] = {}
    if localMachine[category].get(luid) is None:
        localMachine[category][luid] = {}
    if isinstance(localMachine[category][luid].get(key), list):
        raise ValueError("You cannot change a list (key={}) to a"
                         "non-list.".format(key))
    if isinstance(value, list):
        callerName = inspect.stack()[1][3]
        newCallName = callerName + "s"
        raise ValueError("You cannot set a value ({}.{}.{}) to a"
                         " list in setDeepValue. Add the"
                         " individual values using setDeepValues"
                         " or something like {} instead."
                         "".format(category, luid, key, newCallName))
    localMachine[category][luid][key] = value
    if enableSaveOnWrite:
        saveLocalMachine()


def setProgramValue(luid, key, value):
    if not luid_finalized():
        raise RuntimeError(
            "A key for luid {} was attempted to be set before finalized."
            "".format(luid))
    setDeepValue('programs', luid, key, value)


def setPackageValue(sc_name, key, value):
    '''
    Sequential values:
    sc_name -- Provide the shortcut filename (without extension).
        The package name is made unique in multi-version mode using
        sc_name, so sc_name (instead of luid) is used as the key in
        packages. Be sure to also set luid using
        setPackageValue(sc_name, 'luid', luid) so this package can be
        tied back to the unique program id.
    '''
    setDeepValue('packages', sc_name, key, value)


def getDeepValue(category, luid, key, delete=False):
    if localMachine.get(category) is None:
        return None
    if localMachine[category].get(luid) is None:
        return None
    if isinstance(localMachine[category][luid].get(key), list):
        callerName = inspect.stack()[1][3]
        newCallName = callerName + "s"
        raise ValueError("You cannot get from a list ({}.{}.{}) in"
                         " getDeepValue. Use getDeepValues or something"
                         "like {} (plural) instead."
                         "".format(category, luid, key, newCallName))
    if not delete:
        return localMachine[category][luid].get(key)
    value = None
    if key in localMachine[category][luid]:
        value = localMachine[category][luid][key]
        del localMachine[category][luid][key]
        if enableSaveOnWrite:
            saveLocalMachine()
    return value


def deleteDeepValue(category, luid, key):
    return getDeepValue(category, luid, key, delete=True)


def getProgramValue(luid, key, force=False, delete=False):
    '''
    Keyword arguments:
    force -- Only set this to true if caller type is PackageInfo and a
        temporary theoretical PackageInfo is being created. It should
        normally be False to block access when the luid is uncertain.
    delete -- Also delete the value.
    '''
    if not luid_finalized():
        msg = ("A key for luid {} was attempted to be set before finalized."
                "".format(luid))
        if True: # not force:
            raise RuntimeError(msg)
        else:
            echo0("Warning (force={}, but Making temp PackageInfo"
                  " should probably be factored out): {}"
                  "".format(force, msg))
    return getDeepValue('programs', luid, key, delete=delete)

def deleteProgramValue(luid, key, force=False):
    return getProgramValue(luid, key, force=force, delete=True)

def getDeepValues(category, luid, key):
    if localMachine.get(category) is None:
        echo0("Warning: getDeepValues didn't find the category {}"
              "".format(category))
        return None
    if localMachine[category].get(luid) is None:
        return None
    if not isinstance(localMachine[category][luid].get(key), list):
        callerName = inspect.stack()[1][3]
        newCallName = callerName[:-1]  # Remove the 's'.
        raise ValueError("You can only get multiple values from a list"
                         " ({}.{}.{}). Use getDeepValue or"
                         " something like {} (singular) instead."
                         "".format(category, luid, key, newCallName))
    return localMachine[category][luid].get(key)


def getProgramValues(luid, key):
    return getDeepValues('programs', luid, key)


def getPackageValues(sc_name, key):
    '''
    Sequential values:
    sc_name -- Provide the shortcut filename (without extension).
        The package name is made unique in multi-version mode using
        sc_name, so sc_name (instead of luid) is used as the key in
        packages (The luid is still set like
        setPackageValue(sc_name, 'luid', luid) so that the package can
        be tied back to the unique program id).
    '''
    return getDeepValues('packages', sc_name, key)


def addDeepValue(category, luid, key, value, unique=True):
    '''
    Add a value to a list named with `key` in the category's metadata.

    Sequential arguments:
    category -- A category in the local_machine.json such as 'programs'.

    Keyword arguments:
    unique -- True of the value should only be added if it isn't already
        in the list named by `key`.
    '''
    if localMachine.get(category) is None:
        echo0("Warning: addDeepValue didn't find the category {}"
              "".format(category))
        localMachine[category] = {}
    if localMachine[category].get(luid) is None:
        localMachine[category][luid] = {}
    if localMachine[category][luid].get(key) is None:
        localMachine[category][luid][key] = []
    if not isinstance(localMachine[category][luid][key], list):
        raise ValueError("You cannot append to non-list ({}.{}.{})."
                         "".format(category, luid, key))
    if (not unique) or (value not in localMachine[category][luid][key]):
        localMachine[category][luid][key].append(value)
    if enableSaveOnWrite:
        saveLocalMachine()


def addProgramValue(luid, key, value, unique=True):
    '''
    Add a list item to a value within a program's metadata.
    See addDeepValue for further documentation.
    '''
    addDeepValue('programs', luid, key, value, unique=unique)


def addPackageValue(sc_name, key, value, unique=True):
    '''
    Add a list item to a value within a package's metadata.
    See addDeepValue for further documentation.

    Sequential values:
    sc_name -- Provide the shortcut filename (without extension).
        The package name is made unique in multi-version mode using
        sc_name, so sc_name (instead of luid) is used as the key in
        packages. Be sure to also set luid using
        setPackageValue(sc_name, 'luid', luid) so this package can be
        tied back to the unique program id.
    '''
    addDeepValue('packages', sc_name, key, value, unique=unique)


'''
def setVersionedValue(luid, version, key, value):
    # Use setPackageValue instead.
    if isinstance(value, list):
        raise ValueError("You cannot set a value (programs.{}.{}) to a"
                         "list. Add individual values using"
                         "addVersionedValue instead."
                         "".format(luid, key))
    if localMachine['programs'].get(luid) is None:
        localMachine['programs'][luid] = {}
    if localMachine['programs'][luid].get('versions') is None:
        localMachine['programs'][luid]['versions'] = {}
    if localMachine['programs'][luid]['versions'].get(version) is None:
        localMachine['programs'][luid]['versions'][version] = {}
    localMachine['programs'][luid]['versions'][version][key] = value
    if enableSaveOnWrite:
        saveLocalMachine()


def addVersionedValue(luid, version, key, value):
    # Use addPackageValue instead.
    if localMachine['programs'].get(luid) is None:
        localMachine['programs'][luid] = {}
    if localMachine['programs'][luid].get('versions') is None:
        localMachine['programs'][luid]['versions'] = {}
    if localMachine['programs'][luid]['versions'].get(version) is None:
        localMachine['programs'][luid]['versions'][version] = {}
    if localMachine['programs'][luid]['versions'][version].get(key) is None:
        localMachine['programs'][luid]['versions'][version][key] = []
    if not isinstance(
            localMachine['programs'][luid]['versions'][version].get(key), list
            ):
        raise ValueError("You cannot append to non-list"
                         " (programs.{}.versions.{}.{})."
                         "".format(luid, version, key))
    localMachine['programs'][luid]['versions'][version][key].append(value)
    if enableSaveOnWrite:
        saveLocalMachine()
'''


sh_specials = "!\"#$&'()*,;<>?[]\\^`{}|~"
# ^ See <https://unix.stackexchange.com/a/357932/343286>
# TODO: "= - in zsh, when it's at the beginning of a file name
# (filename expansion with PATH lookup)."
# -<https://unix.stackexchange.com/a/357932/343286>


def sh_literal(v):
    '''
    Convert the value to a bash-ready string.
    '''
    if v is None:
        raise ValueError("None is not acceptable for a bash value")
    my_q = None
    if contains_any(v, sh_specials):
        my_q = "'"
    if my_q is not None:
        for c in sh_specials:
            v = v.replace(c, "\\"+c)
        return my_q+v+my_q
    return v


def tests():
    # if hasattr(CompletedProcess, "_custom_impl"):
    test_CompletedProcessException(1)
    test_subprocess_run("ls")
    test_subprocess_run(["ls", "-l"])
    test_return_sh = os.path.join(repoDir, "tests", "data", "exit1.sh")
    if os.path.isfile(test_return_sh):
        test_subprocess_run(test_return_sh)
    else:
        print("* [{}] skipped the process return test since"
              " {} does not exist."
              "".format(me, sh_literal(test_return_sh)))
        # raise RuntimeError("The {} process return test failed since"
        #                    " {} does not exist."
        #                    "".format(me, sh_literal(test_return_sh)))
    # else:
    #     print("* The exception test was skipped since you are using"
    #           " Python's implementation of CompletedProcess.")

    # if failures == 0:
    print("* All tests passed.")
    # else:
    #     print("* Tests completed with {} failure(s).".format(failures))


# TODO: Run tests() using nose.


def test_CompletedProcessException(code):
    proc = CompletedProcess(["(tests)"], code, sys.stdout,
                            sys.stderr)
    try:
        proc.check_returncode()
        raise ValueError("* The exception test failed (running"
                         " check_returncode on returncode {} didn't"
                         " succeed in producing CalledProcessError)"
                         "".format(proc.returncode))
    except subprocess.CalledProcessError:
        pass
        print("* The exception test passed.")


def test_subprocess_run(argsOrString):
    fn_msg = (" (Python {}'s standard implementation)"
              "".format(sys.version_info[0]))
    if hasattr(CompletedProcess, '_custom_impl'):
        fn_msg = " (Python 2 polyfill)"
    print("* Testing subprocess.run{} with {}..."
          "".format(fn_msg, type(argsOrString).__name__))
    proc = subprocess.run(argsOrString)
    print("* proc.returncode: {}".format(proc.returncode))
    print("* proc.stdout: {}".format(proc.stdout))
    print("* proc.stderr: {}".format(proc.stdout))


def toLUID(name):
    return name.replace(" ", ".").lower()


def get_annotation(s):
    '''
    Get the annotation which separates the software from a differently-
    packaged copy.
    '''
    bad_endings = [".sh", ".appimage", ".deb"]
    for ending in bad_endings:
        if s.lower().endswith(ending):
            annotation = annotations.get(ending)
            if annotation is not None:
                return annotation
    # print("  - {} is ok.".format(s))
    return None


def find_all_cs(haystack, needle):
    '''get indices of every match of the needle (case sensitive)'''
    results = []
    i = 0
    nLen = len(needle)
    while i < len(haystack):
        if haystack[i:i+nLen] == needle:
            results.append(i)
            i += nLen
            continue
        i += 1
    return results


def find_all_ci(haystack, needle):
    '''get indices of every match of the needle (case insensitive)'''
    haystack = haystack.lower()
    needle = needle.lower()
    return find_all_cs(haystack, needle)
    # ^ lower so ok to call *_cs


def find_all_any_cs(haystack, needles):
    '''
    Get a list of tuples where each pair is an index of a match of every
    needle (case sensitive) paired with the needle in the second slot.
    '''
    results = []
    for needle in needles:
        found = find_all_cs(haystack, needle)
        results += list(zip(found, [needle]*len(found)))
    return results


def find_all_any_ci(haystack, needles):
    '''
    Get a list of tuples where each pair is an index of a match of every
    needle (case insensitive) paired with the needle in the second slot.
    '''
    results = []
    haystackL = haystack.lower()
    for needle in needles:
        found = find_all_cs(haystackL, needle.lower())
        results += list(zip(found, [needle]*len(found)))
        # ^ lower so ok to call *_cs
    return results


def find_tuple_with(tuples, index, needle):
    '''
    Find the index where element 'index' of the tuple is needle
    (case-sensitive).
    '''
    for i in range(len(tuples)):
        if tuples[i][index] == needle:
            return i
    return -1


def has_tuple_with(tuples, index, needle):
    '''
    Determine if needle is in any element 'index' of any tuple in the
    list of tuples.
    '''
    return find_tuple_with(tuples, index, needle) > -1


def split_any(s, delimiters, blobs=None):
    '''
    Sequential arguments:
    delimiters -- a list of one-character delimiters at which to split s

    Keyword arguments:
    blobs -- a list of strings to never split (for example, include
        'x86_64' as a blob when '_' is in delimiters but you want
        to not split at '_' in cases where it is in that blob)
    '''
    ret = []
    start = 0
    blobIs = None
    oldS = s
    print("[split_any] checking for {}".format(blobs))
    if blobs is not None:
        # replace bad dots with delimiters (example: change .i386 to
        # _i386.
        i = -1
        while i + 1 < len(s):
            i += 1
            for blob in blobs:
                if i == 0:
                    continue
                elif s[i-1] != '.':
                    continue
                if s[i:i+len(blob)].lower() == blob.lower():
                    # if s[i-1] == '.':
                    if len(delimiters[0]) > 1:
                        raise ValueError("delimiter[0] ('{}') is too"
                                         " long (should be 1"
                                         " character)."
                                         "".format(delimiters[0]))
                    s = s[:i-1] + delimiters[0] + s[i:]
                # else:
                #     print("[split_any] {} is not {}"
                #           "".format(s[i:i+len(blob)].lower(),
                #                     blob.lower()))
        del i
    if s != oldS:
        print("[split_any] preprocessed {} to {}".format(oldS, s))
    else:
        print("[split_any] There was nothing to preprocess in {}"
              "".format(s))
    if blobs is not None:
        blobIs = find_all_any_ci(s, blobs)
    i = 0
    while i < len(s):
        c = s[i]
        if blobIs is not None:
            # print("[split_any] checking in {}".format(blobIs))
            foundI = find_tuple_with(blobIs, 0, i)
            if foundI > -1:
                # print("[split_any] {} is in {}".format(i, blobIs))
                # If a blob had been found at i, skip i to end of blob.
                # Do not end here.
                i += len(blobIs[foundI][1])
                continue
        if c in delimiters:
            print("[split_any] {} is in {}".format(c, delimiters))
            ret.append(s[start:i])
            start = i + 1
        i += 1
    # Add the last slice, whether ends in delimiter or not.
    ret.append(s[start:i])
    '''
    parts = s.split(delimiters[0])
    if len(delimiters) > 1:
        for part in parts:
            ret += split_any(part, delimiters[1:])
    else:
        ret = parts
    '''
    # print("[split_any] split into {}".format(ret))
    return ret


def find_startswith(haystacks, needle, cs=True):
    '''
    find the index of the string in the haystacks

    Sequential arguments:
    haystacks -- a list of strings
    needle -- a string to find

    Keyword arguments:
    cs -- case-sensitive (True by default; Set to False for
        case-insensitive)

    Returns:
    An index in haystacks, otherwise -1
    '''
    if not cs:
        needle = needle.lower()
    for i in range(len(haystacks)):
        haystack = haystacks[i]
        if not cs:
            haystack = haystack.lower()
        if haystack.startswith(needle):
            return i
    return -1


def is_version(s, allowLettersAtEnd, allowMore=None):
    '''
    Sequential arguments:
    allowLettersAtEnd -- If True, allow letters (but no more numbers
        after the first letter) at the end if starts with a number
        (such as for "2.79b").

    Keyword arguments:
    allowMore -- a list such as PackageInfo.VPARTS of entire words to
        allow (case-insensive) such as "master" or "dev"
    '''
    # if s.lower in version_strings:
    if allowMore is not None:
        for vPart in allowMore:
            vOpener = vPart.lower()
            if s.lower() == vOpener:
                return True
            elif s.startswith(vOpener) and s[len(vOpener):].isnumeric():
                return True

    startsWithNum = False
    if s[:1] in digits:
        startsWithNum = True

    for c in s:
        if c not in version_chars:
            if (allowLettersAtEnd and startsWithNum):
                if (not c.isalpha()):
                    return False
            else:
                return False
    return True


def is_digits(s):
    '''
    Only numbers, no dots or other symbols.
    '''
    if len(s) < 1:
        raise ValueError("is_digits got an empty string.")
    for c in s:
        if c not in digits:
            # print("{} is not in {}.".format(c, digits))
            return False
    return True


downloading = False


def dl_progress(evt):
    global downloading
    dl_msg_w = 80
    if downloading:
        sys.stderr.write("\r")  # r (to the start of the SAME line).
    line = "{}".format(evt['loaded']).ljust(dl_msg_w)
    # ^ 2nd param of ljust (,`character`) is optional
    sys.stderr.write(line)
    pass


def dl_done(evt):
    global downloading
    downloading = False
    err = evt.get('error')
    if err is None:
        print("  DONE")
    else:
        print(err)


noAlphaErrorFmt = ('Parsing names with no alphabetic characters'
                   ' is not possible (self.fname:"{}"'
                   ', fnamePartial:"{}"'
                   ')')


class PackageInfo:
    '''
    To get a globally unique name based on whether multiVersion or
    multiPackage installs can coexist, use get_coexisting_id(luid,
    multiPackage, multiVersion). See the __init__ documentation for
    more info.
    '''
    DELIMITERS = "_- +"
    X64S = ["x64", "64bit", "linux64", "win64", "windows64", "64-bit",
            "x86_64", "amd64"]
    X32S = ["x32", "686", "386", "i386", "i686", "32bit", "32-bit",
            "windows32", "win32", "x86"]
    NOARCHES = ["noarch"]
    ARCHES = X64S + X32S + NOARCHES
    # ^ NOTE: x86_64 is handled manually below since it contains a
    #   delimiter
    LINS = ["linux", "linux64", "linux32"]
    WINS = ["windows", "windows64", "windows32", "win64", "win32"]
    VPARTS = ['master', 'dev', 'prealpha', 'alpha', 'beta', 'rc',
              'mono', 'stable']
    # mono: a specific version of Godot with C# support
    # stable: This is for the stable version of Godot. It must be kept
    # or the "mono" part after it will be discarded for the mono version
    # (keeping it allows 2 icons, one for each version). The " stable"
    # part is removed manually later. See `if "Godot" in caption:`.
    BIN_EXTS = [
        "",
        "sh",
        "32",  # such as Godot 32-bit
        "64",  # such as Godot 64-bit
    ]
    verbosity = 1
    NO_VER_FLAG = "The end of the program name"

    def __init__(self, src_path, **kwargs):
        '''
        Sequential arguments:
        src_path -- If the init parameter is a directory, the
        extension will not be removed.

        Keyword arguments
        arch -- 64bit or 32bit, to match the first element in the tuple
            returned by Python's platform.architecture(). If no
            delimited segment of the filename is in X64S or X32S, the
            arch will be None after the contructor call.

        platform -- uppercase platform such as "Linux" or "Windows"
            to match the output of Python's platform.system(). If no
            delimited segment of the filename is in LINS or WINS, the
            platform will be None after the contructor call.

        casedName -- The casedName is the human-readable name without
            the version, possibly including uppercase and spaces
            (generated if None).

        luid -- the name ("locally unique identifier" uniquely
            identifying the program (no version); ready to be used as
            an icon file name; used as a key for the icons dict or
            casedNames dict default: toLUID(casedName)
        version -- You must specify a version if the name has no
            version. This script should automatically pass along the
            version such as if the archive but not directory (or
            directory but not not binary) has the version.
        dry_run -- Setting this to True prevents a ValueError when
            src_path is not a file in a way that is more future-proof
            than is_dir=True. The reason for forcing init to
            finish is to obtain metadata for non-install purposes.
        do_uninstall -- This doesn't uninstall the program or change the
            construction of the object, but makes error(s) more clear.
        '''
        raw_src_path = src_path
        print("[PackageInfo __init__] * checking src_path {}..."
              "".format(src_path))
        if PackageInfo.verbosity > 0:
            print("")
            print("Creating PackageInfo...")
        self.metas = ['casedName', 'luid', 'version',
                      'caption', 'platform', 'arch', 'is_dir']
        # TODO: no_error = kwargs.get('no_error') is True
        self.casedName = kwargs.get('casedName')
        self.luid = kwargs.get("luid")
        # ^ decided by transforming casedName below if None
        self.version = kwargs.get('version')
        self.platform = None
        self.arch = None
        do_uninstall = kwargs.get('do_uninstall')
        self.path = src_path
        self.suffix = ""
        self.dry_run = kwargs.get('dry_run')
        is_dir = kwargs.get('is_dir')
        if is_dir is None:
            if not os.path.exists(src_path) and not self.dry_run:
                msg = (
                    "src_path {} must exist or you must specify the"
                    " is_dir keyword argument for PackageInfo"
                    " init (only if running a test)."
                    "".format(sh_literal(src_path))
                )
                if do_uninstall:
                    msg_fmt = (
                        "src_path {} doesn't exist so"
                        " whether it is a directory can't be determined"
                        " and wasn't in {}. If you are uninstalling"
                        " without the full file/folder name of the"
                        " install source, " + bad_id_flag
                        + ": {} (from {})."
                    )
                    msg = msg_fmt.format(
                        sh_literal(src_path),
                        sh_literal(localMachineMetaPath),
                        getProgramIDs(),
                        sh_literal(localMachineMetaPath),
                    )
                # raise ValueError(msg + " {}".format(self.toDict()))
                # ^ every meta is None at this point.
                caller_line = None
                relative_frame = 1
                total_stack = inspect.stack()
                # total_depth = len(total_stack)
                frameinfo = total_stack[relative_frame][0]
                # relative_depth = total_depth - relative_frame
                # func_name = frameinfo.f_code.co_name
                caller_line = frameinfo.f_lineno
                caller_file = os.path.basename(frameinfo.f_code.co_filename)
                raise ValueError(msg + " \n{}:{}: should set is_dir."
                                 "".format(caller_file, caller_line))
            is_dir = os.path.isdir(src_path)
        self.is_dir = is_dir
        if not do_uninstall:
            if (self.is_dir is not None) and (self.luid is not None):
                was_dir = getProgramValue(self.luid, 'is_dir', force=True)
                if was_dir is True:
                    '''
                    It is possible that a previous PackageInfo was
                    constructed for the directory and another was
                    constructed to make the shortcut (and therefore
                    is_dir has to be True in this one to deal with
                    the shortcut, but localMachine should continue to
                    store is_dir as True so a directory is known to
                    be the source.
                    '''
                    print("* was_dir: {}".format(self.is_dir))
                    print("  * is_dir (shortcut): {}"
                          "".format(self.is_dir))
                else:
                    print("* is_dir: {}".format(self.is_dir))
                    setProgramValue(self.luid, 'is_dir', self.is_dir)
        removeExt = kwargs.get('removeExt')
        if removeExt is None:
            removeExt = not is_dir
        self.fname = os.path.split(self.path)[-1]
        fnamePartial = self.fname
        if removeExt:
            fnamePartial = os.path.splitext(self.fname)[0]
            if fnamePartial.lower().endswith(".tar"):
                fnamePartial = fnamePartial[:-4]
        startChar = 0
        while not fnamePartial[startChar].isalpha():
            startChar += 1
            if startChar >= len(fnamePartial):
                msg = noAlphaErrorFmt.format(self.fname, fnamePartial)
                echo0(msg)
                echo0("raw_src_path: {}".format(raw_src_path))
                echo0("src_path: {}".format(src_path))
                echo0("kwargs: {}".format(kwargs))
                raise ValueError(msg)
                # print(msg)
                # break
                # startChar = 0
        fnamePartial = fnamePartial[startChar:]
        self.caption = kwargs.get('caption')
        parts = split_any(fnamePartial, PackageInfo.DELIMITERS,
                          blobs=PackageInfo.ARCHES)
        archI = -1
        if PackageInfo.verbosity > 0:
            print("* name without extension: {}"
                  "".format(encode_py_val(fnamePartial)))
        platformI = -1
        versionI = -1
        if len(parts) < 2:
            # re-split
            tmpParts = fnamePartial.split(".")
            parts, versionI = PackageInfo.unsplit_version(tmpParts)
            print("* split {} into {} len {} (version is at [{}])"
                  "".format(fnamePartial, tmpParts, len(tmpParts),
                            versionI))
        else:
            oldDelimiters = []
            cI = 0
            for i in range(len(parts)):
                cI += len(parts[i])
                if cI < len(fnamePartial):
                    oldDelimiters.append(fnamePartial[cI])
                    cI += 1  # add the delimiter length
                else:
                    oldDelimiters.append("")
                if parts[i][:1].lower() == "v":
                    # Remove v such as "v1.0" to "1.0".
                    if is_digits(parts[i][1:]):
                        parts[i] = parts[i][1:]
                partL = parts[i].lower()
                if partL in PackageInfo.X64S:
                    self.arch = "64bit"
                    archI = i
                    # Always do 64-bit first so that x86_64 is found
                    # before x86.
                elif partL in PackageInfo.X32S:
                    self.arch = "32bit"
                    archI = i
                elif partL == "x86":
                    if (len(parts) > i + 1) and (parts[i+1] == "64"):
                        self.arch = "64bit"
                    else:
                        self.arch = "32bit"
                elif partL in PackageInfo.NOARCHES:
                    self.arch = "noarch"
                if partL in PackageInfo.LINS:
                    self.platform = "Linux"
                    platformI = i
                elif partL in PackageInfo.WINS:
                    self.platform = "Windows"
                    platformI = i
            parts, versionI = PackageInfo.unsplit_version(
                parts,
                oldDelimiters=oldDelimiters
            )
            # ^ still do unsplit_version, because the version may be
            #   multiple parts such as in ['Slic3r', '1.3.1', 'dev']
            del i
        if (len(parts) < 2) and (self.version is None):
            if not self.dry_run:
                usage()
                raise ValueError(PackageInfo.NO_VER_FLAG + " (any of"
                                 " '{}' or '.' is not in {} and you"
                                 " didn't specify a version such as:\n"
                                 " {} {} --version x"
                                 "".format(PackageInfo.DELIMITERS,
                                           encode_py_val(fnamePartial),
                                           me, sh_literal(src_path)))
            else:
                echo0("WARNING: no version is in {}"
                      "".format(fnamePartial))
        if self.version is None:
            # INFO: Any "v" prefix was already removed and multi-part
            #       versions were already un-split into one part
            #       using unsplit_version (in re-split code or the
            #       `else` case).
            if versionI > -1:
                self.version = parts[versionI]
                if True:  # TODO: if PackageInfo.verbosity > 0:
                    print("* using '" + self.version + "' as version")
        else:
            if True:  # TODO: PackageInfo.verbosity > 0:
                print("* using specified '{}' as version"
                      "".format(self.version))

        nameEnder = -1
        if versionI > -1:
            nameEnder = versionI
            if PackageInfo.verbosity > 0:
                print("* ending name at version {}"
                      "".format(encode_py_val(parts[versionI])))
        if platformI > -1:
            if nameEnder < 0 or (platformI < nameEnder):
                nameEnder = platformI
        if versionI > -1:
            if (nameEnder < 0) or (versionI < nameEnder):
                nameEnder = versionI

        if self.casedName is None:
            self.casedName = parts[0]
            hyphenateI = find_startswith(hyphenate_names,
                                         "-".join(parts), cs=False)
            if hyphenateI >= 0:
                lowerCaseParts = hyphenate_names[hyphenateI].split("-")
                newPartsCount = len(lowerCaseParts)
                self.casedName = "-".join(parts[:newPartsCount])
                '''
                ^ Reconstruct the uppercase name even though it will
                  become lowercase later.
                  - Why not add a lookup instead:
                    Adding a lookup for luid based on a partial name
                    such as "ninja" (extracted from "ninja-ide" at this
                    point) would result in a false positive for a
                    program actually called "ninja".
                '''
            elif nameEnder > 0:
                self.casedName = " ".join(parts[:nameEnder])
            else:
                print("WARNING: there is no name ender such as arch,"
                      " platform or version, so the first part will be"
                      " the name: {}."
                      "".format(encode_py_val(self.casedName)))
            if PackageInfo.verbosity > 0:
                print("* using '{}' as human-readable name"
                      " before adding version".format(self.casedName))
        else:
            if PackageInfo.verbosity > 0:
                print("* using specified name: {}"
                      "".format(self.casedName))

        annotation = get_annotation(src_path)
        if annotation is not None:
            self.suffix = "-" + annotation

        if self.luid is None:
            self.luid = toLUID(self.casedName)
            print("* luid (generated from casedName): {}"
                  "".format(self.luid))

        if kwargs.get('casedName') is None:
            # only use a build-in cased name if not specified manually
            # (a casedName may have been generated above, but the
            # following can't be completed until LUID is generated if
            # not present)
            tryCasedName = casedNames.get(self.luid)
            if tryCasedName is None:
                if self.casedName.lower() == self.casedName:
                    if PackageInfo.verbosity > 1:
                        print("* The program {} is not in the"
                              " casedNames dict and is all lowercase,"
                              " so the caption {} will become"
                              " title case (parts: {})."
                              "".format(encode_py_val(self.casedName),
                                        encode_py_val(fnamePartial),
                                        parts))
                    self.casedName = self.casedName.title()
                # else use self.casedName since not all lower.
            else:
                self.casedName = tryCasedName
                if PackageInfo.verbosity > 1:
                    print("* detected '{}' so changed case to '{}'"
                          "".format(self.luid, tryCasedName))

        if PackageInfo.verbosity > 0:
            print("* using {} as icon filename prefix (luid)"
                  " (The version will be added later if multiVersion)"
                  "".format(encode_py_val(self.luid)))

        if self.caption is None:
            if versionI > -1:
                self.caption = self.casedName + " " + parts[versionI]
            else:
                print("WARNING: the caption will not have a version"
                      " since no version was detected in {}"
                      "".format(parts))
                self.caption = self.casedName
            if annotation is not None:
                suffix = " (" + annotation + ")"
                if PackageInfo.verbosity > 1:
                    print("* appending \" ({})\" to caption..."
                          "".format(annotation))
                if not self.caption.endswith(suffix):
                    self.caption += suffix
                    print("  OK")
                else:
                    if PackageInfo.verbosity > 0:
                        print("  - skipped: it already ends with {}"
                              "".format(encode_py_val(suffix)))

    # @classmethod
    # def unsplitArch(cls, tmpParts):

    @classmethod
    def unsplit_version(cls, tmpParts, TwoOnly=False,
                        oldDelimiters=None):
        '''
        Get a ([], int) tuple of (parts, versionI) where versionI is the
        index of the version and parts is the same list except where the
        version is in one element.

        Example: ['blender','2','9','3'] becomes
                 (['blender', '2.9.3'], 1)

        Sequential arguments:
        cls -- Class (Don't specify this--Call
            PackageInfo.unsplit_version to prepend the class)
        TwoOnly -- Combine everything before the version and after the
            start of the version.
        oldDelimiters -- Add old delimiters back when un-splitting.
        '''
        fn = 'unsplit_version'
        firstNumI = -1
        lastNumI = -1
        letteredI = -1
        versionI = -1
        parts = tmpParts
        if PackageInfo.verbosity > 1:
            print("[unsplit_version] tmpParts={}".format(tmpParts))
        if not hasattr(tmpParts, 'append'):
            raise ValueError("tmpParts must be a list but is {}"
                             "".format(tmpParts))
        for i in range(len(tmpParts)):
            if tmpParts[i][:1].lower() == "v":
                # Remove v such as "v1" to "1".
                if is_version(tmpParts[i][1:], True,
                              PackageInfo.VPARTS):
                    tmpParts[i] = tmpParts[i][1:]
                    if PackageInfo.verbosity > 1:
                        print("  * unsplit_version removed a 'v'")
                else:
                    if PackageInfo.verbosity > 1:
                        print("  * unsplit_version kept a 'v'")
            tmpPart = tmpParts[i]
            if is_version(tmpPart, False, PackageInfo.VPARTS):
                if PackageInfo.verbosity > 1:
                    print("  * {} ({}) is a version part."
                          "".format(tmpPart, i))
                if firstNumI < 0:
                    firstNumI = i
                lastNumI = i
            elif is_version(tmpPart, True, PackageInfo.VPARTS):
                if PackageInfo.verbosity > 1:
                    print("  * {} is a lettered version part."
                          "".format(tmpPart))
                if letteredI < 0:
                    letteredI = firstNumI
                if firstNumI < 0:
                    firstNumI = i
                lastNumI = i
            else:
                if PackageInfo.verbosity > 1:
                    print("  * {} ({}) is not a version part."
                          "".format(tmpPart, i))
                if firstNumI > -1:
                    # end the version parts
                    break
        if firstNumI > -1:
            if letteredI > -1:
                if lastNumI > letteredI:
                    print(
                        "  [{}] WARNING: version numbers {} appear"
                        " after the alphabetical suffix {} in {}."
                        "".format(fn, tmpParts[lastNumI],
                                  tmpParts[letteredI],
                                  tmpParts)
                    )
            if firstNumI == 0:
                parts = ["", ".".join(tmpParts)]
                print("  [{}] WARNING: No name was detected in {}"
                      "".format(fn, tmpParts))
            else:
                firstNameI = 0
                lastNameI = firstNumI - 1
                if TwoOnly:
                    parts = [
                        ".".join(tmpParts[firstNameI:lastNameI+1]),
                        ".".join(tmpParts[firstNumI:lastNumI+1]),
                    ]
                    versionI = 1
                    print("  [{}] TwoOnly is enabled, so version part"
                          " is {}".format(fn, parts[versionI]))
                else:
                    if oldDelimiters is not None:
                        parts = tmpParts[:firstNumI]
                        i = len(parts)
                        print("  [{}] firstNumI={}, lastNumI={}"
                              "".format(fn, firstNumI, lastNumI))
                        joined = ""
                        while i <= lastNumI:
                            oldDelimiter = oldDelimiters[i]
                            # ^ last delimiter is ""
                            # print("  [{}]re-adding '{}'"
                            #       "".format(fn, oldDelimiter))
                            if i == lastNumI:
                                oldDelimiter = ""
                                # ^ Don't add the ending delimiter.
                            if (i + 1) < len(tmpParts):
                                if tmpParts[i+1] in PackageInfo.VPARTS:
                                    oldDelimiter = " "
                                    # ^ ensure the icon name wraps
                                    #   to the next line instead of
                                    #   being cut off (such as
                                    #   "Godot 3.3.2 stable mono")
                                    pass
                            joined += tmpParts[i] + oldDelimiter
                            i += 1
                        parts.append(joined)
                        parts += tmpParts[lastNumI+1:]
                    else:
                        parts = (
                            tmpParts[:firstNumI]
                            + [".".join(tmpParts[firstNumI:lastNumI+1])]
                            + tmpParts[lastNumI+1:]
                        )
                    versionI = firstNumI
            if PackageInfo.verbosity > 0:
                print("  [{}] changed parts to {}".format(fn, parts))
            # "since no "
            # "".format(parts, PackageInfo.DELIMITERS))
        else:
            print("  [{}] There are no version strings in {}"
                  "".format(fn, tmpParts))
        return parts, versionI

    def get_bits(self):
        '''
        Get 32 or 64 (integer) or None if unknown.
        '''
        if self.arch is None:
            return None
        if self.arch in PackageInfo.X64S:
            return 64
        elif self.arch in PackageInfo.X32S:
            return 32
        return None

    def toDict(self):
        ret = {}
        for k in self.metas:
            try:
                ret[k] = getattr(self, k)
                # except KeyError:  # only if using self.__dict__
            except AttributeError:
                ret[k] = None
        return ret

    def get_coexisting_id(self, multiPackage, multiVersion):
        '''
        To allow multiple versions, append "-"+pkginfo.version to the
        name when naming the desktop file or for other uses requiring
        separating multiple versions. The output will always be
        lowercase.
        '''
        ret = self.luid
        if multiPackage:
            ret += self.suffix
        if multiVersion:
            ret += "-" + self.version
        return ret

    def toList(self):
        return [self.__dict__[k] for k in self.metas]

    def __str__(self):
        return str(self.toDict())


def dir_is_empty(folder_path):
    count = 0
    sub_names = os.listdir(folder_path)
    for sub_name in sub_names:
        count += 1
    return count < 1

OLD_CONFS = get_unique_path("install_any", "Configs:Unique")
MY_CONFS = get_unique_path("nopackage", "Configs:Unique")  # formerly myAppData
if not os.path.isdir(MY_CONFS):
    os.makedirs(MY_CONFS)

oldLMP = os.path.join(OLD_CONFS, "local_machine.json")
localMachineMetaPath = os.path.join(MY_CONFS, "local_machine.json")
oldLP = os.path.join(OLD_CONFS, "install_any.log")
logPath = os.path.join(MY_CONFS, "nopackage.log")
PIXMAPS

echo0('[nopackage] logPath="{}"'.format(logPath))

if os.path.isfile(oldLMP):
    if not os.path.isfile(localMachineMetaPath):
        shutil.move(oldLMP, localMachineMetaPath)
        echo0("* migrated old metadata:")
        echo0("mv {} {}"
              "".format(sh_literal(oldLMP),
                        sh_literal(localMachineMetaPath)))
if os.path.isfile(oldLP):
    if not os.path.isfile(logPath):
        shutil.move(oldLP, logPath)
        echo0("* migrated an old log:")
        echo0("mv {} {}"
              "".format(sh_literal(oldLP), sh_literal(logPath)))
    else:
        echo0("WARNING: There is an old {} which should be prepended to"
              " the new {}."
              "".format(sh_literal(oldLP), sh_literal(logPath)))
else:
    pass
    # echo0("INFO: There is no {}".format(oldLP))

localMachine = {
    'programs': {}
}

# Date variables below are borrowed from enissue.py in
# <https://github.com/Poikilos/EnlivenMinetest>, but the sanitized
# version instead of the Gitea-specific version is used:
giteaSanitizedDtFmt = "%Y-%m-%dT%H:%M:%S%z"
sanitizedDtExampleS = "2021-11-25T12:00:13-0500"


def fillProgramMeta(programMeta):
    pkginfo = None
    if programMeta.get('src_path') is not None:
        pkginfo = PackageInfo(
            programMeta.get('src_path'),  # required
            casedName=programMeta.get('casedName'),
            version=programMeta.get('version'),
            caption=programMeta.get('caption'),
            luid=programMeta.get('luid'),
            dry_run=True,  # prevents ValueError on no file.
        )
    else:
        print("WARNING: There is no src_path for {}"
              "".format(programMeta))
        return programMeta
    derivedMeta = pkginfo.toDict()
    for k, v in derivedMeta.items():
        if programMeta.get(k) is None:
            programMeta[k] = v
    return programMeta


if not os.path.isfile(localMachineMetaPath):
    if os.path.isfile(logPath):
        echo0("* generating {} from {}"
              "".format(localMachineMetaPath, logPath))
        names = set([])
        programs = localMachine['programs']
        lineN = 0
        regionStarters = set(['install_file', 'uninstall_dir'])
        pkginfo = None
        validNames = set(['uninstall_dir', 'install_file',
                          'uninstall_file', 'recovered_to', 'luid',
                          'ERROR', 'install_move_dir',
                          'install_shortcut', 'uninstall_shortcut'])
        with open(logPath, 'r') as ins:
            thisMeta = {
                'logLineNumber': lineN,
                'installed': True,
            }
            # ^ also set to {} when regionStarters!
            for rawL in ins:
                lineN += 1  # Counting numbers start at 1.
                line = rawL.strip()
                if line == noCmdMsg:
                    continue
                if line == OLD_NO_CMD_MSG:
                    continue
                if line.startswith("*"):
                    continue
                if len(line) < 1:
                    continue
                name = None
                value = None
                signI = -1
                if line.startswith("luid="):
                    signI = 4
                elif "=" in line:
                    raise NotImplementedError("An '=' sign not directly"
                                              " preceded by  \"luid\""
                                              " isn't a recognized log"
                                              " entry.")
                if signI < 0:
                    signI = line.find(":")
                if signI < 0:
                    echo0("{}:{}: Unrecognized line format: {}"
                          "".format(logPath, lineN, line))
                    continue
                name = line[:signI]
                valueStr = line[signI+1:]
                value = decode_py_val(valueStr, lineN=lineN,
                                      path=logPath)
                names.add(name)
                if name in regionStarters:
                    if thisMeta.get('src_path') is not None:
                        thisMeta = fillProgramMeta(thisMeta)
                        if thisMeta.get('luid') is None:
                            echo0("WARNING: A luid was not determined"
                                  " for {}".format(thisMeta))
                        else:
                            programs[thisMeta['luid']] = thisMeta
                            echo1("ENTERED program: {}"
                                  "".format(thisMeta['luid']))
                    elif len(thisMeta) > 2:
                        echo0("WARNING: There is no src_path in {}"
                              "".format(thisMeta))
                    thisMeta = {
                        'logLineNumber': lineN,
                        'installed': True,
                    }
                # Determine the meaning separately from the "if" case
                # above which merely moves on to another program.
                if name == 'uninstall_dir':
                    thisMeta['installed'] = False
                elif name == 'install_file':
                    badValue = os.path.join(lib64, "1.InstallManually")
                    # ^ A bug causes the value to be badValue, so ignore
                    #   it (See ).
                    # src_path = value
                elif name == 'recovered_to':
                    thisMeta['src_path'] = value
                    thisMeta['installed'] = False
                elif name == 'uninstall_file':
                    thisMeta['installed'] = False
                elif name == 'luid':
                    thisMeta['luid'] = value
                elif name == "ERROR":
                    thisMeta['error'] = value
                    if thisMeta['installed']:
                        thisMeta['installed'] = False
                    else:
                        # Assume installed if error was during uninstall
                        thisMeta['installed'] = True
                elif name == 'install_move_dir':
                    thisMeta['install_move_dir'] = value
                elif name == 'install_shortcut':
                    thisMeta['install_shortcut'] = value
                elif name == 'uninstall_shortcut':
                    thisMeta['uninstall_shortcut'] = value
                    thisMeta['installed'] = False
                else:
                    echo0("{}:{}: WARNING: The line variable name {} is"
                          " unrecognized for: {}"
                          "".format(logPath, lineN, name, thisMeta))
            # The loop is over, so get the last one:
            if thisMeta.get('src_path') is not None:
                thisMeta = fillProgramMeta(thisMeta)
                if thisMeta.get('luid') is None:
                    echo0("WARNING: A luid was not determined for"
                          " {}".format(thisMeta))
                else:
                    programs[thisMeta['luid']] = thisMeta
            elif len(thisMeta) > 2:
                echo0("WARNING: There is no src_path in {}"
                      "".format(thisMeta))

        # echo0("names: {}".format(names))
        # ^ should match validNames
        echo0("")
        echo0("localMachine: {}"
              "".format(json.dumps(localMachine, indent=2)))
        with open(localMachineMetaPath, 'w') as outs:
            json.dump(localMachine, outs, indent=2)
else:
    with open(localMachineMetaPath, 'r') as ins:
        localMachine = json.load(ins)

    echo0("* using installed programs metadata: {}"
          "".format(localMachineMetaPath))
fm = None


def saveLocalMachine():
    with open(localMachineMetaPath, 'w') as outs:
        json.dump(localMachine, outs, indent=2)


enableSaveOnWrite = True


def logLn(line, path=logPath):
    print("[logged]:" + line)
    global fm
    if fm is None:
        fm = 'w'
        if os.path.isfile(path):
            fm = 'a'
    with open(path, 'a') as outs:
        outs.write(line + "\n")
        fm = 'a'


def install_program_in_place(src_path, **kwargs):
    """
    Install or uninstall the application.

    Sequential arguments:
    src_path -- This is usually a file or directory source path, but if
        you don't specify the luid keyword argument, init will see if
        src_path is actually a luid (such as 'keepassxc') and will try
        to get the src_path from the local_machine.json configuration
        file that this program should maintain.

    Keyword arguments:
    casedName -- If casedName is not specified, the name and version
        will be calculated from either the filename at src_path or the
        path's parent directory's name.
        Example:
        src_path = \
        ../Downloads/blender-2.79-e045fe53f1b0-linux-glibc217-x86_64/blender
        (In this case, this function will extract the name and version
        from blender-2.79-e045fe53f1b0-linux-glibc217-x86_64 since it
        has more delimiters than the filename "blender")

    move_what -- Only set this to 'file' if src_path is an AppImage or
        other self-contained binary file. Otherwise you may set it to
        'directory' (or None to move nothing). The file or directory
        will be moved to ~/.local/lib64/ (or whatever programs
        directory is detected as a parent of the directory if
        detect_program_parent is True [automaticaly True by calling
        itself in the case of deb]). move_what='file' example: If name
        is not specified, the name and version will be calculated from
        either the filename at src_path or the path's parent
        directory's name. Example: src_path=( "../Downloads/"
        "FreeCAD_0.18-16131-Linux-Conda_Py3Qt5_glibc2.12-x86_64.AppImage"
        ) (In this case, this function will extract the name and
        version from
        FreeCAD_0.18-16131-Linux-Conda_Py3Qt5_glibc2.12-x86_64.AppImage)

    multiVersion -- Allow the version to be in the installed directory
        name and the icon name so that multiple versions of the same
        program (with same luid such as "blender" or "ultimaker.cura")
        can be installed at once. If None, will be set to True if
        "blender" is the luid.

        Even if false, If the file is an appimage, it can coexist with
        other non-appimage installs, since the non- appimage install
        will be a directory or non-appimage binary and since -appimage
        will be appended to the icon filename.

    luid -- This is the unique program name without the version, with
        dots instead of spaces and all lowercase. It is detected
        automatically from the file or directory name if None.
    """
    unfinalize_luid()
    version = kwargs.get("version")
    if version is not None:
        print("- version: {}".format(version))
    casedName = kwargs.get("casedName")
    caption = kwargs.get("caption")
    luid = kwargs.get("luid")
    do_uninstall = kwargs.get("do_uninstall")
    if do_uninstall is None:
        do_uninstall = False
    enable_reinstall = kwargs.get("enable_reinstall")
    if enable_reinstall is None:
        enable_reinstall = False
    detect_program_parent = kwargs.get("detect_program_parent")
    if detect_program_parent is None:
        detect_program_parent = False
    multiVersion = kwargs.get("multiVersion")
    icon_path = kwargs.get("icon_path")
    print("* icon_path was set to: {}".format(icon_path))
    move_what = kwargs.get("move_what")
    print("move_what: {}".format(move_what))
    pull_back = kwargs.get("pull_back")

    enable_force_script = False
    dst_programs = lib64  # changed if deb has a different programs dir
    if '32' in platform.architecture()[0]:
        dst_programs = lib
    dirname = None
    dirpath = None
    ex_tmp = None
    suffix = ""
    new_tmp = None
    verb = "uninstall" if do_uninstall else "install"
    pull_back = None
    knownMeta = None
    tryLuid = None
    # if luid is None:
    if not os.path.isfile(src_path):
        tryLuid = os.path.basename(src_path)
        knownMeta = localMachine['programs'].get(tryLuid)
    # if knownMeta is None:
    #     echo1('There is no meta for "{}"'.format(src_path))
    # ^ In case src_path is a luid, get some metadata.
    is_dir = None
    if knownMeta is not None:
        echo1("The program metadata for '{}' in {} will be used."
              "".format(knownMeta['luid'], localMachineMetaPath))
        luid = knownMeta.get('luid')
        src_path = knownMeta.get('src_path')
        echo1("src_path:{}".format(src_path))
        # ^ In case src_path is a luid, change src_path to the real one.
        if src_path is None:
            raise ValueError("There is an error in {}: The src_path is"
                             " not set for luid {}"
                             "".format(localMachineMetaPath, luid))
        if is_dir is None:
            if knownMeta.get('is_dir') is not None:
                is_dir = knownMeta.get('is_dir')
        if version is None:
            if knownMeta.get('version') is not None:
                version = knownMeta.get('version')
        if casedName is None:
            if knownMeta.get('casedName') is not None:
                casedName = knownMeta.get('casedName')
        if caption is None:
            if knownMeta.get('caption') is not None:
                caption = knownMeta.get('caption')
    else:
        echo0("* generating new metadata for potential luid '{}'"
              "".format(tryLuid))

    if src_path.lower().endswith(".appimage"):
        is_dir = False
        # ^ ONLY manually set this for files that won't be
        # extracted!
        pull_back = True
        if not os.path.exists(src_path):
            print("* attempting to recover to \"{}\"..."
                  "".format(src_path))

    ending = ".deb"
    if src_path.lower()[-(len(ending)):] == ending:
        logLn("* switching to reinstall mode automatically...")
        if enable_reinstall:
            logLn("  * already done")
        else:
            enable_reinstall = True
            logLn("  * OK")
        ex_tmp = tempfile.mkdtemp()
        print("* extracting '{}' to '{}'...".format(src_path, ex_tmp))
        ex_command = "cd '{}' && ar xv '{}'".format(ex_tmp, src_path)
        # NOTE: Instead of `ar`, python-libarchive could also work.
        cmd_return = os.system(ex_command)
        if dir_is_empty(ex_tmp):
            print("ERROR: `{}` did not result in any extracted files or"
                  " directories in"
                  " '{}'".format(ex_command, ex_tmp))
            return False
        elif cmd_return != 0:
            print("ERROR: `{}` returned an error value"
                  " ({})".format(ex_command, cmd_return))
            return False
        print("")
        # tar = tarfile.open(src_path)
        # tar.extractall(path=ex_tmp)
        # tar.close()
        next_path = os.path.join(ex_tmp, "data.tar.xz")
        if not os.path.isfile(next_path):
            print("ERROR: Extracting deb did not result in"
                  " '{}'.".format(next_path))
            shutil.rmtree(ex_tmp)
            print("  * deleted {}.".format(ex_tmp))
            return False
        next_temp = tempfile.mkdtemp()
        print("* extracting '{}'...".format(next_path))
        try:
            tar = tarfile.open(next_path)
            tar.extractall(path=next_temp)
            tar.close()
        except tarfile.ReadError:
            print("ERROR: tar could not extract '{}'".format(next_path))
            return False
        shutil.rmtree(ex_tmp)
        # ^ Remove temporary directory containing only control.tar.gz,
        #   data.tar.xz, and debian-binary.

        # Now next_temp should contain directories such as usr & etc.
        src_usr = os.path.join(next_temp, "usr")
        src_opt = os.path.join(next_temp, "opt")
        src_usr_share = os.path.join(src_usr, "share")
        try_programs_paths = [src_usr_share, src_opt]
        found_any = False
        for folder_path in try_programs_paths:
            if os.path.isdir(folder_path):
                found_any = True
        if not found_any:
            print("ERROR: extracting '{}' from '{}' did not result in"
                  " any of the following:"
                  " '{}'".format(next_temp, next_path,
                                 try_programs_paths))
            shutil.rmtree(next_temp)
            return False
        found_programs_paths = []
        sub_names = None
        for folder_path in try_programs_paths:
            if not os.path.isdir(folder_path):
                continue
            not_programs = ["applications", "icons", "doc"]
            sub_names = os.listdir(folder_path)
            for sub_name in sub_names:
                sub_path = os.path.join(folder_path, sub_name)
                if os.path.isdir(sub_path) and (sub_name[:1] != "."):
                    if sub_name not in not_programs:
                        found_programs_paths.append(sub_path)
        if len(found_programs_paths) == 0:
            print(
                "ERROR: extracting '{}' from '{}' did not result in"
                " any programs in any known directories:".format(
                    next_temp,
                    next_path,
                )
            )
            for folder_path in try_programs_paths:
                if os.path.isdir(folder_path):
                    print("{} only contains:"
                          " {}".format(folder_path,
                                       os.listdir(folder_path)))
            shutil.rmtree(next_temp)
            print("* removed '{}'".format(next_temp))
            return False
        elif len(found_programs_paths) > 1:
            print(
                "ERROR: extracting '{}' from '{}' resulted in"
                " too many unknown directories in '{}': ({})".format(
                    next_temp,
                    next_path,
                    try_programs_paths,
                    found_programs_paths
                )
            )
            shutil.rmtree(next_temp)
            print("* removed '{}'".format(next_temp))
            return False
        # program_temp = tempfile.mkdtemp()
        program_path = found_programs_paths[0]
        program = os.path.split(found_programs_paths[0])[-1]
        this_programs_path = os.path.split(found_programs_paths[0])[0]
        this_programs = os.path.split(this_programs_path)[-1]
        dst_programs = os.path.join(PREFIX, this_programs)
        print("* found programs path in deb: '{}'".format(dst_programs))

        if dst_programs == PREFIX:
            print("ERROR: source programs directory (directory"
                  " containing {}) was not"
                  " detected in deb.".format(program_path))
            shutil.rmtree(next_temp)
            print("* removed '{}'".format(next_temp))
            print("")
            raise RuntimeError("{} did not complete.".format(verb))

        binaries = []
        binary_path = None
        folder_path = program_path
        sub_names = os.listdir(folder_path)
        print("* looking for {}...".format(program))
        try_program_names = [program, program.lower(), program.title(),
                             program.upper()]
        for sub_name in sub_names:
            sub_path = os.path.join(folder_path, sub_name)
            if os.path.isfile(sub_path) and (sub_name[:1] != "."):
                binaries.append(sub_name)
                print("* detected possible program file"
                      " '{}'".format(sub_path))
                if sub_name in try_program_names:
                    binary_path = sub_path
                    break
                elif sub_name == "signal-desktop-beta":
                    binary_path = sub_path
                    break
        if binary_path is None:
            if len(binaries) == 1:
                binary_path = os.path.join(program_path, binaries[0])
            else:
                shutil.rmtree(next_temp)
                if len(binaries) == 0:
                    print(
                        "ERROR: extracting '{}' from '{}' did not"
                        " result in any files such as binaries in"
                        " '{}' (only {})".format(
                            next_temp,
                            next_path,
                            program_path,
                            sub_names
                        )
                    )
                else:
                    print(
                        "ERROR: extracting '{}' from '{}'"
                        " resulted in more than one file in"
                        " '{}' and one is not named {}, so the binary"
                        " could not be detected (among {})".format(
                            next_temp,
                            next_path,
                            program_path,
                            try_program_names,
                            binaries
                        )
                    )
                return False

        # The program is extracted and detected. Now, find the icon:
        src_icons = os.path.join(src_usr_share, "icons")
        icon_path = None
        icon_count = 0
        if os.path.isdir(src_icons):
            for root, dirs, files in os.walk(src_icons):
                for sub_name in files:
                    sub_path = os.path.join(root, sub_name)
                    icon_path = os.path.join(PIXMAPS, sub_name)
                    addProgramValue(luid, 'icon_paths', icon_path)
                    if do_uninstall:
                        if os.path.isfile(icon_path):
                            os.remove(icon_path)
                            print("* removed '{}'".format(icon_path))
                    else:
                        if not os.path.isdir(PIXMAPS):
                            os.makedirs(PIXMAPS)
                        try:
                            shutil.move(sub_path, icon_path)
                            print("* added '{}'".format(icon_path))
                        except Exception as e:
                            print("ERROR: moving '{}' to '{}'"
                                  " failed.".format(sub_path,
                                                    icon_path), e)
                            shutil.rmtree(next_temp)
                            print("* removed '{}'".format(next_temp))
                            return False
                    icon_count += 1
            if icon_count == 0:
                print("INFO: No icons were found in '{}' or its"
                      " subdirectories.".format(src_icons))
            if do_uninstall:
                for root, dirs, files in os.walk(src_icons):
                    for sub_name in dirs:
                        sub_path = os.path.join(PIXMAPS, sub_name)
                        if not os.path.isdir(sub_path):
                            print("* WARNING: '{}' is already not"
                                  " present.".format(sub_path))
                            continue
                        if dir_is_empty(sub_path):
                            # This should work (deepest will be listed
                            # first) since walk sets topdown to False by
                            # default.
                            os.rmdir(sub_path)
                            print("* removed '{}'".format(sub_path))
            else:
                print("* using '{}' as icon".format(icon_path))
        else:
            print("INFO: No '{}' directory was found."
                  "".format(src_icons))
        # Now install the program:

        pkginfo = PackageInfo(
            src_path,
            casedName=casedName,
            version=version,
            caption=caption,
        )
        # ^ Do NOT specify is_dir (The program must exist since it was
        #   extracted from a package)
        if casedName is None:
            casedName = pkginfo.casedName
        if version is None:
            version = pkginfo.version
        if caption is None:
            caption = pkginfo.caption
        if luid is None:
            luid = pkginfo.luid
        # ^ luid may be changed again is multiversion or other reasons.
        #   Don't use it before the finalize_luid() call.
        suffix = pkginfo.suffix
        # ^ Get the info now, because the extracted directory name will
        #   not contain the version.
        print("* forwarding info for recursion: {} luid:{}"
              "".format([casedName, version, caption], luid))
        print("")
        print("")
        result = install_program_in_place(
            binary_path,
            caption=program+" (deb)",
            casedName=casedName,
            version=version,
            move_what='directory',
            do_uninstall=do_uninstall,
            luid=luid,
            icon_path=icon_path,
            enable_reinstall=enable_reinstall,
            detect_program_parent=True,
            pull_back=pull_back,
        )
        shutil.rmtree(next_temp)
        print("* removed '{}'".format(next_temp))
        return result
        # ^ return archive within extracted archive
        # end if deb (containing tar.xz)

    archive_categories = {}
    archive_categories["tar"] = [".tar.bz2", ".tar.gz", ".tar.xz"]
    archive_categories["zip"] = [".zip"]
    # found_ending = None
    ar_cat = None
    for category, endings in archive_categories.items():
        for ending in endings:
            if src_path.lower()[-(len(ending)):] == ending:
                dirname = src_path[:-(len(ending))]
                echo1("* generated dirname {} from src_path {}"
                      "".format(dirname, src_path))
                # found_ending = ending
                ar_cat = category
                pkginfo = PackageInfo(
                    src_path,
                    casedName=casedName,
                    version=version,
                    caption=caption,
                )
                # ^ Do NOT specify is_dir
                if casedName is None:
                    casedName = pkginfo.casedName
                if version is None:
                    version = pkginfo.version
                    print("* version from archive name is: {}"
                          "".format(version))
                if caption is None:
                    caption = pkginfo.caption
                if luid is None:
                    luid = pkginfo.luid
                suffix = pkginfo.suffix
                # ^ Get the info now, because the extracted directory
                #   name may not contain the version.

                break
    if (dirname is not None) and (not do_uninstall):
        move_what = 'directory'
        ex_tmp = tempfile.mkdtemp()
        print("* created '{}'".format(ex_tmp))
        print("* enabling move from directory '{}'".format(ex_tmp))
        sub_dirs = []
        sub_files = []
        print("* extracting '{}'...".format(src_path))
        if ar_cat == "tar":
            tar = tarfile.open(src_path)
            tar.extractall(path=ex_tmp)
            tar.close()
        elif ar_cat == "zip":
            with ZipFile(src_path, 'r') as zipfile:
                zipfile.extractall(path=ex_tmp)
        else:
            raise NotImplementedError("There is no case for " + ar_cat)
        print("* extracted '{}'".format(ex_tmp))
        folder_path = ex_tmp
        for sub_name in os.listdir(folder_path):
            sub_path = os.path.join(folder_path, sub_name)
            if os.path.isfile(sub_path):  # sub_name[:1]!="." and
                sub_files.append(sub_path)
            elif os.path.isdir(sub_path):
                sub_dirs.append(sub_path)
        dirpath = None
        new_tmp = None
        if (len(sub_dirs) == 1) and (len(sub_files) == 0):
            dirpath = sub_dirs[0]
            print("* detected program path '{}'".format(dirpath))
        else:
            dirpath = ex_tmp
            print("* detected program path '{}'".format(dirpath))
            new_tmp = tempfile.mkdtemp()
            dirpath = os.path.join(new_tmp, dirname)
            shutil.move(ex_tmp, dirpath)
            print("* changed temp program path to '{}'".format(dirpath))
        src_path = dirpath
        move_what = 'directory'
        print("* changed {} source to '{}'".format(verb, src_path))

    if os.path.isdir(src_path):
        dirpath = src_path
        print("* trying to detect binary...")
        src_name = os.path.split(src_path)[-1]
        only_name = src_name.strip("-0123456789. ")
        try_name = src_name.split("-")[0]
        try_names = []
        if src_name not in hyphenate_names:
            name_partial = src_name.split("-")[0]
        else:
            name_partial = src_name
        try_names.append(name_partial + ".sh")
        try_names.append(name_partial + ".py")
        # ^ sh takes priority in case environment vars are necessary
        try_names.append(name_partial)
        if len(src_name.split("-")) > 1:
            try_names.append(src_name.split("-")[1] + ".sh")
            # ^ such as studio.sh for android-studio
        print("  src_name: {}".format(src_name))
        print("  only_name: {}".format(only_name))
        print("  name_partial: {}".format(name_partial))
        got_path = None
        try_paths = []
        for try_name in try_names:
            try_paths.append(os.path.join(src_path, "bin", try_name))
            try_paths.append(os.path.join(src_path, try_name))
        for try_path in try_paths:
            if os.path.isfile(try_path):
                got_path = try_path
                break

        if got_path is not None:
            print("* detected binary: '{}'".format(got_path))
            src_path = got_path
        else:
            all_files = os.listdir(src_path)
            scripts = []
            jars = []
            for sub in all_files:
                sub_path = os.path.join(src_path, sub)
                ext = os.path.splitext(sub)[1].strip(".")
                if sub.startswith("."):
                    continue
                if os.path.isdir(sub_path):
                    print("  - \"{}\" is a directory".format(sub))
                    continue
                if sub.endswith(".jar"):
                    jars.append(sub)
                elif ext in PackageInfo.BIN_EXTS:
                    scripts.append(sub)
            if len(scripts) >= 2:
                bad_indices = []
                good_indices = []
                for i in range(len(scripts)):
                    script = scripts[i]
                    if script.startswith(only_name):
                        good_indices.append(i)
                    elif script == "monero-wallet-gui":
                        good_indices.append(i)
                    else:
                        bad_indices.append(i)
                if len(good_indices) == 1:
                    for bad_ii in range(len(bad_indices)-1, -1, -1):
                        bad_i = bad_indices[bad_ii]
                        del scripts[bad_i]
                    print("  only one matches \"{}\"".format(only_name))
                    enable_force_script = True
            if len(scripts) == 2:
                short_i = 0
                long_i = 1
                if len(scripts[0]) > len(scripts[1]):
                    short_i = 1
                    long_i = 0
                # TODO: sName = scripts[short_i]
                lName = scripts[long_i]
                if lName.startswith(os.path.splitext(lName)):
                    # if has something like argouml.sh and
                    # argouml2.sh (experimental), use argouml.sh.
                    del scripts[long_i]
            if len(scripts) > 1:
                for known_binary in known_binaries:
                    if known_binary in scripts:
                        scripts = [known_binary]
                        break
            if len(jars) > 0:
                enable_force_script = True

            if enable_force_script or (len(scripts) == 1):
                src_path = os.path.join(src_path, scripts[0])
                print("* detected executable script: '{}'"
                      "".format(src_path))
            else:
                print("* could not detect binary in {}"
                      "".format(all_files))
                print("  jars: {}".format(jars))
                print("  scripts: {}".format(scripts))
                # if len(scripts) == 1:
                #     print("  - There is only {} script.")
                return False

    if src_path is None:
        usage()
        echo0("")
        echo0("Error: You must specify a path to a binary file.")
        return False
    elif not os.path.isfile(src_path):
        src_name = os.path.split(src_path)[-1]
        try_dest_path = os.path.join(dst_programs, src_name)
        if not do_uninstall:
            usage()
            print("ERROR: '{}' is not a file.".format(src_path))
            try_dest_name = os.path.split(try_dest_path)[1]
            if os.path.isfile(try_dest_path):
                print("'{}' is already {}ed.".format(try_dest_path, verb))
            elif try_dest_name in ['remove', 'uninstall']:
                print("Maybe you meant: nopackage remove")
            return False
    print("{} started.".format(verb.title()))

    filename = os.path.split(src_path)[-1]
    if dirpath is None:
        # dirpath = os.path.split(src_path)[-2]
        # print("* There was no dirpath, so set to parent: \"{}\""
        #       "".format(dirpath))
        # ^ This would be really bad. It would become whatever folder
        #   contains the file if it is a file!
        pass
    else:
        print("* using detected \"{}\" for dirpath (source was \"{}\")"
              "".format(dirpath, os.path.split(src_path)[-2]))
        filename = src_path[len(dirpath)+1:]  # 1 for slash
        # INFO: The filename is a relative path (not merely a name) in
        #       this case.
        print("  * therefore the filename is \"{}\""
              "".format(filename))
        if move_what == 'file':
            raise RuntimeError("A single file install is impossible"
                               " since there is a directory.")
    if detect_program_parent:
        this_programs_path = os.path.split(dirpath)[0]
        this_programs = os.path.split(this_programs_path)[-1]
        dst_programs = os.path.join(PREFIX, this_programs)
        if dst_programs == PREFIX:
            print("ERROR: source programs directory (directory"
                  " containing {}) was not"
                  " detected.".format(src_path))
            if ex_tmp is not None:
                if os.path.isdir(ex_tmp):
                    shutil.rmtree(ex_tmp)
                    print("* removed '{}'".format(ex_tmp))
            if new_tmp is not None:
                if os.path.isdir(new_tmp):
                    shutil.rmtree(new_tmp)
                    print("* removed '{}'".format(new_tmp))
            print("")
            print("{} did not complete.".format(verb.title()))
            print("")
            exit(1)

    print("* using programs path: '{}'".format(dst_programs))
    # dirname = os.path.split(dirpath)[-1]
    # echo1("* generated dirname {} from dirpath {}"
    #       "".format(dirname, dirpath))
    echo1("* dirname: {}"
          "".format(dirname))

    # luid = None
    applications = os.path.join(SHARE, "applications")
    retetected_version_used = False
    if (casedName is None) or (version is None):
        retetected_version_used = True
        echo1("* casedName:{} version:{} () so detecting..."
              "".format(casedName, version))
        # try_names = [filename, dirname]
        # echo1("* detecting name and version from {}".format(src_path))
        # if os.path.isdir(dirpath)
        try_sources = []
        # if not src_path.lower().endswith(".appimage"):
        if dirpath is not None:
            try_sources.append(dirpath)
        try_sources.append(src_path)
        pkg = None
        pkgs = []
        echo0("* detecting name and version from any of {}"
              "".format(try_sources))
        for try_src_i in range(len(try_sources)):
            try_source = try_sources[try_src_i]
            echo0("[install_program_in_place] * try_sources[{}] {}"
                  "".format(try_src_i, try_source))
            # try:
            thisPkg = PackageInfo(
                try_source,
                casedName=casedName,
                version=version,
                caption=caption,
                is_dir=is_dir,
                do_uninstall=do_uninstall,
            )
            pkgs.append(thisPkg)
            if thisPkg.version is not None:
                break
            '''
            except ValueError as ex:
                if PackageInfo.NO_VER_FLAG in str(ex):
                    # If there is any other item in try_sources,
                    # there may still be a package to add to pkgs,
                    # so just keep going if the only problem is that
                    # the format was incorrect.
                    continue
                else:
                    raise ex
            '''
        for thisPkg in pkgs:
            if pkg is None:
                pkg = thisPkg
            if thisPkg.version is not None:
                if version is None:
                    version = pkg.version
            if thisPkg.casedName is not None:
                if casedName is None:
                    casedName = pkg.casedName
                elif len(casedName) < len(thisPkg.casedName):
                    print('WARNING: the previously collected name'
                          ' "{}" is shorter than the detected name'
                          ' "{}" (tries: {})'.format(casedName, thisPkg.casedName, pkgs))
                    casedName = pkg.casedName
                    if luid is None:
                        if thisPkg.luid is None:
                            print("WARNING: converting casedName to"
                                  " LUID in install_program_in_place")
                            luid = toLUID(pkg.casedName)
            if len(thisPkg.suffix) > 0:
                suffix = thisPkg.suffix
            if thisPkg.luid is not None:
                if luid is None:
                    luid = pkg.luid
            if thisPkg.caption is not None:
                if caption is None:
                    caption = thisPkg.caption
            if thisPkg.luid is not None:
                if luid is None:
                    luid = thisPkg.luid
    if not retetected_version_used:
        print("* The known casedName is \"{}\"".format(casedName))
        print("* The known version is \"{}\"".format(version))
        print("* The known luid is \"{}\"".format(luid))
        '''
        suffix_msg = "The icon filename suffix was explicitly"
        if (suffix is None) or (len(suffix) < 1):
            suffix = getProgramValue(luid, "suffix")
            if suffix is None:
                suffix = ""
            else:
                suffix_msg = "The known icon suffix was"
        if (suffix is None) or (len(suffix) < 1):
            print("* There is no icon filename suffix ({})."
                  "".format(encode_py_val(suffix)))
            matches = []
            suffixes = []
            if os.path.isdir(applications):
                for sub in os.listdir(applications):
                    subPath = os.path.join(applications, sub)
                    if sub.startswith("."):
                        continue
                    if not os.path.isfile(subPath):
                        continue
                    if sub.startswith(luid+"-"):
                        matches.append(sub)
                        subName = os.path.splitext(sub)[0]
                        parts = subName.split("-")
                        suffixes.append("-"+parts[1])
                        # ^ [2] may be version
            if len(suffixes) > 0:
                print("WARNING: There are possible matches to {luid} in"
                      " {parent} so the suffix in {lm} for {luid} may"
                      " need to be set to one of the following:"
                      " {suffixes}".format(luid=luid,
                                           parent=applications,
                                           lm=localMachineMetaPath,
                                           suffixes=suffixes))
        else:
            print("* {} {}"
                  "".format(suffix_msg, encode_py_val(suffix)))
        '''
    sc_path = None
    sc_name = None

    old_sc_name = None
    old_sc_name_msg = " (legacy name before git 2021-02-25)"
    if luid == "blender":
        if multiVersion is None:
            multiVersion = True
            print("* enabling multiVersion since using Blender")
        if version is not None:
            sc_name = "blender{}-{}".format(suffix, version)
            if do_uninstall:
                old_sc_name = "org.blender-{}".format(version)
        else:
            if multiVersion is True:
                print("  but the version was not detected!")
            sc_name = "blender" + suffix
            if do_uninstall:
                old_sc_name = "org.blender"
        print("* using {} as shortcut name".format(sc_name))
    elif luid == "godot":
        old_sc_name_msg = (" (for linux-preinstall versions before"
                           " 2021-08-07)")
        if multiVersion is None:
            multiVersion = True
            print("* enabling multiVersion since using Godot")
        if version is not None:
            sc_name = "godot-{}".format(version.replace(" ", "-"))
            # ^ Change "3.3.2 stable mono" to "3.3.2-stable-mono"
            if do_uninstall:
                old_sc_name = "godot"
        else:
            if multiVersion is True:
                print("  but the version was not detected!")
            sc_name = "godot" + suffix
            print("  * using suffix \"{}\"".format(suffix))
            if do_uninstall:
                old_sc_name = "godot"
    elif version is not None:
        if multiVersion is True:
            sc_name = "{}{}-{}".format(luid, suffix, version)
        else:
            sc_name = "{}{}".format(luid, suffix)
    else:
        print("* no version is detected in {}".format(src_path))
        sc_name = "{}".format(luid)
    sc_name += ".desktop"
    sc_path = os.path.join(applications, sc_name)
    old_sc_path = None
    # installed_sc_path = getProgramValue(luid, 'install_shortcut')
    # ^ value was faulty in old versions (used dst_path)!
    if old_sc_name is not None:
        # INFO: Only old_sc_name is valid at this point. See changes
        #   to sc_path further down.
        old_sc_name += ".desktop"
        print("* WARNING:{} name"
              " was {} as shortcut name"
              "".format(old_sc_name_msg, old_sc_name))
        old_sc_path = os.path.join(applications, old_sc_name)
    if luid is None:
        luid = toLUID(casedName)
        echo0("Warning: luid was never set, so '{}' will be used."
              "".format(luid))

    try_icon = icons.get(luid)
    try_icon_url = iconLinks.get(luid)
    old_luid = None
    print("* checking for known icon related to '{}'..."
          "".format(luid))
    installed_luid = None
    if try_icon is not None:
        old_luid = luid
        luid = try_icon
        print("  * using known icon luid '{}'".format(luid))
        old_luid = luid
    if caption is None:
        old_luid = luid
        luid = try_icon
        print("  * using unknown icon luid '{}'".format(luid))
        caption = luid
        if version is not None:
            caption += " " + version
        caption = caption[:1].upper() + caption[1:].lower()
        print("* using '" + caption + "' as caption (from luid)")

    finalize_luid()  # Any `luid = ` after this must account for changes
    # ^ ...and getProgramValue or setProgramValue is not allowed to
    #   occur before this (raises exception).

    if do_uninstall:
        if old_luid is not None:
            if getProgramValue(old_luid, 'dst_path') is not None:
                installed_luid = old_luid
        # if getProgramValue(luid, 'dst_path') is not None:
        #     installed_luid = luid
        # ^ done further down
    # Only generate a different luid if a deprecated luid wasn't
    #   already used for an installed program!

    if do_uninstall:
        installed_sc_path = getProgramValue(luid, 'uninstall_shortcut')
        if installed_sc_path is None:
            installed_sc_path = getProgramValue(luid, 'sc_path')
        if installed_sc_path is not None:
            sc_path = installed_sc_path
            sc_name = os.path.split(sc_path)[1]
            # FIXME: sc_name is used as luid if multiversion!
            #   (See further down where sc_path is saved)
        if installed_luid is not None:
            if getProgramValue(luid, 'dst_path') is None:
                # ^ luid not installed_luid, since luid should only
                #   revert to an old entry if it wasn't also installed
                #   the new way (guaranteed to be most recent install)!
                luid = installed_luid
            else:
                echo0('Warning: There is an old entry for {installed_luid}'
                      ' in "{logPath}" but the new entry "{luid}" will be used.'
                      ' To avoid this warning, delete the entry for'
                      ' {installed_luid}.'
                      ''.format(installed_luid=installed_luid, logPath=logPath,
                                luid=luid))
    logLn("luid=\"{}\"".format(luid))
    setProgramValue(luid, 'luid', luid)

    if not os.path.isdir(meta_dir):
        raise RuntimeError("The shortcut-metadata directory wasn't"
                           " found: \"{}\"".format(meta_dir))
    try_included_icon = os.path.join(meta_dir, "{}.png".format(luid))
    if icon_path is None:
        if os.path.isfile(try_included_icon):
            icon_name = os.path.split(try_included_icon)[1]
            icon_path = os.path.join(PIXMAPS, icon_name)
            print('* copying "{}" to "{}"'
                  ''.format(try_included_icon, icon_path))
            shutil.copy(try_included_icon, icon_path)
        elif try_icon_url is not None:
            icon_name = try_icon_url.split('/')[-1]
            icon_partial_name = iconNames.get(luid)
            if icon_partial_name is not None:
                icon_ext = os.path.splitext(icon_name)[-1]
                icon_name = icon_partial_name + icon_ext
            icon_path = os.path.join(PIXMAPS, icon_name)
            if not do_uninstall:
                if not os.path.isdir(PIXMAPS):
                    os.makedirs(PIXMAPS)
                if os.path.isfile(icon_path):
                    if os.stat(icon_path).st_size == 0:
                        print("* removing bad 0-size icon \"{}\""
                              "".format(icon_path))
                        os.remove(icon_path)
                if not os.path.isfile(icon_path):
                    print("* downloading \"{}\" to \"{}\"..."
                          "".format(try_icon_url, icon_path))
                    with open(icon_path, 'wb') as f:
                        download(
                            f,
                            try_icon_url,
                            cb_progress=dl_progress,
                            cb_done=dl_done,
                            # evt={'total_size': },
                        )
                else:
                    print("* \"{}\" already exists (skipping download)"
                          "".format(icon_path))
    print("    (The version will be added later if multiVersion)")
    dst_path = src_path  # same if in_place
    if do_uninstall:
        prev_dst_path = dst_path
    try_dst_path = getProgramValue(luid, 'dst_path')
    try_dst_dirpath = getProgramValue(luid, 'dst_dirpath')
    dst_dirpath = None
    if (do_uninstall) and (try_dst_path is not None):
        dst_path = try_dst_path
        echo1()
        echo1()
        echo1('dst_path:"{}"'.format(dst_path))
        if dst_path != src_path:
            move_what = 'file'
            echo0("* dst_path '{}' != src_path '{}' and is set in {}"
                  " so move_what will be '{}'."
                  "".format(dst_path, src_path, localMachineMetaPath,
                            move_what))
        else:
            echo0("* try_dst_path '{}' == src_path '{}' and is set in"
                  " {} so move_what will remain as '{}'."
                  "".format(try_dst_path, src_path,
                            localMachineMetaPath, move_what))
    else:
        echo1()
        echo1()
        echo1("luid={} try_dst_path:{}".format(luid, try_dst_path))
    if try_dst_dirpath is not None:
        dst_dirpath = try_dst_dirpath
        if dst_dirpath != src_path:
            move_what = 'directory'
            print("* dst_dirpath '{}' != src_path '{}' and is set in {}"
                  " so move_what will be '{}'."
                  "".format(dst_dirpath, src_path,
                            localMachineMetaPath, move_what))
        else:
            print("* try_dst_path '{}' == src_path '{}' and is set in"
                  " {} so move_what will remain as '{}'."
                  "".format(try_dst_path, src_path,
                            localMachineMetaPath, move_what))

    # dst_programs = os.path.join(os.environ.get("HOME"), ".config")

    if move_what is None:
        if do_uninstall:
            if dst_path == src_path:
                if pull_back:
                    if os.path.isfile(dst_path) or os.path.isfile(src_path):
                        print("* dst_path '{}' or src_path '{}'"
                              " is a file so move_what will be file."
                              "".format(dst_path, src_path))
                        move_what = 'file'
                    elif os.path.isdir(dst_path) or os.path.isdir(src_path):
                        move_what = 'directory'
                    else:
                        raise ValueError(
                            "There is no src_path {} or dst_path {} so"
                            " move_what couldn't be determined."
                            "".format(encode_py_val(src_path),
                                      encode_py_val(dst_path))
                        )
    else:
        echo0("* using setting for move_what: {}"
              "".format(move_what))
    if dirname is not None:
        dst_dirpath = os.path.join(dst_programs, dirname)
        setProgramValue(luid, 'dst_dirpath', dst_dirpath)
    '''
    is_what = None
    if os.path.isfile(dst_path):
        is_what = 'file'
    elif os.path.isfile(src_path):
        is_what = 'file'
    elif os.path.isdir(dst_path):
        is_what = 'directory'
    elif os.path.isdir(dst_path):
        is_what = 'directory'
    if pull_back:
        if move_what not in ['file', 'directory']:
    '''

    if (dst_path is None) or (not do_uninstall):
        # If not do_uninstall, the generated (non-deprecated) value
        #   should be used regardless of what is in the registry.
        if do_uninstall:
            echo0("Warning: dst_path should be in the registry if"
                  " doing an uninstall, but it was not. The path"
                  " you specified will be used.")
        if move_what == 'file':
            dst_path = os.path.join(dst_programs, filename)
            setProgramValue(luid, 'dst_path', dst_path)
        elif move_what == 'directory':
            if dirname is None:
                raise RuntimeError("Failed to generate dirname")
            dst_path = os.path.join(dst_programs, dirname)
            setProgramValue(luid, 'dst_path', dst_path)
    # else it must be an in-place install.
    if pull_back:
        if dst_path == src_path:
            raise RuntimeError("dst_path and src_path"
                               " are the same, preventing"
                               " pull_back.")
    setProgramValue(luid, 'dst_path', dst_path)
    echo1("dst_path: {}".format(encode_py_val(dst_path)))

    # dst_dirpath and dirname should ONLY be not None if the folder
    # is being moved (and renamed to dirname):
    echo1("dst_dirpath: {}".format(encode_py_val(dst_dirpath)))
    echo1("dirname: {}".format(encode_py_val(dirname)))

    dst_bin_path = None
    if os.path.isfile(src_path) or os.path.isfile(dst_path):
        if move_what != 'directory':
            # Do NOT set it to programs, or it may be erased/overwritten
            # dst_dirpath = dst_programs
            # dirname = os.path.split(dst_dirpath)[1]
            # echo1("* detected dst_dirpath "
            #       "".format(encode_py_val(move_what)))
            dst_bin_path = dst_path
            pass
        else:
            print("WARNING: The path is a file but move_what is"
                  " 'directory' so the dst_dirpath {} may not be"
                  " correct.".format(encode_py_val(dst_dirpath)))

    echo1("move_what: {}".format(encode_py_val(move_what)))
    '''
    raise NotImplementedError(
        'move_what None should mean to not move the file (check this'
        ' then comment this). move_what="{}"'.format(move_what)
    )
    '''
    op_date = datetime.now()
    op_date_s = datetime.strftime(op_date, giteaSanitizedDtFmt)
    if do_uninstall:
        if multiVersion:
            addPackageValue(sc_name, 'uninstall_date', op_date_s, unique=True)
            echo0('* uninstalling versioned package "{}"'.format(sc_name))
        else:
            setProgramValue(luid, 'uninstall_date', op_date_s)
    else:
        if multiVersion:
            addPackageValue(sc_name, 'move_what', move_what, unique=True)
            addPackageValue(sc_name, 'install_date', op_date_s, unique=True)
            echo0('* installing versioned package "{}"'.format(sc_name))
        else:
            setProgramValue(luid, 'move_what', move_what)
            setProgramValue(luid, 'install_date', op_date_s)

    if move_what == 'file':
        setProgramValue(luid, 'is_dir', False)
        if not os.path.isdir(dst_programs):
            if not do_uninstall:
                os.makedirs(dst_programs)
            else:
                print("'{}' does not exist, so there is nothing to {}."
                      "".format(dst_programs, verb))
                return True
        # dst_path = os.path.join(dst_programs, filename)
        if src_path != dst_path:
            if not do_uninstall:
                print("mv \"{}\" \"{}\"".format(src_path, dst_path))
                if src_path != dst_path:
                    shutil.move(src_path, dst_path)
                    logLn("install_file:{}".format(dst_path))
                    setProgramValue(luid, 'installed', True)
                else:
                    print("The file is already at '{}'."
                          "".format(dst_path))
                    logLn("#install_file:{}".format(dst_path))
                    setProgramValue(luid, 'install_file', dst_path)
            else:
                if os.path.isfile(dst_path):
                    if not os.path.isfile(src_path) and pull_back:
                        print("mv \"{}\" \"{}\""
                              "".format(dst_path, src_path))
                        shutil.move(dst_path, src_path)
                        logLn("uninstall_file:{}".format(dst_path))
                        logLn("recovered_to:{}".format(src_path))
                        setProgramValue(luid, 'installed', False)
                        setProgramValue(luid, 'src_path', src_path)
                        if src_path == dst_path:
                            print("The source path"
                                  " \"{}\" was moved to \"{}\"."
                                  "".format(dst_path, src_path))
                    else:
                        if pull_back:
                            print("* the file is already recovered at"
                                  " {}".format(src_path))
                        print("rm \"{}\"".format(dst_path))
                        os.remove(dst_path)
                        logLn("uninstall_dir:{}\n".format(dst_path))
                        if src_path == dst_path:
                            print("The source path"
                                  " '{}' is removed.".format(dst_path))
                else:
                    print("'{}' does not exist, so there is nothing to"
                          " {}.".format(dst_path, verb))

    elif move_what == 'directory':
        setProgramValue(luid, 'is_dir', True)
        if do_uninstall:
            if os.path.isdir(dst_dirpath):
                if not os.path.isfile(src_path) and pull_back:
                    print("mv \"{}\" \"{}\"".format(dst_path, src_path))
                    shutil.move(dst_dirpath, src_path)
                    logLn("recovered_to:{}".format(src_path))
                    setProgramValue(luid, 'src_path', src_path)
                    setProgramValue(luid, 'dst_path', dst_path)
                    if src_path == dst_path:
                        print("The source path"
                              " \"{}\" was moved to \"{}\"."
                              "".format(dst_path, src_path))
                else:
                    shutil.rmtree(dst_dirpath)
            else:
                print("There is no '{}'.".format(dst_dirpath))
            logLn("uninstall_dir:{}".format(dst_dirpath))
            setProgramValue(luid, 'installed', False)
            if multiVersion:
                setPackageValue(sc_name, 'luid', luid)
                setPackageValue(sc_name, 'installed', False)
        else:
            print("mv '{}' '{}'".format(dirpath, dst_dirpath))
            if os.path.isdir(dst_dirpath):
                if enable_reinstall:
                    shutil.rmtree(dst_dirpath)
                else:
                    logLn("ERROR: '{}' already exists. Use the"
                          " reinstall command to ERASE the"
                          " entire directory!".format(dst_dirpath))
                    return False
            if os.path.isfile(src_path):
                bin_name = os.path.split(src_path)[-1]
                dst_bin_path = os.path.join(dst_path, bin_name)
                echo1("* set dst_bin_path to \"{}\" since src_path"
                      " was a file."
                      "".format(dst_bin_path))

            shutil.move(dirpath, dst_dirpath)
            logLn("install_move_dir:{}".format(dst_dirpath))
    else:
        if os.path.isdir(src_path):
            setProgramValue(luid, 'is_dir', True)
        elif os.path.isfile(src_path):
            setProgramValue(luid, 'is_dir', False)
        else:
            echo0("* is_dir wasn't set since \"{}\" doesn't exist."
                  "".format(src_path))
        echo1("* move_what: {}".format(encode_py_val(move_what)))
    # Still set generic values for the program even if multiVersion,
    # so that the last install is recorded:
    setProgramValue(luid, 'src_path', src_path)

    if multiVersion:
        '''
        if thisPkg is not None:
            gotMeta = thisPkg.toDict()
            for k,v in gotMeta.items():
                setPackageValue(sc_name, k, v)
        else:
            echo0("WARNING: thisPkg is None after move_what, so the"
                  " derived metadata won't be recorded.")
        '''
        # ^ thisPkg referenced before assignment
        setPackageValue(sc_name, 'luid', luid)
        setPackageValue(sc_name, 'dst_dirpath', dst_dirpath)
    else:
        setProgramValue(luid, 'dst_dirpath', dst_dirpath)

    if not do_uninstall:
        sys.stderr.write("* marking \"{}\" as executable..."
                         "".format(dst_path))
        sys.stderr.flush()
        os.chmod(dst_path, stat.S_IRWXU | stat.S_IXGRP | stat.S_IRGRP
                 | stat.S_IROTH | stat.S_IXOTH)
        sys.stderr.write("OK\n")
        sys.stderr.flush()
        # stat.S_IRWXU : Read, write, and execute by owner
        # stat.S_IEXEC : Execute by owner
        # stat.S_IXGRP : Execute by group
        # stat.S_IXOTH : Execute by others
        # stat.S_IREAD : Read by owner
        # stat.S_IRGRP : Read by group
        # stat.S_IROTH : Read by others
        # stat.S_IWOTH : Write by others
        # stat.S_IXOTH : Execute by others

    if icon_path is None:
        icon_path = luid
    if "Godot" in caption:
        caption = caption.replace(" stable", "")
        # ^ otherwise both "stable mono" and "stable" icons will always
        #   look the same in gnome as it forever mercilessly and
        #   incompetently botches the name as something like
        #   "Godot 3.3.2 sta..." for both.
    setProgramValue(luid, 'caption', caption)
    setProgramValue(luid, 'sc_path', sc_path)
    if multiVersion:
        setPackageValue(sc_name, 'luid', luid)
        setPackageValue(sc_name, 'caption', caption)
        setPackageValue(sc_name, 'sc_path', sc_path)
    else:
        if version is not None:
            setProgramValue(luid, 'version', version)
    '''
    dst_bin_path = dst_path
    if src_path is not None:
        if not os.path.isfile(dst_bin_path):
            bin_name = os.path.split(src_path)[-1]
            dst_bin_path = os.path.join(dst_path, bin_name)
    '''
    tryBinDir = None
    packageIcon = None
    packageShortcut = None
    if not do_uninstall:
        tryBinDir = os.path.dirname(dst_bin_path)
        if os.path.split(tryBinDir)[1] == 'bin':
            # Try examining the local directory (such as a venv) for
            # matching metadata.
            tryVenv = os.path.dirname(tryBinDir)
            tryIconsDir = os.path.join(tryVenv, "share", "icons")
            tryIcons = os.listdir(tryIconsDir)
            if len(tryIcons) == 1:
                packageIcon = os.path.join(tryIconsDir, tryIcons[0])
                echo0('* detected packageIcon "{}"'
                      ''.format(packageIcon))
            else:
                echo0('* There was more than one image in "{}"'
                      ' so the icon name is unknown: {}'
                      ''.format(tryIconsDir, tryIcons))
            tryShortcutsDir = os.path.join(tryVenv, "share", "applications")
            tryShortcuts = os.listdir(tryShortcutsDir)
            if len(tryShortcuts) == 1:
                packageShortcut = os.path.join(tryShortcutsDir,
                                               tryShortcuts[0])
                echo0('* detected packageShortcut "{}"'
                      ''.format(packageShortcut))
            else:
                echo0('* There was more than one file in "{}"'
                      ' so the icon name is unknown: {}'
                      ''.format(tryShortcutsDir, tryShortcuts))
        else:
            echo0('* checking for a virtualenv...'
                  'no (since "{}" is not named bin).'
                  ''.format(tryBinDir))
    if packageIcon is not None:
        icon_path = packageIcon
    if packageShortcut is not None:
        shortcut_data = format_shortcut(
            None,
            dict(
                Exec=dst_bin_path,
                TryExec=dst_bin_path,
                Name=caption,
                Icon=icon_path,
            ),
            path=packageShortcut,
        )
    else:
        shortcut_data = shortcut_data_template.format(
            Exec=dst_bin_path,
            Name=caption,
            Icon=icon_path,
        )
    # ^ IF CHANGES, also update `print("  Exec=` etc. below
    #   so that the log matches.
    for knownLuid, knownFields in shortcutMetas.items():
        if knownLuid == luid:
            for knownName, knownValue in knownFields.items():
                scLine = "{}={}".format(knownName, knownValue)
                shortcut_data += "{}\n".format(scLine)
                print("* using known {} {}".format(luid, scLine))

    meta_path = os.path.join(meta_dir, "{}.txt".format(luid))

    shortcut_append_lines = None
    if os.path.isfile(meta_path):
        with open(meta_path) as f:
            print("* using shortcut metadata from '{}'"
                  "".format(meta_path))
            lines = f.readlines()  # includes newlines!
            shortcut_append_lines = []
            for line_original in lines:
                line = line_original.rstrip()
                shortcut_append_lines.append(line)

    if shortcut_append_lines is not None:
        shortcut_data += "\n".join(shortcut_append_lines)
    if shortcut_data[-1] != "\n":
        shortcut_data += "\n"
    if not do_uninstall:
        # shutil.rmtree(dirpath)
        if ex_tmp is not None:
            if os.path.isdir(ex_tmp):
                shutil.rmtree(ex_tmp)
        if new_tmp is not None:
            if os.path.isdir(new_tmp):
                shutil.rmtree(new_tmp)
    desktop_installer = "xdg-desktop-menu"
    u_cmd_parts = [desktop_installer, "uninstall", sc_path]
    # PATH_ELEMENT_I = -1  # The place in u_cmd_parts that is the path
    if old_sc_path is not None:
        if os.path.isfile(old_sc_path):
            u_cmd_parts = [desktop_installer, "uninstall", old_sc_path]
            if os.path.isfile(sc_path):
                logLn("WARNING: You'll have to run uninstall again"
                      " because both shortcut path \"{}\" and legacy"
                      " shortcut path \"{}\" are present."
                      "".format(sc_path, old_sc_path))
            sc_path = old_sc_path
            # ^ Ensure the checks below use the found path.

    if do_uninstall:
        logLn("sc_path:{}".format(sc_path))
        # FIXME: At this point, cura is not known to be an appimage
        #   if local_machine.json contains the wrong filename
        #   (such as a version that isn't installed).
        #   However, this may be due to the registry having the
        #   incorrect value:
        #   "sc_path":
        #     "/home/owner/.local/share/applications/cura.desktop",
        try_sc_path = getProgramValue(luid, "uninstall_shortcut")
        if try_sc_path is not None:
            if os.path.isfile(try_sc_path):
                if sc_path != try_sc_path:
                    echo0("WARNING: sc_path {} will be corrected to"
                          " existing uninstall_shortcut {}."
                          "".format(encode_py_val(sc_path),
                                    encode_py_val(try_sc_path)))
                    sc_path = try_sc_path
                    setProgramValue(luid, "sc_path", sc_path)
            else:
                echo0("WARNING: uninstall_shortcut {} does not exist."
                      " The sc_path {} will be used instead."
                      "".format(encode_py_val(try_sc_path),
                                encode_py_val(sc_path)))
        install_shortcut = getProgramValue(luid, 'uninstall_shortcut')
        # ^ deprecated, see sc_path below.
        # if install_shortcut is None:
        #     install_shortcut = getProgramValue(luid, 'install_shortcut')
        #     ^ faulty in versions that used it (was set to dst_path)!
        if install_shortcut is None:
            install_shortcut = getProgramValue(luid, 'sc_path')
        if (not os.path.isfile(sc_path)) and (install_shortcut is not None):
            if os.path.isfile(install_shortcut):
                sc_path = install_shortcut
        logLn("uninstall_shortcut:{}".format(sc_path))
        if os.path.isfile(sc_path):
            print(u_cmd_parts)
            install_proc = subprocess.run(u_cmd_parts)
            xdg_msg = "succeeded"
            if install_proc.returncode != 0:
                xdg_msg = "failed"
            if os.path.isfile(sc_path):
                print("rm {}".format(sh_literal(sc_path)))
                os.remove(sc_path)
            else:
                print("{} {} ({} is no longer present so no"
                      " steps seem to be necessary)."
                      "".format(" ".join(u_cmd_parts), xdg_msg,
                                encode_py_val(sc_path)))
        else:
            print("* The shortcut was not present: {}"
                  "".format(encode_py_val(sc_path)))
        return True
    else:
        tmp_sc_dir_path = tempfile.mkdtemp()
        tmp_sc_path = os.path.join(tmp_sc_dir_path, sc_name)
        ok = False
        with open(tmp_sc_path, 'w') as outs:
            outs.write(shortcut_data)
            ok = True
        if ok:
            # NOTE: There is no vendor prefix but xdg specifies that
            # there should be. The --novendor flag forces the install.
            if os.path.isfile(sc_path):
                # Remove the old one, otherwise xdg-desktop-menu install
                # will not refresh the icon from storage.
                # print("* removing shortcut \"{}\"".format(sc_path))
                # os.remove(sc_path)
                print("* uninstalling shortcut \"{}\"".format(sc_path))
                subprocess.run(u_cmd_parts)
                # ^ using only the name also works: sc_name])
                # ^ uninstall ensures that the name updates if existed
            install_proc = subprocess.run([desktop_installer,
                                           "install", "--novendor",
                                           tmp_sc_path])
            inst_msg = "OK"
            # print("sp_run's returned process {} has {}"
            #       "".format(install_proc, dir(install_proc)))
            if install_proc.returncode != 0:
                inst_msg = "FAILED"
            if os.path.isfile(sc_path):
                setProgramValue(luid, 'sc_path', sc_path)
                if getProgramValue(luid, 'uninstall_shortcut') is not None:
                    # fix the deprecated value.
                    deleteProgramValue(luid, 'uninstall_shortcut', sc_path)
                if getProgramValue(luid, 'install_shortcut') is not None:
                    # fix the deprecated (which was also faulty) value.
                    deleteProgramValue(luid, 'install_shortcut', sc_path)
                os.chmod(sc_path,
                         (stat.S_IROTH | stat.S_IREAD | stat.S_IRGRP
                          | stat.S_IWUSR))
                print("* installing '{}'...{}".format(sc_path,
                                                      inst_msg))
                sys.stderr.write("* marking \"{}\" as executable..."
                                 "".format(dst_path))
                os.chmod(dst_path, stat.S_IRWXU | stat.S_IXGRP
                         | stat.S_IRGRP
                         | stat.S_IROTH | stat.S_IXOTH)
                sys.stderr.write("OK\n")
            else:
                print("* installing '{}'...{}".format(sc_name, inst_msg))
            print("  Name={}".format(caption))
            print("  Exec={}".format(dst_bin_path))
            logLn("dst_path:{}".format(dst_path))
            # logLn("install_shortcut:{}".format(sc_path))
            logLn("sc_path:{}".format(sc_path))
            print("  Icon={}".format(icon_path))
            # print("")
            # print("You may need to reload the application menu, such"
            # #     " as via one of the following commands:")
            # print("  ")
            # or xdg-desktop-menu install mycompany-myapp.desktop
        else:
            logLn("install_shortcut_failed:{}".format(dst_path))
        return ok
    return False


def main():
    print("")
    caption = None
    src_path = None
    global verbosity
    if len(sys.argv) < 2:
        usage()
        echo0("")
        echo0("Error: You must specify a command.")
        echo0("")
        echo0("")
        return 1
    do_uninstall = False
    enable_reinstall = False
    move_what = None
    multiVersion = None
    valueParams = {}
    valueParamsKey = None
    command = None
    COMMANDS = ['install', 'reinstall', 'remove']
    for i in range(1, len(sys.argv)):
        arg = sys.argv[i]
        if (i == 1) and (arg in COMMANDS):
            command = arg
        elif arg[:2] == "--":
            if arg == "--move":
                move_what = 'any'
            elif arg == "--version":
                valueParamsKey = "version"
            elif arg == "--multi-version":
                multiVersion = True
            elif arg == "--help":
                usage()
                return 0
            elif arg == "--verbose":
                verbosity = 1
            elif arg == "--debug":
                verbosity = 2
            else:
                print("ERROR: '{}' is not a valid option.".format(arg))
                return 1
        elif valueParamsKey is not None:
            valueParams[valueParamsKey] = arg
            valueParamsKey = None
        else:
            if src_path is None:
                src_path = arg
            elif caption is None:
                caption = arg
            else:
                print("A 3rd parameter is unexpected: '{}'".format(arg))
                return 1
    if command is None:
        usage()
        echo0("")
        echo0("Error: You must specify a command: {}".format(COMMANDS))
        echo0("")
    if command == "remove":
        do_uninstall = True
    elif command == "reinstall":
        enable_reinstall = True
    if src_path is None:
        echo0("")
        echo0("Error: You must specify a source path.")
        return 1
    src_path = os.path.abspath(src_path)
    if move_what == 'any':
        if os.path.isdir(src_path):
            move_what = 'directory'
        elif os.path.isfile(src_path):
            print("* [main] src_path is a file so move_what"
                  " will be file.")
            move_what = 'file'
        else:
            print("{} is not a file nor a directory.".format(src_path))
            return 1

    parts = src_path.split('.')
    if parts[-1] == "AppImage":
        move_what = 'file'
    version = valueParams.get('version')
    try:
        install_program_in_place(
            src_path,
            caption=caption,
            move_what=move_what,
            do_uninstall=do_uninstall,
            enable_reinstall=enable_reinstall,
            multiVersion=multiVersion,
            version=version,
        )
    except ValueError as ex:
        if bad_id_flag in str(ex):
            print("Error: " + str(ex))
            return 1
        else:
            raise ex
    return 0


if __name__ == "__main__":
    sys.exit(main())
