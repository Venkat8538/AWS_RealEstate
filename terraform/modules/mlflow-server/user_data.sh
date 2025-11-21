#!/bin/bash
set -eux

apt update -y
apt install -y python3 python3-pip python3-venv git awscli

# Install SSM agent
snap install amazon-ssm-agent --classic
systemctl enable snap.amazon-ssm-agent.amazon-ssm-agent.service
systemctl start snap.amazon-ssm-agent.amazon-ssm-agent.service

pip3 install mlflow boto3 gunicorn

mkdir -p /mlflow
cd /mlflow

# Create systemd service for MLflow
cat > /etc/systemd/system/mlflow.service << EOF
[Unit]
Description=MLflow Server
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/mlflow
ExecStart=/usr/local/bin/mlflow server --host 0.0.0.0 --port 5000 --backend-store-uri sqlite:///mlflow.db --default-artifact-root s3://${s3_bucket}/mlflow-artifacts --serve-artifacts --allowed-hosts '*'
Restart=always

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable mlflow
systemctl start mlflow