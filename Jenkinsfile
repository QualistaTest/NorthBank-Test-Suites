pipeline {
    agent any

    stages {
        stage('Checkout') {
            steps {
                git credentialsId: '905f8175-0bda-480f-8607-df38125d9eb1', url: 'https://github.com/QualistaTest/NorthBank-Test-Suites.git', branch: 'main'
            }
        }

        stage('Install Robot Framework') {
            steps {
                sh '''
                apt-get update
                apt-get install -y python3-pip
                pip3 install robotframework
                '''
            }
        }

        stage('Run Robot Tests') {
            steps {
                sh 'robot -d results tests/'
            }
        }

        stage('Publish Robot Report') {
            steps {
                robot outputPath: 'results'
            }
        }
    }
}
