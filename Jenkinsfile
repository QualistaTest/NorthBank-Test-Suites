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

        stage('Upload to Xray') {
            steps {
xrayImportResult(
  serverInstance: 'xray-cloud',
  resultFile: 'results/output.xml',
  testFormat: 'ROBOT',
  projectKey: 'SCRUM',
  testExecutionKey: ''
)
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

            script {
                def xml = readFile('results/xunit.xml')
                def parser = new XmlParser()
                def testSuite = parser.parseText(xml)
                def attrs = testSuite.attributes()

                def total = attrs['tests']?.toInteger() ?: 0
                def failures = attrs['failures']?.toInteger() ?: 0
                def skipped = attrs['skipped']?.toInteger() ?: 0
                def passed = total - failures - skipped

                env.TEST_SUMMARY = "✅ ${passed} passed, ❌ ${failures} failed, ⚠️ ${skipped} skipped"
            }

            jiraComment issueKey: "${env.JIRA_ISSUE_KEY}", body: """
🔁 *Build completed:* [View Build](${env.BUILD_URL})

📊 *Test Summary:* ${env.TEST_SUMMARY}
"""
        }
    }
}
