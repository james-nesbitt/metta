#!/usr/bin/env bash

python -m pytest --junitxml=./reports/junit.xml --html=./reports/report.html $@
