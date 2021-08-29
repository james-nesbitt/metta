#!groovy
/**
 * @NOTE this expects to be run from the repo root.
 */
pipeline {
    agent none
    options {
        timeout(time: 4, unit: 'HOURS')
    }
    parameters {
        string(name: 'PYTEST_TESTS', defaultValue: '', description: 'Optionally limit which tests pytest will run. IF empty, all tests will be run.')
        text(name: 'METTA_CONFIGJSON', defaultValue: '', description: 'Include JSON config to override config options.  This will be consumed as an ENV variable.')
    }
    environment {
        TEST_CHANNEL = "prodeng"
        TEST_SUITE = "clients"
    }
    stages {

        stage('Prepare workspace') {
            steps {

                Print "HERE"

            }
        }

    }
}
