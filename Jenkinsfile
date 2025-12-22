pipeline {
    agent any
    
    // Global environment variables to ensure Terraform always sees the region
    environment {
        AWS_DEFAULT_REGION = "us-east-1"
    }

    parameters {
        choice(name: 'TF_ACTION', choices: ['plan', 'apply', 'destroy'], description: 'Select Terraform Action')
        choice(name: 'INSTANCE_TYPE', choices: ['t3.small', 't3.micro'], description: 'Select EC2 Size')
        string(name: 'INSTANCE_NAME', defaultValue: 'my-ec2-machine', description: 'Name tag for the EC2 instance')
        password(name: 'SSH_PUBLIC_KEY', description: 'Paste the content of your id_rsa.pub')
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Terraform Execution') {
            steps {
                // Connect to the secret file ID 'aws-credentials-file'
                withCredentials([file(credentialsId: 'aws-credentials-file', variable: 'SECRET_FILE_PATH')]) {
                    script {
                        // Force Terraform to look at the decrypted file path
                        // We use env.XXX to ensure it persists for the sh steps below
                        env.AWS_SHARED_CREDENTIALS_FILE = "${SECRET_FILE_PATH}"

                        sh "terraform init"

                        // Use withEnv to safely inject the SSH key into the environment
                        // This prevents the "Syntax error: '(' unexpected"
                        withEnv(["TF_VAR_public_key_data=${params.SSH_PUBLIC_KEY}"]) {
                            
                            def tfArgs = "-var='instance_type=${params.INSTANCE_TYPE}' " +
                                         "-var='instance_name=${params.INSTANCE_NAME}'"
                            
                            if (params.TF_ACTION == 'plan') {
                                sh "terraform plan ${tfArgs}"
                            } 
                            else {
                                // apply or destroy
                                sh "terraform ${params.TF_ACTION} -auto-approve ${tfArgs}"
                            }
                        }
                    }
                }
            }
        }
    }
}
