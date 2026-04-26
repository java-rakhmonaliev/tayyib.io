variable "aws_region" {
  default = "us-east-1"
}

variable "ec2_ami" {
  description = "Ubuntu 22.04 LTS AMI — update for your region"
  default     = "ami-0c7217cdde317cfec"
}

variable "ssh_public_key_path" {
  description = "Path to your SSH public key"
  default     = "~/.ssh/id_ed25519.pub"
}

variable "db_name" {
  default = "tayyib_io"
}

variable "db_user" {
  default = "tayyib_admin"
}

variable "db_password" {
  sensitive = true
}