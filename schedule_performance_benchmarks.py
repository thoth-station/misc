#!/usr/bin/env python3
# Copyright(C) 2019 Francesco Murdaca
#
# This program is free software: you can redistribute it and / or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

"""Schedule Inspections for testing Performance Benchmarks to be evaluated using Amun."""


import sys
import logging
import os
import subprocess
import json
from thoth.python import Source
from thoth.python import Project
from thoth.python import PackageVersion
from pathlib import Path
from exceptions import NotInstalledIndexException
from exceptions import FileCreationException
from exceptions import ScriptFrameworkIncompatibilityException


import click
import daiquiri

from pipefile2json import pipfile2dict

daiquiri.setup(level=logging.INFO)

_LOGGER = logging.getLogger(__name__)


def verify_framework_version_installed(framework_name: str, path: str, index_url: str):
    """Verify framework/version installed provenance."""
    p = subprocess.Popen(
        ["pipenv", "run", "pip", "show", framework_name],
        cwd=path,
        stdout=subprocess.PIPE,
    )
    out, err = p.communicate()
    _LOGGER.info(out.decode("utf-8"))
    if not index_url == "https://pypi.org/simple":
        if "Red Hat Inc." in out.decode("utf-8"):
            _LOGGER.info(
                "The index used for installation is from Red Hat AICoE Thoth Project"
            )
        else:
            raise NotInstalledIndexException(
                f"The index used for installation is not the one requested: {out}"
            )


def create_amun_api_input(
    name_inspection: str,
    base_image: str,
    native_packages: str,
    python_packages: str,
    framework: str,
    framework_version: str,
    index_url: str,
    benchmark: str,
) -> dict:
    """Create specification for Amun API input."""
    with open("./inspection.json") as json_file:
        specification = json.load(json_file)

    # Name of the inspection/s
    specification["identifier"] = name_inspection

    specification["base"] = base_image
    if native_packages:
        native_packages = native_packages.split(",")
    else:
        native_packages = []
    specification["packages"] = native_packages
    if python_packages:
        python_packages = python_packages.split(",")
    else:
        python_packages = []
    specification["python_packages"] = python_packages
    create_pipfile_and_pipfile_lock_inputs(
        framework=framework, framework_version=framework_version, index_url=index_url
    )
    # Insert Pipfile and Pipfile.lock and make them str for input
    current_path = Path.cwd()
    new_dir_path = current_path.joinpath("amun")
    pipfile_path = new_dir_path.joinpath("Pipfile")
    pipfile_lock_path = new_dir_path.joinpath("Pipfile.lock")

    specification["python"]["requirements"] = pipfile2dict(pipfile_path=pipfile_path)
    with open(pipfile_lock_path) as json_file:
        requirements_locked = json.load(json_file)

    specification["python"]["requirements_locked"] = requirements_locked

    # Insert script for performance test
    specification["script"] = benchmark

    update_json_specification(
        path_template_specification="./inspection.json", content=specification
    )
    _LOGGER.info(f"Updated the new json specification file for Amun API.")
    return specification


def update_json_specification(path_template_specification: str, content: object):
    """Update the json specification with new changes."""
    os.remove("{}".format(path_template_specification))

    with open("{}".format(path_template_specification), "w") as outfile:
        json.dump(content, outfile, indent=4)


def create_pipfile(
    index_url: str, framework: str, framework_version: str, pipfile_path: str
):
    """Create Pipfile from inputs."""
    packages = [
        PackageVersion(
            name=f"{framework}",
            version=f"=={framework_version}",
            develop=False,
            index=Source(index_url),
        )
    ]
    project = Project.from_package_versions(packages)

    if not index_url == "https://pypi.org/simple":
        project.add_source("https://pypi.org/simple")

    project.set_python_version("3.6")
    _LOGGER.info(f"Pipfile created:\n {project.pipfile.to_string()}")

    with open(pipfile_path, "w+") as pipfile:
        pipfile.write(project.pipfile.to_string())


def create_pipfile_and_pipfile_lock_inputs(
    framework: str, framework_version: str, index_url: str
):
    """Create requirements and requirements_locked."""
    current_path = Path.cwd()
    new_dir_path = current_path.joinpath("amun")
    os.makedirs(new_dir_path, exist_ok=True)

    pipfile_path = new_dir_path.joinpath("Pipfile")
    pipfile_lock_path = new_dir_path.joinpath("Pipfile.lock")

    if pipfile_path.exists():
        os.remove(pipfile_path)
    else:
        _LOGGER.info("Pipfile was not present!")

    if os.path.exists(pipfile_lock_path):
        os.remove(pipfile_lock_path)
    else:
        _LOGGER.info("Pipfile.lock was not present!")

    create_pipfile(
        index_url=index_url,
        framework=framework,
        framework_version=framework_version,
        pipfile_path=pipfile_path,
    )
    if pipfile_path.exists():
        _LOGGER.info("Pipfile was created!")
    else:
        raise FileCreationException("Pipfile was not created!")

    _LOGGER.info(" ".join(["Running...", "pipenv", "install"]))
    subprocess.call(["pipenv", "install"], cwd=new_dir_path)
    verify_framework_version_installed(
        framework_name=framework, path=new_dir_path, index_url=index_url
    )

    if os.path.exists(pipfile_lock_path):
        _LOGGER.info("Pipfile.lock was created!")
    else:
        raise FileCreationException("Pipfile.lock was not created!")


