
terraform {
  required_version = ">= 0.12"

  required_providers {
    azurerm = "= 2.32.0"
    local   = "= 2.0.0"
    random  = "= 3.0.0"
    tls     = "= 3.0.0"
  }
}
