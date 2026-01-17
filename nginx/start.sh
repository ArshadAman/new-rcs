#!/bin/sh
set -e

# Auto-generate a dummy certificate if it doesn't exist
# This allows Nginx to start so Certbot can verify the domain
if [ ! -f /etc/nginx/certs/live/api.level-4u.com/fullchain.pem ]; then
    echo "00-generate-dummy-cert: Certificate not found for api.level-4u.com"
    echo "00-generate-dummy-cert: Generating dummy certificate..."
    
    mkdir -p /etc/nginx/certs/live/api.level-4u.com
    
    openssl req -x509 -nodes -newkey rsa:2048 -days 1 \
        -keyout /etc/nginx/certs/live/api.level-4u.com/privkey.pem \
        -out /etc/nginx/certs/live/api.level-4u.com/fullchain.pem \
        -subj '/CN=localhost' 2>/dev/null
        
    echo "00-generate-dummy-cert: Dummy certificate generated successfully."
else
    echo "00-generate-dummy-cert: Certificate found. Skipping generation."
fi
