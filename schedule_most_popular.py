#!/usr/bin/env python3
# Copyright(C) 2019 Fridolin Pokorny
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

"""Schedule analysis of most popular Python packages on PyPI."""

import requests
import logging
import sys

import click
import daiquiri


daiquiri.setup(level=logging.INFO)

_LOGGER = logging.getLogger(__name__)

_POPULAR_PYPI_PACKAGES = "https://hugovk.github.io/top-pypi-packages/top-pypi-packages-365-days.json"


def schedule_most_popular(management_api_url: str, api_secret: str, *, offset: int, count: int) -> None:
    """Schedule analysis of most popular Python packages present on PyPI."""
    _LOGGER.info("Obtaining list of most popular Python packages...")
    response = requests.get(_POPULAR_PYPI_PACKAGES)
    response.raise_for_status()

    for idx, item in enumerate(response.json()["rows"][offset:offset + count]):
        project = item["project"]
        if project in ("wheel", "pip", "setuptools", "six"):
            _LOGGER.info("Omitting %d. most popular project %r", offset + idx, item["project"])
            continue

        _LOGGER.info("Scheduling solver run for %d. most popular project %r", offset + idx, item["project"])

        # A simple workaround for network issues in the cluster when talking to the graph database.
        retries = 0
        while True:
            response = requests.post(
                f"{management_api_url}/solver/python",
                json={
                    "package_name": project,
                    "version_specifier": ""
                },
                params={
                    "secret": api_secret,
                    "debug": True,
                    "no_subgraph_checks": False,
                }
            )
            try:
                response.raise_for_status()
            except Exception:
                retries += 1
                if retries == 3:
                    raise

            _LOGGER.info(response.json())
            break


@click.command()
@click.option('--api-secret', required=True, type=str,
              help="Secret used when communicating with management API.")
@click.option('--management-api-url', '-a', required=True, type=str,
              default="https://management.stage.thoth-station.ninja/api/v1", show_default=True,
              help="Management API URL to talk to.")
@click.option('--offset', '-f', type=int, default=0, show_default=True,
              help="Offset in the popularity package listing.")
@click.option('--count', '-c', type=int, default=100, show_default=True,
              help="Number of packages to be scheduled.")
def cli(api_secret: str, management_api_url: str, offset: int, count: int):
    """Trigger analysis of most popular Python packages on PyPI."""
    schedule_most_popular(
        management_api_url,
        api_secret,
        offset=offset,
        count=count,
    )


if __name__ == "__main__":
    sys.exit(cli())
