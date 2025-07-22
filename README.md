# Vinaigrette

Build those damn .deb's

## How this shit works

The build chain relies on `sbuild`, a wrapper tool for building the `.deb`, and `reprepro` to handle the apt repo part (signing and serving)

* You need to initialize a Debian repository
  * `reprepro` is configured in [`/var/www/repo/debian/conf/distributions`](config/distributions).
    In this file, you'll find the supported distributions (aka codenames), and branches
    (aka components: stable, testing, unstable).
    It also declares which GPG key to use to sign the repo.

* All data is stored in `./data`
  * git repositories
  * chroots
  * build directories
  * flag files to know if rebuilds are required or not
  
Builds are launched either manually via `./vinaigrette <package> <branch> <version>` or via a cron job via `./vinaigrette rebuild-unstable`.

* Consistency checks are run to ensure the proper version / branch was selected
* rebuild-unstable tweaks the changelog and version number
* For every deb/change generated, `reprepro include` is called to add the new build to the apt repo. The builds are signed with the key declared in `conf/distributions`.

## Setup

### Install dependencies

```bash
apt-get install sbuild schroot reprepro gawk debhelper dh-python boxes -y --no-install-recommends
```

### Initialize the Debian repository

```bash
# Import the keys
gpg --import FOOBAR.key
gpg --import FOOBAR.pub

# Link debian repo conf
ln -s $PWD/config/distributions <some_www_exposed_path>/debian/conf/distributions
```

### Initialize the unstable rebuild cron

Add this in /etc/crontab :

```crontab
*/15 *	* * *	root    (cd <path_to_vinaigrette> && date && ./vinaigrette rebuild-unstable) >> /var/log/rebuild-unstable.log
```

## Including a .deb from an external source


For example with rspamd :

1. Obtain the .deb from some other source (possibly for different architectures)

2. Include it in the repo (tweak the `--component`, `--architecture`, distname, ... if needed)

```
reprepro --component testing --architecture armhf -Vb /var/www/repo/debian includedeb bullseye remote-deb/rspamd_3.2-1~bpo11+1_armhf.deb
reprepro --component testing --architecture arm64 -Vb /var/www/repo/debian includedeb bullseye remote-deb/rspamd_3.2-1~bpo11+1_arm64.deb
reprepro --component testing --architecture amd64 -Vb /var/www/repo/debian includedeb bullseye remote-deb/rspamd_3.2-1~bpo11+1_amd64.deb
reprepro --component testing --architecture i386  -Vb /var/www/repo/debian includedeb bullseye remote-deb/rspamd_3.2-1~bpo11+1_i386.deb
```

## Troubleshooting

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
