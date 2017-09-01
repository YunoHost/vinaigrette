#!/usr/bin/env python3
import os
import glob
import json
import time
import shutil
import tarfile
import tempfile
import threading
import subprocess
import collections
import urllib.request
from queue import Queue

from bottle import route, request, run

DISTRIBUTION = "jessie"
BRANCHES=['stable', 'testing', 'unstable']

# -- Variables

# The backend to use for running the server
# See: http://bottlepy.org/docs/0.12/deployment.html#switching-the-server-backend
# Note: flup allows to run as FastCGI process
SERVER_BACKEND = 'flup'

# Host and port on which the server will listen
HOST = '127.0.0.1'
PORT = 9908

# Path to the script to build a package
BUILD_CMD = '/home/vinaigrette/scripts/build_deb'

# Directory where build logs are stored
BUILD_LOG_DIR = '/home/vinaigrette/webhooks/logs'

# Number of worker threads
WORKERS = 1

# -- Types and methods

# Represent a new release of a package
PackageRelease = collections.namedtuple('PackageRelease', [
    'name', 'tarball', 'tag', 'branch', 'pid',
])


def package_files(tar, pkgname, callback=None):
    """Return the members of a package tarball safely."""
    if not callable(callback):
        callback = lambda m: None
    for member in tar:
        if member.name.startswith(pkgname):
            callback(member.name)
            yield member
        else:
            callback("nope: " + member.name)


def build(pkg):
    """Build the given PackageRelease."""
    with open(os.path.join(
            BUILD_LOG_DIR, "{0}.log".format(pkg.pid)), 'w') as logfile:
        log = lambda m: print(m, file=logfile)
        log("== Building {0} ==".format(pkg))

        # create a temporary directory for the package
        pkg_dir = tempfile.mkdtemp()

        # download and extract tarball
        log(":: Downloading and extract tarball to {0}...".format(pkg_dir))
        tarball_stream = urllib.request.urlopen(pkg.tarball)
        tarball = tarfile.open(fileobj=tarball_stream, mode="r|gz")
        for member in tarball:
            if member.name[0] not in ['/', '.']:
                try:
                    _, member.name = member.name.split('/', 1)
                except ValueError:
                    continue
                log(member.name)
                tarball.extract(member, pkg_dir)
            else:
                log("ignoring: {0}".format(member.name))
        tarball.close()

        # build the package
        log("\n:: Building the Debian package...")
        logfile.flush()
        retcode = subprocess.call([
                BUILD_CMD, '-d', pkg.branch,
                '-c', DISTRIBUTION, '.'
            ], cwd=pkg_dir, stdout=logfile, stderr=subprocess.STDOUT,
        )

        # cleaning...
        shutil.rmtree(pkg_dir)
        return retcode


def worker():
    while True:
        item = queue.get()
        if item is None:
            break
        build(item)
        queue.task_done()


# -- Web app and routes

@route("/", method=['GET', 'POST'])
def index():
    if request.method == 'GET':
        return ' Yolo '

    if request.method == 'POST':

        # Answer to GitHub events
        if request.headers.get('X-GitHub-Event') == "ping":
            return json.dumps({'msg': 'Hi!'})

        # Only accept create event:
        # https://developer.github.com/v3/activity/events/types/#releaseevent
        if request.headers.get('X-GitHub-Event') != "release":
            return json.dumps({'msg': "wrong event type"})

        payload = request.json
        if not payload:
            return json.dumps({'msg': "invalid payload"})

        # Only handle tag creation (create event also triggers for branch creation)
        if payload['action'] != "published":
            return json.dumps({'msg': "uninteresting action"})

        # Validate tag and branch
        tag = payload['release']['tag_name']
        if not tag:
            return json.dumps({'msg': "invalid tag"})
        branch = payload['release']['target_commitish']
        if branch not in BRANCHES:
            return json.dumps({'msg': "uninteresting branch"})

        # Init new package release and put it in the queue
        package = PackageRelease(
            name=payload['repository']['name'].lower(),
            tarball=payload['release']['tarball_url'],
            tag=tag, branch=branch, pid=int(time.time()),
        )
        queue.put(package, False)

        # Return the pid to be able to track building
        return "Queue id: {0}".format(package.pid)


# -- Main program

if __name__ == '__main__':
    # Create the queue and the workers
    queue = Queue()
    threads = []
    for i in range(WORKERS):
        t = threading.Thread(target=worker)
        t.start()
        threads.append(t)

    # Run the Web server
    run(server=SERVER_BACKEND, host=HOST, port=PORT)

    # Block until all tasks are done
    queue.join()

    # Stop workers
    for i in range(WORKERS):
        queue.put(None)
        for t in threads:
            t.join()
