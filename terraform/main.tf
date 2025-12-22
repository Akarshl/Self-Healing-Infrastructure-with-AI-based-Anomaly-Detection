provider "aws" {
  region = var.aws_region
}

# 1. Create Security Group
resource "aws_security_group" "jenkins_sg" {
  name        = "${var.instance_name}-sg"
  description = "Allow SSH and K8s"

  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    from_port   = 30000
    to_port     = 32767
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port = 0
    to_port   = 0
    protocol  = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

# 2. Create Key Pair using the string passed from Jenkins
resource "aws_key_pair" "jenkins_key" {
  key_name   = "${var.instance_name}-key"
  public_key = var.public_key_data
}

# 3. Create EC2 Instance
resource "aws_instance" "app_server" {
  ami                    = "ami-0e2c8ccd4e0269736" # Ubuntu 22.04 LTS
  instance_type          = var.instance_type
  key_name               = aws_key_pair.jenkins_key.key_name
  vpc_security_group_ids = [aws_security_group.jenkins_sg.id]

  tags = { Name = var.instance_name }
}
