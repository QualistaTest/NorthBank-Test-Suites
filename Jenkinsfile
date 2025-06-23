pipeline {
    agent any

    environment {
        QASE_PROJECT_CODE = credentials('QASE_PROJECT_CODE')
        QASE_API_TOKEN = credentials('QASE_API_TOKEN')
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
                sh '''
                pkill -f chrome || true
                . /opt/robot-env/bin/activate
                robot -d results --output results/output.xml --xunit results/xunit.xml robot/tests
                '''
            }
        }

        stage('Publish Robot Report') {
            steps {
                robot outputPath: 'results'
            }
        }

        stage('Push to Qase') {
            steps {
                sh '''
                . /opt/robot-env/bin/activate
                pip install requests
                python3 scripts/push_to_qase.py
                '''
            }
        }
    }
}
