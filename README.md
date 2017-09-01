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

- Let's say you run `ynh-build` because of a new version of yunohost
- (Warning : make sure that you have a new entry in debian/changelog, and a tag debian/x.y.z - otherwise it won't be happy if the version already exists)
- The script make sure the repo and the proper branch is up to date locally
- It calls `build_deb`, which will build the sources with `pbuilder` and push the sources with `reprepro`
- With some magic involved (?), `rebuildd` understands that there's something new to build
- `rebuildd` picks up the job. It gets the sources (`get-sources`) and starts building the binaries (`build-binaries`). After that, it uploads the binaries to reprepro (`upload-binaries`) and sends an XMPP notification

Misc notes
----------

#### If you need to rebuild custom packages (for instance, metronome ?)

- Go to a git clone of https://github.com/yunohost/metronome/
- Inside the git clone, call `/path/to/build_deb -c jessie -d unstable .`
- This will build the source and add a rebuildd job.

#### Chroot images

- To build stuff, pbuilder needs to chroot in environnement.
- These are contained in `images/$arch/$dist.tgz`
- You may be able to regerate them 'from scratch' with `rebuildd-init-build-system`. Not sure entirely how this works though. I guess it reads distributions and archs from conf file ?
