#!groovy
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
        string(name: 'GIT_TARGET', defaultValue: 'main', description:'When checking out METTA, what target to pick. Can be a tag, branch or commit id.')
        choice(name: 'TEST_SUITE', choices: ['dummy', 'sanity', 'upgrade', 'cncf', 'docker-k8s-helm'], description: 'Pick a test suite to run')
        text(name: 'METTA_CONFIGJSON', description: 'Include JSON config to override config options.  This will be consumed as an ENV variable.')
    }
    environment {
        DOCKER_BUILDKIT = '1'
        METTA_CONFIGJSON="${params.METTA_CONFIGJSON}"
        METTA_VARIABLES_ID="ci-${params.TEST_SUITE}-${env.BUILD_NUMBER}"
        METTA_USER_ID="sandbox-ci"
    }
    stages {
        stage('Test Execute') {
            when { not { changeRequest() } }
            steps {
                container('docker') {
                    script {
                        currentBuild.displayName = "${params.TEST_SUITE} (${params.GIT_TARGET})"

                        // Allow this jenkinsfile to be run without job SCM configured
                        if (!fileExists('setup.cfg')) {
                            git branch: "${params.GIT_TARGET}", url: 'https://github.com/james-nesbitt/metta.git'
                        }

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

                            dir("suites/${params.TEST_SUITE}") {

                                try {

                                    sh(
                                        label: "Running sanity test",
                                        script: """
                                            pytest -s --junitxml=reports/junit.xml --html=reports/pytest.html
                                        """
                                    )

                                } catch (Exception e) {

                                    dir('error') {
                                        try {
                                            sh(
                                                label: "Exporting metta debug information",
                                                script: """
                                                    metta config get metta > metta.config.metta.json
                                                    metta config get environment > metta.config.environment.json
                                                    metta config get variables > metta.config.variables.json
                                                    metta contrib terraform info --deep > metta.contrib.terraform.info.json
                                                    metta contrib launchpad info --deep > metta.contrib.launchpad.info.json
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


                                    archiveArtifacts artifacts: '.metta/*,error/*', allowEmptyArchive: true

                                    currentBuild.result = 'FAILURE'

                                } finally {

                                    archiveArtifacts artifacts: 'reports', allowEmptyArchive: true
                                    archiveArtifacts artifacts: 'results', allowEmptyArchive: true

                                    if ( fileExists('reports/junit.xml') ) {
                                        junit 'reports/junit.xml'
                                    }
                                    publishHTML (target : [
                                        allowMissing: false,
                                        alwaysLinkToLastBuild: true,
                                        keepAll: true,
                                        reportFiles: 'pytest.html',
                                        reportDir: 'reports',
                                        reportName: 'PyTest Report'
                                    ])

                                }
                            }
                        }

                    }
                }
            }
        }
    }
}
