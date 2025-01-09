# Deployment Guide

This guide explains how to deploy the Trading Bot in both development and production environments.

## Prerequisites

- Node.js (v18 or higher)
- PostgreSQL (v14 or higher)
- Git
- PM2 (for production)

## Development Setup

1. Clone the repository:
```bash
git clone https://github.com/your-username/trading-bot.git
cd trading-bot
```

2. Install dependencies:
```bash
npm install
```

3. Create environment files:
```bash
cp backend/.env.example backend/.env
```

4. Configure environment variables in `backend/.env`:
```env
# Server Configuration
PORT=3001
NODE_ENV=development

# Database Configuration
DB_USER=postgres
DB_HOST=localhost
DB_NAME=trading_bot
DB_PASSWORD=your_password
DB_PORT=5432

# JWT Configuration
JWT_SECRET=your_jwt_secret

# WebSocket Configuration
WS_PORT=3002

# Logging Configuration
LOG_LEVEL=debug

# Backup Configuration
BACKUP_STORAGE_PATH=./backups
BACKUP_RETENTION_DAYS=30

# Exchange API Configuration
EXCHANGE_API_KEY=your_api_key
EXCHANGE_API_SECRET=your_api_secret
```

5. Initialize the database:
```bash
psql -U postgres
CREATE DATABASE trading_bot;
```

6. Run database migrations:
```bash
cd backend
npm run migrate
```

7. Start the development server:
```bash
cd ..
npm run dev
```

## Production Deployment

### Server Requirements

- Ubuntu 20.04 LTS or higher
- 2 CPU cores
- 4GB RAM minimum
- 50GB SSD storage

### Installation Steps

1. Update system packages:
```bash
sudo apt update && sudo apt upgrade -y
```

2. Install Node.js:
```bash
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install -y nodejs
```

3. Install PostgreSQL:
```bash
sudo apt install postgresql postgresql-contrib -y
```

4. Install PM2:
```bash
sudo npm install -g pm2
```

5. Clone the repository:
```bash
git clone https://github.com/your-username/trading-bot.git
cd trading-bot
```

6. Install dependencies:
```bash
npm install --production
```

7. Configure environment variables:
```bash
cp backend/.env.example backend/.env
nano backend/.env
```

Update the environment variables with production values:
```env
NODE_ENV=production
PORT=3001
DB_USER=production_user
DB_PASSWORD=strong_password
JWT_SECRET=long_random_string
```

8. Set up SSL with Let's Encrypt:
```bash
sudo apt install certbot
sudo certbot certonly --standalone -d your-domain.com
```

9. Configure Nginx:
```bash
sudo apt install nginx
sudo nano /etc/nginx/sites-available/trading-bot
```

Add the following configuration:
```nginx
server {
    listen 443 ssl;
    server_name your-domain.com;

    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;

    location / {
        proxy_pass http://localhost:3001;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }

    location /ws {
        proxy_pass http://localhost:3002;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "Upgrade";
        proxy_set_header Host $host;
    }
}
```

10. Enable the site:
```bash
sudo ln -s /etc/nginx/sites-available/trading-bot /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

11. Set up the database:
```bash
sudo -u postgres psql
CREATE DATABASE trading_bot;
CREATE USER production_user WITH PASSWORD 'strong_password';
GRANT ALL PRIVILEGES ON DATABASE trading_bot TO production_user;
```

12. Run database migrations:
```bash
cd backend
NODE_ENV=production npm run migrate
```

13. Build the application:
```bash
npm run build
```

14. Start the application with PM2:
```bash
pm2 start ecosystem.config.js
pm2 startup
pm2 save
```

## Monitoring

1. Monitor application logs:
```bash
pm2 logs
```

2. Monitor application status:
```bash
pm2 status
```

3. Monitor system resources:
```bash
pm2 monit
```

## Backup Procedures

1. Database Backups:
```bash
# Manual backup
pg_dump -U production_user trading_bot > backup_$(date +%Y%m%d).sql

# Automated daily backups
0 0 * * * pg_dump -U production_user trading_bot > /path/to/backups/backup_$(date +%Y%m%d).sql
```

2. Application Data Backups:
The application includes an automated backup system. Configure it through the API or web interface.

## Recovery Procedures

1. Database Recovery:
```bash
# Restore from backup
psql -U production_user trading_bot < backup_file.sql
```

2. Application Recovery:
```bash
# Pull latest changes
git pull origin main

# Install dependencies
npm install --production

# Build application
npm run build

# Restart application
pm2 restart all
```

## Security Considerations

1. Firewall Configuration:
```bash
sudo ufw allow ssh
sudo ufw allow http
sudo ufw allow https
sudo ufw enable
```

2. Regular Updates:
```bash
# Update system packages
sudo apt update && sudo apt upgrade -y

# Update Node.js packages
npm audit
npm update
```

3. SSL Certificate Renewal:
```bash
sudo certbot renew
```

4. Security Headers:
The application uses Helmet.js for security headers. Additional headers can be configured in Nginx:
```nginx
add_header X-Frame-Options "SAMEORIGIN";
add_header X-XSS-Protection "1; mode=block";
add_header X-Content-Type-Options "nosniff";
```

## Troubleshooting

1. Check application logs:
```bash
pm2 logs
```

2. Check system logs:
```bash
sudo journalctl -u nginx
sudo journalctl -u postgresql
```

3. Check database connection:
```bash
psql -U production_user -d trading_bot -c "\conninfo"
```

4. Restart services:
```bash
sudo systemctl restart nginx
sudo systemctl restart postgresql
pm2 restart all
```

## Performance Tuning

1. Node.js Configuration:
```bash
# Update max old space size if needed
NODE_OPTIONS="--max-old-space-size=4096" pm2 restart all
```

2. PostgreSQL Configuration:
Edit `/etc/postgresql/14/main/postgresql.conf`:
```conf
max_connections = 100
shared_buffers = 1GB
effective_cache_size = 3GB
maintenance_work_mem = 256MB
checkpoint_completion_target = 0.9
wal_buffers = 16MB
default_statistics_target = 100
random_page_cost = 1.1
effective_io_concurrency = 200
work_mem = 10485kB
min_wal_size = 1GB
max_wal_size = 4GB
```

3. Nginx Configuration:
Edit `/etc/nginx/nginx.conf`:
```nginx
worker_processes auto;
worker_connections 1024;
keepalive_timeout 65;
gzip on;
``` 