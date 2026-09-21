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
            }
        }
    }
}