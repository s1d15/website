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
                bat '''
                    if exist TEST-*.xml del /q TEST-*.xml
                    if exist coverage.xml del /q coverage.xml
                '''

                bat 'docker compose exec -T web python -m coverage erase'

                bat '''
                    docker compose exec -T web ^
                    python -m coverage run ^
                    --source=home,utils ^
                    manage.py test ^
                    home.tests.test_user_blog_crud ^
                    home.tests.test_sanitizer ^
                    --testrunner=xmlrunner.extra.djangotestrunner.XMLTestRunner
                '''

                bat 'docker compose exec -T web python -m coverage report -m --fail-under=28'

                bat 'docker compose exec -T web python -m coverage xml -o /app/coverage.xml'
            }

            post {
                always {
                    junit(
                        testResults: 'TEST-*.xml',
                        allowEmptyResults: true
                    )

                    archiveArtifacts(
                        artifacts: 'coverage.xml',
                        fingerprint: true,
                        allowEmptyArchive: true
                    )
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
                echo "Deploying ${env.REGISTRY_IMAGE} to staging"

                withEnv(["DEPLOY_IMAGE=${env.REGISTRY_IMAGE}"]) {

                    bat 'docker pull %DEPLOY_IMAGE%'

                    bat 'docker compose -p hardhat-staging -f docker-compose.staging.yml up -d --no-build'

                    bat 'curl --fail --retry 12 --retry-delay 5 --retry-all-errors http://localhost:8082/'
                }
            }
        }

        stage('Release') {
            steps {
                script {
                    env.RELEASE_TAG = "release-${env.BUILD_NUMBER}"

                    env.RELEASE_IMAGE = "localhost:5000/hardhat-website:${env.RELEASE_TAG}"

                    echo "Promoting ${env.REGISTRY_IMAGE}"
                    echo "Release image: ${env.RELEASE_IMAGE}"
                }

                bat 'docker pull %REGISTRY_IMAGE%'

                bat 'docker tag %REGISTRY_IMAGE% %RELEASE_IMAGE%'

                bat 'docker push %RELEASE_IMAGE%'

                withEnv(["DEPLOY_IMAGE=${env.RELEASE_IMAGE}"]) {

                    bat 'docker pull %DEPLOY_IMAGE%'

                    bat 'docker compose -p hardhat-production -f docker-compose.production.yml up -d --no-build'

                    bat 'curl --fail --retry 12 --retry-delay 5 --retry-all-errors http://localhost:8083/'
                }

                bat '''
                    @echo Jenkins Build: %BUILD_NUMBER%> release-info.txt
                    @echo Git Commit: %GIT_COMMIT_SHORT%>> release-info.txt
                    @echo Source Artifact: %REGISTRY_IMAGE%>> release-info.txt
                    @echo Release Artifact: %RELEASE_IMAGE%>> release-info.txt
                    @docker image inspect ^
                    %RELEASE_IMAGE% ^
                    --format "Image ID: {{.Id}}" >> release-info.txt
                '''

                archiveArtifacts(artifacts: 'release-info.txt',fingerprint: true)
            }
        }

        stage('Monitoring') {
            steps {
                bat 'docker compose -p hardhat-monitoring -f docker-compose.monitoring.yml up -d'

                bat 'curl --fail --retry 12 --retry-delay 5 --retry-all-errors http://localhost:9090/-/ready'

                bat 'curl --fail --retry 12 --retry-delay 5 --retry-all-errors http://localhost:3000/api/health'

                bat 'curl -s "http://localhost:9115/probe?target=http://nginx:80/&module=http_2xx" | findstr /C:"probe_success 1"'
            }
        }
    }
}