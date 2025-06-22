pipeline {
    agent any

    stages {
        stage('Checkout') {
            steps {
                git credentialsId: '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', url: 'https://github.com/QualistaTest/NorthBank-Test-Suites.git', branch: 'main'
            }
        }

        stage('Install Robot Framework') {
            steps {
                sh '''
                sudo apt update
                sudo apt install -y python3-pip
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
