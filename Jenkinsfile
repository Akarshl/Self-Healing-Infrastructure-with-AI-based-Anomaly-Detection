pipeline {
    agent any
    parameters {
        choice(name: 'TF_ACTION', choices: ['plan', 'apply', 'destroy'])
        choice(name: 'INSTANCE_TYPE', choices: ['t3.small', 't3.micro'])
        string(name: 'INSTANCE_NAME', defaultValue: 'Capstone')
    }

    stages {
        stage('Initialize') {
            steps {
                // Wipe old plugins to save space/RAM and prevent corruption
                sh "rm -rf .terraform"
                sh "terraform init"
            }
        }

        stage('Terraform Execution') {
            steps {
                // Bind both the AWS file AND the SSH Public Key secret
                withCredentials([
                    file(credentialsId: 'aws-credentials-file', variable: 'SECRET_FILE_PATH'),
                    string(credentialsId: 'machine-public-key', variable: 'PUB_KEY')
                ]) {
                    script {
                        // Extract AWS keys
                        def accessKey = sh(script: "grep aws_access_key_id ${SECRET_FILE_PATH} | cut -d' ' -f3", returnStdout: true).trim()
                        def secretKey = sh(script: "grep aws_secret_access_key ${SECRET_FILE_PATH} | cut -d' ' -f3", returnStdout: true).trim()

                        withEnv([
                            "AWS_ACCESS_KEY_ID=${accessKey}",
                            "AWS_SECRET_ACCESS_KEY=${secretKey}",
                            "AWS_DEFAULT_REGION=us-east-1",
                            "TF_VAR_public_key_data=${env.PUB_KEY}", // Injected automatically
                            "TF_LOG=ERROR"
                        ]) {
                            def tfArgs = "-var='instance_type=${params.INSTANCE_TYPE}' -var='instance_name=${params.INSTANCE_NAME}'"
                            
                            sh "terraform ${params.TF_ACTION} -auto-approve ${tfArgs}"
                        }
                    }
                }
            }
        }
    }
    
    post {
        always {
            // Clean up to keep local 8GB system healthy
            sh "rm -rf .terraform"
            cleanWs()
        }
    }
}
