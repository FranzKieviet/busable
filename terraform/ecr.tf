resource "aws_ecr_repository" "busable_api" {
  name                 = "busable-api"
  image_tag_mutability = "MUTABLE"
  force_delete         = true

  image_scanning_configuration {
    scan_on_push = true
  }
}