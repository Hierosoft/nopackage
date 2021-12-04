# Migrated from linux-preinstall
The functionality of nopackage was formerly in `linux-preinstall/utilities/install_any.py`.

The process of migrating the git history is described below as a script, but migration was already done for nopackage, and only ever needs to be done once.

This script was formerly called prun-nopackage but the file was renamed and put into Markdown format as this md file.

```bash
# See [blang's Answer](https://stackoverflow.com/a/10524661) May 9, 2012 at 21:57, edited 22:45 on <https://stackoverflow.com/questions/10524578/how-to-move-a-file-from-one-git-repository-to-another-while-preserving-history>

git clone https://github.com/poikilos/linux-preinstall  ~/tmp/linux-preinstall--move_install_any
# mkdir ~/tmp/linux-preinstall--move_install_any
cd ~/tmp/linux-preinstall--move_install_any
if [ $? -ne 0 ]; then
    echo "cd ~/tmp/linux-preinstall--move_install_any failed."
    exit 1
fi
# git filter-branch --subdirectory-filter FooBar HEAD
git filter-branch --prune-empty --subdirectory-filter utilities -- --all
# git filter-branch -f --prune-empty --index-filter "git rm --cached --ignore-unmatch $(git ls-files | grep -v 'install_any.py')"
# ^ fails if any existing file, regardless of filtering, has a space (There was no benefit in adding a backslash before .py)
git filter-branch -f --prune-empty --index-filter "git rm --cached --ignore-unmatch \"`git ls-files | grep -v 'install_any.py'`\""
git reset --hard
git remote rm origin
rm -r .git/refs/original/
git reflog expire --expire=now --all
git gc --aggressive
git prune

# But the whole utilities directory is still there, so see [Petro Franko's answer](https://stackoverflow.com/a/52643437) Oct 4, 2018 on <https://stackoverflow.com/questions/43762338/how-to-remove-file-from-git-history>:

cat << END
Keeping:
install_any.py
dist/share/applications/clean-lbry.desktop
dist/share/applications/tame-lbry.desktop
dist/share/applications/install_any.desktop
HOME/.config/geany/geany.conf
^ required by install_geany_plugin
dist/share/applications/install_any.desktop
install_ia-nonroot.sh
shortcut-metadata/blender.txt
clean-lbry.py (removed by accident but re-added in a later commit)
tame-lbry.py (removed by accident but re-added in a later commit)
^ required by "Clean LBRY" icon installed by nopackage

Removed: Only in linux-preinstall but nopackage should eventually get the functionality:
install-geany-plugin.sh
blender-install-git-addon.sh
jar-run.sh
# ^ installed by linux-preinstall: everyone/jar-file-handler.sh:./install_any.py jar-run.sh "Jar Run"
keepassxc-2.5.2-already-open-workaround.sh
owncloud-maintenance-mode-off.sh
pulseaudio-restart.sh
refresh-any-panel.nonroot.sh
clean-lbry.py (See also utilities/dist/share/applications/clean-lbry.desktop)
tame-lbry.py (See also utilities/dist/share/applications/tame-lbry.desktop)
whichicon
utilities/3DPrinting/filacalc.py
^ (Add metadata to install it, but first move it to its own repo)

Everything else not in lists above is also removed.
END



export FILTER_BRANCH_SQUELCH_WARNING=1

for path in \
3DPrinting/filacalc.py \
add-nonet-user.sh \
arch \
antergos/refresh-keys.sh \
audiosinkprobe/349312__newagesoup__pink-noise-10s.wav \
audiosinkprobe/audiosinkprobe.py \
audiosinkprobe/audiosinkprobe.sh \
audiosinkprobe/credits.txt \
audiosinkprobe/HDMI-audio.md \
audiosinkprobe/subroutine.sh \
blender-install-git-addon.sh \
booklet_page_list.py \
change_extensions.py \
clean-lbry.py \
clock.sh \
convert-all-to-jpg.sh \
convert-seq-to-gif-invert.sh \
cron-example/cron-echotest \
cron-example/preload-cron-echotest.sh \
diffmin.py \
dudirs.py \
fix-bad-kde-screen-settings.sh \
git.rc \
jar-run.sh \
jpg-this-dir.sh \
keepassxc-2.5.2-already-open-workaround.sh \
keyboard-layouts \
long-to-short.sh \
lxqt-reset.sh \
meldq \
nonworking \
ntfs-mount-hibernated.sh \
oracle_date_convert.py \
owncloud-maintenance-mode-off.sh \
pulseaudio-restart.sh \
purgeabrt.sh \
pysecuritycam.py \
rebootif \
refresh-any-panel.nonroot.sh \
refresh-any-panel.sh \
scanremote.sh \
show-biggest.sh \
soundcard-set-default.sh \
thumbnail.sh \
unsplitarc.py \
update-src.sh \
upgrade.fedora.sh \
view-cron-log.sh \
whatismyip.sh \
whichicon \
wifi-enable.sh \
wmv-to-mp4.sh \
zfs-health-script.sh \
advanced/preload_ffpmeg_from_src.sh \
advanced/ssh-speedup.md \
advanced/ubuntu-live-unetbootin-drive-can-only-be-fixed-using-existing-ubuntu.sh \
advanced/upgrade-monero-appimage.sh \
install-geany-plugin.sh \
keyboard-layouts/us/colemak.sh \
keyboard-layouts/us/colemak-nonroot.sh \
keyboard-layouts/us/qwerty.sh \
keyboard-layouts/us/qwerty-nonroot.sh \
keyboard-layouts/us/UN-CAPSLOCK \
keyboard-layouts/us/bin/colemak_x.sh \
keyboard-layouts/us/etc/xdg/autostart/colemak_x.desktop \
keyboard-layouts/us/local/share/applications/qwerty.desktop \
nonworking/scanremote.py \
; do
#    cat <<END
    if [ -d ".git/refs/original" ]; then
        rm -r .git/refs/original/
    fi
git filter-branch --index-filter "git rm -rf --cached --ignore-unmatch $path" HEAD
#END
done

echo ""
echo ""
echo "Now try ones with spaces:"
for path in \
'check drive for errors.txt' \
'resize image, batch - by longest side.txt' \
'scan from terminal.txt' \
'advanced/Android - move apps using linux.txt' \
'advanced/antergos-keyring (and therefore everything else) has key error on update.txt' \
'advanced/kmines - compiling - fedora.txt' \
'advanced/kmines - compiling - why so hard.txt' \
'advanced/perl, reinstalling - such as if mismatched version when modules compiled against old.sh' \
'advanced/sgdisk zap gpt.txt' \
'advanced/zpool incremental backup to external drive.txt' \
'advanced/zpool replace instructions.txt' \
; do
#    cat <<END
    if [ -d ".git/refs/original" ]; then
        rm -r .git/refs/original/
    fi
    git reflog expire --expire=now --all
    git gc --aggressive
    git prune
    git filter-branch -f --index-filter "git rm -rf --cached --ignore-unmatch '$path'" HEAD
    # -f must be BEFORE --index-filter! Or you'll still get the following even after deleting .git/refs/original:
    # "Cannot create new backup. A previous backup already exists in refs/original/
    # Force overwriting the backup with -f"
    # - see <https://stackoverflow.com/questions/6403601/purging-file-from-git-repo-failed-unable-to-create-new-backup>
#END
done
echo "* adding new origin..."
git remote add origin git://github.com/poikilos/nopackage.git

echo "* resetting..."
git reset --hard
echo "* gc..."
git gc --aggressive
echo "* prune..."
git prune

echo "Verify origin is nopackage before continuing:"
git remote show origin
git branch -m master main
#^ match the new upstream
git branch --set-upstream-to=origin/main main
# git pull # "Refusing to merge unrelated histories", so as per <>:
#"fatal: remote error:
#  You can't push to git://github.com/poikilos/nopackage.git
#  Use https://github.com/poikilos/nopackage.git"
# so:
git remote set-url origin https://github.com/poikilos/nopackage.git

git push --force
git checkout FETCH_HEAD -- readme.md
git checkout FETCH_HEAD -- license.txt
# ^ automatically stages the files
# FAILS: git checkout FETCH_HEAD -- .gitignore
git commit -m "Add the default readme and license."
git push
```
