variable "name" {
    type = string
    description = "Base name for the project's resources"
}

variable "app_name" {
    type = string
    description = "App name for function app"
}

variable "location" {
    type = string
    description = "Azure zone for deployment"
}

variable "env" {
    type = set(string)
    description = "environment name"
}

variable "python_version" {
    type = string
    description = "Exact version of the python runtime"
}

variable "admin_username" {
    type = string
    description = "Administrator user name for virtual machine / db server"
}

variable "admin_password" {
    type = string
    description = "Password must meet Azure complexity requirements"
}

variable "aad_admin" {
    type = string
    description = "Azure AD Admin username"
}

variable "aad_admin_id" {
    type = string
    description = "Azure AD admin object ID on the Tenant"
}

variable "subnet_idx" {
    type = map
    description = "subnet index depneding on environment"
}

variable "inbound_rules" {
    type = list(map(string))
    description = "list of allowed inbound IPs for SQL and Key Vault querying"
}

variable "app_tier"{
    type = string
    description = "tier for Azure App Service plan pricing"
}

variable "storage_tier"{
    type = string
    description = "tier for Azure Storage Account plan pricing"
}

variable "app_sku" {
    type = string
    description = "SKU for App Service Plan"
}

variable "vault_sku" {
    type = string
    description = "SKU for App Service Plan"
}

variable "db_sku" {
    type = map
    description = "SKU for MS SQL database"
}

variable "nat_sku" {
    type = string
    description = "SKU for the NAT gateway"
}

variable "ip_sku" {
    type = string
    description = "SKU for the IP address"
}