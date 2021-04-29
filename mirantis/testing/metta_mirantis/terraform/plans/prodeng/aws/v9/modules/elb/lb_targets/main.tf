resource "aws_lb_target_group" "api" {
  name     = "${var.globals.cluster_name}-${var.component}-${var.port}-api"
  port     = var.port
  protocol = "TCP"
  vpc_id   = var.globals.vpc_id
  tags     = var.tags
  health_check {
    interval = 10
    protocol = "TCP"
  }
}

resource "aws_lb_listener" "api" {
  load_balancer_arn = var.arn
  port              = var.port
  protocol          = "TCP"
  default_action {
    target_group_arn = aws_lb_target_group.api.arn
    type             = "forward"
  }
}

resource "aws_lb_target_group_attachment" "api" {
  count            = var.node_count
  target_group_arn = aws_lb_target_group.api.arn
  target_id        = var.machine_ids[count.index]
  port             = var.port
}
