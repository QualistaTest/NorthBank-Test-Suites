pipeline {
    agent any

    environment {
        QASE_PROJECT_CODE = credentials('QASE_PROJECT_CODE')
        QASE_API_TOKEN = credentials('QASE_API_TOKEN')
        JIRA_ISSUE_KEY = 'SCRUM-3'
    }

    stages {
        stage('Checkout') {
            steps {
                git credentialsId: '905f8175-0bda-480f-8607-df38125d9eb1',
                    url: 'https://github.com/QualistaTest/NorthBank-Test-Suites.git',
                    branch: 'main'
            }
        }

        stage('Run Robot Tests') {
            steps {
                script {
                    def exitCode = sh(
                        script: '''
                            pkill -f chrome || true
                            . /opt/robot-env/bin/activate
                            robot -d results --output output.xml --xunit xunit.xml --log log.html --report report.html robot/tests || true
                        ''',
                        returnStatus: true
                    )
                    echo "Robot tests finished with exit code: ${exitCode}"
                    if (exitCode != 0) {
                        currentBuild.result = 'UNSTABLE'
                    }
                }
            }
        }

        stage('Publish Robot Report') {
            steps {
                robot outputPath: 'results', outputFileName: 'output.xml'
            }
        }

        stage('Push to Qase') {
            steps {
                sh '''
                    . /opt/robot-env/bin/activate
                    python3 scripts/push_to_qase.py
                '''
            }
        }
    }

    post {
    always {
        archiveArtifacts artifacts: 'results/**/*.*', fingerprint: true

        jiraComment issueKey: "${env.JIRA_ISSUE_KEY}", body: "🔁 Build completed: ${env.BUILD_URL}"
    }
       }

          }
}
