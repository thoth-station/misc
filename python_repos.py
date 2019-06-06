#!/usr/bin/env python3

import sys
import logging

import requests
import daiquiri
import click

GITHUB_URL_BASE = "https://api.github.com/search/repositories"
SELINON_API_URL = "http://selinon-api-fpokorny-thoth-dev.cloud.paas.psi.redhat.com/api/v1/run-flow"

daiquiri.setup(level=logging.INFO)

_LOGGER = logging.getLogger(__name__)


@click.command()
@click.option('--travis-token', '-t', required=True, type=str, prompt=True, hide_input=True,
              help="Travis token to be used to obtain logs.")
@click.option('--github-token', '-g', required=True, type=str, prompt=True, hide_input=True,
              help="GitHub token to be used to obtain Python repositories.")
@click.option('--selinon-api', '-a', type=str, default=SELINON_API_URL, show_default=True, required=True,
              help="An URL to Thoth's user API.")
@click.option('--pages', '-p', type=int, default=1, show_default=True,
              help="Number of pages to be considered when querying GitHub API.")
@click.option('--offset', '-f', type=int, default=0, show_default=True,
              help="Offset for pages considered when querying GitHub API.")
def cli(travis_token: str = None, github_token: str = None, selinon_api: str = None, pages: int = 1, offset: int = 0):
    """Trigger aggregation of build logs in Travis API."""
    for i in range(offset, offset + pages):
        response = requests.get(
            GITHUB_URL_BASE,
            params={"q": "language:python", "sort": "stars", "order": "desc", "page": i},
            headers={"Authorization": f"token {github_token}"},
        )
        response.raise_for_status()
        content = response.json()

        for item in content['items']:
            org, repo = item["full_name"].split("/")

            response = requests.post(
                selinon_api,
                params={"flow_name": "travis_repo_logs"},
                json={"organization": org, "repo": repo, "token": travis_token},
            )
            response.raise_for_status()
            _LOGGER.info("Submitted %s/%s" % (org, repo))


if __name__ == "__main__":
    sys.exit(cli())
