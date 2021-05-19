#!/usr/bin/env bash

python -m pytest -s --junitxml=./reports/junit.xml --html=./reports/report.html $@
