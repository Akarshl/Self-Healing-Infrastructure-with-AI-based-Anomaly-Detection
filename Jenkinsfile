pipeline {
    agent any
    parameters {
        choice(name: 'TF_ACTION', choices: ['plan', 'apply', 'destroy'])
        choice(name: 'INSTANCE_TYPE', choices: ['t3.micro', 't3.small'])
        string(name: 'INSTANCE_NAME', defaultValue: 'my-ec2-machine')
        password(name: 'SSH_PUBLIC_KEY', description: 'AAAAB3NzaC1yc2EAAAADAQABAAABAQCr382LNJrqSc9JPo3CrVxpfhkZ+3ropSsY
knkJaB+5FWbil81BIVoYSojQATuKzoK3zyn55TI+tIjK/TAZ0y9ficbbow4h1ntB
oMBmNL+VAUzPxKYwJOJ/M3o8gR0TrGbi4WYPzeDNLnzB8o9yMnnqAMPziAUOBJBs
OlvBW6hbgGWFkZaWYWqLcgQx307bWBnG6JQZVihW5b+740OvNrxnOljan5QOSaD7
J8npUPAs2UHcn4vou8Ex7wI/rFfW38LVQhsCsZewbDDePwZzfWCSS5C2ndau0tfk
yd1dNHCSiufOZx4fv+BabQeCHXEihGs1D3VzO+RURl6ad2Uy91bh')
    }
    stages {
        stage('Terraform') {
            steps {
                // 'credentialsId' MUST match the ID in your credentials.xml: aws-credentials-file
                // 'variable' creates a temp environment variable holding the file path
                withCredentials([file(credentialsId: 'aws-credentials-file', variable: 'SECRET_FILE_PATH')]) {
                    script {
                        // We tell Terraform to use this specific file for authentication
                        env.AWS_SHARED_CREDENTIALS_FILE = "${SECRET_FILE_PATH}"
                        
                        // If your credentials file doesn't define a region, set it here
                        env.AWS_DEFAULT_REGION = "us-east-1" 

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
