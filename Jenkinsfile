pipeline {
  agent any
  stages {
    stage('Build') {
      steps {
        sh 'docker build -t aiwarssoc/web-api:latest .'
      }
    }

    stage('Push') {
      steps {
        sh 'docker push aiwarssoc/web-api:latest'
      }
    }

  }
}