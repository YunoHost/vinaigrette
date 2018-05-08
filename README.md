Vinaigrette
===========

Build those damn .deb's

Todo
-----

- [ ] Understand how the whole arch shit works
	- When do we need a specific arch (e.g. armhf) build ? (e.g. for pure python stuff we don't care, but probably for C/C++ we do ?)
	- How does it actually works (debootstrap stuff ?)
	- How do we manage extra archs like armel, arm64 ...?

- [ ] Test repo in practice
	- Dummy tests when using vinaigrette.yunohost.org in sources.list
	- Test metronome on arm ?
	- Test stretch builds 

- [ ] Moar cleaning of scripts (e.g. specific arch argument in `build_deb` ?)

Content
-------

The script `init.sh` is here to be able to easily redeploy the whole ecosystem on a new machine.

#### Scripts to handle common tasks

- `ynh-build`, to build a new version of Yunohost packages from the git repositories
- `build_deb` (in `/scripts/`, which is used by `ynh-build` but can also be used to manually build stuff like metronome ...)

#### Tools used

- `pbuilder` build the packages (using `dpkg-buildpackage` I believe)
- `rebuildd` handles 'build jobs' (gets notified by
- `reprepro` manages the HTTP(S) repo in `/var/www/repo/debian/`
- `nginx` to serve the repo
- (not yet repaired?) a custom service to handle hooks from github

#### Services

These services should be running for everything to work properly
- `rebuildd`
- `rebuildd-httpd` (and `nginx`) to have "nice" interface to monitor and read build logs
- (not yet repaired?) the github webhook handling service

Useful commands
---------------

- `rebuildd-job list` to list jobs
- `rebuildd` starts the rebuildd server/daemon - for now I have to start it manually and `disown` it. The service should be working but there's some weird stuff about lxc making it crashed ?
- `rebuildd-httpd 127.0.0.1:9998` starts the monitoring/log web interface - same as `rebuildd`, gotta start it manually for now :/
- in `/var/www/repo/debian`, you can list available packages with `reprepro list jessie`

How this shit works
-------------------

![](doc/buildchain.png)

Misc notes
----------

#### Hooks thingy

At the start of the build, pbuilder will call the hooks in scripts/pbuilder/hooks 

#### If you need to rebuild custom packages (for instance, metronome ?)

- See scripts/ynh-custom-builds

#### Chroot images

- To build stuff, pbuilder needs to chroot in environnement.
- These are contained in `images/$dist-$arch.tgz`
- You can rebuild them from `images/make-images`

#### 'Packages' are generally 'source packages' for debian people

Interesting note from [this page](http://tldp.org/HOWTO/html_single/Debian-Binary-Package-Building-HOWTO/)

>an maintainers, packages are source packages, not binary packages. They never interact directly with the internals binary packages. In fact only 'dpkg-deb' and 'dpkg' developers need to know what they are. In fact it is not recommended to do so.
>
>If a developer were to explain someone how to build a Debian package, he will certainly explain how to make a source package and how to build it.
>
>On the other hand, not every developer wants to submit his software to Debian (yet), but still wants to profit from the advantages a packaging system like 'dpkg' offers without releasing package source code. Personally I will release my freeware projects still as tar.gz files with source code etc. for all kind of platforms, while I plan to offer more and more '.deb' packages for the convenience of Debian users who just want to install and use my software. 

#### Relaunching a build manually with a shell ?

- Copy the 'shell after error' hook : `cp /usr/share/doc/pbuilder/examples/C10shell /home/vinaigrette/scripts/pbuilder/hooks/`
- cd /var/cache/rebuildd/build/
- /home/vinaigrette/scripts/rebuildd/build-binaries stretch rspamd 1.6.4 armhf

#### Removing "conflicting" sources

- Sometimes reprepro is an ass and wont let you add some sources because a
  supposedly more recent version already exists
- To make it happy, you can use the undocumented `removesrc` feature :

```
reprepro removesrc <codename> <source-package-names> [<source-version>]

# For instance
 reprepro removesrc stretch yunohost-admin 3.0.0+201804281857
```





