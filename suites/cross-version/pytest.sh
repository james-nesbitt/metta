#!/usr/bin/env bash

pytest -s --junitxml=./reports/junit.xml --html=./reports/report.html -n auto --dist loadscope $@
