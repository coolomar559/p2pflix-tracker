# P2PFlix Tracker

This program is the tracker portion of the distributed P2PFlix application.

[![Build Status](https://travis-ci.org/coolomar559/p2pflix-tracker.svg?branch=master)](https://travis-ci.org/coolomar559/p2pflix-tracker)

## Requirements

This project requires:

- Python 3.7 or greater
- pipenv

## Getting started

To install all requirements use `pipenv install`. To install extra requirements for
linting and testing, use `pipenv install --dev`.

## Linting

This project is linted using `flake8` and some related plugins. To lint use `pipenv run
flake8`.

## Testing

This project uses pytest for testing. To run tests, use `pipenv run pytest`. To write
tests, put everything needed in the `tests` directory.

## Running

To run the tracker, use `pipenv run ./tracker.py`
