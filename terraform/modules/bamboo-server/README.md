# Bamboo Server Module

Deploys Atlassian Bamboo on EC2 using Podman.

## Usage

```hcl
module "bamboo_server" {
  source       = "./modules/bamboo-server"
  project_name = "mlops"
  ami_id       = "ami-0c55b159cbfafe1f0"  # Amazon Linux 2023
  key_name     = "your-key-name"
  vpc_id       = "vpc-xxxxx"
  subnet_id    = "subnet-xxxxx"
  
  # Optional overrides
  bamboo_port           = 8085
  bamboo_image          = "atlassian/bamboo-server:latest"
  bamboo_data_dir       = "/var/bamboo"
  bamboo_container_name = "bamboo"
}

output "bamboo_url" {
  value = module.bamboo_server.bamboo_url
}
```

## Template Variables

The `linux_user_data.tpl` template accepts:

```hcl
user_data = templatefile("${path.module}/linux_user_data.tpl", {
  bamboo_port           = 8085
  bamboo_image          = "atlassian/bamboo-server:latest"
  bamboo_data_dir       = "/var/bamboo"
  bamboo_container_name = "bamboo"
})
```
