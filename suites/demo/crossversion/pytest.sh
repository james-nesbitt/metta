#!/usr/bin/env bash

# Non-threaded run
pytest -s --junitxml=./reports/junit.xml --html=./reports/report.html $@
# Threaded run
# pytest -s --junitxml=./reports/junit.xml --html=./reports/report.html -n auto --dist loadscope $@
