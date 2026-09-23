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

                bat '''
                    docker compose up -d db
                '''

                bat '''
                    docker compose run --rm ^
                    -e SECRET_KEY=jenkins-test-secret-key ^
                    web ^
                    python -m coverage erase
                '''

                bat '''
                    docker compose run --rm ^
                    -e SECRET_KEY=jenkins-test-secret-key ^
                    web ^
                    python -m coverage run ^
                    --source=home,utils ^
                    manage.py test ^
                    home.tests.test_user_blog_crud ^
                    home.tests.test_sanitizer ^
                    --testrunner=xmlrunner.extra.djangotestrunner.XMLTestRunner
                '''

                bat '''
                    docker compose run --rm ^
                    -e SECRET_KEY=jenkins-test-secret-key ^
                    web ^
                    python -m coverage report -m --fail-under=28
                '''

                bat '''
                    docker compose run --rm ^
                    -e SECRET_KEY=jenkins-test-secret-key ^
                    web ^
                    python -m coverage xml -o /app/coverage.xml
                '''
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


        stage('Code Quality') {
            steps {
                script {
                    env.SCANNER_HOME = tool 'SonarScanner'
                }

                withSonarQubeEnv('SonarQube') {
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
                echo "Running source-code and container security analysis"

                bat '''
                    docker compose run --rm ^
                    -e SECRET_KEY=jenkins-test-secret-key ^
                    web ^
                    bandit -r home utils ^
                    -x home/tests ^
                    -f json ^
                    -o /app/bandit-report.json ^
                    --exit-zero
                '''

                bat '''
                    docker compose run --rm ^
                    -e SECRET_KEY=jenkins-test-secret-key ^
                    web ^
                    bandit -r home utils ^
                    -x home/tests ^
                    -ll
                '''

                bat 'docker pull %REGISTRY_IMAGE%'

                bat 'docker save %REGISTRY_IMAGE% -o hardhat-image.tar'

                bat '''
                    docker run --rm ^
                    -v "%CD%:/work" ^
                    -v trivy-cache:/root/.cache/trivy ^
                    aquasec/trivy:0.74.0 ^
                    image ^
                    --input /work/hardhat-image.tar ^
                    --scanners vuln ^
                    --severity HIGH,CRITICAL ^
                    --timeout 15m ^
                    --format json ^
                    --output /work/trivy-report.json ^
                    --exit-code 0
                '''

                bat 'if exist hardhat-image.tar del /q hardhat-image.tar'
            }

            post {
                always {
                    archiveArtifacts(
                        artifacts: 'bandit-report.json,trivy-report.json,security-review.md',
                        fingerprint: true,
                        allowEmptyArchive: true
                    )

                    bat 'if exist hardhat-image.tar del /q hardhat-image.tar'
                }
            }
        }
        stage('Deploy') {
            steps {
                script {
                    echo "Deploying ${env.REGISTRY_IMAGE} to staging"

                    def currentStagingContainer = bat(
                        script: '@docker compose -p hardhat-staging -f docker-compose.staging.yml ps -q web',
                        returnStdout: true
                    ).trim()

                    if (currentStagingContainer) {
                        env.PREVIOUS_STAGING_IMAGE = bat(
                            script: "@docker inspect --format=\"{{.Config.Image}}\" ${currentStagingContainer}",
                            returnStdout: true
                        ).trim()

                        echo "Previous staging image: ${env.PREVIOUS_STAGING_IMAGE}"
                    } else {
                        env.PREVIOUS_STAGING_IMAGE = ""
                        echo "No previous staging deployment found."
                    }
                }

                bat 'docker pull %REGISTRY_IMAGE%'

                withEnv(["DEPLOY_IMAGE=${env.REGISTRY_IMAGE}"]) {
                    bat 'docker compose -p hardhat-staging -f docker-compose.staging.yml up -d --no-build'
                }

                bat 'docker compose -p hardhat-staging -f docker-compose.staging.yml ps'

                script {
                    def healthStatus = bat(
                        script: '@curl --fail --retry 12 --retry-delay 5 --retry-all-errors http://localhost:8082/',
                        returnStatus: true
                    )

                    if (healthStatus != 0) {
                        echo "Staging deployment failed health check."

                        if (env.PREVIOUS_STAGING_IMAGE?.trim()) {
                            echo "Rolling back to ${env.PREVIOUS_STAGING_IMAGE}"

                            withEnv(["DEPLOY_IMAGE=${env.PREVIOUS_STAGING_IMAGE}"]) {
                                bat 'docker compose -p hardhat-staging -f docker-compose.staging.yml up -d --no-build'
                            }

                            bat 'curl --fail --retry 12 --retry-delay 5 --retry-all-errors http://localhost:8082/'

                            echo "Rollback completed successfully."
                        } else {
                            echo "No previous staging image available for rollback."
                        }

                        error("Staging deployment failed.")
                    }

                    echo "Staging health check passed."
                }
            }
        }
        stage('Release') {
            steps {
                script {
                    env.RELEASE_TAG = "release-${env.BUILD_NUMBER}"
                    env.RELEASE_IMAGE = "localhost:5000/hardhat-website:${env.RELEASE_TAG}"

                    echo "Promoting tested artifact:"
                    echo "Source: ${env.REGISTRY_IMAGE}"
                    echo "Release: ${env.RELEASE_IMAGE}"
                }

                bat 'docker pull %REGISTRY_IMAGE%'

                bat 'docker tag %REGISTRY_IMAGE% %RELEASE_IMAGE%'

                bat 'docker push %RELEASE_IMAGE%'

                withEnv(["DEPLOY_IMAGE=${env.RELEASE_IMAGE}"]) {
                    bat 'docker pull %DEPLOY_IMAGE%'

                    bat 'docker compose -p hardhat-production -f docker-compose.production.yml up -d --no-build'
                }

                bat 'docker compose -p hardhat-production -f docker-compose.production.yml ps'

                bat 'curl --fail --retry 12 --retry-delay 5 --retry-all-errors http://localhost:8083/'

                bat '''
                    @echo Jenkins Build: %BUILD_NUMBER%> release-info.txt
                    @echo Git Commit: %GIT_COMMIT_SHORT%>> release-info.txt
                    @echo Source Artifact: %REGISTRY_IMAGE%>> release-info.txt
                    @echo Release Tag: %RELEASE_TAG%>> release-info.txt
                    @echo Release Artifact: %RELEASE_IMAGE%>> release-info.txt
                    @docker image inspect ^
                    %RELEASE_IMAGE% ^
                    --format "Image ID: {{.Id}}" >> release-info.txt
                '''

                archiveArtifacts(artifacts: 'release-info.txt', fingerprint: true)
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