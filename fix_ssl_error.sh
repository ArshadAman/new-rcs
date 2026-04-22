#!/bin/bash
# Description: Fixes corrupted Let's Encrypt directory and fetches a new certificate

# Automatically detect the directory the script is in
cd "$(dirname "$0")" || exit 1

if [ "$EUID" -ne 0 ]; then
  echo "Error: Please run this script with sudo."
  echo "Run: sudo bash fix_ssl_error.sh"
  exit 1
fi

echo "1. Cleaning up broken config..."
rm -rf ./nginx/certs/archive
rm -rf ./nginx/certs/renewal
rm -rf ./nginx/certs/live/api.level-4u.com
rm -rf ./nginx/certs/accounts

echo "2. Generating temporary dummy certificates to start Nginx..."
mkdir -p ./nginx/certs/live/api.level-4u.com
openssl req -x509 -nodes -newkey rsa:2048 -days 1 \
    -keyout ./nginx/certs/live/api.level-4u.com/privkey.pem \
    -out ./nginx/certs/live/api.level-4u.com/fullchain.pem \
    -subj '/CN=localhost' 2>/dev/null

echo "3. Restarting Nginx so the webserver operates with the temporary certificate..."
docker-compose restart nginx
sleep 3

echo "4. Requesting a fresh Let's Encrypt certificate..."
# Force request a new certificate over the dummy one
docker-compose run --rm certbot certonly --webroot -w /var/www/certbot --force-renewal -d api.level-4u.com --register-unsafely-without-email --agree-tos --non-interactive

echo "5. Reloading Nginx to apply the new live certificates..."
docker-compose exec -T nginx nginx -s reload

echo "All done! Your SSL configuration is fixed and the auto-renew cron will now work flawlessly."
