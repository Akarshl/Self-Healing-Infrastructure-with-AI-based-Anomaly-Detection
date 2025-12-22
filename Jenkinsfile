pipeline {
    agent any
    parameters {
        choice(name: 'TF_ACTION', choices: ['plan', 'apply', 'destroy'], description: 'Terraform Action')
        choice(name: 'INSTANCE_TYPE', choices: ['t3.small', 't3.micro'], description: 'EC2 Instance Size')
        string(name: 'INSTANCE_NAME', defaultValue: 'my-ec2-machine', description: 'Name Tag')
        password(name: 'SSH_PUBLIC_KEY', description: 'Paste your SSH Public Key content')
    }
    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }
        stage('Terraform') {
            steps {
                withCredentials([file(credentialsId: 'aws-credentials-file', variable: 'AWS_SHARED_CREDENTIALS_FILE')]) {
                    script {
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
