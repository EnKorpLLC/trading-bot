import { Box, Container, Typography } from '@mui/material';

export default function Home() {
  return (
    <Container maxWidth="xl">
      <Box sx={{ my: 4 }}>
        <Typography variant="h2" component="h1" gutterBottom>
          Trading Bot Platform
        </Typography>
        <Typography variant="h5" component="h2" gutterBottom>
          AI-powered Forex trading with TradeLocker integration
        </Typography>
      </Box>
    </Container>
  );
} 