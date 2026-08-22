# --- VPC & Networking Setup ---
data "aws_vpc" "default" {
  default = true
}

data "aws_subnets" "default" {
  filter {
    name   = "vpc-id"
    values = [data.aws_vpc.default.id]
  }
}

# Security group to allow inbound traffic on port 8080
resource "aws_security_group" "ecs_api_sg" {
  name        = "busable-api-sg-${var.branch}"
  description = "Allow HTTP inbound traffic on port 8080 for Busable API"
  vpc_id      = data.aws_vpc.default.id

  ingress {
    description     = "Allow inbound HTTP from ALB"
    from_port       = 8080
    to_port         = 8080
    protocol        = "tcp"
    security_groups = [aws_security_group.alb_sg.id]
}

  egress {
    description = "Allow all outbound traffic (MongoDB, ECR, internet)"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Environment = var.branch
  }
}

resource "aws_ecs_cluster" "busable" {
  name = "busable-cluster-${var.branch}"
}

resource "aws_ecs_task_definition" "busable_api" {
  family                   = "busable-api-${var.branch}"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = "256" # 0.25 vCPU
  memory                   = "512" # 512 MB
  execution_role_arn       = aws_iam_role.ecs_execution_role.arn

  container_definitions = jsonencode([
    {
      name      = "busable-api"
      image     = "${aws_ecr_repository.busable_api.repository_url}:latest"
      essential = true

      portMappings = [
        {
          containerPort = 8080
          hostPort      = 8080
          protocol      = "tcp"
        }
      ]

      environment = [
        {
            name  = "Mongo__ConnectionString"
            value = var.mongodb_uri
        },
        {
            name  = "Mongo__DatabaseName"
            value = "busable_${var.branch}"
        },
        {
            name  = "ASPNETCORE_ENVIRONMENT"
            value = "Production"
        },
        {
            name  = "ASPNETCORE_URLS"
            value = "http://+:8080"
        }
    ]

      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = aws_cloudwatch_log_group.ecs_api_logs.name
          "awslogs-region"        = "us-west-2"
          "awslogs-stream-prefix" = "api"
        }
      }
    }
  ])
}

# --- ECS Fargate Service ---
resource "aws_ecs_service" "busable_api" {
  name            = "busable-api-${var.branch}"
  cluster         = aws_ecs_cluster.busable.id
  task_definition = aws_ecs_task_definition.busable_api.arn
  desired_count   = 1
  launch_type     = "FARGATE"

  network_configuration {
    subnets          = data.aws_subnets.default.ids
    security_groups  = [aws_security_group.ecs_api_sg.id]
    assign_public_ip = true
  }

  load_balancer {
  target_group_arn = aws_lb_target_group.busable_api.arn
  container_name   = "busable-api"
  container_port   = 8080
}

depends_on = [
  aws_iam_role_policy_attachment.ecs_execution_role_policy,
  aws_lb_listener.http
]
}

# --- CloudWatch Log Group ---
resource "aws_cloudwatch_log_group" "ecs_api_logs" {
  name              = "/ecs/busable-api-${var.branch}"
  retention_in_days = 7
}