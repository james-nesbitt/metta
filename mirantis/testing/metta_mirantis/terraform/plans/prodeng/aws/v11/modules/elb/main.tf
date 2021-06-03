locals {
  tags = merge(
    var.globals.tags,
    {
      "Name" = "${var.globals.cluster_name}-elb"
      "Role" = "${upper(var.component)} ELB"
    }
  )
}

resource "aws_lb" "lb" {
  name               = "${var.globals.cluster_name}-${var.component}-lb"
  internal           = false
  load_balancer_type = "network"
  subnets            = var.globals.subnet_ids
  tags               = local.tags
}

module "lb_targets" {
  source          = "./lb_targets"
  for_each        = toset(var.ports)
  port            = each.key
  arn             = aws_lb.lb.arn
  component       = var.component
  globals         = var.globals
  machine_ids     = var.machine_ids
  node_count      = var.node_count
  tags            = local.tags
}
