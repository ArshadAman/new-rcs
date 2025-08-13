echo "Pulling latest changes..."
git pull origin master
echo "Rebuilding project..."
docker-compose down
docker-compose up -d --build
echo "Project rebuilt successfully."