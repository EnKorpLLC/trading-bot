# Configuration Management

## Environment Variables

### Core Configuration
```env
NODE_ENV=development|production
PORT=3000
HOST=localhost
```

### Database Configuration
```env
DATABASE_URL=postgres://user:password@neon.tech:5432/dbname
DATABASE_SSL=true
DATABASE_MAX_CONNECTIONS=20
DATABASE_IDLE_TIMEOUT=10000
```

### TradeLocker API
```env
TRADELOCKER_API_URL=https://api.tradelocker.com
TRADELOCKER_WS_URL=wss://stream.tradelocker.com
TRADELOCKER_API_KEY=your_api_key
TRADELOCKER_API_SECRET=your_api_secret
```

### Authentication
```env
JWT_SECRET=your_jwt_secret
JWT_EXPIRY=24h
REFRESH_TOKEN_EXPIRY=7d
SESSION_SECRET=your_session_secret
```

### Security
```env
CORS_ORIGIN=https://yourdomain.com
RATE_LIMIT_WINDOW=15m
RATE_LIMIT_MAX=100
TLS_KEY_PATH=/path/to/key.pem
TLS_CERT_PATH=/path/to/cert.pem
```

### AI System
```env
AI_MODEL_PATH=/path/to/models
AI_UPDATE_INTERVAL=24h
AI_CONFIDENCE_THRESHOLD=0.75
MAX_PARALLEL_STRATEGIES=5
```

## Configuration Files

### Next.js Configuration
```javascript
// next.config.js
module.exports = {
  env: {
    API_URL: process.env.API_URL,
  },
  webpack: (config, { isServer }) => {
    // Custom webpack configuration
    return config
  },
}
```

### TypeScript Configuration
```json
// tsconfig.json
{
  "compilerOptions": {
    "target": "es5",
    "lib": ["dom", "dom.iterable", "esnext"],
    "allowJs": true,
    "skipLibCheck": true,
    "strict": true,
    "forceConsistentCasingInFileNames": true,
    "noEmit": true,
    "esModuleInterop": true,
    "module": "esnext",
    "moduleResolution": "node",
    "resolveJsonModule": true,
    "isolatedModules": true,
    "jsx": "preserve",
    "incremental": true
  },
  "include": ["next-env.d.ts", "**/*.ts", "**/*.tsx"],
  "exclude": ["node_modules"]
}
```

## Development Environments

### Local Development
```env
NODE_ENV=development
API_URL=http://localhost:3000
WS_URL=ws://localhost:3001
DATABASE_URL=postgres://localhost:5432/tradingbot_dev
```

### Staging Environment
```env
NODE_ENV=staging
API_URL=https://staging-api.tradingbot.com
WS_URL=wss://staging-ws.tradingbot.com
DATABASE_URL=postgres://staging.neon.tech/tradingbot_staging
```

### Production Environment
```env
NODE_ENV=production
API_URL=https://api.tradingbot.com
WS_URL=wss://ws.tradingbot.com
DATABASE_URL=postgres://prod.neon.tech/tradingbot_prod
```

## Deployment Configuration

### Vercel Configuration
```json
{
  "version": 2,
  "builds": [
    {
      "src": "package.json",
      "use": "@vercel/next"
    }
  ],
  "env": {
    "NODE_ENV": "production",
    "DATABASE_URL": "@database_url"
  }
}
```

### Docker Configuration
```dockerfile
# Dockerfile
FROM node:18-alpine
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build
EXPOSE 3000
CMD ["npm", "start"]
```

## Security Configurations

### CORS Configuration
```javascript
const corsOptions = {
  origin: process.env.CORS_ORIGIN,
  methods: ['GET', 'POST', 'PUT', 'DELETE'],
  allowedHeaders: ['Content-Type', 'Authorization'],
  credentials: true
};
```

### Rate Limiting
```javascript
const rateLimitConfig = {
  windowMs: 15 * 60 * 1000, // 15 minutes
  max: 100 // limit each IP to 100 requests per windowMs
};
```

## Monitoring Configuration

### Logging
```javascript
const loggingConfig = {
  level: process.env.LOG_LEVEL || 'info',
  format: winston.format.json(),
  transports: [
    new winston.transports.Console(),
    new winston.transports.File({ filename: 'error.log', level: 'error' }),
    new winston.transports.File({ filename: 'combined.log' })
  ]
};
```

### Performance Monitoring
```javascript
const performanceConfig = {
  metricsInterval: 60000, // 1 minute
  histogramBuckets: [0.1, 0.5, 1, 2, 5],
  defaultLabels: { service: 'trading-bot' }
};
``` 