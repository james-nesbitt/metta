#!groovy
/**
 * @NOTE this expects to be run from the repo root.
 */
pipeline {
    agent {
        kubernetes {
          yaml """\
            apiVersion: v1
            kind: Pod
            spec:
              volumes:
              containers:
              - name: workspace
                image: jamesnmirantis/dockerized-builds:0.1.12
                command:
                - sleep
                args:
                - 99d
            """.stripIndent()
        }
    }

    options {
        timeout(time: 4, unit: 'HOURS')
    }
    parameters {
        string(name: 'PYTEST_TESTS', defaultValue: '', description: 'Optionally limit which tests pytest will run. IF empty, all tests will be run.')
        text(name: 'METTA_CONFIGJSON', defaultValue: '', description: 'Include JSON config to override config options.  This will be consumed as an ENV variable.')
    }
    environment {
        TEST_SUITE = "cncf"
    }    
    stages {

        stage('Prepare workspace') {
            steps {
                container('workspace') {
                    script {

                        dir("suites/${env.TEST_SUITE}") {

                            GIT_TAG = sh(
                                label: "Confirming git branch",
                                script: """
                                    git describe --tags
                                """,
                                returnStdout: true
                            ).trim()

                            currentBuild.displayName = "${env.TEST_SUITE} (${GIT_TAG}) ${env.BUILD_DISPLAY_NAME}"

                            /** Starting PIP preparation */

                            sh(
                                label: "Installing metta (pip)",
                                script: """
                                    pip install --upgrade .
                                """
                            )

                        }
                    }
                }
            }
        }

        stage('Test Execute') {
            environment {
                METTA_CONFIGJSON="${params.METTA_CONFIGJSON}"
                METTA_VARIABLES_ID="ci-${env.TEST_SUITE}-${env.BUILD_NUMBER}"
                METTA_USER_ID="ci"
            }              
            steps {
                container('workspace') {
                    script {

                        dir("suites/${env.TEST_SUITE}") {

                            withCredentials([
                                [ $class: 'AmazonWebServicesCredentialsBinding', credentialsId: 'aws-creds-docker-core', accessKeyVariable: 'AWS_ACCESS_KEY_ID', secretKeyVariable: 'AWS_SECRET_ACCESS_KEY'],
                                usernamePassword(credentialsId: 'docker-hub-generic-up', usernameVariable: 'REGISTRY_USERNAME', passwordVariable: 'REGISTRY_PASSWORD')
                            ]) {

                                try {

                                    sh(
                                        label: "Running ${env.TEST_SUITE} test",
                                        script: """
                                            pytest -s --junitxml=./reports/junit.xml --html=./reports/report.html ${params.PYTEST_TESTS}
                                        """
                                    )

                                } catch (Exception e) {

                                    dir('error') {
                                        // Build a whole bunch of error data from metta calls

                                        try {
                                            sh(
                                                label: "Exporting metta debug information",
                                                script: """
                                                    metta config get metta > metta.config.metta.json
                                                    metta config get environment > metta.config.environment.json
                                                    metta config get variables > metta.config.variables.json
                                                    metta fixtures info --deep > metta.fixtures.json
                                                """
                                            )

                                            if (METTA_CONFIGJSON != '') {
                                               writeFile file:'metta.config.overrides.json', text:env.METTA_CONFIGJSON
                                            }
                                        } catch(Exception edown) {
                                            print "Exception occurred reading catching metta output"
                                        }
                                    }

                                    try {

                                        // sometimes an exception leaves an orphan cluster
                                        sh(
                                            label: "Terminating resources on exception",
                                            script: """
                                                metta provisioner destroy
                                            """
                                        )
                                    } catch(Exception edown) {
                                        print "Exception occured tearing down"
                                    }

                                    archiveArtifacts artifacts:'.metta/*', allowEmptyArchive: true
                                    archiveArtifacts artifacts:'error/*', allowEmptyArchive: true

                                    currentBuild.result = 'FAILURE'

                                }

                            }

                        }

                    }
                }
            }
        }

        stage('Reporting') {
            steps {
                container('workspace') {

                    dir("suites/${env.TEST_SUITE}") {

                        if (fileExists('reports')) {
                            dir('reports') {
                                archiveArtifacts artifacts:'*', allowEmptyArchive: true

                                if (fileExists('junit.xml')) {
                                    junit 'junit.xml'
                                }
                                if (fileExists('pytest.html')) {
                                    publishHTML (target : [
                                        allowMissing: false,
                                        alwaysLinkToLastBuild: true,
                                        keepAll: true,
                                        reportFiles: 'pytest.html',
                                        reportDir: '.',
                                        reportName: 'PyTest Report'
                                    ])
                                }
                            }
                        }
                        if (fileExists('results')) {
                            archiveArtifacts artifacts: 'results/*', allowEmptyArchive: true
                        }

                    }
 
                }
            }
        }

    }
}
