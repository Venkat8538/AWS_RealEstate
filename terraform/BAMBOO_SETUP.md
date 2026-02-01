# Bamboo Server - Setup Summary

## Issues Fixed

### 1. Wrong AMI Issue
**Problem**: The instance was using AlmaLinux 9.7 instead of Amazon Linux 2023
- The `java-17-amazon-corretto` package doesn't exist in AlmaLinux repos
- User-data script failed early due to `set -e` flag

**Solution**: 
- Added AWS SSM parameter data source to automatically fetch the latest AL2023 AMI
- Removed hardcoded AMI ID from variables

```hcl
data "aws_ssm_parameter" "al2023_ami" {
  name = "/aws/service/ami-amazon-linux-latest/al2023-ami-kernel-6.1-x86_64"
}
```

### 2. Terraform Best Practices Added
- `user_data_replace_on_change = true` - Forces instance replacement when user-data changes
- `lifecycle { create_before_destroy = true }` - Ensures smooth instance replacement

## Current Status

✅ **Bamboo Server is Running**

- **Instance ID**: i-0d5a17e1f97270f1e
- **Public IP**: 3.95.170.192
- **Bamboo URL**: http://3.95.170.192:8085
- **AMI**: Amazon Linux 2023 (via SSM parameter)
- **Instance Type**: t3.small
- **Region**: us-east-1

## Installed Components

1. **Java**: Amazon Corretto 17
2. **Bamboo**: Version 9.6.5
3. **Installation Path**: /opt/atlassian/bamboo
4. **Data Directory**: /var/atlassian/application-data/bamboo
5. **Service**: systemd service (enabled and running)

## Access Information

### Web Interface
- URL: http://3.95.170.192:8085
- First-time setup wizard will be displayed

### SSH Access
```bash
ssh -i <your-key.pem> ec2-user@3.95.170.192
```

### Check Service Status
```bash
sudo systemctl status bamboo
sudo journalctl -u bamboo -f
```

### Bamboo Logs
```bash
sudo tail -f /opt/atlassian/bamboo/logs/catalina.out
sudo tail -f /var/atlassian/application-data/bamboo/logs/atlassian-bamboo.log
```

## Security Group Rules

- **Port 8085**: Open to 0.0.0.0/0 (Bamboo web interface)
- **Port 22**: Open to 0.0.0.0/0 (SSH access)
- **Egress**: All traffic allowed

## IAM Permissions

The instance has the following IAM role attached:
- **Role**: house-price-bamboo-role
- **Policy**: AmazonSSMManagedInstanceCore (for Systems Manager access)

## Next Steps

1. **Initial Setup**: Access http://3.95.170.192:8085 and complete the setup wizard
2. **License**: Enter your Bamboo license key (or request a trial)
3. **Database**: Configure H2 (embedded) or external database
4. **Admin User**: Create the administrator account
5. **Build Agents**: Configure remote agents if needed

## Troubleshooting

If Bamboo doesn't start:
```bash
# Check service status
sudo systemctl status bamboo

# View logs
sudo journalctl -u bamboo -n 100

# Check if port is listening
sudo ss -lntp | grep 8085

# Restart service
sudo systemctl restart bamboo
```

## Files Modified

1. `/Users/venkat/Documents/devops/AWS_RealEstate/terraform/modules/bamboo-server/main.tf`
   - Added SSM parameter data source for AL2023 AMI
   - Added `user_data_replace_on_change = true`
   - Added lifecycle block with `create_before_destroy = true`

2. `/Users/venkat/Documents/devops/AWS_RealEstate/terraform/modules/bamboo-server/variables.tf`
   - Removed `ami_id` variable (now using SSM parameter)

3. `/Users/venkat/Documents/devops/AWS_RealEstate/terraform/main.tf`
   - Removed `ami_id` parameter from bamboo_server module call