def verify_script_framework_compatibility(framework: str, script: str):
    """Verify compatibility between framework and script to used for performances."""
    _LOGGER.info(f"Verifying compatibility between framework and script...")
    if framework in script:
        _LOGGER.info(
            f"Script selected for performance testing: {script}, is compatible with ML framework chosen: '{framework}'."
        )
    else:
        raise ScriptFrameworkIncompatibilityException(
            f"Script selected for performance testing: {script}, is not compatible with ML framework chosen: '{framework}'."
        )


def schedule_performance_benchmarks(
    amun_api_url: str,
    name_inspection: str,
    framework: str,
    framework_version: str,
    benchmark: str,
    base_image: str,
    native_packages: str,
    python_packages: str,
    index_url: str,
    count: int,
    dry_run: bool,
):
    """Schedule Performance benchmark."""
    verify_script_framework_compatibility(framework=framework, script=benchmark)
    _LOGGER.info(f"Platform/Base Image selected is {base_image}")
    _LOGGER.info(f"Native packages to be installed on base image: {native_packages}")
    _LOGGER.info(f"Python packages to be installed on base image: {python_packages}")
    _LOGGER.info(f"Framework/Version selected is: {framework}:{framework_version}")
    _LOGGER.info(f"Index source is: {index_url}")
    _LOGGER.info(f"Performance test selected is: {benchmark}")
    _LOGGER.info(f"Number of inspections requested is: {count}")
    specification = create_amun_api_input(
        name_inspection=name_inspection,
        base_image=base_image,
        native_packages=native_packages,
        python_packages=python_packages,
        framework=framework,
        framework_version=framework_version,
        index_url=index_url,
        benchmark=benchmark,
    )
    _LOGGER.info(f"Scheduling inspection at {amun_api_url}")
    _LOGGER.info(f"Specification input for Amun API is: {specification}")
    for inspection_n in range(0, count):
        _LOGGER.info(inspection_n + 1)
        if not dry_run:
            subprocess.call(
                [
                    "curl",
                    "-X",
                    "POST",
                    "--header",
                    "Content-Type: application/json",
                    "--header",
                    "Accept: application/json",
                    "-d",
                    "@inspection.json",
                    amun_api_url,
                ]
            )


@click.command()
@click.option(
    "--amun-api-url",
    "-a",
    required=True,
    type=str,
    default="http://amun-api-thoth-amun-api-stage.cloud.paas.psi.redhat.com/api/v1/inspect",
    show_default=True,
    help="Amun API URL to talk to.",
)
@click.option(
    "--name-inspection",
    "-n",
    required=True,
    type=str,
    help="User' name given to the inspections.",
)
@click.option(
    "--base-image",
    "-i",
    required=True,
    type=str,
    help="Platform/Base_image used to run the inspection.",
)
@click.option(
    "--native-packages",
    "-r",
    type=str,
    default="",
    show_default=True,
    help="List of native packages (RPM or Deb packages) that should be installed into the requested base image.",
)
@click.option(
    "--python-packages",
    "-p",
    type=str,
    default="",
    show_default=True,
    help="List of python packages that should be installed into the requested base image.",
)
@click.option(
    "--framework",
    "-f",
    required=True,
    type=str,
    help="Framework to be installed for the performance test.",
)
@click.option(
    "--framework-version",
    "-v",
    required=True,
    type=str,
    help="Framework version to be installed for the performance test.",
)
@click.option(
    "--index-url",
    "-u",
    required=True,
    type=str,
    help="URL of the framework:version to be installed for the performance test.",
)
@click.option(
    "--benchmark",
    "-b",
    required=True,
    type=str,
    help="URL of the benchmark to be used to test performances of the python package.",
)
@click.option(
    "--count",
    "-c",
    type=int,
    default=100,
    show_default=True,
    help="Number of inspections to be scheduled.",
)
@click.option(
    "--dry-run",
    "-d",
    type=bool,
    default=False,
    show_default=True,
    help="Do not schedule inspections, just check all inputs are created.",
)
def cli(
    amun_api_url: str,
    name_inspection: str,
    framework: str,
    framework_version: str,
    benchmark: str,
    base_image: str,
    native_packages: str,
    python_packages: str,
    index_url: str,
    count: int,
    dry_run: bool,
):
    """Trigger analysis of inspections for the selected platform/base_image, index_url and framework."""
    schedule_performance_benchmarks(
        amun_api_url=amun_api_url,
        name_inspection=name_inspection,
        base_image=base_image,
        native_packages=native_packages,
        python_packages=python_packages,
        framework=framework,
        framework_version=framework_version,
        benchmark=benchmark,
        index_url=index_url,
        count=count,
        dry_run=dry_run,
    )


if __name__ == "__main__":
    cli()
