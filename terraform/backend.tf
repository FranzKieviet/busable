terraform {
  backend "s3" {
    bucket         = "franzkieviet-infra-terraform"
    key            = "busable/terraform.tfstate"
    region         = "us-west-2"
    dynamodb_table = "franzkieviet-infra-terraform"
    encrypt        = true
  }
}