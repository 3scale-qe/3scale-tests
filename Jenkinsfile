pipeline {
    agent { 
        docker { image 'mganisin/python4jenkins' } 
    }
    post {
        failure { updateGitlabCommitStatus name: 'build', state: 'failed' }
        success { updateGitlabCommitStatus name: 'build', state: 'success' } 
    }
    options { gitLabConnection('gitlab.cee.redhat.com') }
    stages {
        stage('quality-check') {
            steps {
                sh 'make clean commit-acceptance'
            } 
        }
    } 
}
