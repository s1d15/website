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
                bat 'docker compose run --rm web python manage.py test home.tests.test_user_blog_crud'
            }
        }
    }
}