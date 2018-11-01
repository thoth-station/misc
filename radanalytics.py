#!/usr/bin/env python3

import requests
import click
import logging
import daiquiri

daiquiri.setup(level=logging.INFO)

_LOGGER = daiquiri.getLogger(__name__)

DOCKERHUB_ORGANIZATION = 'radanalyticsio'
DOCKERHUB_API_URL = 'https://hub.docker.com/'
THOTH_ANALYZER_NAME = 'fridex/thoth-package-extract'


def list_dockerhub_images(dockerhub_user: str, dockerhub_password: str, organization: str) -> list:
    """List images on docker hub in the given organization."""
    response = requests.post(DOCKERHUB_API_URL + '/v2/users/login/', json={
        'username': dockerhub_user,
        'password': dockerhub_password
    })
    response.raise_for_status()
    token = response.json()['token']

    # TODO: pagination
    response = requests.get(
        DOCKERHUB_API_URL + f'/v2/repositories/{organization}',
        headers={'Authorization': f'JWT {token}'},
        params={'page_size': 100}
    )
    response.raise_for_status()

    return response.json()['results']


def analyze_image(image: str, thoth_user_api: str) -> str:
    """Analyze the given image in Thoth."""
    _LOGGER.info(f"Requesting analysis of image {image}")
    response = requests.post(thoth_user_api + '/api/v1/analyze', params={
        'image': image,
        'analyzer': THOTH_ANALYZER_NAME,
        'debug': True
    })
    response.raise_for_status()
    _LOGGER.debug(f"Thoth user API responded with: {response.json()}")
    return response.json()['analysis_id']


def analyze_radanalytics_images(dockerhub_user: str, dockerhub_password: str, thoth_user_api: str) -> None:
    """Analyze radanalytics.io images."""
    images = list_dockerhub_images(dockerhub_user, dockerhub_password, organization=DOCKERHUB_ORGANIZATION)
    if thoth_user_api.endswith('/'):
        thoth_user_api = thoth_user_api[:-1]

    for image in images:
        try:
            image = f"{image['namespace']}/{image['name']}"
            analysis_id = analyze_image(image, thoth_user_api)
            _LOGGER.info(f"Image {image!r} is analyzed by {analysis_id!r}")
        except Exception as exc:
            _LOGGER.exception(f"Failed to submit image for analysis: {str(exc)}")


@click.command()
@click.pass_context
@click.option('-v', '--verbose', is_flag=True,
              help="Be verbose about what's going on.")
@click.option('--dockerhub-user', '-u', required=True, type=str,
              help="A username of Dockerhub account to be used.")
@click.option('--dockerhub-password', '-p', required=True, type=str, prompt=True, hide_input=True,
              help="A username of Dockerhub account to be used.")
@click.option('--thoth-user-api', '-a', required=True, type=str,
              help="An URL to Thoth's user API.")
def cli(ctx=None, verbose=0, dockerhub_user=None, dockerhub_password=None, thoth_user_api=None):
    """Submit analysis for Radanalytics images hosted on Dockerhub."""
    if ctx:
        ctx.auto_envvar_prefix = 'THOTH_RADANALYTICS'

    if verbose:
        _LOGGER.setLevel(logging.DEBUG)
        _LOGGER.debug("Debug mode turned on")
        _LOGGER.debug(f"Passed options: {locals()}")

    analyze_radanalytics_images(dockerhub_user, dockerhub_password, thoth_user_api)


if __name__ == '__main__':
    cli()
