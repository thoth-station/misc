#!/usr/bin/env python3
# thoth-performance
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

"""Run Performance benchmark for testing using Amun."""


import sys
import logging
import os
import subprocess
from subprocess import call
import json

import click
import daiquiri

from pipefile2json import pipfile2dict

daiquiri.setup(level=logging.INFO)

_LOGGER = logging.getLogger(__name__)


def verify_framework_version_installed(framework: str, script: str):
    """Verify framework/version installed provenance."""
    # TODO: Use provenance checker


def create_amun_api_input(
    image: str, framework: str, framework_version: str, index_url: str, benchmark: str
) -> dict:
    """Create specification for Amun API input"""
    with open("./inspection.json") as json_file:
        specification = json.load(json_file)

    specification["base"] = image
    create_pipfile_and_pipfile_lock_inputs(
        framework=framework, framework_version=framework_version, index_url=index_url
    )
    # Insert Pipfile and Pipfile.lock and make them str for input
    specification["python"]["requirements"] = pipfile2dict(pipfile_path="./Pipfile")
    with open("./Pipfile.lock") as json_file:
        requirements_locked = json.load(json_file)
    specification["python"]["requirements_locked"] = requirements_locked

    # Insert script for performance test
    specification["script"] = benchmark

    update_json_specification(
        path_template_specification="./inspection.json", content=specification
    )
    return specification


def update_json_specification(path_template_specification: str, content: object):
    """Update the dashboard with new changes"""
    os.remove("{}".format(path_template_specification))
    with open("{}".format(path_template_specification), "w") as outfile:
        json.dump(content, outfile, indent=4)
    _LOGGER.info(f"Updated the new json specification file for Amun API.")


def create_pipfile_and_pipfile_lock_inputs(
    framework: str, framework_version: str, index_url: str
):
    """Create requirements and requirements_locked"""
    if os.path.exists("{}".format("./Pipfile")):
        os.remove("{}".format("./Pipfile"))
    else:
        _LOGGER.info("Pipfile was not present!")

    if os.path.exists("{}".format("./Pipfile.lock")):
        os.remove("{}".format("./Pipfile.lock"))
    else:
        _LOGGER.info("Pipfile.lock was not present!")

    if index_url == "https://pypi.python.org/simple":
        _LOGGER.info(
            " ".join(
                [
                    "pipenv",
                    "install",
                    f"{framework}=={framework_version}",
                    "--python",
                    "3.6",
                ]
            )
        )
        subprocess.call(
            [
                "pipenv",
                "install",
                f"{framework}=={framework_version}",
                "--python",
                "3.6",
            ]
        )
    else:
        _LOGGER.info(
            " ".join(
                [
                    "pipenv",
                    "install",
                    f"{framework}=={framework_version}",
                    "--index",
                    index_url,
                    "--extra-index-url",
                    '"https://pypi.python.org/simple"',
                    "--python",
                    "3.6",
                ]
            )
        )
        subprocess.call(
            [
                "pipenv",
                "install",
                f"{framework}=={framework_version}",
                "--index",
                index_url,
                "--extra-index-url",
                '"https://pypi.python.org/simple"',
                "--python",
                "3.6",
            ]
        )

    if os.path.exists("{}".format("./Pipfile")):
        _LOGGER.info("Pipfile was created!")
    else:
        _LOGGER.error("Pipfile was not created!")

    if os.path.exists("{}".format("./Pipfile.lock")):
        _LOGGER.info("Pipfile.lock was created!")
    else:
        _LOGGER.error("Pipfile.lock was not created!")


def verify_script_framework_compatibility(framework: str, script: str):
    """Verify compatibility between framework and script to used for performances."""
    _LOGGER.info(f"Verifying compatibility between framework and script...")
    if framework in script:
        _LOGGER.info(
            f"Script selected for performance testing: {script}, is not compatible with ML framework chosen: '{framework}'."
        )
    else:
        raise ValueError(
            f"Script selected for performance testing: {script}, is not compatible with ML framework chosen: '{framework}'."
        )


def schedule_performance_benchmarks(
    amun_api_url: str,
    framework: str,
    framework_version: str,
    benchmark: str,
    image: str,
    index_url: str,
    count: int,
):
    """Run Performance benchmark."""
    verify_script_framework_compatibility(framework=framework, script=benchmark)
    _LOGGER.info(f"Platform/Image selected is {image}")
    _LOGGER.info(f"Framework/Version selected is: {framework}:{framework_version}")
    _LOGGER.info(f"Index source is: {index_url}")
    _LOGGER.info(f"Performance test selected is: {benchmark}")
    _LOGGER.info(f"Number of inspections requested is: {count}")
    specification = create_amun_api_input(
        image=image,
        framework=framework,
        framework_version=framework_version,
        index_url=index_url,
        benchmark=benchmark,
    )
    _LOGGER.info(f"Specification input for Amun API is: {specification}")
    for inspection_n in range(0, count):
        print(inspection_n + 1)
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
    "--image",
    "-i",
    required=True,
    type=str,
    help="Platform/ image used to run the inspection.",
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
    "-fv",
    required=True,
    type=str,
    help="Framework version to be installed for the performance test.",
)
@click.option(
    "--index-url",
    "-iu",
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
def cli(
    amun_api_url: str,
    framework: str,
    framework_version: str,
    benchmark: str,
    image: str,
    index_url: str,
    count: int,
):
    """Trigger analysis of inspections for the selected platform/image, index_url and framework."""
    schedule_performance_benchmarks(
        amun_api_url=amun_api_url,
        image=image,
        framework=framework,
        framework_version=framework_version,
        benchmark=benchmark,
        index_url=index_url,
        count=count,
    )


if __name__ == "__main__":
    cli()
