resource "aws_ecr_repository" "busable_api" {
  name                 = "busable-api"
  image_tag_mutability = "MUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }
}


resource "aws_apprunner_service" "busable_api" {
  service_name = "busable-api-${var.branch}"

  source_configuration {
    authentication_configuration {
      access_role_arn = aws_iam_role.apprunner_ecr_access.arn
    }

    image_repository {
      image_identifier      = "${aws_ecr_repository.busable_api.repository_url}:latest"
      image_repository_type = "ECR"

      image_configuration {
        port = "8080"

        runtime_environment_variables = {
          "ConnectionStrings__MongoDb" = var.mongodb_uri
          "ASPNETCORE_ENVIRONMENT"     = "Production"
        }
      }
    }

    auto_deployments_enabled = true
  }

  health_check_configuration {
    protocol = "HTTP"
    path     = "/health" # Adjust to a valid route in your API
  }

  depends_on = [aws_iam_role_policy_attachment.apprunner_ecr_access_attachment]
}