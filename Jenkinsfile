pipeline {
    agent any

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
                . /opt/robot-env/bin/activate
                robot -d results robot/tests
                '''
            }
        }

        stage('Publish Robot Report') {
            steps {
                robot outputPath: 'results'
            }
        }
    }
}
