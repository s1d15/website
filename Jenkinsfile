pipeline {
    agent any

    stages {
        stage('Build') {
            steps {
                script {
                    env.GIT_COMMIT_SHORT = bat(
                        script: '@git rev-parse --short=7 HEAD',
                        returnStdout: true
                    ).trim()

                    env.IMAGE_VERSION = "build-${env.BUILD_NUMBER}-${env.GIT_COMMIT_SHORT}"

                    env.REGISTRY_IMAGE = "localhost:5000/hardhat-website:${env.IMAGE_VERSION}"

                    echo "Building image version: ${env.IMAGE_VERSION}"
                    echo "Registry artifact: ${env.REGISTRY_IMAGE}"
                }

                bat 'docker compose -p hardhat-registry -f docker-compose.registry.yml up -d'

                bat 'curl --fail --retry 10 --retry-delay 2 --retry-all-errors http://localhost:5000/v2/'

                bat 'docker compose build web'

                bat 'docker tag hardhat-website:ci hardhat-website:%IMAGE_VERSION%'

                bat 'docker tag hardhat-website:%IMAGE_VERSION% localhost:5000/hardhat-website:%IMAGE_VERSION%'

                bat 'docker push localhost:5000/hardhat-website:%IMAGE_VERSION%'

                bat '''
                    @echo Jenkins Build: %BUILD_NUMBER%> build-info.txt
                    @echo Git Commit: %GIT_COMMIT_SHORT%>> build-info.txt
                    @echo Docker Image: hardhat-website:%IMAGE_VERSION%>> build-info.txt
                    @echo Registry Image: localhost:5000/hardhat-website:%IMAGE_VERSION%>> build-info.txt
                    @docker image inspect ^
                    hardhat-website:%IMAGE_VERSION% ^
                    --format "Image ID: {{.Id}}" >> build-info.txt
                '''

                archiveArtifacts(artifacts: 'build-info.txt', fingerprint: true)

                bat 'docker images hardhat-website'
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

        stage('Quality Gate') {
            steps {
                timeout(time: 5, unit: 'MINUTES') {
                    waitForQualityGate abortPipeline: true
                }
            }
        }

        stage('Security') {
            steps {
                bat 'docker compose run --rm -e SECRET_KEY=jenkins-test-secret-key web bandit -r home utils -x home/tests -ll'

            bat '''
                docker run --rm ^
                -v /var/run/docker.sock:/var/run/docker.sock ^
                aquasec/trivy:0.74.0 ^
                image ^
                --severity HIGH,CRITICAL ^
                hardhat-website:ci
            '''
            }
        }

        stage('Deploy') {
            steps {
                bat 'docker compose -p hardhat-staging -f docker-compose.staging.yml up -d'

                bat 'curl --fail --retry 12 --retry-delay 5 http://localhost:8082'
            }
        }

        stage('Release') {
            steps {
                script {
                    env.RELEASE_TAG = "release-${env.BUILD_NUMBER}"
                }

                bat 'docker tag hardhat-website:ci hardhat-website:%RELEASE_TAG%'

                bat '''
                    set IMAGE_TAG=%RELEASE_TAG%&& docker compose ^
                    -p hardhat-production ^
                    -f docker-compose.production.yml ^
                    up -d
                '''

                bat '''
                    curl --fail ^
                    --retry 12 ^
                    --retry-delay 5 ^
                    http://localhost:8083/
                '''
            }
        }

        stage('Monitoring') {
            steps {
                bat 'docker compose -p hardhat-monitoring -f docker-compose.monitoring.yml up -d'

                bat 'curl --fail --retry 12 --retry-delay 5 http://localhost:9090/-/healthy'

                bat 'curl --fail --retry 12 --retry-delay 5 http://localhost:3000/api/health'

                bat 'curl -s "http://localhost:9115/probe?target=http://nginx:80/&module=http_2xx" | findstr /C:"probe_success 1"'
            }
        }
    }
}