Vinaigrette
===========

Build those damn .deb's

How this shit works
-------------------

The build chain relies on `sbuild`, a wrapper tool for building the `.deb`, and `reprepro` to handle the apt repo part (signing and serving) 

1. Initially, some chroots are prepared, one per available distribution (buster, bullseye, ...), pre-installed with build dependencies to speed up builds. See the `scripts/make-chroots` script.
2. `reprepro` is configured in [`/var/www/repo/debian/conf/distributions`](config/distributions). In this file, you'll find the supported distributions (aka codenames), and branches (aka components: stable, testing, unstable). It also declares what GPG key to use to sign the repo. 
3. Upstream codes are kept in `gitrepos/`
4. Builds are launched, either manually via `./ynh-build` and `scripts/ynh-custom-builds` - or via a cron job (c.f. `./daily-build` which in fact runs every 15ish mins?)
    - These scripts usually perform consistency checks, or tweak the changelog / version number, and then call `scripts/build_deb`, itself calling `sbuild` and `reprepro include`
    - In the most simple case, the software being build is arch-independent, such as Python. In that case, it is pretty straightforward : `sbuild` starts the chroot, in which build dependencies are installed, and `dpkg-buildpackage` is called.
    - In more complex cases, the software is arch-dependent. In that case, `sbuild` is called multiple times with `--host=$arch`. It will  still run in the same amd64 chroot, but will install dependencies for the foreign architecture (such as the C compiler for armhf, or lib-foobar-dev for armhf), and build the package using these.
    - For every `.deb`/`.changes` generated, `reprepro include` is called to add the new build to the apt repo. The builds are signed with the key declared in `conf/distributions`.
5. ???
6. PROFIT!


Troubleshooting
---------------

#### Debugging apt/dpkg being in broken state in the chroot

If you savagely Ctrl+C during a build, dpkg/apt may end up in a broken state

You can debug this by entering the chroot with `schroot -c $DIST-amd64-sbuild`

#### Relaunching a build manually with a shell ?

If a build fails and needs to be debugged, you should run `export DEBUG=true`, and re-run the appropriate build command. This should add the option `--anything-failed-commands='%s'` to the `sbuild` command, which will then drop you in an interactive shell inside the chroot, right after the failure. This should help investigate what's happening.

#### Removing "conflicting" sources

- Sometimes reprepro is an ass and wont let you add some sources because a
  supposedly more recent version already exists
- To make it happy, you can use the undocumented `removesrc` feature :

```
# From the folder /var/www/repo/debian
reprepro removesrc <codename> <source-package-names> [<source-version>]

# For instance
 reprepro removesrc stretch yunohost-admin 3.0.0+201804281857
```

#### Removing a deb package from the repo

```
reprepro remove <codename> <package>

# For instance, from anywhere
reprepro -Vb /var/www/repo/debian remove buster python3-miniupnpc
```
(`-Vb /var/www/repo/debian` is where the repo is stored)
