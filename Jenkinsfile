pipeline {
    agent any
    
    parameters {
        choice(name: 'TF_ACTION', choices: ['plan', 'apply', 'destroy'])
        choice(name: 'INSTANCE_TYPE', choices: ['t3.small', 't3.micro'])
        string(name: 'INSTANCE_NAME', defaultValue: 'my-ec2-machine')
        password(name: 'SSH_PUBLIC_KEY', description: 'Paste SSH Public Key content')
    }

    stages {
        stage('Terraform Execution') {
            steps {
                withCredentials([file(credentialsId: 'aws-credentials-file', variable: 'SECRET_FILE_PATH')]) {
                    script {
                        // 1. Manually extract keys from your uploaded file
                        // This ensures Terraform gets the keys even if it ignores the file path
                        def accessKey = sh(script: "grep aws_access_key_id ${SECRET_FILE_PATH} | cut -d' ' -f3", returnStdout: true).trim()
                        def secretKey = sh(script: "grep aws_secret_access_key ${SECRET_FILE_PATH} | cut -d' ' -f3", returnStdout: true).trim()

                        // 2. Inject everything into the environment
                        withEnv([
                            "AWS_ACCESS_KEY_ID=${accessKey}",
                            "AWS_SECRET_ACCESS_KEY=${secretKey}",
                            "AWS_DEFAULT_REGION=us-east-1",
                            "TF_VAR_public_key_data=${params.SSH_PUBLIC_KEY}"
                        ]) {
                            
                            sh "terraform init"

                            def tfArgs = "-var='instance_type=${params.INSTANCE_TYPE}' " +
                                         "-var='instance_name=${params.INSTANCE_NAME}'"
                            
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
