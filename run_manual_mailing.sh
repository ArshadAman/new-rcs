#!/bin/bash

# 🚀 Manual Mailing Docker Setup Script
# This script will build and run the complete manual mailing system

echo "🚀 Setting up Manual Mailing with Docker..."

# Check if .env file exists
if [ ! -f .env ]; then
    echo "❌ .env file not found! Please create one with your environment variables."
    echo "Required variables:"
    echo "POSTGRES_DB=your_db_name"
    echo "POSTGRES_USER=your_db_user"
    echo "POSTGRES_PASSWORD=your_db_password"
    echo "SENDGRID_API_KEY=your_sendgrid_key"
    echo "DEFAULT_FROM_EMAIL=your_email@domain.com"
    echo "SITE_URL=https://your-domain.com"
    exit 1
fi

echo "📦 Building Docker images..."
docker-compose build

echo "🗄️ Running database migrations..."
docker-compose run --rm web python manage.py makemigrations orders
docker-compose run --rm web python manage.py migrate

echo "📊 Collecting static files..."
docker-compose run --rm collectstatic

echo "🚀 Starting all services..."
docker-compose up -d

echo "✅ Manual Mailing is now running!"
echo ""
echo "🌐 Services available:"
echo "   - Web API: http://localhost:8000"
echo "   - Frontend: http://localhost (nginx)"
echo "   - Admin: http://localhost:8000/admin"
echo ""
echo "📧 Manual Mailing endpoints:"
echo "   - Monthly Usage: http://localhost:8000/api/orders/mailing/monthly-usage/"
echo "   - Send Mailing: http://localhost:8000/api/orders/mailing/send/"
echo "   - Mailing History: http://localhost:8000/api/orders/mailing/history/"
echo ""
echo "🔧 To check logs:"
echo "   docker-compose logs -f web"
echo "   docker-compose logs -f celery"
echo ""
echo "🛑 To stop:"
echo "   docker-compose down"


