#!/bin/bash -xe

# Log everything to user-data.log for debugging
exec > >(tee -a /var/log/user-data.log) 2>&1

echo "=== Starting Airflow user-data ==="

# Basic OS packages
apt-get update -y
apt-get install -y python3 python3-pip python3-venv curl unzip

# Install AWS CLI
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip -q awscliv2.zip
./aws/install
rm -rf aws awscliv2.zip

# Create airflow user if not exists
if ! id -u airflow >/dev/null 2>&1; then
  useradd -m -s /bin/bash airflow
fi

# Install Airflow in a virtualenv as airflow user
sudo -u airflow bash << 'EOF'
set -xe

cd /home/airflow

# Create venv
python3 -m venv airflow-venv
source airflow-venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install Airflow with official constraints
AIRFLOW_VERSION=2.7.3
CONSTRAINT_URL="https://raw.githubusercontent.com/apache/airflow/constraints-2.7.3/constraints-3.10.txt"

pip install "apache-airflow[amazon,postgres]==${AIRFLOW_VERSION}" --constraint "${CONSTRAINT_URL}"

# Set AIRFLOW_HOME and database connection
export AIRFLOW_HOME=/home/airflow/airflow
export AIRFLOW__DATABASE__SQL_ALCHEMY_CONN=postgresql+psycopg2://${db_username}:${db_password}@${db_endpoint}/${db_name}
export AIRFLOW__CORE__EXECUTOR=LocalExecutor
mkdir -p "$AIRFLOW_HOME"

# Initialize DB with PostgreSQL
airflow db init

# Update airflow.cfg to use PostgreSQL permanently
sed -i "s|sql_alchemy_conn = sqlite.*|sql_alchemy_conn = postgresql+psycopg2://${db_username}:${db_password}@${db_endpoint}/${db_name}|" $AIRFLOW_HOME/airflow.cfg
sed -i "s|executor = SequentialExecutor|executor = LocalExecutor|" $AIRFLOW_HOME/airflow.cfg

# Create admin user (UI login: admin / admin123)
airflow users create \
  --username admin \
  --firstname Admin \
  --lastname User \
  --role Admin \
  --email admin@example.com \
  --password admin123

# Create DAGs directory
mkdir -p $AIRFLOW_HOME/dags
EOF

# Create S3 DAG sync script
cat >/home/airflow/sync_dags.sh << 'SYNCEOF'
#!/bin/bash
export PATH=/usr/local/bin:/usr/bin:/bin
S3_BUCKET="house-price-mlops-dev-itzi2hgi"
DAGS_DIR="/home/airflow/airflow/dags"

# Sync DAGs from S3
/usr/local/bin/aws s3 sync s3://$S3_BUCKET/dags/ $DAGS_DIR/ --delete --region us-east-1

# Set proper permissions
chown -R airflow:airflow $DAGS_DIR
chmod -R 644 $DAGS_DIR/*.py 2>/dev/null || true
SYNCEOF

chmod +x /home/airflow/sync_dags.sh
chown airflow:airflow /home/airflow/sync_dags.sh

# Initial DAG sync
sudo -u airflow /home/airflow/sync_dags.sh

# Create cron job for DAG sync every minute
(echo "PATH=/usr/local/bin:/usr/bin:/bin"; echo "* * * * * /home/airflow/sync_dags.sh") | sudo -u airflow crontab -

# Fix permissions just in case
chown -R airflow:airflow /home/airflow

# Create systemd service for webserver
cat >/etc/systemd/system/airflow-webserver.service << EOF
[Unit]
Description=Airflow webserver
After=network.target

[Service]
User=airflow
Group=airflow
Environment=AIRFLOW_HOME=/home/airflow/airflow
Environment=PATH=/home/airflow/airflow-venv/bin:/usr/local/bin:/usr/bin:/bin
WorkingDirectory=/home/airflow
ExecStart=/home/airflow/airflow-venv/bin/airflow webserver --port 8080 --hostname 0.0.0.0
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Create systemd service for scheduler
cat >/etc/systemd/system/airflow-scheduler.service << EOF
[Unit]
Description=Airflow Scheduler
After=network.target

[Service]
User=airflow
Group=airflow
Environment=AIRFLOW_HOME=/home/airflow/airflow
Environment=PATH=/home/airflow/airflow-venv/bin:/usr/local/bin:/usr/bin:/bin
WorkingDirectory=/home/airflow
ExecStart=/home/airflow/airflow-venv/bin/airflow scheduler
Restart=always
RestartSec=5s

[Install]
WantedBy=multi-user.target
EOF

# Enable and start services
systemctl daemon-reload
systemctl enable airflow-webserver airflow-scheduler
systemctl start airflow-webserver airflow-scheduler

echo "=== Airflow user-data complete ==="