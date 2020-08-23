terraform {
  backend "s3" {
    encrypt        = true
    bucket         = "grocky-tfstate"
    dynamodb_table = "tfstate-lock"
    region         = "us-east-1"
    key            = "resume.rockygray.com/terraform.tfstate"
  }
}

provider "aws" {
  region = "us-east-1"
}

data "terraform_remote_state" "root" {
  backend = "s3"
  config = {
    bucket = "grocky-tfstate"
    region = "us-east-1"
    key    = "rockygray.com/terraform.tfstate"
  }
}

variable "root_domain_name" {
  default = "rockygray.com"
}

variable "sub_domain_name" {
  default = "resume.rockygray.com"
}

output "site_url" {
  value = aws_route53_record.sub.fqdn
}
