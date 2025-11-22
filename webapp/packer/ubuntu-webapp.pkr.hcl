packer {
  required_plugins {
    amazon = {
      source  = "github.com/hashicorp/amazon"
      version = ">= 1.5.0"
    }
  }
}

# -----------------------
# Variables
# -----------------------
variable "aws_region" {
  type    = string
  default = "us-east-2"
}

variable "demo_account_id" {
  type    = string
  default = ""
}

variable "app_port" {
  type    = number
  default = 8000
}

variable "artifact_path" {
  type    = string
  default = "../app.zip"
}

variable "envfile_path" {
  type    = string
  default = "../.env"
}

# -----------------------
# Builder Configuration
# -----------------------
source "amazon-ebs" "ubuntu24" {
  region        = var.aws_region
  instance_type = "t2.micro"
  ssh_username  = "ubuntu"

  # Canonical official Ubuntu 24.04 LTS (Noble Numbat) - us-east-2
  source_ami = "ami-09fc502518063b6c2"

  ami_name        = "csye6225-webapp-ubuntu24-{{timestamp}}"
  ami_description = "Django + MySQL + Cloudwatch image for CSYE6225"
  ami_users       = [var.demo_account_id] # Auto-share with demo account
  ami_groups      = []                    # Keep private
  ena_support     = true

  # Volume configuration
  launch_block_device_mappings {
    device_name           = "/dev/sda1"
    volume_size           = 25
    volume_type           = "gp2"
    delete_on_termination = true
  }
}

# -----------------------
# Build Process
# -----------------------
build {
  name    = "csye6225-webapp"
  sources = ["source.amazon-ebs.ubuntu24"]

  # Upload required files
  provisioner "file" {
    source      = "${var.artifact_path}"
    destination = "/tmp/app.zip"
  }

  # Copy .env (for testing or defaults)
  provisioner "file" {
    source      = "${var.envfile_path}"
    destination = "/tmp/.env"
  }

  # Copy setup.sh
  provisioner "file" {
    source      = "../scripts/setup.sh"
    destination = "/tmp/setup.sh"
  }

  # Upload CloudWatch Agent config JSON
  provisioner "file" {
    source      = "../scripts/amazon-cloudwatch-agent.json"
    destination = "/tmp/amazon-cloudwatch-agent.json"
  }

  # Run setup and install CloudWatch Agent
  provisioner "shell" {
    inline = [
      "echo 'Updating system packages...'",
      "sudo apt-get update -y",
      "sudo apt-get install -y unzip curl",

      "echo 'Running setup.sh...'",
      "sudo chmod +x /tmp/setup.sh",
      "sudo /tmp/setup.sh",

      "echo 'Installing CloudWatch Agent...'",
      "curl -o /tmp/cwagent.deb https://s3.amazonaws.com/amazoncloudwatch-agent/ubuntu/amd64/latest/amazon-cloudwatch-agent.deb",
      "sudo dpkg -i /tmp/cwagent.deb",

      "echo 'Placing CloudWatch configuration file...'",
      "sudo mkdir -p /opt/aws/amazon-cloudwatch-agent/etc/",
      "sudo cp /tmp/amazon-cloudwatch-agent.json /opt/aws/amazon-cloudwatch-agent/etc/amazon-cloudwatch-agent.json",
      "sudo chmod 644 /opt/aws/amazon-cloudwatch-agent/etc/amazon-cloudwatch-agent.json",
      "sudo chown root:root /opt/aws/amazon-cloudwatch-agent/etc/amazon-cloudwatch-agent.json",

      "echo 'Enabling CloudWatch service...'",
      "sudo systemctl enable amazon-cloudwatch-agent.service",

      "echo 'Starting and validating CloudWatch agent config...'",
      "sudo /opt/aws/amazon-cloudwatch-agent/bin/amazon-cloudwatch-agent-ctl -a fetch-config -m ec2 -c file:/opt/aws/amazon-cloudwatch-agent/etc/amazon-cloudwatch-agent.json -s",

      "echo 'Restarting CloudWatch agent to apply configuration...'",
      "sudo systemctl restart amazon-cloudwatch-agent",

      "echo 'CloudWatch agent setup completed successfully!'"
    ]
  }

}
