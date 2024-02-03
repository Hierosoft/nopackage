#!/usr/bin/env python3
import sys
import os

import unittest
from unittest import TestCase

if __name__ == "__main__":
    TESTS_DIR = os.path.dirname(os.path.realpath(__file__))
    MODULE_DIR = os.path.dirname(TESTS_DIR)
    REPO_DIR = os.path.dirname(MODULE_DIR)
    sys.path.insert(0, REPO_DIR)  # Find module when running test manually.

from nopackage import (
    PackageInfo,
    find_all_any_ci,
    tests,
    echo0,
)

if sys.version_info.major < 3:
    FileNotFoundError = IOError

myPath = os.path.realpath(__file__)
testsDir = os.path.dirname(myPath)
testDataPath = os.path.join(testsDir, "data")
if not os.path.isdir(testDataPath):
    raise IOError("The test folder is missing: \"{}\""
                  "".format(testDataPath))


def toPythonLiteral(v):
    '''
    [copied from pycodetools.parsing by author]
    '''
    if v is None:
        return None
    elif v is False:
        return "False"
    elif v is True:
        return "True"
    elif ((type(v) == int) or (type(v) == float)):
        return str(v)
    elif (type(v) == tuple) or (type(v) == list):
        enclosures = '()'
        if type(v) == list:
            enclosures = '[]'
        s = enclosures[0]
        for val in v:
            s += toPythonLiteral(val) + ", "
            # ^ Ending with an extra comma has no effect on length.
        s += enclosures[1]
        return s
    return "'{}'".format(
        v.replace("'", "\\'").replace("\r", "\\r").replace("\n", "\\n")
    )


"""
def assertEqual(v1, v2, tbs=None):
    '''
    [copied from pycodetools.parsing by author]
    Show the values if they differ before the assertion error stops the
    program.

    Keyword arguments:
    tbs -- traceback string (either caller or some sort of message to
           show to describe what data produced the arguments if they're
           derived from something else)
    '''
    if ((v1 is True) or (v2 is True) or (v1 is False) or (v2 is False)
            or (v1 is None) or (v2 is None)):
        if v1 is not v2:
            echo0("")
            echo0("{} is not {}".format(toPythonLiteral(v1),
                                        toPythonLiteral(v2)))
            if tbs is not None:
                echo0("for {}".format(tbs))
        assert(v1 is v2)
    else:
        if v1 != v2:
            echo0("")
            echo0("{} != {}".format(toPythonLiteral(v1),
                                    toPythonLiteral(v2)))
            if tbs is not None:
                echo0("for {}".format(tbs))
        assert(v1 == v2)
"""

"""
def assertAllEqual(list1, list2, tbs=None):
    '''
    [copied from pycodetools.parsing by author]
    '''
    if len(list1) != len(list2):
        echo0("The lists are not the same length: list1={}"
              " and list2={}".format(list1, list2))
        assertEqual(len(list1), len(list2))
    for i in range(len(list1)):
        assertEqual(list1[i], list2[i], tbs=tbs)
"""

PackageInfo.verbosity = 2


