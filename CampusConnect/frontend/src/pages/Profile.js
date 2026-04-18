import React, { useEffect, useState } from 'react';
import {
  Container, Box, Typography, Avatar, Grid, Card, CardContent,
  CardMedia, Chip, CircularProgress, Alert, Divider, Button,
  Tabs, Tab, Badge, Tooltip,
} from '@mui/material';
import {
  Restaurant, Group, ShoppingCart, MeetingRoom, ShoppingBag,
  Groups, Work, MenuBook, Store, CalendarToday, LocationOn,
  AttachMoney, Download,
} from '@mui/icons-material';
import axios from 'axios';
import { useSelector } from 'react-redux';
import { useNavigate } from 'react-router-dom';

const STATUS_COLORS = {
  available: 'success', sold: 'default', rented: 'warning',
  active: 'success', closed: 'default', inactive: 'default',
};

const fmt = (iso) => {
  if (!iso) return '';
  return new Date(iso).toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' });
};

const TABS = [
  { key: 'food_stalls', label: 'Food Stalls', icon: <Store fontSize="small" />, path: '/food', emoji: '🍽️' },
  { key: 'meetups', label: 'Meetups', icon: <Group fontSize="small" />, path: '/meetups', emoji: '👥' },
  { key: 'marketplace', label: 'Marketplace', icon: <ShoppingCart fontSize="small" />, path: '/marketplace', emoji: '🛒' },
  { key: 'rooms', label: 'Rooms', icon: <MeetingRoom fontSize="small" />, path: '/rooms', emoji: '🏠' },
  { key: 'rentals', label: 'Rentals', icon: <ShoppingBag fontSize="small" />, path: '/rental', emoji: '📦' },
  { key: 'clubs', label: 'Clubs', icon: <Groups fontSize="small" />, path: '/clubs', emoji: '🎭' },
  { key: 'jobs', label: 'Jobs', icon: <Work fontSize="small" />, path: '/jobs', emoji: '💼' },
  { key: 'notes', label: 'Notes', icon: <MenuBook fontSize="small" />, path: '/notes', emoji: '📝' },
];

