#!/bin/bash
BAMBOO_URL="http://54.209.197.255:8085"
MAX_ATTEMPTS=20
ATTEMPT=1

echo "Checking Bamboo server status..."
echo "URL: $BAMBOO_URL"
echo ""

while [ $ATTEMPT -le $MAX_ATTEMPTS ]; do
    echo "Attempt $ATTEMPT/$MAX_ATTEMPTS..."
    
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout 5 $BAMBOO_URL)
    
    if [ "$HTTP_CODE" = "200" ] || [ "$HTTP_CODE" = "302" ]; then
        echo "✓ Bamboo is running!"
        echo "✓ Access it at: $BAMBOO_URL"
        exit 0
    fi
    
    echo "  Status: $HTTP_CODE (waiting...)"
    sleep 15
    ATTEMPT=$((ATTEMPT + 1))
done

echo "✗ Bamboo did not start within the expected time"
echo "  Please check the instance logs or wait a bit longer"
exit 1
