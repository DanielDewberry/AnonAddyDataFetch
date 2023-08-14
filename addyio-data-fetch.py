#!/usr/bin/env python3
# coding: utf-8

"""Fetch addy.io data and generate a CSV output file."""

import argparse
import csv
import logging
import sys
from typing import Any, Dict, List, Optional

import requests


def argument_parser_factory() -> argparse.ArgumentParser:
    """Create the argument parser."""
    parser = argparse.ArgumentParser()
    parser.add_argument('token', help='The addy.io API token, or the file in which the token is the first line')
    parser.add_argument('output_file', help='The filename to overwrite with CSV data')
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
    page_size: int = 100

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


def perform_fetches(token: str, column_names: List[str]) -> List[List[Any]]:
    """Coordinate all data fetches until no data is returned."""
    logger = logging.getLogger('email-info-fetcher')

    raw_json_records: List[Dict] = []
    page_number: int = 0
    while True:
        page_number += 1
        response = request_page(page_number, token)

        if response.status_code >= 400:
            logger.error('Failed to acquire data. Request yielded response code %s',
                         response.status_code)
            exit(1)

        page_data = response.json()
        page_data: List[Dict] = page_data['data']
        if len(page_data) == 0:
            break

        if column_names is not None:
            for n, datum in enumerate(page_data):
                missing_keys = [column_name for column_name in column_names if datum.get(column_name) is None]
                if len(missing_keys) > 0:
                    logger.error('Missing keys detected on page %s, record %s. Missing keys: [%s]. Aborting',
                                 page_number,
                                 n,
                                 ', '.join(missing_keys))
                    sys.exit(1)
                raw_json_records.append({key: datum[key] for key in column_names})
        else:
            raw_json_records.extend(page_data)

    if column_names is None:
        column_names = sorted({item for record in raw_json_records for item in record.keys()})

    data_list = [column_names]
    for record in raw_json_records:
        data_list.append([record[key] for key in column_names])

    return data_list


def write_data_to_csv(filename, data) -> None:
    """Write the data to the provided filename, as  CSV format.

    Existing data will be truncated.
    """
    logger = logging.getLogger('email-info-fetcher')
    logger.info('Writing to file %s', filename)

    with open(filename, 'w', encoding='UTF8') as fp:
        csv_writer = csv.writer(fp, dialect='excel')
        for record in data:
            csv_writer.writerow(record)


def main(token: str, filename: str, column_names: Optional[List[str]]) -> None:
    """Application entrypoint."""
    logger = logging.getLogger('email-info-fetcher')
    logger.info('Startup')
    data = perform_fetches(token, column_names)
    write_data_to_csv(filename, data)
    logger.info('Done')


def logging_level_from_string(log_level: str) -> int:
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
    logger = logging.getLogger('email-info-fetcher')

    columns: Optional[List[str]] = [s.strip() for s in args.columns.split(',')] if args.columns is not None else None

    try:
        with open(args.token, 'r') as fp:
            token = fp.readline().strip()
            main(token, args.output_file, columns)
    except FileNotFoundError:
        main(args.token, args.output_file, columns)
