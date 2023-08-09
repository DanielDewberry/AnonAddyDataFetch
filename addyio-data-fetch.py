#!/usr/bin/env python3
# coding: utf-8

"""Fetch addy.io data and generate a CSV output file."""

import argparse
import csv
import logging
import sys
from typing import List

import requests


def argument_parser_factory():
    """Create the argument parser."""
    parser = argparse.ArgumentParser()
    parser.add_argument('token', help='The addy.io API token')
    parser.add_argument('filename', help='The filename to overwrite with CSV data')
    parser.add_argument('--log-level',
                        choices=['debug', 'info', 'warning', 'error', 'critical'],
                        default='info',
                        help='The logging level which will affect reporting information')
    parser.add_argument('--columns',
                        default=None,
                        help='Comma-separated list of column names to use.  All columns selected by default.')

    return parser


def logger_factory(logging_level) -> None:
    """Register and configure the application logger."""
    logger = logging.getLogger('email-info-fetcher')
    logger.setLevel(logging.DEBUG)

    ch = logging.StreamHandler()
    ch.setLevel(logging_level)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    ch.setFormatter(formatter)
    logger.addHandler(ch)
    return None


def request_page(page_number: int, token: str):
    """Perform a page request, using the pagenumber and token.

    The pagesize is size is set internally.
    """
    logger = logging.getLogger('email-info-fetcher')
    page_size = 100

    base_url = 'https://app.addy.io/api/v1/aliases'
    params = {'page[size]': page_size,
              'page[number]': page_number,
              }
    headers = {'Content-Type': 'application/json',
               'X-Requested-With': 'XMLHttpRequest',
               'Authorization': f'Bearer {token}',
               }
    logger.info('Fetching page %s', page_number)
    return requests.get(base_url, params=params, headers=headers)


def key_is_missing(d: dict, key: str):
    """Determine whether a key is missing from a dictionary."""
    try:
        d.get(key)
        return False
    except KeyError:
        return True


def perform_fetches(token: str, column_names: List[str]):
    """Coordinate all data fetches until no data is returned."""
    logger = logging.getLogger('email-info-fetcher')

    data_list = [
        column_names,
        ]

    page_number = 0
    while True:
        page_number += 1
        response = request_page(page_number, token)

        if response.status_code >= 400:
            logger.error('Failed to acquire data. Request yielded response code %s',
                         response.status_code)
            exit(1)

        page_data = response.json()
        page_data = page_data['data']
        if len(page_data) == 0:
            break

        for datum in page_data:
            missing_keys = [column_name for column_name in column_names if key_is_missing(datum, column_name)]
            if len(missing_keys) > 0:
                logger.error('Missing keys detected: [%s]', ', '.join(missing_keys))
                sys.exit(1)
            data_list.append([datum[column_name] for column_name in column_names])

    return data_list


def write_data_to_csv(filename, data):
    """Write the data to the provided filename, as  CSV format.

    Existing data will be truncated.
    """
    logger = logging.getLogger('email-info-fetcher')
    logger.info('Writing to file %s', filename)

    with open(filename, 'w', encoding='UTF8') as fp:
        csv_writer = csv.writer(fp, dialect='excel')
        for record in data:
            csv_writer.writerow(record)


def main(token: str, filename: str, column_names: List[str]):
    """Application entrypoint."""
    logger = logging.getLogger('email-info-fetcher')
    logger.info('Startup')
    data = perform_fetches(token, column_names)
    write_data_to_csv(filename, data)
    logger.info('Done')


def logging_level_from_string(log_level: str):
    """Translate a text logging level to it's equivilent object.

    Input Value | Mapping
    ------------+-----------------
    debug       | logging.DEBUG
    info        | logging.INFO
    warning     | logging.WARNING
    error       | logging.ERROR
    critical    | logging.CRITICAL
    fatal       | logging.FATAL
    """
    mapping = {
        'debug':        logging.DEBUG,
        'info':         logging.INFO,
        'warning':      logging.WARNING,
        'error':        logging.ERROR,
        'critical':     logging.CRITICAL,
        'fatal':        logging.FATAL,
        }
    logging_level = mapping.get(log_level, None)
    if logging_level is None:
        raise ValueError('Unknown level supplied.')

    return logging_level


def main_column_list() -> List[str]:
    """Return the full list of permissible column names."""
    return [
        'id',
        'user_id',
        'aliasable_id',
        'aliasable_type',
        'local_part',
        'extension',
        'domain',
        'email',
        'active',
        'description',
        'emails_forwarded',
        'emails_blocked',
        'emails_replied',
        'emails_sent',
        'recipients',
        'created_at',
        'updated_at',
        'deleted_at',
        ]


def validate_user_column_selection(selection: List[str]) -> bool:
    """Validate the list of supplied columns against the master list."""
    logger = logging.getLogger('email-info-fetcher')
    main_list = main_column_list()
    for column_name in selection:
        if column_name not in main_list:
            logger.warning('Column "%s" not in main list', column_name)
            return False
        else:
            logger.debug('Column "%s" in main list', column_name)
    return True


if __name__ == '__main__':
    parser = argument_parser_factory()
    args = parser.parse_args()

    logging_level = logging_level_from_string(args.log_level)
    logger_factory(logging_level)
    logger = logging.getLogger('email-info-fetcher')

    if args.columns is None:
        column_names = main_column_list()
    else:
        column_names = [column_name.strip() for column_name in args.columns.split(',')]
        if validate_user_column_selection(column_names) is False:
            exit(1)

    main(args.token, args.filename, column_names)
