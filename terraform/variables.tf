variable "aws_region" {
  description = "AWS region to deploy into"
  type        = string
  default     = "us-west-2"
}

variable "environment" {
  description = "Deployment environment tag"
  type        = string
  default     = "dev"
}

variable "project_name" {
  type        = string
  description = "Project name"
}

variable "branch" {
  type        = string
  description = "Branch letter"
}

variable "mongodb_uri" {
  type        = string
  description = "MongoDB Connection String"
  sensitive   = true
}

variable "image_tag" {
  type        = string
  description = "The container image tag to deploy (Git commit SHA)"
  default     = "latest"
}