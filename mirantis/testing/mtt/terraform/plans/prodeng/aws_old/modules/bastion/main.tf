resource "aws_security_group" "bastion" {
  name        = "${var.cluster_name}-bastion"
  description = "mke cluster bastion hosts"
  vpc_id      = var.vpc_id

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

locals {
  subnet_count = length(var.subnet_ids)
}


resource "aws_instance" "mke_bastion" {
  count = 1

  tags = {
    "Name"                    = "${var.cluster_name}-bastion-${count.index + 1}"
    "Role"                    = "bastion"
    (var.kube_cluster_tag)    = "shared"
    "project"                 = var.project
    "platform"                = var.platform
    "expire"                  = var.expire
  }

  instance_type          = var.bastion_type
  iam_instance_profile   = var.instance_profile_name
  ami                    = var.image_id
  key_name               = var.ssh_key
  vpc_security_group_ids = [aws_security_group.bastion.id]
  subnet_id              = var.subnet_ids[count.index % local.subnet_count]
  ebs_optimized          = true
  user_data              = <<EOF
#!/bin/bash
# Use full qualified private DNS name for the host name.  Kube wants it this way.
HOSTNAME=$(curl http://169.254.169.254/latest/meta-data/hostname)
echo $HOSTNAME > /etc/hostname
sed -i "s|\(127\.0\..\.. *\)localhost|\1$HOSTNAME|" /etc/hosts
hostname $HOSTNAME
EOF

  lifecycle {
    ignore_changes = [ami]
  }

  root_block_device {
    volume_type = "gp2"
    volume_size = var.bastion_volume_size
  }
}
