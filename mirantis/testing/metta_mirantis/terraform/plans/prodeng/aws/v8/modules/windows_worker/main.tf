locals {
  tags = merge(
    var.tags,
    {
      "Name" = "${var.constants.cluster_name}-win-${var.node_role}"
      "Role" = "win-${var.node_role}"
    }
  )
  os_type          = "windows"
  platform_details = "Windows"
  az_names_count   = length(var.globals.az_names)
  node_ids         = var.node_count == 0 ? [] : data.aws_instances.machines.ids
}

resource "aws_security_group" "worker" {
  name        = "${var.constants.cluster_name}-win-workers"
  description = "mke cluster windows workers"
  vpc_id      = var.globals.vpc_id

  ingress {
    from_port   = 5985
    to_port     = 5986
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

data "aws_ec2_spot_price" "current" {
  count = local.az_names_count

  instance_type     = var.node_instance_type
  availability_zone = var.globals.az_names[count.index]

  filter {
    name   = "product-description"
    values = [local.platform_details]
  }
}

data "template_file" "windows" {
  template = file("${path.module}/../templates/user_data_windows.tpl")
  vars = {
    win_admin_password = var.win_admin_password
  }
}

resource "aws_launch_template" "windows" {
  name                   = "${var.constants.cluster_name}-win-worker"
  image_id               = var.image_id
  instance_type          = var.node_instance_type
  key_name               = var.globals.key_pair_name
  vpc_security_group_ids = [var.globals.security_group_id, aws_security_group.worker.id]
  ebs_optimized          = true
  block_device_mappings {
    device_name = var.globals.root_device_name
    ebs {
      volume_type = "gp2"
      volume_size = var.node_volume_size
    }
  }
  connection {
    type     = "winrm"
    user     = "Administrator"
    password = var.win_admin_password
    timeout  = "10m"
    https    = "true"
    insecure = "true"
    port     = 5986
  }
  user_data = base64encode(data.template_file.windows.rendered)
  tags      = local.tags
  tag_specifications {
    resource_type = "instance"
    tags          = local.tags
  }
  tag_specifications {
    resource_type = "volume"
    tags          = local.tags
  }
  tag_specifications {
    resource_type = "spot-instances-request"
    tags          = local.tags
  }
}

resource "aws_spot_fleet_request" "windows" {
  iam_fleet_role      = var.constants.iam_fleet_role
  allocation_strategy = "lowestPrice"
  target_capacity     = var.node_count
  # valid_until     = "2019-11-04T20:44:20Z"
  wait_for_fulfillment                = true
  tags                                = local.tags
  terminate_instances_with_expiration = true

  launch_template_config {
    launch_template_specification {
      id      = aws_launch_template.windows.id
      version = aws_launch_template.windows.latest_version
    }
    overrides {
      subnet_id = var.globals.subnet_ids[0]
      spot_price = var.globals.pct_over_spot_price == 0 ? null : format(
        "%f",
        data.aws_ec2_spot_price.current[0].spot_price * var.globals.spot_price_multiplier
      )
    }
    overrides {
      subnet_id = var.globals.subnet_ids[1]
      spot_price = var.globals.pct_over_spot_price == 0 ? null : format(
        "%f",
        data.aws_ec2_spot_price.current[1].spot_price * var.globals.spot_price_multiplier
      )
    }
    overrides {
      subnet_id = var.globals.subnet_ids[2]
      spot_price = var.globals.pct_over_spot_price == 0 ? null : format(
        "%f",
        data.aws_ec2_spot_price.current[2].spot_price * var.globals.spot_price_multiplier
      )
    }
  }
}

data "aws_instances" "machines" {
  # we use this to collect the instance IDs from the spot fleet request
  filter {
    name   = "tag:aws:ec2spot:fleet-request-id"
    values = [aws_spot_fleet_request.windows.id]
  }
  instance_state_names = ["running", "pending"]
  depends_on           = [aws_spot_fleet_request.windows]
}

module "instances" {
  source      = "../instances"
  count       = var.node_count
  instance_id = data.aws_instances.machines.ids[count.index]
}
