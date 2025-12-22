pipeline {
    agent any
    
    parameters {
        choice(name: 'TF_ACTION', choices: ['plan', 'apply', 'destroy'], description: 'Select Terraform Action')
        choice(name: 'INSTANCE_TYPE', choices: ['t3.small', 't3.micro'], description: 'Select EC2 Size')
        string(name: 'INSTANCE_NAME', defaultValue: 'my-ec2-machine', description: 'Name tag for the EC2 instance')
        password(name: 'SSH_PUBLIC_KEY', description: 'Paste the content of your id_rsa.pub')
    }

    stages {
        stage('Checkout') {
            steps {
                // Pulls the main.tf, variables.tf, etc., from your Git repo
                checkout scm
            }
        }

        stage('Terraform Execution') {
            steps {
                // Connect to the AWS secret file you created in Jenkins
                withCredentials([file(credentialsId: 'aws-credentials-file', variable: 'SECRET_FILE_PATH')]) {
                    script {
                        // 1. Setup AWS Environment for the Terraform Provider
                        env.AWS_SHARED_CREDENTIALS_FILE = "${SECRET_FILE_PATH}"
                        env.AWS_DEFAULT_REGION = "us-east-1" 

                        // 2. Initialize Terraform
                        sh "terraform init"

                        // 3. Use withEnv to safely handle the SSH Public Key.
                        // Terraform automatically maps TF_VAR_xyz to the variable "xyz"
                        withEnv(["TF_VAR_public_key_data=${params.SSH_PUBLIC_KEY}"]) {
                            
                            // Define other variables as a string
                            def tfArgs = "-var='instance_type=${params.INSTANCE_TYPE}' " +
                                         "-var='instance_name=${params.INSTANCE_NAME}'"
                            
                            if (params.TF_ACTION == 'plan') {
                                echo "Running Terraform Plan..."
                                sh "terraform plan ${tfArgs}"
                            } 
                            else if (params.TF_ACTION == 'apply') {
                                echo "Running Terraform Apply..."
                                sh "terraform apply -auto-approve ${tfArgs}"
                            }
                            else if (params.TF_ACTION == 'destroy') {
                                echo "Running Terraform Destroy..."
                                sh "terraform destroy -auto-approve ${tfArgs}"
                            }
                        }
                    }
                }
            }
        }
    }
    
    post {
        always {
            // Clean up the temporary environment variables
            cleanWs()
        }
    }
}
