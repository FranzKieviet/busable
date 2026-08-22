resource "aws_security_group" "alb_sg" {
  name        = "busable-alb-sg-${var.branch}"
  description = "Allow public HTTP traffic to ALB"
  vpc_id      = data.aws_vpc.default.id

  ingress {
    description = "Allow inbound HTTP from anywhere"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    description = "Allow all outbound traffic to ECS tasks"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

# The Load Balancer
resource "aws_lb" "busable_api" {
  name               = "busable-alb-${var.branch}"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.alb_sg.id]
  subnets            = data.aws_subnets.default.ids
}

# The Target Group pointing to Fargate tasks
resource "aws_lb_target_group" "busable_api" {
  name        = "busable-tg-${var.branch}"
  port        = 8080
  protocol    = "HTTP"
  vpc_id      = data.aws_vpc.default.id
  target_type = "ip"

  health_check {
    enabled             = true
    path                = "/health"
    protocol            = "HTTP"
    port                = "8080"
    matcher             = "200"
  }
}

# HTTP Listener on Port 80
resource "aws_lb_listener" "http" {
  load_balancer_arn = aws_lb.busable_api.arn
  port              = "80"
  protocol          = "HTTP"

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.busable_api.arn
  }
}