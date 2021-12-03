import setuptools

# - For another example, see
#   https://github.com/poikilos/pypicolcd/blob/master/setup.py
# - For nose, see https://github.com/poikilos/mgep/blob/master/setup.py

long_description = ""
with open("readme.md", "r") as fh:
    long_description = fh.read()
setuptools.setup(
    name='nopackage',
    version='0.9.0',
    description=("Automate the installation of any source with zero"
                 " configuration. The source can be a zip or gz binary"
                 " package, appimage, directory, or executable file."),
    long_description=long_description,
    long_description_content_type="text/markdown",
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Programming Language :: Python :: 3',
        ('License :: OSI Approved ::'
         ' GNU General Public License v3 or later (GPLv3+)'),
        'Operating System :: POSIX :: Linux',
        'Topic :: System :: Installation/Setup',
    ],
    keywords='python install installer deb debian AppImage shortcut',
    url="https://github.com/poikilos/nopackage",
    author="Jake Gustafson",
    author_email='7557867+poikilos@users.noreply.github.com',
    license='GPLv3+',
    # packages=setuptools.find_packages(),
    packages=['nopackage'],
    include_package_data=True,  # look for MANIFEST.in
    # scripts=['example'] ,
    # See <https://stackoverflow.com/questions/27784271/
    # how-can-i-use-setuptools-to-generate-a-console-scripts-entry-
    # point-which-calls>
    entry_points={
        'console_scripts': ['nopackage=nopackage:main'],
    },
    install_requires=[
        'urllib'
    ]
 )
