pipeline {
    agent any
    parameters {
        choice(name: 'TF_ACTION', choices: ['plan', 'apply', 'destroy'])
        choice(name: 'INSTANCE_TYPE', choices: ['t3.micro', 't3.small'])
        string(name: 'INSTANCE_NAME', defaultValue: 'my-ec2')
        password(name: 'SSH_PUBLIC_KEY', description: 'SSH Public Key')
    }
    stages {
        stage('Terraform') {
            steps {
                // 'credentialsId' must match the ID you gave the Secret File in Jenkins
                withCredentials([file(credentialsId: 'aws-credentials-file', variable: 'AWS_CREDENTIALS_PATH')]) {
                    script {
                        // EXPLICITLY set the environment variable Terraform looks for
                        env.AWS_SHARED_CREDENTIALS_FILE = "${AWS_CREDENTIALS_PATH}"
                        
                        def tfVars = "-var='instance_type=${params.INSTANCE_TYPE}' " +
                                     "-var='instance_name=${params.INSTANCE_NAME}' " +
                                     "-var='public_key_data=${params.SSH_PUBLIC_KEY}'"
                        
                        sh "terraform init"
                        
                        if (params.TF_ACTION == 'plan') {
                            sh "terraform plan ${tfVars}"
                        } else {
                            sh "terraform ${params.TF_ACTION} -auto-approve ${tfVars}"
                        }
                    }
                }
            }
        }
    }
}
