locals {
  node_ids = var.node_count == 0 ? [] : data.aws_instances.machines.ids
}

data "aws_ec2_spot_price" "current" {
  count             = length(var.globals.az_names)
  instance_type     = var.instance_type
  availability_zone = var.globals.az_names[count.index]
  filter {
    name   = "product-description"
    values = [var.globals.platform_details]
  }
}

data "template_file" "linux" {
  template = file("${path.module}/../templates/user_data_linux.tpl")
}

resource "aws_launch_template" "linux" {
  name                   = "${var.globals.cluster_name}-${var.node_role}"
  image_id               = var.globals.image_id
  instance_type          = var.instance_type
  key_name               = var.globals.ssh_key
  vpc_security_group_ids = [var.globals.security_group_id, var.asg_node_id]
  ebs_optimized          = true
  block_device_mappings {
    device_name = var.globals.root_device_name
    ebs {
      volume_type = "gp2"
      volume_size = var.volume_size
    }
  }
  user_data = base64encode(data.template_file.linux.rendered)
  tags      = var.tags
}

###

resource "aws_spot_fleet_request" "node" {
  iam_fleet_role      = var.globals.iam_fleet_role
  allocation_strategy = "lowestPrice"
  target_capacity     = var.node_count
  # valid_until     = "2019-11-04T20:44:20Z"
  wait_for_fulfillment                = true
  terminate_instances_with_expiration = true
  tags                                = var.tags

  launch_template_config {
    launch_template_specification {
      id      = aws_launch_template.linux.id
      version = aws_launch_template.linux.latest_version
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
  # we use this to collect the instance IDs/IPs from the spot fleet request
  filter {
    name   = "tag:aws:ec2spot:fleet-request-id"
    values = [aws_spot_fleet_request.node.id]
  }
  instance_state_names = ["running", "pending"]
  depends_on           = [aws_spot_fleet_request.node]
}

module "instances" {
  source      = "../instances"
  count       = var.node_count
  instance_id = data.aws_instances.machines.ids[count.index]
}
