pipeline {
    agent any
    
    parameters {
        choice(name: 'TF_ACTION', choices: ['plan', 'apply', 'destroy'], description: 'Select Terraform Action')
        choice(name: 'INSTANCE_TYPE', choices: ['t3.small', 't3.micro'], description: 'Select EC2 Size')
        string(name: 'INSTANCE_NAME', defaultValue: 'Capstone', description: 'Name tag for the EC2 instance')
    }

    stages {
        stage('Initialize') {
            steps {
                script {
                    // Clean old state/plugins to prevent "Plugin did not respond" OOM errors
                    sh "rm -rf .terraform"
                    sh "terraform init"
                }
            }
        }

        stage('Terraform Execution') {
            steps {
                withCredentials([file(credentialsId: 'aws-credentials-file', variable: 'SECRET_FILE_PATH')]) {
                    script {
                        // Extract AWS keys from the secret file
                        def accessKey = sh(script: "grep aws_access_key_id ${SECRET_FILE_PATH} | cut -d' ' -f3", returnStdout: true).trim()
                        def secretKey = sh(script: "grep aws_secret_access_key ${SECRET_FILE_PATH} | cut -d' ' -f3", returnStdout: true).trim()

                        withEnv([
                            "AWS_ACCESS_KEY_ID=${accessKey}",
                            "AWS_SECRET_ACCESS_KEY=${secretKey}",
                            "AWS_DEFAULT_REGION=us-east-1",
                            "TF_LOG=ERROR" // Minimizes memory logging overhead
                        ]) {
                            def tfArgs = "-var='instance_type=${params.INSTANCE_TYPE}' -var='instance_name=${params.INSTANCE_NAME}'"
                            
                            if (params.TF_ACTION == 'plan') {
                                sh "terraform plan ${tfArgs}"
                            } else {
                                sh "terraform ${params.TF_ACTION} -auto-approve ${tfArgs}"
                            }
                        }
                    }
                }
            }
        }
    }
}
