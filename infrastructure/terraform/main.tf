# Terraform Configuration for ConsultaRPP Infrastructure

terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
  backend "s3" {
    bucket         = "consulta-rpp-terraform-state"
    key            = "prod/terraform.tfstate"
    region         = "us-east-1"
    encrypt        = true
    dynamodb_table = "terraform-locks"
  }
}

provider "aws" {
  region = var.aws_region
}

# EKS Cluster
resource "aws_eks_cluster" "consulta_rpp" {
  name            = "consulta-rpp-prod"
  version         = "1.27"
  role_arn        = aws_iam_role.eks_cluster_role.arn
  
  vpc_config {
    subnet_ids = aws_subnet.private[*].id
  }
}

# Auto Scaling Group for EKS Workers
resource "aws_autoscaling_group" "eks_workers" {
  name                = "consulta-rpp-workers"
  vpc_zone_identifier = aws_subnet.private[*].id
  min_size            = 3
  max_size            = 20
  desired_capacity    = 5
  
  launch_template {
    id      = aws_launch_template.eks_worker.id
    version = "$Latest"
  }
  
  tag {
    key                 = "Name"
    value               = "consulta-rpp-worker"
    propagate_launch_template = true
  }
}

# Application Load Balancer
resource "aws_lb" "consulta_rpp" {
  name               = "consulta-rpp-alb"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.alb.id]
  subnets            = aws_subnet.public[*].id
}

# RDS PostgreSQL Database
resource "aws_db_instance" "consulta_rpp" {
  identifier     = "consulta-rpp-prod"
  engine         = "postgres"
  engine_version = "15"
  instance_class = "db.r6g.xlarge"
  
  allocated_storage = 500
  storage_type     = "gp3"
  storage_encrypted = true
  
  db_name  = "consulta_rpp"
  username = "admin"
  password = random_password.db_password.result
  
  multi_az = true
  
  backup_retention_period = 30
  backup_window          = "02:00-03:00"
  
  performance_insights_enabled = true
  monitoring_interval         = 60
  
  vpc_security_group_ids = [aws_security_group.rds.id]
  db_subnet_group_name   = aws_db_subnet_group.default.name
}

# ElastiCache Redis
resource "aws_elasticache_cluster" "consulta_rpp" {
  cluster_id           = "consulta-rpp-redis"
  engine               = "redis"
  node_type           = "cache.r6g.large"
  num_cache_nodes     = 3
  parameter_group_name = "default.redis7"
  engine_version      = "7.0"
  
  automatic_failover_enabled = true
  multi_az_enabled           = true
  
  security_group_ids = [aws_security_group.redis.id]
}

# CloudFront Distribution
resource "aws_cloudfront_distribution" "consulta_rpp" {
  enabled = true
  
  origin {
    domain_name = aws_lb.consulta_rpp.dns_name
    origin_id   = "alb"
  }
  
  default_cache_behavior {
    allowed_methods  = ["GET", "HEAD", "OPTIONS", "PUT", "POST", "PATCH", "DELETE"]
    cached_methods   = ["GET", "HEAD"]
    target_origin_id = "alb"
    
    forwarded_values {
      query_string = true
      cookies {
        forward = "all"
      }
    }
  }
  
  restrictions {
    geo_restriction {
      restriction_type = "none"
    }
  }
  
  viewer_certificate {
    cloudfront_default_certificate = true
  }
}
