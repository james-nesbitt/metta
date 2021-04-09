#!groovy
/**
 * Jenkins: Upgrade test suite execute
 *
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
              - name: docker-socket
                emptyDir: {}
              containers:
              - name: docker
                image: jamesnmirantis/dockerized-builds:0.1.12
                command:
                - sleep
                args:
                - 99d
                volumeMounts:
                - name: docker-socket
                  mountPath: /var/run
              - name: docker-daemon
                image: docker:dind
                securityContext:
                  privileged: true
                volumeMounts:
                - name: docker-socket
                  mountPath: /var/run
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
    stages {
        stage('Test Execute') {
            when { not { changeRequest() } }
            environment {
                DOCKER_BUILDKIT = '1'
                TEST_SUITE = "upgrade"
                METTA_CONFIGJSON="${params.METTA_CONFIGJSON}"
                METTA_VARIABLES_ID="ci-upgrade-${env.BUILD_NUMBER}"
                METTA_USER_ID="sandbox-ci"
            }
            steps {
                container('docker') {
                    script {

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
                        dir('suites') {
                            sh(
                                label: "Installing metta-suites",
                                script: """
                                    pip install --upgrade .
                                """
                            )
                        }

                        withCredentials([
                            [ $class: 'AmazonWebServicesCredentialsBinding', credentialsId: 'aws-creds-docker-core', accessKeyVariable: 'AWS_ACCESS_KEY_ID', secretKeyVariable: 'AWS_SECRET_ACCESS_KEY'],
                            usernamePassword(credentialsId: 'docker-hub-generic-up', usernameVariable: 'REGISTRY_USERNAME', passwordVariable: 'REGISTRY_PASSWORD')
                        ]) {

                            dir("suites/${env.TEST_SUITE}") {

                                try {

                                    sh(
                                        label: "Running sanity test",
                                        script: """
                                            pytest -s --junitxml=reports/junit.xml --html=reports/pytest.html ${params.PYTEST_TESTS}
                                        """
                                    )

                                } catch (Exception e) {

                                    dir('error') {
                                        if (METTA_CONFIGJSON != '') {
                                            writeFile file:'metta.config.overrides.json', text:env.METTA_CONFIGJSON
                                        }
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
                                        } catch(Exception edown) {
                                            print "Exception occurred reading catching metta output"
                                        }
                                    }

                                    try {
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

                                } finally {

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
        }
    }
}
