#!/usr/bin/env python3
# ps2prescriptions
# Copyright(C) 2021 Fridolin Pokorny
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

import os
import logging
import requests
from typing import List

import click
from thoth.common import init_logging
from thoth.python import Pipfile

init_logging()

_LOGGER = logging.getLogger(__name__)

_BOOT_BASE = """\
  - name: {unit_name}
    type: boot
    should_include:
      adviser_pipeline: true
      runtime_environments:
        base_images:
          not:
          - {image}
    match:
      package_name: {package_name}
    run:
      stack_info:
      - type: INFO
        message: {message}
        link: {link}
"""


def _make_prescription_boot_name(ps_package: str, ps_name: str) -> str:
    """Create a name for predictable stack boot."""
    prescription_name = ""
    for part in map(str.capitalize, ps_package.split("-")):
        prescription_name += part

    prescription_name += "PredictableStack"

    for part in map(str.capitalize, ps_name.split("-")):
        prescription_name += part

    return prescription_name + "Boot"


def _create_units(
    ps_packages: List[str],
    ps_name: str,
    info: str,
    prescriptions_path: str,
    abbreviation: str,
) -> None:
    """Create a boot with the specified packages"""
    predictable_stacks_path = os.path.join(
        prescriptions_path, "prescriptions", "_containers"
    )
    _LOGGER.info("Creating directory structure in %r", predictable_stacks_path)
    os.makedirs(predictable_stacks_path, exist_ok=True)

    image_repo = f"https://quay.io/repository/thoth-station/{ps_name}"
    image = f"quay.io/thoth-station/{ps_name}"

    response = requests.head(f"https://{image}", allow_redirects=True)
    if response.status_code != 200:
        _LOGGER.warning("Image %r is not accessible on Quay", image)

    prescription_file_path = (
        os.path.join(predictable_stacks_path, abbreviation, ps_name.replace("-", "_"))
        + ".yaml"
    )
    os.makedirs(os.path.dirname(prescription_file_path), exist_ok=True)
    _LOGGER.info("Writing prescription YAML file to %r", prescription_file_path)

    with open(os.path.join(prescription_file_path), "w") as f:
        f.write("units:\n  boots:\n")
        for package_name in ps_packages:
            message = (
                f"Consider using a {info + ' ' if info else ''}predictable stack {ps_name!r} that "
                f"has prepared environment with {package_name!r}"
            )

            f.write(
                _BOOT_BASE.format(
                    package_name=package_name,
                    message=message,
                    link=image_repo,
                    unit_name=_make_prescription_boot_name(package_name, ps_name),
                    image=image,
                )
            )


@click.command()
@click.option("--verbose", "-v", is_flag=True, help="Be verbose about what's going on.")
@click.option(
    "--overlays-path",
    "-p",
    type=str,
    required=True,
    help="A path to predictable stack overlays where Pipfile is located",
)
@click.option(
    "--prescriptions-path",
    "-p",
    type=str,
    required=True,
    help="A root path to prescriptions directory",
)
@click.option(
    "--info",
    "-i",
    type=str,
    required=False,
    help="Additional info about the stack (ex. natural language).",
)
@click.option(
    "--predictable-stack-abbreviation",
    "-a",
    type=str,
    required=False,
    help="Abbreviation used for the give predictable stack.",
)
def cli(
    verbose: bool,
    overlays_path: str,
    info: str,
    prescriptions_path: str,
    predictable_stack_abbreviation: str,
) -> None:
    """Create prescriptions out of a predictable stack repository."""
    if verbose:
        _LOGGER.setLevel(logging.DEBUG)

    for ps_name in os.listdir(overlays_path):
        overlays_dir = os.path.join(overlays_path, ps_name)
        if not overlays_dir:
            _LOGGER.warning("Skipping %r: not a directory", overlays_dir)
            continue

        _LOGGER.info("Processing overlay %r", ps_name)
        pipfile = Pipfile.from_file(os.path.join(overlays_dir, "Pipfile"))
        ps_direct_packages = list(pipfile.packages.packages)

        _create_units(
            ps_direct_packages,
            ps_name,
            info,
            prescriptions_path,
            predictable_stack_abbreviation,
        )


__name__ == "__main__" and cli()
