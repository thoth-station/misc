#!/usr/bin/env python3

"""A simple script to test AICoE Python index structure.

See the following PEP standards:
 * Simple Repository API:
    https://www.python.org/dev/peps/pep-0503/
 * A Platform Tag for Portable Linux Built Distributions
    https://www.python.org/dev/peps/pep-0513/
 * The Wheel Binary Package Format 1.0
    https://www.python.org/dev/peps/pep-0427/
"""

import os
import sys
import re
import logging

import click
import daiquiri

daiquiri.setup()

_LOGGER = logging.getLogger(__name__)

# Adjusted based on: https://www.python.org/dev/peps/pep-0427/
_WHEEL_RE = re.compile(
    "(?P<distribution>.+)-(?P<version>.+)(-(?P<build_tag>.+))?-(?P<python_tag>.+)-(?P<abi_tag>.+)-(?P<platform_tag>.+).whl"
)


def _check_python_artifacts(package_dir: str) -> bool:
    """Check Python artifacts present in the corresponding package directory."""
    any_error = False

    for package_artifact in os.listdir(package_dir):
        artifact_path = os.path.join(package_dir, package_artifact)

        if not package_artifact.endswith(".whl"):
            _LOGGER.error("Found artifact that is not a wheel file: %r", artifact_path)
            any_error = True
            continue

        package_parts = _WHEEL_RE.fullmatch(package_artifact)
        if not package_parts:
            _LOGGER.error(
                "Found wheel file does not correspond to Python naming standard: %r",
                artifact_path,
            )
            any_error = True
            continue

        # Now check Python tags.
        if package_parts.group("platform_tag") != "manylinux1_x86_64":
            _LOGGER.error(
                "Found platform tag %r, not manylinux1 tag for: %r",
                package_parts.group("platform_tag"),
                artifact_path,
            )
            any_error = True

    return any_error


def _check_package_listing(packages_dir: str) -> bool:
    """Check listing of package directories under Simple API."""
    any_error = False

    for item in os.listdir(packages_dir):
        package_dir = os.path.join(packages_dir, item)

        if not os.path.isdir(package_dir):
            _LOGGER.error(
                "Expected directory with a package name in %r (not a directory)",
                package_dir,
            )
            any_error = True
            continue

        any_error = _check_python_artifacts(package_dir) or any_error

    return any_error


def _check_simple_api(simple_path: str) -> bool:
    """Check simple API directory listing as per PEP-503."""
    any_error = False

    content = os.listdir(simple_path)

    try:
        content.remove("simple")
    except ValueError:
        _LOGGER.error("No directory called 'simple' found in %r", simple_path)
        return True

    if content:
        _LOGGER.error(
            "Found %r in %r, there is expected only simple directory to be present",
            content,
            simple_path,
        )
        any_error = True

    return _check_package_listing(os.path.join(simple_path, "simple")) or any_error


def _check_config_dir(platform_path: str) -> bool:
    """Check directory structure under the platform directory (containing build configuration)."""
    any_error = False

    for configuration in os.listdir(platform_path):
        config_path = os.path.join(platform_path, configuration)
        if not os.path.isdir(config_path):
            _LOGGER.error(
                "Path %r expects configuration which is a directory", config_path
            )
            any_error = True
            continue

        any_error = _check_simple_api(config_path) or any_error

    return any_error


def _check_platform_dir(path: str) -> bool:
    """Check platform directory structure."""
    any_error = False

    for platform in os.listdir(path):
        platform_path = os.path.join(path, platform)

        if not os.path.isdir(platform_path):
            _LOGGER.error(
                "Path %r expects platform which is a directory", platform_path
            )
            any_error = True
            continue

        any_error = _check_config_dir(platform_path) or any_error

    return any_error


@click.command()
@click.option(
    "--path",
    "-p",
    required=True,
    help="Path to a directory for which AICoE index should be checked.",
)
def cli(path: str):
    """A simple script to test AICoE Python index structure."""
    any_error = _check_platform_dir(path)
    sys.exit(1 if any_error else 0)


if __name__ == "__main__":
    cli()
