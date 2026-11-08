#!/usr/bin/env python3

import argparse
import logging
import os
import re
import shutil
import subprocess
import zipfile
from pathlib import Path
from typing import cast

import colorlog
import github
import github.Artifact
import github.Commit
import github.Repository
import github.Tag
import github.WorkflowRun
import packaging.version
import requests

from .config import get_config


class Project:
    def __init__(self, repo: github.Repository.Repository) -> None:
        self.repo = repo
        self.name = self.repo.name
        self.ci_run: github.WorkflowRun.WorkflowRun | None
        self.tag: github.Tag.Tag | None = None
        self.artifact: github.Artifact.Artifact | None = None
        self.extract_dir: Path | None = None

    @staticmethod
    def _sanitize_tag(tag: str) -> str:
        return tag.replace("testing", "rc").replace("beta1.", "rc1")

    def repo_find_last_tag(self, version_re: str) -> github.Tag.Tag | None:
        tags = {
            packaging.version.Version(self._sanitize_tag(match.group(1))): tag
            for tag in self.repo.get_tags()
            if (match := re.match(version_re, tag.name)) is not None
        }
        return tags.get(max(tags, default=None))

    def repo_commit_last_run(self, commit: github.Commit.Commit, head: str) -> github.WorkflowRun.WorkflowRun | None:
        runs = {
            run.run_number: run
            for run in self.repo.get_workflow_runs(event="push", head_sha=commit.sha)
            if run.head_branch == head
        }
        return runs.get(max(runs, default=None))

    def find_repo_tag_last_run(self, version_re: str, *, tag_name: str | None) -> None:
        regex = version_re if tag_name is None else rf"^{tag_name}$"
        if (tag := self.repo_find_last_tag(regex)) is None:
            msg = f"{self.name}: No tag {tag_name} not found matching '{regex}'!"
            raise RuntimeError(msg)
        logging.info(f"{self.name}: Found matching tag {tag.name} (commit is {tag.commit.sha})")

        if (tag_run := self.repo_commit_last_run(tag.commit, tag.name)) is None:
            msg = f"{self.name}: no workflow run found for tag {tag.name}"
            raise RuntimeError(msg)
        if msg := self.ci_run_is_valid(tag_run) is not None:
            raise RuntimeError(msg)
        self.ci_run = tag_run

    def find_repo_branch_last_run(self, branch_name: str) -> None:
        logging.info(f"{self.name}: Searching for a CI run for branch {branch_name}...")
        for it, commit in enumerate(self.repo.get_commits(sha=branch_name)):
            logging.debug(f"Searching for a CI run for commit {commit.sha}...")
            if (run := self.repo_commit_last_run(commit, branch_name)) is None:
                msg = "Could not find a CI run!"
            elif (msg := self.ci_run_is_valid(run)) is None:
                logging.info(f"{self.name}: Found branch commit with CI run: {commit.sha}")
                self.ci_run = run
                return
            logging.warning(f"{self.name}: Branch {branch_name} commit {commit.sha} was skipped: {msg}")
            if it >= 10:
                raise RuntimeError(f"{self.name}: Could not find a commit with a valid CI run!")

    def ci_run_is_valid(self, run: github.WorkflowRun.WorkflowRun) -> str | None:
        run_state = cast("tuple[str, str | None]", (run.status, run.conclusion))
        msg = f"{self.name}: run '{run.name}' is {run.status} ({run.conclusion}), see {run.html_url}"
        logging.info(msg)
        if run_state == ("in_progress", None):
            return f"{self.name}: workflow run {run.id} is still running!"
        if run_state != ("completed", "success"):
            return f"{self.name}: workflow run {run.id} was not successful!"
        return None

    def find_repo_tag_artifact(self) -> None:
        assert self.ci_run is not None
        artifacts: list[github.Artifact.Artifact] = []
        for artifact in self.ci_run.get_artifacts():
            if artifact.expired:
                logging.warning(f"{self.name}: artifact {artifact.name} has expired")
                continue
            artifacts.append(artifact)

        if len(artifacts) != 1:
            msg = f"{self.name}: workflow run {self.ci_run.id} should have one and only one artifact, has {len(artifacts)}!"
            raise RuntimeError(msg)
        self.artifact = artifacts[0]
        logging.info(f"{self.name}: Found artifact: {self.artifact.name}")

    def download_artifact(self, workdir: Path) -> None:
        assert self.artifact is not None
        auth = self.repo.requester.auth
        assert auth is not None
        logging.info(f"{self.name}: Downloading artifact {self.artifact.name}...")
        headers = {"Accept": "application/vnd.github+json", "Authorization": f"Bearer {auth.token}"}
        response = requests.get(self.artifact.archive_download_url, headers=headers, timeout=30)
        zip_path = workdir / self.artifact.name
        zip_path.write_bytes(response.content)
        self.extract_dir = workdir / self.name
        logging.info(f"Extracting artifacts to {self.extract_dir}...")
        if self.extract_dir.exists():
            shutil.rmtree(self.extract_dir)
        zipfile.ZipFile(zip_path, "r").extractall(self.extract_dir)
        zip_path.unlink()

    def distribute_package(self, repository: Path, *, branch: str, debian_codename: str) -> None:
        assert self.extract_dir is not None
        if len(changes_files := list(self.extract_dir.glob("*.changes"))) != 1:
            msg = f"{self.name}: Artifacts should contain one and only one .changes file. has {len(changes_files)}!"
            raise RuntimeError(msg)
        changes_file = changes_files[0]
        logging.info(f"{self.name}: Distributing package to {repository} for Debian {debian_codename} {branch}...")

        cmd = [
            "reprepro",
            "--waitforlock",
            "6",
            "--basedir",
            str(repository),
            "--component",
            branch,
            "include",
            debian_codename,
            str(changes_file),
        ]
        subprocess.check_call(cmd)