const Profile = () => {
  const { user, token } = useSelector((s) => s.auth);
  const navigate = useNavigate();
  const [activity, setActivity] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [tab, setTab] = useState(0);

  useEffect(() => {
    if (!token) { setLoading(false); return; }
    axios.get('/profile/activity', { headers: { Authorization: `Bearer ${token}` } })
      .then((r) => setActivity(r.data))
      .catch(() => setError('Could not load your activity. Please try again.'))
      .finally(() => setLoading(false));
  }, [token]);

  if (!user) {
    return (
      <Container maxWidth="sm" sx={{ py: 8, textAlign: 'center' }}>
        <Typography variant="h6" gutterBottom>Please log in to view your profile</Typography>
        <Button variant="contained" onClick={() => navigate('/login')}>Log In</Button>
      </Container>
    );
  }

  const totalListings = activity
    ? Object.values(activity).reduce((s, arr) => s + arr.length, 0)
    : 0;

  const tabInfo = TABS[tab];
  const items = activity?.[tabInfo.key] ?? [];

  const EmptyCard = ({ tabItem }) => (
    <Box sx={{ textAlign: 'center', py: 6, color: 'text.secondary' }}>
      <Typography sx={{ fontSize: 48, mb: 1 }}>{tabItem.emoji}</Typography>
      <Typography variant="body1">No {tabItem.label.toLowerCase()} listed yet</Typography>
      <Button variant="outlined" size="small" sx={{ mt: 1.5 }} onClick={() => navigate(tabItem.path)}>
        Go to {tabItem.label}
      </Button>
    </Box>
  );

  const ItemCard = ({ children, path }) => (
    <Card variant="outlined" sx={{
      borderRadius: 2, height: '100%', display: 'flex', flexDirection: 'column',
      cursor: 'pointer', transition: 'box-shadow 0.2s',
      '&:hover': { boxShadow: 4 },
    }} onClick={() => navigate(path)}>
      {children}
    </Card>
  );

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      {/* ── Profile header ── */}
      <Card sx={{ mb: 4, borderRadius: 3, overflow: 'visible' }}>
        <Box sx={{
          height: 120,
          background: 'linear-gradient(135deg, #1976d2 0%, #42a5f5 60%, #90caf9 100%)',
          borderRadius: '12px 12px 0 0',
        }} />
        <CardContent sx={{ pt: 0, pb: 3, px: { xs: 2, sm: 4 } }}>
          <Box sx={{ display: 'flex', alignItems: 'flex-end', gap: 3, mt: '-40px', flexWrap: 'wrap' }}>
            <Avatar sx={{
              width: 88, height: 88, fontSize: '2rem', fontWeight: 'bold',
              bgcolor: 'primary.dark', border: '4px solid white', boxShadow: 3,
            }}>
              {(user.full_name || user.email || '?')[0].toUpperCase()}
            </Avatar>
            <Box sx={{ flexGrow: 1, pb: 0.5 }}>
              <Typography variant="h5" fontWeight="bold">{user.full_name || 'Campus User'}</Typography>
              <Typography variant="body2" color="text.secondary">{user.email}</Typography>
            </Box>
            <Box sx={{ display: 'flex', gap: 3, flexWrap: 'wrap', pb: 0.5, alignItems: 'center' }}>
              <Box sx={{ textAlign: 'center' }}>
                <Typography variant="h5" fontWeight="bold" color="primary">{totalListings}</Typography>
                <Typography variant="caption" color="text.secondary">Total Listings</Typography>
              </Box>
              {activity && TABS.filter((t) => (activity[t.key]?.length ?? 0) > 0).map((t) => (
                <Tooltip key={t.key} title={t.label}>
                  <Box sx={{ textAlign: 'center', cursor: 'pointer' }} onClick={() => setTab(TABS.indexOf(t))}>
                    <Typography variant="h6" fontWeight="bold">{activity[t.key].length}</Typography>
                    <Typography variant="caption" color="text.secondary" sx={{ display: 'flex', alignItems: 'center', gap: 0.3 }}>
                      {t.icon} {t.label}
                    </Typography>
                  </Box>
                </Tooltip>
              ))}
            </Box>
          </Box>
        </CardContent>
      </Card>

      {error && <Alert severity="error" sx={{ mb: 3 }}>{error}</Alert>}

      {loading ? (
        <Box sx={{ display: 'flex', justifyContent: 'center', py: 8 }}><CircularProgress /></Box>
      ) : !activity ? null : (
        <>
          {/* ── Tabs ── */}
          <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 3 }}>
            <Tabs value={tab} onChange={(_, v) => setTab(v)} variant="scrollable" scrollButtons="auto">
              {TABS.map((t, i) => (
                <Tab key={t.key}
                  icon={
                    <Badge badgeContent={activity[t.key]?.length ?? 0} color="primary"
                      sx={{ '& .MuiBadge-badge': { fontSize: '0.6rem', minWidth: 16, height: 16 } }}>
                      {t.icon}
                    </Badge>
                  }
                  iconPosition="start"
                  label={t.label}
                  sx={{ minHeight: 48, textTransform: 'none', fontWeight: 600 }}
                />
              ))}
            </Tabs>
          </Box>

          {/* ── Tab content ── */}
          {items.length === 0 ? (
            <EmptyCard tabItem={tabInfo} />
          ) : (
            <Grid container spacing={2}>

              {/* Food Stalls */}
              {tabInfo.key === 'food_stalls' && items.map((s) => (
                <Grid item xs={12} sm={6} md={4} key={s.id}>
                  <ItemCard path="/food">
                    {s.image_url
                      ? <CardMedia component="img" height="140" image={s.image_url} alt={s.name} sx={{ objectFit: 'cover' }} />
                      : <Box sx={{ height: 8, bgcolor: 'primary.main' }} />}
                    <CardContent sx={{ p: 2 }}>
                      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 1 }}>
                        <Typography variant="subtitle1" fontWeight="bold">{s.name}</Typography>
                        <Chip label={s.type} size="small" color="primary" variant="outlined" />
                      </Box>
                      {s.location && <Box sx={{ display: 'flex', gap: 0.5, alignItems: 'center' }}>
                        <LocationOn sx={{ fontSize: 14 }} color="action" />
                        <Typography variant="caption" color="text.secondary">{s.location}</Typography>
                      </Box>}
                      <Typography variant="caption" color="text.disabled" sx={{ mt: 0.5, display: 'block' }}>Listed {fmt(s.created_at)}</Typography>
                    </CardContent>
                  </ItemCard>
                </Grid>
              ))}

              {/* Meetups */}
              {tabInfo.key === 'meetups' && items.map((m) => (
                <Grid item xs={12} sm={6} md={4} key={m.id}>
                  <ItemCard path="/meetups">
                    <CardContent sx={{ p: 2 }}>
                      <Typography variant="subtitle1" fontWeight="bold" gutterBottom>{m.title}</Typography>
                      {m.location && <Box sx={{ display: 'flex', gap: 0.5, alignItems: 'center', mb: 0.5 }}>
                        <LocationOn sx={{ fontSize: 14 }} color="action" />
                        <Typography variant="caption" color="text.secondary">{m.location}</Typography>
                      </Box>}
                      {m.event_date && <Box sx={{ display: 'flex', gap: 0.5, alignItems: 'center', mb: 0.5 }}>
                        <CalendarToday sx={{ fontSize: 14 }} color="action" />
                        <Typography variant="caption" color="text.secondary">{fmt(m.event_date)}</Typography>
                      </Box>}
                      {m.description && <Typography variant="caption" color="text.secondary"
                        sx={{ display: '-webkit-box', WebkitLineClamp: 2, WebkitBoxOrient: 'vertical', overflow: 'hidden' }}>
                        {m.description}
                      </Typography>}
                    </CardContent>
                  </ItemCard>
                </Grid>
              ))}

              {/* Marketplace */}
              {tabInfo.key === 'marketplace' && items.map((item) => (
                <Grid item xs={12} sm={6} md={4} key={item.id}>
                  <ItemCard path="/marketplace">
                    <CardContent sx={{ p: 2 }}>
                      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 1 }}>
                        <Typography variant="subtitle1" fontWeight="bold" sx={{ flexGrow: 1, mr: 1 }}>{item.title}</Typography>
                        <Chip label={item.status || 'available'} size="small" color={STATUS_COLORS[item.status] || 'success'} />
                      </Box>
                      <Box sx={{ display: 'flex', gap: 0.5, alignItems: 'center', mb: 0.5 }}>
                        <AttachMoney sx={{ fontSize: 14 }} color="action" />
                        <Typography variant="body2" fontWeight="bold" color="primary">₹{parseFloat(item.price).toFixed(0)}</Typography>
                      </Box>
                      <Chip label={item.category} size="small" variant="outlined" />
                      <Typography variant="caption" color="text.disabled" sx={{ display: 'block', mt: 0.5 }}>Listed {fmt(item.created_at)}</Typography>
                    </CardContent>
                  </ItemCard>
                </Grid>
              ))}

              {/* Rooms */}
              {tabInfo.key === 'rooms' && items.map((r) => (
                <Grid item xs={12} sm={6} md={4} key={r.id}>
                  <ItemCard path="/rooms">
                    <CardContent sx={{ p: 2 }}>
                      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 1 }}>
                        <Typography variant="subtitle1" fontWeight="bold" sx={{ flexGrow: 1, mr: 1 }}>{r.title}</Typography>
                        <Chip label={r.status || 'available'} size="small" color={STATUS_COLORS[r.status] || 'success'} />
                      </Box>
                      {r.location && <Box sx={{ display: 'flex', gap: 0.5, alignItems: 'center', mb: 0.5 }}>
                        <LocationOn sx={{ fontSize: 14 }} color="action" />
                        <Typography variant="caption" color="text.secondary">{r.location}</Typography>
                      </Box>}
                      <Typography variant="body2" fontWeight="bold" color="primary">₹{parseFloat(r.rent_amount).toFixed(0)}/mo</Typography>
                      <Chip label={r.room_type} size="small" variant="outlined" sx={{ mt: 0.5 }} />
                    </CardContent>
                  </ItemCard>
                </Grid>
              ))}

              {/* Rentals */}
              {tabInfo.key === 'rentals' && items.map((r) => (
                <Grid item xs={12} sm={6} md={4} key={r.id}>
                  <ItemCard path="/rental">
                    <CardContent sx={{ p: 2 }}>
                      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 1 }}>
                        <Typography variant="subtitle1" fontWeight="bold" sx={{ flexGrow: 1, mr: 1 }}>{r.name}</Typography>
                        <Chip label={r.availability_status ? 'Available' : 'Unavailable'} size="small"
                          color={r.availability_status ? 'success' : 'default'} />
                      </Box>
                      <Typography variant="body2" fontWeight="bold" color="primary">₹{parseFloat(r.daily_rate).toFixed(0)}/day</Typography>
                      <Chip label={r.category} size="small" variant="outlined" sx={{ mt: 0.5 }} />
                      <Typography variant="caption" color="text.disabled" sx={{ display: 'block', mt: 0.5 }}>Listed {fmt(r.created_at)}</Typography>
                    </CardContent>
                  </ItemCard>
                </Grid>
              ))}

              {/* Clubs */}
              {tabInfo.key === 'clubs' && items.map((c) => (
                <Grid item xs={12} sm={6} md={4} key={c.id}>
                  <ItemCard path="/clubs">
                    <CardContent sx={{ p: 2 }}>
                      <Typography variant="subtitle1" fontWeight="bold" gutterBottom>{c.name}</Typography>
                      <Chip label={c.category} size="small" color="secondary" sx={{ mb: 1 }} />
                      <Typography variant="caption" color="text.disabled" sx={{ display: 'block' }}>Founded {fmt(c.created_at)}</Typography>
                    </CardContent>
                  </ItemCard>
                </Grid>
              ))}

              {/* Jobs */}
              {tabInfo.key === 'jobs' && items.map((j) => (
                <Grid item xs={12} sm={6} md={4} key={j.id}>
                  <ItemCard path="/jobs">
                    <CardContent sx={{ p: 2 }}>
                      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 1 }}>
                        <Typography variant="subtitle1" fontWeight="bold" sx={{ flexGrow: 1, mr: 1 }}>{j.title}</Typography>
                        <Chip label={j.status || 'active'} size="small" color={STATUS_COLORS[j.status] || 'success'} />
                      </Box>
                      <Typography variant="body2" color="text.secondary">{j.company_name}</Typography>
                      <Chip label={j.job_type} size="small" variant="outlined" sx={{ mt: 0.5 }} />
                      <Typography variant="caption" color="text.disabled" sx={{ display: 'block', mt: 0.5 }}>Posted {fmt(j.created_at)}</Typography>
                    </CardContent>
                  </ItemCard>
                </Grid>
              ))}

              {/* Notes */}
              {tabInfo.key === 'notes' && items.map((n) => (
                <Grid item xs={12} sm={6} md={4} key={n.id}>
                  <ItemCard path="/notes">
                    <CardContent sx={{ p: 2 }}>
                      <Typography variant="subtitle1" fontWeight="bold" gutterBottom>{n.title}</Typography>
                      <Typography variant="body2" color="text.secondary" gutterBottom>{n.subject}</Typography>
                      <Box sx={{ display: 'flex', gap: 1, alignItems: 'center', flexWrap: 'wrap' }}>
                        <Chip label={n.file_type?.toUpperCase() || 'PDF'} size="small" color="primary" variant="outlined" />
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.3 }}>
                          <Download sx={{ fontSize: 14 }} color="action" />
                          <Typography variant="caption" color="text.secondary">{n.download_count || 0} downloads</Typography>
                        </Box>
                      </Box>
                      <Typography variant="caption" color="text.disabled" sx={{ display: 'block', mt: 0.5 }}>Uploaded {fmt(n.created_at)}</Typography>
                    </CardContent>
                  </ItemCard>
                </Grid>
              ))}

            </Grid>
          )}
        </>
      )}
    </Container>
  );
};

export default Profile;
