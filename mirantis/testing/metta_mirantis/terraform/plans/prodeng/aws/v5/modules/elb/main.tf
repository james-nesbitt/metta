locals {
  tags = merge(
    var.globals.tags,
    {
      "Name" = "${var.globals.cluster_name}-elb"
      "Role" = "MKE ELB"
    }
  )
}

resource "aws_lb" "mke_manager" {
  name               = "${var.globals.cluster_name}-manager-lb"
  internal           = false
  load_balancer_type = "network"
  subnets            = var.globals.subnet_ids
  tags               = local.tags
}

resource "aws_lb_target_group" "mke_manager_api" {
  name     = "${var.globals.cluster_name}-api"
  port     = var.controller_port
  protocol = "TCP"
  vpc_id   = var.globals.vpc_id
  health_check {
    path     = "/_ping"
    protocol = "HTTPS"
  }
}

resource "aws_lb_listener" "mke_manager_api" {
  load_balancer_arn = aws_lb.mke_manager.arn
  port              = var.controller_port
  protocol          = "TCP"
  default_action {
    target_group_arn = aws_lb_target_group.mke_manager_api.arn
    type             = "forward"
  }
}

resource "aws_lb_target_group_attachment" "mke_manager_api" {
  count            = var.manager_count
  target_group_arn = aws_lb_target_group.mke_manager_api.arn
  target_id        = var.machine_ids[count.index]
  port             = var.controller_port
}

resource "aws_lb_target_group" "mke_kube_api" {
  name     = "${var.globals.cluster_name}-kube-api"
  port     = 6443
  protocol = "TCP"
  vpc_id   = var.globals.vpc_id
}

resource "aws_lb_listener" "mke_kube_api" {
  load_balancer_arn = aws_lb.mke_manager.arn
  port              = 6443
  protocol          = "TCP"
  default_action {
    target_group_arn = aws_lb_target_group.mke_kube_api.arn
    type             = "forward"
  }
}

resource "aws_lb_target_group_attachment" "mke_kube_api" {
  count            = var.manager_count
  target_group_arn = aws_lb_target_group.mke_kube_api.arn
  target_id        = var.machine_ids[count.index]
  port             = 6443
}
