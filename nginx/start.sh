#!/bin/sh

# Auto-generate a dummy certificate if it doesn't exist
# This allows Nginx to start so Certbot can verify the domain
if [ ! -f /etc/nginx/certs/live/api.level-4u.com/fullchain.pem ]; then
    echo "Check: Certificate not found for api.level-4u.com"
    echo "Action: Generating dummy certificate..."
    
    mkdir -p /etc/nginx/certs/live/api.level-4u.com
    
    openssl req -x509 -nodes -newkey rsa:4096 -days 1 \
        -keyout /etc/nginx/certs/live/api.level-4u.com/privkey.pem \
        -out /etc/nginx/certs/live/api.level-4u.com/fullchain.pem \
        -subj '/CN=localhost'
        
    echo "Result: Dummy certificate generated."
else
    echo "Check: Certificate found. Skipping generation."
fi

# Execute the CMD from Dockerfile (nginx)
exec "$@"
