terraform {
  backend "s3" {
    bucket         = "franzkieviet-infra-terraform"
    key            = "{var.project-name}/terraform.tfstate"
    region         = "us-west-2"
    dynamodb_table = "franzkieviet-infra-terraform"
    encrypt        = true
  }
}