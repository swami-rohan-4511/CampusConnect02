import React, { useState, useEffect } from 'react';
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
  Fab,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Alert,
  useTheme,
} from '@mui/material';
import {
  Add,
  Group,
  LocationOn,
  Person,
  Event,
  AccessTime,
} from '@mui/icons-material';
import { useSelector } from 'react-redux';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';

const Meetups = () => {
  const theme = useTheme();
  const navigate = useNavigate();
  const { isAuthenticated, user } = useSelector((state) => state.auth);

  const [meetups, setMeetups] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [openDialog, setOpenDialog] = useState(false);
  const [formData, setFormData] = useState({
    title: '',
    description: '',
    host_name: '',
    social_handle: '',
    location: '',
    event_date: '',
    max_participants: '',
  });

  const API_BASE_URL = process.env.REACT_APP_API_URL || '';

  useEffect(() => {
    fetchMeetups();
  }, []);

  const fetchMeetups = async () => {
    try {
      setLoading(true);
      const response = await axios.get(`${API_BASE_URL}/meetups`);
      setMeetups(response.data);
      setError(null);
    } catch (err) {
      setError('Failed to load meetups');
      console.error('Error fetching meetups:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateMeetup = async () => {
    if (!isAuthenticated) {
      navigate('/login');
      return;
    }

    try {
      const token = localStorage.getItem('token');
      const response = await axios.post(`${API_BASE_URL}/meetups`, formData, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      setMeetups([response.data, ...meetups]);
      setOpenDialog(false);
      setFormData({
        title: '',
        description: '',
        host_name: '',
        social_handle: '',
        location: '',
        event_date: '',
        max_participants: '',
      });
    } catch (err) {
      console.error('Error creating meetup:', err);
      setError('Failed to create meetup');
    }
  };

  const handleRSVP = async (meetupId, status) => {
    if (!isAuthenticated) {
      navigate('/login');
      return;
    }

    try {
      const token = localStorage.getItem('token');
      await axios.post(`${API_BASE_URL}/meetups/${meetupId}/rsvp`, { status }, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      // Update the meetup in the list
      setMeetups(meetups.map(meetup =>
        meetup.id === meetupId
          ? { ...meetup, participant_count: status === 'yes' ? meetup.participant_count + 1 : meetup.participant_count }
          : meetup
      ));
    } catch (err) {
      console.error('Error RSVPing to meetup:', err);
    }
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      weekday: 'long',
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  if (loading) {
    return (
      <Container maxWidth="lg" sx={{ py: 4 }}>
        <Typography variant="h4" align="center">Loading meetups...</Typography>
      </Container>
    );
  }

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 4 }}>
        <Typography variant="h3" component="h1" fontWeight="bold">
          Campus Meetups
        </Typography>
        {isAuthenticated && (
          <Fab
            color="primary"
            aria-label="add meetup"
            onClick={() => setOpenDialog(true)}
            sx={{ boxShadow: theme.shadows[8] }}
          >
            <Add />
          </Fab>
        )}
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}

      {!isAuthenticated && (
        <Alert severity="info" sx={{ mb: 3 }}>
          Please <Button onClick={() => navigate('/login')}>sign in</Button> to create meetups and RSVP to events.
        </Alert>
      )}

      <Grid container spacing={3}>
        {meetups.map((meetup) => (
          <Grid item xs={12} md={6} lg={4} key={meetup.id}>
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
              <CardContent sx={{ flexGrow: 1 }}>
                <Typography variant="h5" component="h2" gutterBottom fontWeight="bold">
                  {meetup.title}
                </Typography>

                <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                  <Person sx={{ mr: 1, color: 'text.secondary' }} />
                  <Typography variant="body2" color="text.secondary">
                    Hosted by {meetup.host_name}
                  </Typography>
                </Box>

                <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                  <LocationOn sx={{ mr: 1, color: 'text.secondary' }} />
                  <Typography variant="body2" color="text.secondary">
                    {meetup.location}
                  </Typography>
                </Box>

                <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                  <Event sx={{ mr: 1, color: 'text.secondary' }} />
                  <Typography variant="body2" color="text.secondary">
                    {formatDate(meetup.event_date)}
                  </Typography>
                </Box>

                <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                  <Group sx={{ mr: 1, color: 'text.secondary' }} />
                  <Typography variant="body2" color="text.secondary">
                    {meetup.participant_count || 0} attending
                    {meetup.max_participants && ` / ${meetup.max_participants} max`}
                  </Typography>
                </Box>

                <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                  {meetup.description}
                </Typography>

                <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                  <Chip
                    size="small"
                    label={`${meetup.participant_count || 0} attending`}
                    color="primary"
                    variant="outlined"
                  />
                  {meetup.max_participants && (
                    <Chip
                      size="small"
                      label={`Max: ${meetup.max_participants}`}
                      color="secondary"
                      variant="outlined"
                    />
                  )}
                </Box>
              </CardContent>

              <CardActions>
                {isAuthenticated && (
                  <Box sx={{ display: 'flex', gap: 1, width: '100%' }}>
                    <Button
                      size="small"
                      variant="contained"
                      color="primary"
                      onClick={() => handleRSVP(meetup.id, 'yes')}
                      sx={{ flex: 1 }}
                    >
                      RSVP Yes
                    </Button>
                    <Button
                      size="small"
                      variant="outlined"
                      onClick={() => handleRSVP(meetup.id, 'maybe')}
                      sx={{ flex: 1 }}
                    >
                      Maybe
                    </Button>
                  </Box>
                )}
              </CardActions>
            </Card>
          </Grid>
        ))}
      </Grid>

      {meetups.length === 0 && !loading && (
        <Box sx={{ textAlign: 'center', py: 8 }}>
          <Group sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
          <Typography variant="h5" color="text.secondary" gutterBottom>
            No meetups found
          </Typography>
          <Typography variant="body1" color="text.secondary">
            Be the first to create a meetup for your campus community!
          </Typography>
        </Box>
      )}

      {/* Create Meetup Dialog */}
      <Dialog open={openDialog} onClose={() => setOpenDialog(false)} maxWidth="md" fullWidth>
        <DialogTitle>Create New Meetup</DialogTitle>
        <DialogContent>
          <TextField
            autoFocus
            margin="dense"
            label="Title"
            fullWidth
            variant="outlined"
            value={formData.title}
            onChange={(e) => setFormData({ ...formData, title: e.target.value })}
            sx={{ mb: 2 }}
          />
          <TextField
            margin="dense"
            label="Description"
            fullWidth
            multiline
            rows={3}
            variant="outlined"
            value={formData.description}
            onChange={(e) => setFormData({ ...formData, description: e.target.value })}
            sx={{ mb: 2 }}
          />
          <TextField
            margin="dense"
            label="Host Name"
            fullWidth
            variant="outlined"
            value={formData.host_name}
            onChange={(e) => setFormData({ ...formData, host_name: e.target.value })}
            sx={{ mb: 2 }}
          />
          <TextField
            margin="dense"
            label="Social Handle (Optional)"
            fullWidth
            variant="outlined"
            value={formData.social_handle}
            onChange={(e) => setFormData({ ...formData, social_handle: e.target.value })}
            sx={{ mb: 2 }}
          />
          <TextField
            margin="dense"
            label="Location"
            fullWidth
            variant="outlined"
            value={formData.location}
            onChange={(e) => setFormData({ ...formData, location: e.target.value })}
            sx={{ mb: 2 }}
          />
          <TextField
            margin="dense"
            label="Event Date & Time"
            type="datetime-local"
            fullWidth
            variant="outlined"
            value={formData.event_date}
            onChange={(e) => setFormData({ ...formData, event_date: e.target.value })}
            InputLabelProps={{
              shrink: true,
            }}
            sx={{ mb: 2 }}
          />
          <TextField
            margin="dense"
            label="Max Participants (Optional)"
            type="number"
            fullWidth
            variant="outlined"
            value={formData.max_participants}
            onChange={(e) => setFormData({ ...formData, max_participants: e.target.value })}
            sx={{ mb: 2 }}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenDialog(false)}>Cancel</Button>
          <Button onClick={handleCreateMeetup} variant="contained">
            Create Meetup
          </Button>
        </DialogActions>
      </Dialog>
    </Container>
  );
};

export default Meetups;