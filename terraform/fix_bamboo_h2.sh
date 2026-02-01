#!/bin/bash
# Fix H2 Database JAR on running Bamboo instance

BAMBOO_IP="3.95.170.192"

echo "Fixing H2 database JAR on Bamboo server..."
echo "This will download the H2 JAR and restart Bamboo"
echo ""

# Create the fix script
cat << 'EOF' > /tmp/fix_h2.sh
#!/bin/bash
set -e

echo "Stopping Bamboo..."
sudo systemctl stop bamboo

echo "Downloading H2 database JAR..."
sudo wget -O /opt/atlassian/bamboo/lib/h2.jar "https://repo1.maven.org/maven2/com/h2database/h2/2.1.214/h2-2.1.214.jar"

echo "Setting permissions..."
sudo chown bamboo:bamboo /opt/atlassian/bamboo/lib/h2.jar

echo "Starting Bamboo..."
sudo systemctl start bamboo

echo "Done! Wait 30 seconds and refresh your browser."
EOF

chmod +x /tmp/fix_h2.sh

echo "To apply the fix, run:"
echo "  ssh -i <your-key.pem> ec2-user@${BAMBOO_IP} 'bash -s' < /tmp/fix_h2.sh"
echo ""
echo "Or manually SSH and run:"
echo "  sudo systemctl stop bamboo"
echo "  sudo wget -O /opt/atlassian/bamboo/lib/h2.jar https://repo1.maven.org/maven2/com/h2database/h2/2.1.214/h2-2.1.214.jar"
echo "  sudo chown bamboo:bamboo /opt/atlassian/bamboo/lib/h2.jar"
echo "  sudo systemctl start bamboo"
