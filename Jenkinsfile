pipeline {
    agent any

    stages {
        stage('Build') {
            steps {
                bat 'docker compose build'
            }
        }

        stage('Test') {
            steps {
                bat 'docker compose run --rm -e SECRET_KEY=jenkins-test-secret-key web sh -c "python -m coverage run --source=home,utils manage.py test home.tests.test_user_blog_crud home.tests.test_sanitizer && python -m coverage report -m && python -m coverage xml -o /app/coverage.xml"'

                bat 'if exist coverage.xml (echo coverage.xml FOUND) else (echo coverage.xml MISSING & exit /b 1)'
            }
        }
        stage('Code Quality') {
            steps {
                script {
                    env.SCANNER_HOME = tool 'SonarScanner'
                }

                withSonarQubeEnv('SonarQube') {
                    bat 'echo SonarScanner location: %SCANNER_HOME%'
                    bat '"%SCANNER_HOME%\\bin\\sonar-scanner.bat"'
                }
            }
        }
    }
}