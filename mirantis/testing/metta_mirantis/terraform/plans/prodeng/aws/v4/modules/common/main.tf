
data "aws_availability_zones" "available" {}

resource "tls_private_key" "ssh_key" {
  algorithm = "RSA"
  rsa_bits  = "4096"
}

resource "local_file" "ssh_public_key" {
  content  = tls_private_key.ssh_key.private_key_pem
  filename = var.key_path
  provisioner "local-exec" {
    command = "chmod 0600 ${local_file.ssh_public_key.filename}"
  }
}

resource "aws_key_pair" "key" {
  key_name   = var.cluster_name
  public_key = tls_private_key.ssh_key.public_key_openssh
}

data "aws_ami" "linux" {
  most_recent = true

  filter {
    name   = "name"
    values = [var.ami_obj.ami_name]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }

  owners = [var.ami_obj.owner]
}

data "aws_ami" "windows_2019" {
  most_recent = true

  filter {
    name   = "name"
    values = [var.ami_obj_win.ami_name]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }

  owners = [var.ami_obj_win.owner]
}

data "http" "myip" {
  url = "http://ifconfig.me"
}

resource "aws_security_group" "common" {
  name        = "${var.cluster_name}-common"
  description = "mke cluster common rules"
  vpc_id      = var.vpc_id

  ingress {
    from_port = 0
    to_port   = 0
    protocol  = "-1"
    self      = true
  }

  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_security_group_rule" "open_myip" {
  # conditionally add this rule to SG 'common'
  security_group_id = aws_security_group.common.id
  count             = var.open_sg_for_myip ? 1 : 0
  type              = "ingress"
  from_port         = 0
  to_port           = 0
  protocol          = "-1"
  cidr_blocks       = ["${chomp(data.http.myip.body)}/32"]
}

resource "aws_iam_role" "role" {
  name = "${var.cluster_name}_host"

  assume_role_policy = <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "",
      "Effect": "Allow",
      "Principal": {
        "Service": "ec2.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
EOF
}

resource "aws_iam_instance_profile" "profile" {
  name = "${var.cluster_name}_host"
  role = aws_iam_role.role.name
}

resource "aws_iam_role_policy" "policy" {
  name = "${var.cluster_name}_host"
  role = aws_iam_role.role.id

  policy = <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": ["ec2:*"],
      "Resource": ["*"]
    },
    {
      "Effect": "Allow",
      "Action": ["elasticloadbalancing:*"],
      "Resource": ["*"]
    },
    {
      "Effect": "Allow",
      "Action": ["ecr:*"],
      "Resource": ["*"]
    },
    {
      "Effect": "Allow",
      "Action": [
          "autoscaling:DescribeLaunchConfigurations",
          "autoscaling:DescribeAutoScalingGroups",
          "autoscaling:DescribeAutoScalingInstances",
          "autoscaling:DescribeTags",
          "autoscaling:SetDesiredCapacity",
          "autoscaling:TerminateInstanceInAutoScalingGroup"
      ],
      "Resource": "*"
    }
  ]
}
EOF
}