def set_logging_level(level: int) -> None:
    levels = [logging.INFO, logging.DEBUG]
    level = max(0, min(level, len(levels) - 1))
    logfmt = "%(log_color)s%(asctime)s %(levelname)-8s %(message)s"
    handler = logging.StreamHandler()
    handler.setFormatter(colorlog.ColoredFormatter(logfmt))
    logging.basicConfig(handlers=[handler], level=levels[level])


def main() -> None:
    env_token = os.environ.get("GITHUB_TOKEN", None)
    parser = argparse.ArgumentParser()
    parser.add_argument("-v", "--verbose", default=0, action="count", help="Verbosity, can be used multiple times")
    parser.add_argument("-g", "--github-token", required=env_token is None, help="Github Token, or export GITHUB_TOKEN")
    parser.add_argument("-p", "--project", type=str, help="Project to handle, all if not specified")
    parser.add_argument("-t", "--tag", type=str, help="Git tag to use, for a single project")
    parser.add_argument("-u", "--unstable", action="store_true", help="Fetch builds for HEADs of dev branches")
    parser.add_argument("-r", "--repository", type=Path, help="Path to the Debian repository")
    parser.add_argument("-b", "--branch", type=str, help="Debian branch (stable, testing, unstable)")
    parser.add_argument("-d", "--debian", type=str, required=True, help="Debian version (bookworm, trixie etc)")
    parser.add_argument("-y", "--yes", type=str, help="Reply yes to all questions")
    parser.add_argument("-w", "--workdir", type=Path, required=True, help="Work directory (to extract the artifacts)")
    args = parser.parse_args()
    set_logging_level(args.verbose)

    if args.tag and not args.project:
        logging.error("--tag is only valid when --project is passed!")
        raise SystemExit(1)
    if args.tag and args.unstable:
        logging.error("--tag and --unstable are incompatible!")
        raise SystemExit(1)

    workdir = cast("Path", args.workdir).resolve()
    repository = cast("Path | None", args.repository)
    token = args.github_token or env_token
    branch = "unstable" if args.unstable else cast("str", args.branch)
    debian_rel = cast("str", args.debian)
    assert token is not None

    gh = github.Github(auth=github.Auth.Token(token))

    config = get_config()
    org = gh.get_organization(config.projects.organization)
    projects = [args.project] if args.project else config.projects.projects
    projects = [Project(org.get_repo(project)) for project in projects]

    for project in projects:
        if args.unstable:
            project.find_repo_branch_last_run(config.unstable_debian_branches[debian_rel])
        else:
            project.find_repo_tag_last_run(config.projects.version_re, tag_name=args.tag)
        project.find_repo_tag_artifact()

    if not args.yes:
        while True:
            match input("OK to download and distribute found packages?").lower():
                case "y" | "yes":
                    break
                case "n" | "no":
                    raise SystemExit(0)
                case _ as e:
                    print(f"Invalid choice: '{e}'")

    for project in projects:
        project.download_artifact(workdir)

    if repository:
        for project in projects:
            project.distribute_package(repository, branch=branch, debian_codename=debian_rel)
