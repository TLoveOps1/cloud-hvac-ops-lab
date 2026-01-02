provider "aws" {
  region = "us-east-1"
}

variable "image_tag" {
  description = "Docker image tag for microservices"
  type        = string
}

# Placeholder for Staging VPC
resource "aws_vpc" "staging_vpc" {
  cidr_block = "10.0.0.0/16"
  tags = {
    Name = "hvac-staging-vpc"
  }
}

# Placeholder for Staging ECS Cluster
resource "aws_ecs_cluster" "staging_cluster" {
  name = "hvac-staging-cluster"
}

# Placeholder for a single Fargate service (e.g., sensor-service)
resource "aws_ecs_task_definition" "sensor_task_staging" {
  family                   = "hvac-sensor-service-staging"
  cpu                      = "256"
  memory                   = "512"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  execution_role_arn       = "arn:aws:iam::123456789012:role/ecsTaskExecutionRole" # Replace with actual role ARN
  container_definitions    = jsonencode([
    {
      name      = "sensor-service"
      image     = "ghcr.io/your-org/cloud-hvac-operations-lab/sensor-service:${var.image_tag}"
      cpu       = 256
      memory    = 512
      essential = true
      portMappings = [
        {
          containerPort = 5000
          hostPort      = 5000
        }
      ]
      environment = [
        { name = "PORT", value = "5000" },
        { name = "MESSAGE_QUEUE_HOST", value = "rabbitmq.staging.internal" } # Placeholder for internal RabbitMQ
      ]
      logConfiguration = {
        logDriver = "awslogs"
        options = {
          awslogs-group         = "/ecs/hvac-staging-sensor"
          awslogs-region        = "us-east-1"
          awslogs-stream-prefix = "ecs"
        }
      }
    }
  ])

  tags = {
    Environment = "Staging"
    Service     = "Sensor"
  }
}

resource "aws_ecs_service" "sensor_service_staging" {
  name            = "hvac-sensor-service-staging"
  cluster         = aws_ecs_cluster.staging_cluster.id
  task_definition = aws_ecs_task_definition.sensor_task_staging.arn
  desired_count   = 1
  launch_type     = "FARGATE"

  network_configuration {
    subnets          = ["subnet-0abcdef1234567890"] # Replace with actual staging subnet IDs
    security_groups  = ["sg-0abcdef1234567890"] # Replace with actual staging security group IDs
    assign_public_ip = true
  }

  tags = {
    Environment = "Staging"
    Service     = "Sensor"
  }
}

# Add similar resources for other microservices (monitoring, logging, alerting, automation)
# and other AWS services like RDS, Kinesis, S3, etc.

output "staging_sensor_service_url" {
  description = "URL for the staging sensor service (example)"
  value       = "http://staging-sensor.cloud-hvac.example.com" # Placeholder
}
