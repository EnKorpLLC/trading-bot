# Configuration Guide

## Environment Variables

### Frontend Variables
```env
NEXT_PUBLIC_API_URL=http://localhost:3001
NEXT_PUBLIC_WS_URL=ws://localhost:3001
```

### Backend Variables
```env
# Server
PORT=3001
NODE_ENV=development

# Database
DATABASE_URL=postgresql://user:password@host:port/database

# Authentication
JWT_SECRET=your-secret-key

# TradeLocker Integration
TRADELOCKER_SERVER=default-server.tradelocker.com  # Default server
TRADELOCKER_SESSION_TIMEOUT=3600  # Session timeout in seconds
TRADELOCKER_MAX_CONNECTIONS=5     # Max concurrent connections per user
```

## Dependencies

### Frontend Dependencies
- Next.js 13+
- React 18+
- TailwindCSS
- Chart.js
- WebSocket client
- Trading View lightweight charts

### Backend Dependencies
- Express.js
- PostgreSQL (via Neon)
- WebSocket server
- JWT authentication
- TradeLocker client library
- Winston logger

## Development Setup

1. Clone the repository
```bash
git clone <repository-url>
cd trading-bot
```

2. Install dependencies
```bash
npm install
```

3. Set up environment variables
```bash
cp .env.example .env
# Edit .env with your configuration
```

4. Start development servers
```bash
npm run dev
```

## Production Setup

1. Build the application
```bash
npm run build
```

2. Start production server
```bash
npm start
```

## Security Considerations

### API Keys
- Store API keys in environment variables
- Encrypt sensitive data in database
- Regular key rotation
- Access logging and monitoring

### Authentication
- JWT token expiration
- Secure password hashing
- Rate limiting
- IP whitelisting (optional)
- Session token encryption
- Automatic session refresh
- Secure credential handling

### TradeLocker Security
- Credentials never stored locally
- Session tokens encrypted at rest
- Regular session rotation
- Secure WebSocket connections
- Rate limit monitoring
- Failed login attempt tracking

### Data Protection
- HTTPS/WSS only
- Input validation
- SQL injection prevention
- XSS protection

## Monitoring

### Application Metrics
- Server response times
- WebSocket connection status
- Database query performance
- Memory usage
- CPU utilization

### Trading Metrics
- Order execution time
- Position update latency
- Market data feed latency
- TradeLocker API response times
- Error rates

### Alerts
- Server errors
- Database connection issues
- TradeLocker connection problems
- High error rates
- Performance degradation

## Backup and Recovery

### Database Backups
- Daily automated backups
- Point-in-time recovery
- Backup verification
- Retention policy: 30 days

### Application State
- Regular state snapshots
- Transaction logs
- Recovery procedures
- Failover configuration

### TradeLocker Integration
- Connection retry mechanism
- Order status reconciliation
- Position verification
- Balance confirmation

## Logging

### Log Levels
- ERROR: Critical issues
- WARN: Potential problems
- INFO: Normal operations
- DEBUG: Detailed information

### Log Categories
- Application logs
- Access logs
- Error logs
- Trading logs
- TradeLocker integration logs

### Log Storage
- Local file rotation
- Cloud storage backup
- Log aggregation
- Search and analysis

## Maintenance

### Regular Tasks
- Database optimization
- Log rotation
- Cache clearing
- SSL certificate renewal
- API key rotation

### Updates
- Dependency updates
- Security patches
- Feature deployments
- TradeLocker client updates

### Monitoring
- System health checks
- Performance metrics
- Error tracking
- Usage statistics

## Troubleshooting

### Common Issues
1. Database Connection
   - Check connection string
   - Verify network access
   - Check credentials

2. API Integration
   - Verify API keys
   - Check rate limits
   - Monitor response times

3. WebSocket Issues
   - Check connection status
   - Verify authentication
   - Monitor message flow

4. TradeLocker Integration
   - Verify API credentials
   - Check connection status
   - Monitor rate limits
   - Verify data consistency

### Recovery Steps
1. Server Issues
   - Restart application
   - Check logs
   - Verify configuration

2. Database Issues
   - Check connections
   - Verify migrations
   - Restore from backup

3. Trading Issues
   - Verify TradeLocker connection
   - Check order status
   - Reconcile positions
   - Verify account balance 