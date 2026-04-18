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
      title: 'Notes & Printing',
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
          background: `linear-gradient(135deg, ${theme.palette.primary.main} 0%, ${theme.palette.secondary.main} 100%)`,
          borderRadius: 4,
          color: 'white',
          mb: 6,
        }}
      >
        <Typography variant="h2" component="h1" gutterBottom fontWeight="bold">
          Welcome to Campus Connect
        </Typography>
        <Typography variant="h5" component="p" sx={{ mb: 4, opacity: 0.9 }}>
          Your one-stop platform for all campus needs
        </Typography>
        {isAuthenticated ? (
          <Box sx={{ display: 'flex', justifyContent: 'center', gap: 2, flexWrap: 'wrap' }}>
            <Chip
              avatar={<Avatar>{user?.full_name?.charAt(0) || user?.email?.charAt(0)}</Avatar>}
              label={`Welcome back, ${user?.full_name || user?.email}!`}
              sx={{ bgcolor: 'rgba(255, 255, 255, 0.2)', color: 'white' }}
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
                color: theme.palette.primary.main,
                '&:hover': { bgcolor: 'rgba(255, 255, 255, 0.9)' },
              }}
            >
              Get Started
            </Button>
            <Button
              variant="outlined"
              size="large"
              onClick={() => navigate('/login')}
              sx={{
                borderColor: 'white',
                color: 'white',
                '&:hover': { bgcolor: 'rgba(255, 255, 255, 0.1)' },
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
                '&:hover': {
                  transform: 'translateY(-4px)',
                  boxShadow: theme.shadows[8],
                },
              }}
            >
              <CardContent sx={{ flexGrow: 1, textAlign: 'center' }}>
                <Box sx={{ mb: 2 }}>
                  {feature.icon}
                </Box>
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
                    '&:hover': {
                      backgroundColor: feature.color,
                      opacity: 0.9,
                    },
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
          backgroundColor: theme.palette.grey[100],
          borderRadius: 4,
          textAlign: 'center',
        }}
      >
        <Typography variant="h4" component="h3" gutterBottom fontWeight="bold">
          Join Thousands of Students
        </Typography>
        <Typography variant="body1" color="text.secondary" sx={{ mb: 4 }}>
          Connect, share, and thrive in your campus community
        </Typography>
        <Grid container spacing={4} justifyContent="center">
          <Grid item xs={6} sm={3}>
            <Typography variant="h3" color="primary" fontWeight="bold">
              10K+
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Active Users
            </Typography>
          </Grid>
          <Grid item xs={6} sm={3}>
            <Typography variant="h3" color="primary" fontWeight="bold">
              500+
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Daily Transactions
            </Typography>
          </Grid>
          <Grid item xs={6} sm={3}>
            <Typography variant="h3" color="primary" fontWeight="bold">
              50+
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Campus Clubs
            </Typography>
          </Grid>
          <Grid item xs={6} sm={3}>
            <Typography variant="h3" color="primary" fontWeight="bold">
              24/7
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Support
            </Typography>
          </Grid>
        </Grid>
      </Box>
    </Container>
  );
};

export default Home;