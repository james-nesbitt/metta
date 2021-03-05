
pip install .

cd sanity && pytest -s --junitxml=./reports/pytest_juni.xml --html=./reports/pytest_report.html
