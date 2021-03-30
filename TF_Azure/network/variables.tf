variable "rg" {
    type = object({
        id       = string
        name     = string
        location = string
        tags = map(string)
    })
}

variable "storage" {
    type = object({
        id       = string
        name     = string
    })
}

variable "sqlserver_name" {
    type = string
}

variable "name" {
    default = ""
}

variable "app_name" {
    default = ""
}

variable "function_app_id" {
    default = ""
}

variable "env" {
    default = []
}

variable "subnet_idx" {
    default = {}
}

variable "inbound_rules" {
    default = []
}

variable "nat_sku" {
    default = ""
}

variable "ip_sku" {
    default = ""
}