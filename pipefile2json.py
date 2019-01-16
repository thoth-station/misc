#!/usr/bin/env python3
# 2019, Fridolin Pokorny <fridolin@redhat.com>
#
# This script is handy if you would like to manually use Thoth services such as
# Amun where a service expects JSON representation of Pipfile or Pipfile.lock
# as an input. This script converts the TOML or Pipfile.lock file into expected
# representation so you can easily test and perform evaluations on a software
# stack.

import sys
import json
import logging
from pathlib import Path

import toml
import click
import daiquiri

daiquiri.setup(level=logging.INFO)
_LOGGER = logging.getLogger(__name__)


def pipfile2dict(pipfile_path: str):
    """Convert Pipfile or Pipfile.lock file into JSON representation for Thoth services."""
    content = Path(pipfile_path).read_text()

    # For Pipfile, return direct parsed JSON.
    try:
        return toml.loads(content)
    except Exception:
        _LOGGER.info("Failed to parse provided file %r as Pipfile, fallback to Pipfile.lock parsing", pipfile_path)
        try:
            content = json.loads(content)
        except Exception:
            _LOGGER.error("Failed to parse provided file as TOML or JSON file")

        # For Pipfile.lock, return packages as they would be stated in a Pipfile but in JSON structure.
        result = {
            "source": None,
            "packages": {},
            "dev-packages": {},
        }
        for package_name, package_info in content["default"].items():
            version = package_info.get("version")
            if not version:
                _LOGGER.warning("Package %r does not have a locked version assigned: %r", package_name, package_info)
                continue

            result["packages"][package_name] = version

        for package_name, package_info in content.get("develop", {}).items():
            version = package_info.get("version")
            if not version:
                _LOGGER.warning("Package %r does not have a locked version assigned: %r", package_name, package_info)
                continue

            result["dev-packages"][package_name] = version

        result["source"] = content["_meta"].pop("sources", [])

        if "requires" in content["_meta"]:
            result["requires"] = content["_meta"]["requires"]

    return result


@click.command()
@click.argument('pipfile_path', type=str)
def pipefile2json_cli(pipfile_path: str):
    json.dump(pipfile2dict(pipfile_path), sys.stdout, indent=2)



if __name__ == "__main__":
    sys.exit(pipefile2json_cli())

