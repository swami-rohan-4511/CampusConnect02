import React from 'react';
import {
  Container,
  Typography,
  Grid,
  Card,
  CardContent,
  CardActions,
  Button,
  Box,
  Chip,
  Avatar,
  useTheme,
} from '@mui/material';
import {
  Group,
  ShoppingCart,
  Report,
  Room,
  ShoppingBag,
  GroupWork,
  Work,
  MenuBook,
  Restaurant,
  ArrowForward,
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import { useSelector } from 'react-redux';

const Home = () => {
  const theme = useTheme();
  const navigate = useNavigate();
  const { isAuthenticated, user } = useSelector((state) => state.auth);
  const isDark = theme.palette.mode === 'dark';

  const features = [
    {
      title: 'Meetups',
      description: 'Connect with fellow students through events and gatherings',
      icon: <Group fontSize="large" color="primary" />,
      path: '/meetups',
      color: '#1976d2',
    },
    {
      title: 'Marketplace',
      description: 'Buy and sell items with real-time chat functionality',
      icon: <ShoppingCart fontSize="large" color="primary" />,
      path: '/marketplace',
      color: '#388e3c',
    },
    {
      title: 'Stolen & Found',
      description: 'Report lost items and find what others have found',
      icon: <Report fontSize="large" color="primary" />,
      path: '/stolen-found',
      color: '#f57c00',
    },
    {
      title: 'Rooms & Roommates',
      description: 'Find accommodation and connect with potential roommates',
      icon: <Room fontSize="large" color="primary" />,
      path: '/rooms',
      color: '#7b1fa2',
    },
    {
      title: 'Rental Hub',
      description: 'Rent gadgets, books, and equipment from fellow students',
      icon: <ShoppingBag fontSize="large" color="primary" />,
      path: '/rental',
      color: '#d32f2f',
    },
    {
      title: 'Clubs & Communities',
      description: 'Join clubs and participate in campus activities',
      icon: <GroupWork fontSize="large" color="primary" />,
      path: '/clubs',
      color: '#0288d1',
    },
    {
      title: 'Jobs & Internships',
      description: 'Find job opportunities and internship positions',
      icon: <Work fontSize="large" color="primary" />,
      path: '/jobs',
      color: '#689f38',
    },
    {
      title: 'Notes & Resources',
      description: 'Share study materials and find printing services',
      icon: <MenuBook fontSize="large" color="primary" />,
      path: '/notes',
      color: '#f06292',
    },
    {
      title: 'Food Services',
      description: 'Discover campus eateries and food delivery options',
      icon: <Restaurant fontSize="large" color="primary" />,
      path: '/food',
      color: '#ff7043',
    },
  ];

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      {/* Hero Section */}
      <Box
        sx={{
          textAlign: 'center',
          py: 8,
          px: 3,
          background: isDark
            ? 'linear-gradient(135deg, #0d1b2a 0%, #1a1a2e 50%, #16213e 100%)'
            : `linear-gradient(135deg, ${theme.palette.primary.main} 0%, ${theme.palette.secondary.main} 100%)`,
          borderRadius: 4,
          color: 'white',
          mb: 6,
          border: isDark ? '1px solid rgba(255,255,255,0.08)' : 'none',
          boxShadow: isDark
            ? '0 8px 32px rgba(0,0,0,0.5)'
            : '0 8px 32px rgba(25,118,210,0.3)',
          position: 'relative',
          overflow: 'hidden',
          '&::before': isDark
            ? {
                content: '""',
                position: 'absolute',
                top: 0,
                left: 0,
                right: 0,
                bottom: 0,
                background:
                  'radial-gradient(circle at 20% 50%, rgba(25,118,210,0.15) 0%, transparent 60%), radial-gradient(circle at 80% 20%, rgba(220,0,78,0.1) 0%, transparent 50%)',
                pointerEvents: 'none',
              }
            : {},
        }}
      >
        <Typography
          variant="h2"
          component="h1"
          gutterBottom
          fontWeight="bold"
          sx={{
            textShadow: isDark ? '0 2px 12px rgba(0,0,0,0.6)' : 'none',
          }}
        >
          Welcome to Campus Connect
        </Typography>
        <Typography
          variant="h5"
          component="p"
          sx={{ mb: 4, opacity: isDark ? 0.75 : 0.9 }}
        >
          Your one-stop platform for all campus needs
        </Typography>
        {isAuthenticated ? (
          <Box sx={{ display: 'flex', justifyContent: 'center', gap: 2, flexWrap: 'wrap' }}>
            <Chip
              avatar={<Avatar>{user?.full_name?.charAt(0) || user?.email?.charAt(0)}</Avatar>}
              label={`Welcome back, ${user?.full_name || user?.email}!`}
              sx={{
                bgcolor: isDark ? 'rgba(255,255,255,0.1)' : 'rgba(255,255,255,0.2)',
                color: 'white',
                border: isDark ? '1px solid rgba(255,255,255,0.15)' : 'none',
              }}
            />
          </Box>
        ) : (
          <Box sx={{ display: 'flex', justifyContent: 'center', gap: 2 }}>
            <Button
              variant="contained"
              size="large"
              onClick={() => navigate('/signup')}
              sx={{
                bgcolor: 'white',
                color: isDark ? '#0d1b2a' : theme.palette.primary.main,
                fontWeight: 700,
                '&:hover': { bgcolor: 'rgba(255,255,255,0.88)' },
              }}
            >
              Get Started
            </Button>
            <Button
              variant="outlined"
              size="large"
              onClick={() => navigate('/login')}
              sx={{
                borderColor: isDark ? 'rgba(255,255,255,0.5)' : 'white',
                color: 'white',
                '&:hover': {
                  bgcolor: 'rgba(255,255,255,0.1)',
                  borderColor: 'white',
                },
              }}
            >
              Sign In
            </Button>
          </Box>
        )}
      </Box>

      {/* Features Grid */}
      <Typography variant="h3" component="h2" textAlign="center" gutterBottom fontWeight="bold">
        Explore Our Features
      </Typography>
      <Typography variant="h6" component="p" textAlign="center" color="text.secondary" sx={{ mb: 6 }}>
        Everything you need for your campus life, all in one place
      </Typography>

      <Grid container spacing={4}>
        {features.map((feature, index) => (
          <Grid item xs={12} sm={6} md={4} key={index}>
            <Card
              sx={{
                height: '100%',
                display: 'flex',
                flexDirection: 'column',
                transition: 'transform 0.2s, box-shadow 0.2s',
                bgcolor: isDark ? 'background.paper' : 'white',
                '&:hover': {
                  transform: 'translateY(-4px)',
                  boxShadow: theme.shadows[8],
                },
              }}
            >
              <CardContent sx={{ flexGrow: 1, textAlign: 'center' }}>
                <Box sx={{ mb: 2 }}>{feature.icon}</Box>
                <Typography variant="h5" component="h3" gutterBottom fontWeight="bold">
                  {feature.title}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  {feature.description}
                </Typography>
              </CardContent>
              <CardActions sx={{ justifyContent: 'center', pb: 2 }}>
                <Button
                  variant="contained"
                  endIcon={<ArrowForward />}
                  onClick={() => navigate(feature.path)}
                  sx={{
                    backgroundColor: feature.color,
                    '&:hover': { backgroundColor: feature.color, opacity: 0.88 },
                  }}
                >
                  Explore
                </Button>
              </CardActions>
            </Card>
          </Grid>
        ))}
      </Grid>

      {/* Stats Section */}
      <Box
        sx={{
          mt: 8,
          py: 6,
          px: 4,
          background: isDark
            ? 'linear-gradient(135deg, #1a1a2e 0%, #16213e 100%)'
            : 'linear-gradient(135deg, #f5f7fa 0%, #e8ecf1 100%)',
          borderRadius: 4,
          textAlign: 'center',
          border: isDark ? '1px solid rgba(255,255,255,0.06)' : 'none',
        }}
      >
        <Typography variant="h4" component="h3" gutterBottom fontWeight="bold">
          Join Thousands of Students
        </Typography>
        <Typography variant="body1" color="text.secondary" sx={{ mb: 4 }}>
          Connect, share, and thrive in your campus community
        </Typography>
        <Grid container spacing={4} justifyContent="center">
          {[
            { value: '10K+', label: 'Active Users' },
            { value: '500+', label: 'Daily Transactions' },
            { value: '50+', label: 'Campus Clubs' },
            { value: '24/7', label: 'Support' },
          ].map((stat) => (
            <Grid item xs={6} sm={3} key={stat.label}>
              <Typography variant="h3" color="primary" fontWeight="bold">
                {stat.value}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                {stat.label}
              </Typography>
            </Grid>
          ))}
        </Grid>
      </Box>
    </Container>
  );
};

export default Home;