class TestNopackage(TestCase):
    def test_1_self(self):
        echo0()
        echo0()
        echo0()
        echo0("BEGIN nopackage self tests")
        tests()
        echo0("END nopackage self tests")
        echo0()
        echo0()
        echo0()

    def assertAllEqual(self, list1, list2, tbs=None):
        '''
        [copied from pycodetools.parsing by author]
        '''
        if len(list1) != len(list2):
            echo0("The lists are not the same length: list1={}"
                  " and list2={}".format(list1, list2))
            self.assertEqual(len(list1), len(list2))
        for i in range(len(list1)):
            try:
                self.assertEqual(list1[i], list2[i])
            except AssertionError as ex:
                if tbs is not None:
                    echo0(tbs)
                raise ex

    def test_2_name_parsing(self):

        fn = "blender-2.79b-linux-glibc219-x86_64"
        chunks = ['linux', 'X86_64']
        # ^ intentionally different case for CI test
        results = find_all_any_ci(
            fn,
            chunks,
        )
        self.assertAllEqual(results, [(14, 'linux'), (29, 'X86_64')],
                            tbs="{} in {}".format(chunks, fn))
        echo0("* find_all_any_ci test...OK ({} at {} in {})"
              "".format(chunks, results, fn))

        pkg = PackageInfo("flashprint_4.6.2_amd64.deb", is_dir=False)
        self.assertEqual(pkg.luid, "flashprint")
        self.assertEqual(pkg.luid+pkg.suffix, "flashprint-deb")
        self.assertEqual(pkg.casedName, "FlashPrint")
        self.assertEqual(pkg.caption, "FlashPrint 4.6.2 (deb)")

        pkg = PackageInfo("FlashPrint-4.5.1.deb", is_dir=False)
        self.assertEqual(pkg.luid, "flashprint")
        self.assertEqual(pkg.luid+pkg.suffix, "flashprint-deb")
        self.assertEqual(pkg.casedName, "FlashPrint")
        self.assertEqual(pkg.caption, "FlashPrint 4.5.1 (deb)")

        tests_dir = os.path.dirname(os.path.realpath(__file__))
        if not os.path.isdir(tests_dir):
            raise FileNotFoundError("{} is missing.".format(tests_dir))
        test1_dir = os.path.join(tests_dir, "someprogram-1.0")
        src_path = test1_dir
        pkg = PackageInfo(src_path)
        self.assertEqual(pkg.luid, "someprogram")
        self.assertEqual(pkg.version, "1.0")

        src_path = "blender-2.79b-linux-glibc219-x86_64"
        pkg = PackageInfo(src_path, is_dir=True)
        self.assertEqual(pkg.luid, "blender")
        self.assertEqual(pkg.caption, "Blender 2.79b")
        self.assertEqual(pkg.arch, "64bit")

        src_path = os.path.join(tests_dir, "some_program-1.0.0.dummy")
        pkg = PackageInfo(src_path)
        self.assertEqual(pkg.caption, "Some Program 1.0.0")
        self.assertEqual(pkg.casedName, "Some Program")

        src_path = "blender-2.79b-linux-glibc219-x86"
        pkg = PackageInfo(src_path, is_dir=True)
        self.assertEqual(pkg.caption, "Blender 2.79b")
        self.assertEqual(pkg.arch, "32bit")

        src_path = \
            "FreeCAD_0.18-16131-Linux-Conda_Py3Qt5_glibc2.12-x86_64.AppImage"
        pkg = PackageInfo(src_path, is_dir=False)
        self.assertEqual(pkg.caption, "FreeCAD 0.18-16131 (AppImage)")
        self.assertEqual(pkg.arch, "64bit")
        self.assertEqual(pkg.platform, "Linux")

        src_path = "Mirage-v0.6.4-x86_64.AppImage"
        pkg = PackageInfo(src_path, is_dir=False)
        self.assertEqual(pkg.caption, "Mirage 0.6.4 (AppImage)")
        self.assertEqual(pkg.arch, "64bit")

        src_path = "Slic3r-1.3.1-dev-2ef957d-x86_64.AppImage"
        pkg = PackageInfo(src_path, is_dir=False)
        # self.assertEqual(pkg.caption, "Slic3r 1.3.1-dev-2ef957d (AppImage)")
        self.assertEqual(pkg.caption, "Slic3r 1.3.1 dev-2ef957d (AppImage)")
        # ^ This is a better format so filenames like
        #   "*-1.0-stable" become "* 1.0 stable"
        self.assertEqual(pkg.arch, "64bit")

        src_path = "Slic3r-master-latest.AppImage"
        pkg = PackageInfo(src_path, is_dir=False)
        self.assertEqual(pkg.caption, "Slic3r master (AppImage)")
        self.assertEqual(pkg.version, "master")

        src_path = "Ultimaker_Cura-4.8.0.AppImage"
        pkg = PackageInfo(src_path, is_dir=False)
        self.assertEqual(pkg.caption, "Ultimaker Cura 4.8.0 (AppImage)")
        self.assertEqual(pkg.luid, "ultimaker.cura")

        src_path = "4.9_20210511_Ultimaker_Cura-4.9.1.AppImage"
        pkg = PackageInfo(src_path, is_dir=False)
        self.assertEqual(pkg.caption, "Ultimaker Cura 4.9.1 (AppImage)")
        self.assertEqual(pkg.luid, "ultimaker.cura")

        found = False
        try:
            src_path = "4.9_20210511-4.9.1.AppImage"
            pkg = PackageInfo(src_path, is_dir=False)
        except ValueError as ex:
            if "no alphabetic" in str(ex):
                found = True
                echo0("- Parsing names with no alphabetic characters"
                      " shouldn't be possible,"
                      " so the test result is good.")
            else:
                raise ex
        if not found:
            raise RuntimeError("The program should have detected a filename"
                               " (not including extension) with no alphabetic"
                               " characters as bad (See code near `startChar`"
                               " in nopackage).")

        src_path = "blender-2.49b-linux-glibc236-py26-x86_64.tar.bz2"
        pkg = PackageInfo(src_path, is_dir=False)
        self.assertEqual(pkg.caption, "Blender 2.49b")
        self.assertEqual(pkg.arch, "64bit")

        src_path = "PrusaSlicer-2.3.0+linux-x64-202101111322.AppImage"
        pkg = PackageInfo(src_path, is_dir=False)
        self.assertEqual(pkg.platform, "Linux")
        self.assertEqual(pkg.luid, "prusaslicer")
        self.assertEqual(pkg.caption, "PrusaSlicer 2.3.0 (AppImage)")
        self.assertEqual(pkg.version, "2.3.0")
        self.assertEqual(pkg.arch, "64bit")

        PackageInfo.verbosity = 2
        src_path = "mfcl2740dwlpr-3.2.0-1.i386.rpm"
        pkg = PackageInfo(src_path, is_dir=False)
        self.assertEqual(pkg.casedName, "Mfcl2740Dwlpr")
        self.assertEqual(pkg.luid, "mfcl2740dwlpr")
        # self.assertEqual(pkg.caption, "Mfcl2740Dwlpr 3.2.0-1.i386")
        self.assertEqual(pkg.caption, "Mfcl2740Dwlpr 3.2.0-1")
        self.assertEqual(pkg.arch, "32bit")
        # ^ i386 becomes "32bit" (see PackageInfo.X32S)

        src_path = "Meshroom-2019.2.0-linux.tar.gz"
        pkg = PackageInfo(src_path, is_dir=False)
        self.assertEqual(pkg.casedName, "Meshroom")
        self.assertEqual(pkg.platform, "Linux")
        self.assertEqual(pkg.luid, "meshroom")
        self.assertEqual(pkg.caption, "Meshroom 2019.2.0")

        src_path = "brscan-skey-0.2.4-1.x86_64.rpm"
        pkg = PackageInfo(src_path, is_dir=False)
        self.assertEqual(pkg.casedName, "Brscan Skey")
        self.assertEqual(pkg.luid, "brscan.skey")
        self.assertEqual(pkg.caption, "Brscan Skey 0.2.4-1")
        self.assertEqual(pkg.arch, "64bit")
        # ^ x86_64 becomes "64bit" (see PackageInfo.X64S)

        src_path = "tsetup.1.8.2.tar.xz"
        pkg = PackageInfo(src_path, is_dir=False)
        self.assertEqual(pkg.casedName, "Tsetup")
        self.assertEqual(pkg.luid, "tsetup")
        self.assertEqual(pkg.caption, "Tsetup 1.8.2")
        self.assertEqual(pkg.version, "1.8.2")

        src_path = "DAIN_APP Alpha 0.41.rar"
        pkg = PackageInfo(src_path, is_dir=False)
        self.assertEqual(pkg.casedName, "DAIN APP")
        self.assertEqual(pkg.luid, "dain.app")
        self.assertEqual(pkg.caption, "DAIN APP Alpha 0.41")
        self.assertEqual(pkg.version, "Alpha 0.41")

        src_path = "duplicati-2.0.4.5-2.0.4.5_beta_20181128.noarch.rpm"
        pkg = PackageInfo(src_path, is_dir=False)
        self.assertEqual(pkg.casedName, "Duplicati")
        self.assertEqual(pkg.luid, "duplicati")
        # self.assertEqual(pkg.caption, "Duplicati 2.0.4.5-2.0.4.5")
        # self.assertEqual(pkg.caption, "Duplicati 2.0.4.5-2.0.4.5 beta")
        # ^ TODO: add BETA
        # self.assertEqual(pkg.caption, "Duplicati 2.0.4.5-2.0.4.5_beta_20181128.noarch")
        # self.assertEqual(pkg.caption, "Duplicati 2.0.4.5-2.0.4.5_beta_20181128")
        self.assertEqual(pkg.caption, "Duplicati 2.0.4.5-2.0.4.5 beta_20181128")
        # ^ This is a better format (See the earlier comment containing
        #   "This is a better format").
        self.assertEqual(pkg.arch, "noarch")
        echo0("{}:\n  {}".format(src_path, pkg))

        src_path = "monero-gui-linux-x64-v0.17.1.9.tar.bz2"
        pkg = PackageInfo(src_path, is_dir=False)
        self.assertEqual(pkg.casedName, "Monero Gui")
        self.assertEqual(pkg.platform, "Linux")
        self.assertEqual(pkg.luid, "monero.gui")
        self.assertEqual(pkg.caption, "Monero Gui 0.17.1.9")
        self.assertEqual(pkg.version, "0.17.1.9")
        self.assertEqual(pkg.arch, "64bit")

        # src_path = "org.gimp.GIMP.flatpakref"
        # ^ not relevant, but the resulting casedName is "Org".

        fileNames = [
        ]

        dirNames = [
        ]

        src_path = "bash2py-3.6"
        pkg = PackageInfo(src_path, is_dir=True)
        self.assertEqual(pkg.casedName, "Bash2Py")
        self.assertEqual(pkg.luid, "bash2py")
        self.assertEqual(pkg.caption, "Bash2Py 3.6")
        self.assertEqual(pkg.version, "3.6")

        for fname in fileNames:
            echo0("")
            pkg = PackageInfo(fname, is_dir=False)
            echo0("{}:\n  {}".format(fname, pkg))

        for fname in dirNames:
            echo0("")
            pkg = PackageInfo(fname, is_dir=True)
            echo0("{}:\n  {}".format(fname, pkg))

    def test_bin_in_folder(self):
        src_path = os.path.join(testDataPath, "blender-3.0.1-linux-x64")
        file_path = os.path.join(src_path, "blender")
        echo0("* testing non-versioned filename in versioned directory"
              " \"{}\"".format(src_path))
        pkg = PackageInfo(src_path)
        self.assertEqual(pkg.casedName, "Blender")
        self.assertEqual(pkg.caption, "Blender 3.0.1")
        self.assertEqual(pkg.version, "3.0.1")
        self.assertEqual(pkg.luid, "blender")


if __name__ == "__main__":
    sys.exit(unittest.main())
    # echo0("")
    # echo0("All tests passed.")
    # echo0("")
