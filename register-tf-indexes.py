import logging

import requests
import click
from bs4 import BeautifulSoup
import daiquiri


daiquiri.setup(level=logging.INFO)

_LOGGER = logging.getLogger(__name__)

DEFAULT_INDEX_BASE_URL = 'http://tensorflow.pypi.thoth-station.ninja/index'


def _get_build_configuration(index_base_url, distro) -> list:
    """Get available configration for a distro."""
    build_configuration_url = index_base_url + '/' + distro

    response = requests.get(build_configuration_url)
    soup = BeautifulSoup(response.text, 'lxml')
    table = soup.find('table')
    if not table:
        return []

    configurations = []
    for row in table.find_all('tr'):
        for cell in row.find_all('td'):
            if cell.a:
                configuration = cell.a.text
                if configuration == 'Parent Directory':
                    continue

                configurations.append(build_configuration_url + configuration + 'simple')

    return configurations


def _list_available_indexes(index_base_url: str) -> list:
    """List available indexes on AICoE index."""
    _LOGGER.info("Listing available indexes on AICoE index %r.", index_base_url)
    response = requests.get(index_base_url)
    soup = BeautifulSoup(response.text, 'lxml')

    result = []
    for row in soup.find('table').find_all('tr'):
        for cell in row.find_all('td'):
            if cell.a:
                distro = cell.a.text
                if distro == 'Parent Directory':
                    continue
                
                result.extend(_get_build_configuration(index_base_url, distro))

    return result


def _register_index(index: str, management_api_url: str, secret: str = None):
    """Register the given index on management API."""
    _LOGGER.info("Registering index %r on management API %r", index, management_api_url)
    if not management_api_url.endswith('/'):
        management_api_url += '/'

    endpoint = management_api_url + 'api/v1/register-python-package-index'
    response = requests.post(
            endpoint,
            json={
                'url': index,
                'verify_ssl': False,
                'warehouse_api_url': ''
            },
            params={'secret': secret}
    )
    print(response.text)
    response.raise_for_status()


@click.command()
@click.option('--verbose', '-v', is_flag=True,
              help="Be verbose about what's going on.")
@click.option('--index-base-url', '-i', type=str, default=DEFAULT_INDEX_BASE_URL,
              help="AICoE URL base for discovering packages.")
@click.option('--management-api-url', type=str, required=True,
              help="Management API where indexes should be registered.")
@click.option('--secret', type=str,
              help="Management API where indexes should be registered.")
def cli(verbose: bool = False, management_api_url: str = None, index_base_url: str = None, secret: str = None):
    """Register AICoE indexes in Thoth's database."""
    for index in _list_available_indexes(index_base_url):
        _register_index(index, management_api_url, secret)


if __name__ == '__main__':
    cli()
