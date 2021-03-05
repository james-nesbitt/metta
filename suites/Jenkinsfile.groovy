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
            image: jamesnmirantis/dockerized-builds:0.1.9
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
        choice(name: 'TEST_SUITE', choices: ['sanity', 'upgrade'], description: 'Pick a test suite to run')
        booleanParam(name: 'DEBUG_BUILD', defaultValue: false, description: 'Make output verbose')
    }
    environment {
        DOCKER_BUILDKIT = '1'
    }
    stages {
        stage('Build') {
            when { not { changeRequest() } }
            environment {
              METTA_VARIABLES_ID="sandbox-metta-${env.BUILD_NUMBER}"
            }
            steps {
                container('docker') {
                    script {
                        git branch: 'main', url: 'https://github.com/james-nesbitt/metta.git'

                        sh(
                            label: "Installing metta (pip)",
                            script: """
                              pip install --upgrade .
                            """
                        )

                        withCredentials([
                            [ $class: 'AmazonWebServicesCredentialsBinding', credentialsId: 'aws-infra-test', accessKeyVariable: 'AWS_ACCESS_KEY_ID', secretKeyVariable: 'AWS_SECRET_ACCESS_KEY'],
                            usernamePassword(credentialsId: 'dockerhub-ci', usernameVariable: 'REGISTRY_USERNAME', passwordVariable: 'REGISTRY_PASSWORD')
                        ]) {

                            dir("suites/${params.TEST_SUITE}") {

                                try {


                                    sh(
                                        label: "Running sanity test",
                                        script: """
                                            pytest ${params.DEBUG_BUILD ? '-s' : ''} --junitxml=./reports/${env.METTA_VARIABLES_ID}.pytest_junit.xml --html=./reports/${env.METTA_VARIABLES_ID}.pytest_report.html
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

                                }
                            }
                        }

                    }
                }
            }
        }
    }
}
