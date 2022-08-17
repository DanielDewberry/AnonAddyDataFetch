#!/usr/bin/env python3
# coding: utf-8

"""Fetch AnonAddy data and generate a CSV output file."""

import argparse
import csv
import logging

import requests


def argument_parser_factory():
    """Create the argument parser."""
    parser = argparse.ArgumentParser()
    parser.add_argument('token', help='The AnonAddy API token')
    parser.add_argument('filename', help='The filename to overwrite with CSV data')
    parser.add_argument('--log-level',
                        choices=['debug', 'info', 'warning', 'error', 'critical'],
                        default='info',
                        help='The logging level which will affect reporting information')
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

    base_url = 'https://app.anonaddy.com/api/v1/aliases'
    params = {'page[size]': page_size,
              'page[number]': page_number,
              }
    headers = {'Content-Type': 'application/json',
               'X-Requested-With': 'XMLHttpRequest',
               'Authorization': f'Bearer {token}',
               }
    logger.info('Fetching page %s', page_number)
    return requests.get(base_url, params=params, headers=headers)


def perform_fetches(token: str):
    """Coordinate all data fetches until no data is returned."""
    logger = logging.getLogger('email-info-fetcher')

    data_list = [
        ('email', 'description'),
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
            data_list.append((datum['email'], datum['description']))

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


def main(token: str, filename: str):
    """Application entrypoint."""
    logger = logging.getLogger('email-info-fetcher')
    logger.info('Startup')
    data = perform_fetches(token)
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


if __name__ == '__main__':
    parser = argument_parser_factory()
    args = parser.parse_args()

    logging_level = logging_level_from_string(args.log_level)
    logger_factory(logging_level)

    main(args.token, args.filename)
