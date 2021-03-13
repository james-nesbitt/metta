#!groovy
/**
 * Jenkins: Sanity test suite execute
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
                image: jamesnmirantis/dockerized-builds:0.1.11
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
        timeout(time: 2, unit: 'HOURS')
    }
    parameters {
        string(name: 'BRANCH_NAME', defaultValue: '', description:'When checking out METTA, what target to pick. Can be a tag, branch or commit id.')
        string(name: 'PYTEST_TESTS', description: 'Optionally limit which tests pytest will run. IF empty, all tests will be run.')
        text(name: 'METTA_CONFIGJSON', description: 'Include JSON config to override config options.  This will be consumed as an ENV variable.')
    }
    environment {
        DOCKER_BUILDKIT = '1'
        TEST_SUITE = "sanity"
        METTA_CONFIGJSON="${params.METTA_CONFIGJSON}"
        METTA_VARIABLES_ID="ci-sanity-${env.BUILD_NUMBER}"
        METTA_USER_ID="sandbox-ci"
        PYTEST_TESTS="${params.PYTEST_TESTS}"
        BRANCH_NAME="${params.BRANCH_NAME}"
    }
    stages {
        stage('Test Execute') {
            when { not { changeRequest() } }
            steps {
                container('docker') {
                    script {
                        currentBuild.displayName = "${env.TEST_SUITE} (${env.BRANCH_NAME}) ${env.BUILD_DISPLAY_NAME}"

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
                            [ $class: 'AmazonWebServicesCredentialsBinding', credentialsId: 'aws-infra-test', accessKeyVariable: 'AWS_ACCESS_KEY_ID', secretKeyVariable: 'AWS_SECRET_ACCESS_KEY'],
                            usernamePassword(credentialsId: 'docker-hub-generic-up', usernameVariable: 'REGISTRY_USERNAME', passwordVariable: 'REGISTRY_PASSWORD')
                        ]) {

                            dir("suites/${env.TEST_SUITE}") {

                                try {

                                    sh(
                                        label: "Running sanity test",
                                        script: """
                                            pytest -s --junitxml=reports/junit.xml --html=reports/pytest.html
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