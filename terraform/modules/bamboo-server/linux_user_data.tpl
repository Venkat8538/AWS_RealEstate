#!/bin/bash
set -euxo pipefail

# --- Packages ---
dnf -y update
dnf -y install java-17-amazon-corretto wget tar

# --- User ---
id bamboo || useradd --system --create-home --shell /bin/bash bamboo

# --- Install Bamboo ---
mkdir -p /opt/atlassian
cd /opt/atlassian

BAMBOO_VERSION="9.6.5"
wget -O bamboo.tar.gz "https://product-downloads.atlassian.com/software/bamboo/downloads/atlassian-bamboo-${BAMBOO_VERSION}.tar.gz"
tar -xzf bamboo.tar.gz

BAMBOO_DIR=$(ls -d atlassian-bamboo-*/ | head -n 1)
ln -sfn "/opt/atlassian/$BAMBOO_DIR" /opt/atlassian/bamboo

# --- Ensure H2 driver JAR exists (needed for Embedded DB setup) ---
BAMBOO_LIB="/opt/atlassian/bamboo/lib"
mkdir -p "$BAMBOO_LIB"

if ! ls -1 "$BAMBOO_LIB"/h2-*.jar >/dev/null 2>&1; then
  echo "H2 jar not found in $BAMBOO_LIB. Downloading..."
  wget -O "$BAMBOO_LIB/h2-1.4.200.jar" \
    "https://repo1.maven.org/maven2/com/h2database/h2/1.4.200/h2-1.4.200.jar"
  cp "$BAMBOO_LIB/h2-1.4.200.jar" /opt/atlassian/bamboo/atlassian-bamboo/WEB-INF/lib/
fi

# --- Bamboo Home (H2 DB lives here) ---
mkdir -p /var/atlassian/application-data/bamboo
chown -R bamboo:bamboo /var/atlassian/application-data/bamboo
chown -R bamboo:bamboo /opt/atlassian

# --- Set bamboo.home ---
echo "bamboo.home=/var/atlassian/application-data/bamboo" > \
  /opt/atlassian/bamboo/atlassian-bamboo/WEB-INF/classes/bamboo-init.properties
chown bamboo:bamboo /opt/atlassian/bamboo/atlassian-bamboo/WEB-INF/classes/bamboo-init.properties

# --- systemd service ---
cat >/etc/systemd/system/bamboo.service <<'SERVICE'
[Unit]
Description=Atlassian Bamboo
After=network.target

[Service]
Type=forking
User=bamboo
Group=bamboo
Environment="BAMBOO_HOME=/var/atlassian/application-data/bamboo"
Environment="JAVA_HOME=/usr/lib/jvm/java-17-amazon-corretto"
ExecStart=/opt/atlassian/bamboo/bin/start-bamboo.sh
ExecStop=/opt/atlassian/bamboo/bin/stop-bamboo.sh
TimeoutStartSec=300
TimeoutStopSec=120
Restart=on-failure

[Install]
WantedBy=multi-user.target
SERVICE

systemctl daemon-reload
systemctl enable bamboo
systemctl start bamboo
