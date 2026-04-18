import React, { useState, useEffect } from 'react';
import {
  Container, Typography, Box, Grid, Card, CardContent, CardActions,
  Button, Chip, Dialog, DialogTitle, DialogContent, DialogActions,
  TextField, FormControl, InputLabel, Select, MenuItem, Switch, FormControlLabel,
  Alert, CircularProgress, IconButton, InputAdornment,
  Snackbar, Divider, Avatar, Tooltip, Fab, Paper,
} from '@mui/material';
import {
  Code, Business, Brush, Group, SportsSoccer, LibraryBooks, MusicNote,
  Add, Close, Search, Delete, Email, Schedule, Person, Stars, PostAdd, HowToReg, CheckCircle,
} from '@mui/icons-material';
import axios from 'axios';
import { useSelector } from 'react-redux';
import { useNavigate } from 'react-router-dom';

const CLUB_CATEGORIES = [
  { id: 'Technical',      label: 'Technical',      icon: <Code />,         color: '#1565c0', bg: '#e3f2fd' },
  { id: 'Business',       label: 'Business',       icon: <Business />,     color: '#2e7d32', bg: '#e8f5e9' },
  { id: 'Arts & Culture', label: 'Arts & Culture', icon: <Brush />,        color: '#6a1b9a', bg: '#f3e5f5' },
  { id: 'Social',         label: 'Social',         icon: <Group />,        color: '#e65100', bg: '#fff3e0' },
  { id: 'Sports',         label: 'Sports',         icon: <SportsSoccer />, color: '#c62828', bg: '#ffebee' },
  { id: 'Academic',       label: 'Academic',       icon: <LibraryBooks />, color: '#558b2f', bg: '#f1f8e9' },
  { id: 'Cultural',       label: 'Cultural',       icon: <MusicNote />,    color: '#00838f', bg: '#e0f7fa' },
  { id: 'Other',          label: 'Other',          icon: <Stars />,        color: '#455a64', bg: '#eceff1' },
];
const CAT_MAP = Object.fromEntries(CLUB_CATEGORIES.map((c) => [c.id, c]));
const getInitials = (name = '') => name.split(' ').map((w) => w[0]).join('').toUpperCase().slice(0, 2);

const Clubs = () => {
  const { user, token } = useSelector((s) => s.auth);
  const navigate = useNavigate();
  const isLoggedIn = !!user;
  const isAdmin = user?.role === 'admin';

  const [clubs, setClubs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [snack, setSnack] = useState('');
  const [search, setSearch] = useState('');
  const [activeCategory, setActiveCategory] = useState('all');
  const [showRecruiting, setShowRecruiting] = useState(false);
  const [detailClub, setDetailClub] = useState(null);
  const [postOpen, setPostOpen] = useState(false);
  const [form, setForm] = useState({ name: '', description: '', category: 'Technical', faculty_advisor: '', meeting_schedule: '', contact_email: '', is_recruiting: false });
  const [formError, setFormError] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [joiningId, setJoiningId] = useState(null);

  const fetchClubs = async () => {
    try { setLoading(true); const res = await axios.get('/clubs'); setClubs(res.data); }
    catch { setError('Failed to load clubs'); } finally { setLoading(false); }
  };

  useEffect(() => { fetchClubs(); }, []);

  const isMine = (c) => c.president_id === user?.id;
  const canManage = (c) => isAdmin || isMine(c);

  const handleJoin = async (clubId) => {
    if (!isLoggedIn) { navigate('/login'); return; }
    setJoiningId(clubId);
    try {
      const res = await axios.post(`/clubs/${clubId}/join`, {}, { headers: { Authorization: `Bearer ${token}` } });
      setSnack(res.data.message === 'joined' ? '✓ Joined the club!' : 'Left the club');
      fetchClubs();
    } catch { setSnack('Failed'); } finally { setJoiningId(null); }
  };

  const handlePost = async () => {
    if (!form.name.trim()) { setFormError('Club name is required'); return; }
    setSubmitting(true); setFormError('');
    try {
      const res = await axios.post('/clubs', form, { headers: { Authorization: `Bearer ${token}` } });
      setClubs((prev) => [res.data, ...prev]);
      setPostOpen(false);
      setForm({ name: '', description: '', category: 'Technical', faculty_advisor: '', meeting_schedule: '', contact_email: '', is_recruiting: false });
      setSnack('Club registered!');
    } catch (err) { setFormError(err.response?.data?.detail || 'Failed'); }
    finally { setSubmitting(false); }
  };

  const handleDelete = async (id) => {
    if (!window.confirm('Delete this club?')) return;
    try {
      await axios.delete(`/clubs/${id}`, { headers: { Authorization: `Bearer ${token}` } });
      setClubs((prev) => prev.filter((c) => c.id !== id));
      if (detailClub?.id === id) setDetailClub(null);
      setSnack('Club deleted');
    } catch { setSnack('Failed to delete'); }
  };

  const filtered = clubs.filter((c) => {
    if (activeCategory !== 'all' && c.category !== activeCategory) return false;
    if (showRecruiting && !c.is_recruiting) return false;
    if (search) { const q = search.toLowerCase(); if (!c.name.toLowerCase().includes(q) && !(c.description || '').toLowerCase().includes(q)) return false; }
    return true;
  });
  const catCounts = clubs.reduce((acc, c) => { acc[c.category] = (acc[c.category] || 0) + 1; return acc; }, {});

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      {!isLoggedIn ? (
        <Paper elevation={0} sx={{ mb: 4, p: 4, borderRadius: 3, textAlign: 'center', background: 'linear-gradient(135deg, #4a148c 0%, #7b1fa2 100%)', color: 'white' }}>
          <Typography variant="h4" fontWeight="bold" gutterBottom>🎓 Campus Clubs</Typography>
          <Typography variant="body1" sx={{ mb: 3, opacity: 0.9 }}>Join clubs, make friends, build skills. From technical to cultural — there's something for everyone.</Typography>
          <Box sx={{ display: 'flex', gap: 2, justifyContent: 'center', flexWrap: 'wrap' }}>
            <Button variant="contained" size="large" sx={{ bgcolor: 'white', color: '#4a148c', fontWeight: 'bold' }} onClick={() => navigate('/login')}>Log In to Join</Button>
            <Button variant="outlined" size="large" sx={{ borderColor: 'white', color: 'white', fontWeight: 'bold' }} onClick={() => navigate('/signup')}>Sign Up Free</Button>
          </Box>
        </Paper>
      ) : (
        <Box sx={{ mb: 3, display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 2 }}>
          <Box>
            <Typography variant="h4" fontWeight="bold">🎓 Campus Clubs</Typography>
            <Typography variant="body1" color="text.secondary">{clubs.length} clubs · Join, connect, and grow</Typography>
          </Box>
          <Button variant="contained" size="large" startIcon={<PostAdd />} onClick={() => { setFormError(''); setPostOpen(true); }}
            sx={{ borderRadius: 2, fontWeight: 'bold', px: 3, bgcolor: '#4a148c', '&:hover': { bgcolor: '#6a1b9a' } }}>
            + Register Your Club
          </Button>
        </Box>
      )}

      {error && <Alert severity="error" sx={{ mb: 3 }}>{error}</Alert>}

      {/* Category pills */}
      <Box sx={{ mb: 2, display: 'flex', gap: 1.5, flexWrap: 'wrap' }}>
        <Paper elevation={0} onClick={() => setActiveCategory('all')}
          sx={{ px: 2, py: 1, borderRadius: 3, cursor: 'pointer', display: 'flex', alignItems: 'center', gap: 1,
            border: '2px solid', borderColor: activeCategory === 'all' ? '#4a148c' : 'divider',
            bgcolor: activeCategory === 'all' ? '#f3e5f5' : 'background.paper' }}>
          <Group fontSize="small" sx={{ color: activeCategory === 'all' ? '#4a148c' : 'text.secondary' }} />
          <Typography variant="body2" fontWeight={activeCategory === 'all' ? 'bold' : 'normal'} sx={{ color: activeCategory === 'all' ? '#4a148c' : 'text.secondary' }}>All ({clubs.length})</Typography>
        </Paper>
        {CLUB_CATEGORIES.map((cat) => {
          const active = activeCategory === cat.id;
          const count = catCounts[cat.id] || 0;
          if (!count) return null;
          return (
            <Paper key={cat.id} elevation={0} onClick={() => setActiveCategory(active ? 'all' : cat.id)}
              sx={{ px: 2, py: 1, borderRadius: 3, cursor: 'pointer', display: 'flex', alignItems: 'center', gap: 1,
                border: '2px solid', borderColor: active ? cat.color : 'divider', bgcolor: active ? cat.bg : 'background.paper' }}>
              <Box sx={{ color: active ? cat.color : 'text.secondary', display: 'flex', alignItems: 'center' }}>{React.cloneElement(cat.icon, { fontSize: 'small' })}</Box>
              <Typography variant="body2" fontWeight={active ? 'bold' : 'normal'} sx={{ color: active ? cat.color : 'text.secondary' }}>{cat.label} ({count})</Typography>
            </Paper>
          );
        })}
      </Box>

      <Box sx={{ mb: 3, display: 'flex', gap: 2, flexWrap: 'wrap', alignItems: 'center' }}>
        <TextField placeholder="Search clubs…" value={search} onChange={(e) => setSearch(e.target.value)} size="small" sx={{ flexGrow: 1, minWidth: 200 }}
          InputProps={{ startAdornment: <InputAdornment position="start"><Search fontSize="small" /></InputAdornment> }} />
        <FormControlLabel control={<Switch checked={showRecruiting} onChange={(e) => setShowRecruiting(e.target.checked)} color="success" />}
          label={<Typography variant="body2">Recruiting Only</Typography>} />
        <Typography variant="body2" color="text.secondary"><b>{filtered.length}</b> clubs</Typography>
      </Box>

      {loading ? <Box sx={{ display: 'flex', justifyContent: 'center', py: 10 }}><CircularProgress /></Box>
        : filtered.length === 0 ? (
          <Box sx={{ textAlign: 'center', py: 10 }}>
            <Group sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
            <Typography variant="h6" color="text.secondary">No clubs found</Typography>
          </Box>
        ) : (
          <Grid container spacing={3}>
            {filtered.map((club) => {
              const catInfo = CAT_MAP[club.category] || CAT_MAP['Other'];
              const memberCount = club.actual_member_count ?? club.member_count ?? 0;
              return (
                <Grid item xs={12} sm={6} md={4} key={club.id}>
                  <Card elevation={2} sx={{ height: '100%', display: 'flex', flexDirection: 'column', borderRadius: 3,
                    transition: 'transform 0.2s, box-shadow 0.2s', '&:hover': { transform: 'translateY(-4px)', boxShadow: 6 }, borderTop: `4px solid ${catInfo.color}` }}>
                    <CardContent sx={{ flexGrow: 1, p: 2.5 }}>
                      <Box sx={{ display: 'flex', gap: 2, mb: 1.5 }}>
                        <Avatar sx={{ width: 52, height: 52, bgcolor: catInfo.color, fontSize: '1rem', fontWeight: 'bold', boxShadow: 2 }}>{getInitials(club.name)}</Avatar>
                        <Box sx={{ flexGrow: 1 }}>
                          <Typography variant="subtitle1" fontWeight="bold" sx={{ lineHeight: 1.3 }}>{club.name}</Typography>
                          <Box sx={{ display: 'flex', gap: 0.5, flexWrap: 'wrap', mt: 0.3 }}>
                            <Chip icon={React.cloneElement(catInfo.icon, { style: { color: catInfo.color, fontSize: 12 } })}
                              label={catInfo.label} size="small" sx={{ bgcolor: catInfo.bg, color: catInfo.color, fontWeight: 'bold', fontSize: '0.6rem', height: 20 }} />
                            {club.is_recruiting && <Chip label="Recruiting!" color="success" size="small" sx={{ height: 20, fontSize: '0.6rem', fontWeight: 'bold' }} />}
                          </Box>
                        </Box>
                      </Box>
                      {club.description && (
                        <Typography variant="body2" color="text.secondary"
                          sx={{ mb: 1.5, display: '-webkit-box', WebkitLineClamp: 3, WebkitBoxOrient: 'vertical', overflow: 'hidden', lineHeight: 1.6 }}>
                          {club.description}
                        </Typography>
                      )}
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                        <Group fontSize="small" color="action" />
                        <Typography variant="body2" color="text.secondary"><b>{memberCount}</b> members</Typography>
                      </Box>
                      {(club.president_display_name || club.president_name) && (
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5, mt: 0.5 }}>
                          <Person fontSize="small" color="action" />
                          <Typography variant="caption" color="text.secondary">President: {club.president_display_name || club.president_name}</Typography>
                        </Box>
                      )}
                    </CardContent>
                    <CardActions sx={{ px: 2.5, pb: 2.5, gap: 1, flexDirection: 'column', alignItems: 'stretch' }}>
                      <Button variant="outlined" size="small" fullWidth sx={{ borderRadius: 2 }} onClick={() => setDetailClub(club)}>View Details</Button>
                      {isLoggedIn && !isMine(club) && (
                        <Button variant={club.is_recruiting ? 'contained' : 'outlined'} size="small" fullWidth startIcon={<HowToReg />}
                          sx={{ borderRadius: 2 }} disabled={joiningId === club.id} onClick={() => handleJoin(club.id)}>
                          {joiningId === club.id ? 'Joining…' : 'Join Club'}
                        </Button>
                      )}
                      {canManage(club) && <Tooltip title="Delete club"><IconButton size="small" color="error" onClick={() => handleDelete(club.id)} sx={{ alignSelf: 'flex-end' }}><Delete fontSize="small" /></IconButton></Tooltip>}
                    </CardActions>
                  </Card>
                </Grid>
              );
            })}
          </Grid>
        )}

      {isLoggedIn && <Fab sx={{ position: 'fixed', bottom: 32, right: 32, bgcolor: '#4a148c', '&:hover': { bgcolor: '#6a1b9a' }, color: 'white' }} onClick={() => { setFormError(''); setPostOpen(true); }}><Add /></Fab>}

      {/* Detail dialog */}
      <Dialog open={!!detailClub} onClose={() => setDetailClub(null)} maxWidth="sm" fullWidth>
        {detailClub && (() => {
          const catInfo = CAT_MAP[detailClub.category] || CAT_MAP['Other'];
          const memberCount = detailClub.actual_member_count ?? detailClub.member_count ?? 0;
          return (
            <>
              <DialogTitle sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', pb: 0 }}>
                <Box sx={{ display: 'flex', gap: 2, alignItems: 'flex-start', flexGrow: 1, mr: 1 }}>
                  <Avatar sx={{ width: 56, height: 56, bgcolor: catInfo.color, fontWeight: 'bold', boxShadow: 2 }}>{getInitials(detailClub.name)}</Avatar>
                  <Box>
                    <Typography variant="h6" fontWeight="bold">{detailClub.name}</Typography>
                    <Box sx={{ display: 'flex', gap: 1, mt: 0.5, flexWrap: 'wrap' }}>
                      <Chip icon={React.cloneElement(catInfo.icon, { style: { color: catInfo.color, fontSize: 12 } })} label={catInfo.label} size="small" sx={{ bgcolor: catInfo.bg, color: catInfo.color, fontWeight: 'bold' }} />
                      {detailClub.is_recruiting && <Chip label="Recruiting!" color="success" size="small" icon={<CheckCircle sx={{ fontSize: '14px !important' }} />} sx={{ fontWeight: 'bold' }} />}
                      <Chip label={`${memberCount} Members`} size="small" icon={<Group sx={{ fontSize: '14px !important' }} />} variant="outlined" />
                    </Box>
                  </Box>
                </Box>
                <IconButton onClick={() => setDetailClub(null)}><Close /></IconButton>
              </DialogTitle>
              <DialogContent sx={{ pt: 2 }}>
                {detailClub.description && <Box sx={{ mb: 2 }}><Typography variant="subtitle2" fontWeight="bold" gutterBottom>About</Typography><Typography variant="body2" color="text.secondary" sx={{ lineHeight: 1.7 }}>{detailClub.description}</Typography></Box>}
                <Divider sx={{ my: 2 }} />
                <Grid container spacing={2}>
                  {(detailClub.president_display_name || detailClub.president_name) && (
                    <Grid item xs={6}><Box sx={{ display: 'flex', gap: 1, alignItems: 'center' }}><Person fontSize="small" color="primary" /><Box><Typography variant="caption" color="text.secondary">President</Typography><Typography variant="body2" fontWeight="bold">{detailClub.president_display_name || detailClub.president_name}</Typography></Box></Box></Grid>
                  )}
                  {detailClub.faculty_advisor && (
                    <Grid item xs={6}><Box sx={{ display: 'flex', gap: 1, alignItems: 'center' }}><Stars fontSize="small" color="warning" /><Box><Typography variant="caption" color="text.secondary">Faculty Advisor</Typography><Typography variant="body2" fontWeight="bold">{detailClub.faculty_advisor}</Typography></Box></Box></Grid>
                  )}
                  {detailClub.meeting_schedule && (
                    <Grid item xs={12}><Box sx={{ display: 'flex', gap: 1, alignItems: 'center' }}><Schedule fontSize="small" color="action" /><Box><Typography variant="caption" color="text.secondary">Meeting Schedule</Typography><Typography variant="body2" fontWeight="bold">{detailClub.meeting_schedule}</Typography></Box></Box></Grid>
                  )}
                  {detailClub.contact_email && (
                    <Grid item xs={12}><Box sx={{ display: 'flex', gap: 1, alignItems: 'center' }}><Email fontSize="small" color="action" /><Box><Typography variant="caption" color="text.secondary">Contact</Typography><Typography variant="body2" fontWeight="bold">{detailClub.contact_email}</Typography></Box></Box></Grid>
                  )}
                </Grid>
                {detailClub.is_recruiting && (
                  <Box sx={{ mt: 2.5, p: 2, borderRadius: 2, bgcolor: 'success.50', border: '1px solid', borderColor: 'success.200' }}>
                    <Typography variant="subtitle2" fontWeight="bold" color="success.main" gutterBottom>🎉 Open for New Members!</Typography>
                    <Typography variant="body2" color="text.secondary">This club is actively recruiting. Click "Join Club" to become a member.</Typography>
                  </Box>
                )}
              </DialogContent>
              <DialogActions sx={{ px: 3, pb: 2, gap: 1 }}>
                {isLoggedIn && !isMine(detailClub) && (
                  <Button variant="contained" startIcon={<HowToReg />} sx={{ borderRadius: 2, bgcolor: catInfo.color, '&:hover': { filter: 'brightness(0.85)' } }}
                    disabled={joiningId === detailClub.id} onClick={() => handleJoin(detailClub.id)}>
                    {joiningId === detailClub.id ? 'Joining…' : 'Join This Club'}
                  </Button>
                )}
                {!isLoggedIn && <Button variant="contained" onClick={() => { setDetailClub(null); navigate('/login'); }}>Log In to Join</Button>}
                {canManage(detailClub) && <Button color="error" variant="outlined" startIcon={<Delete />} onClick={() => handleDelete(detailClub.id)}>Delete Club</Button>}
              </DialogActions>
            </>
          );
        })()}
      </Dialog>

      {/* Post dialog */}
      <Dialog open={postOpen} onClose={() => setPostOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>
          <Typography variant="h6" fontWeight="bold">Register Your Club</Typography>
          <Typography variant="body2" color="text.secondary">You will be listed as the club president</Typography>
        </DialogTitle>
        <DialogContent sx={{ pt: 1 }}>
          {formError && <Alert severity="error" sx={{ mb: 2 }}>{formError}</Alert>}
          <TextField fullWidth label="Club Name *" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} sx={{ mb: 2, mt: 1 }} />
          <Grid container spacing={2} sx={{ mb: 2 }}>
            <Grid item xs={6}>
              <FormControl fullWidth><InputLabel>Category *</InputLabel>
                <Select value={form.category} label="Category *" onChange={(e) => setForm({ ...form, category: e.target.value })}>
                  {CLUB_CATEGORIES.map((c) => <MenuItem key={c.id} value={c.id}>{c.label}</MenuItem>)}
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={6} sx={{ display: 'flex', alignItems: 'center' }}>
              <FormControlLabel control={<Switch checked={form.is_recruiting} onChange={(e) => setForm({ ...form, is_recruiting: e.target.checked })} color="success" />}
                label={<Typography variant="body2">Open for Joining</Typography>} />
            </Grid>
          </Grid>
          <TextField fullWidth label="Faculty Advisor" value={form.faculty_advisor} onChange={(e) => setForm({ ...form, faculty_advisor: e.target.value })} sx={{ mb: 2 }} placeholder="Prof. A. Kumar" />
          <TextField fullWidth label="Meeting Schedule" value={form.meeting_schedule} onChange={(e) => setForm({ ...form, meeting_schedule: e.target.value })} sx={{ mb: 2 }}
            placeholder="e.g. Saturdays 3–5 PM, CS Lab"
            InputProps={{ startAdornment: <InputAdornment position="start"><Schedule fontSize="small" /></InputAdornment> }} />
          <TextField fullWidth label="Contact Email" value={form.contact_email} onChange={(e) => setForm({ ...form, contact_email: e.target.value })} sx={{ mb: 2 }}
            InputProps={{ startAdornment: <InputAdornment position="start"><Email fontSize="small" /></InputAdornment> }} />
          <TextField fullWidth label="Description" multiline rows={3} value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} placeholder="What does your club do?" />
        </DialogContent>
        <DialogActions sx={{ px: 3, pb: 2 }}>
          <Button onClick={() => setPostOpen(false)}>Cancel</Button>
          <Button variant="contained" onClick={handlePost} disabled={submitting} startIcon={<PostAdd />} size="large" sx={{ bgcolor: '#4a148c', '&:hover': { bgcolor: '#6a1b9a' } }}>
            {submitting ? 'Registering…' : 'Register Club →'}
          </Button>
        </DialogActions>
      </Dialog>

      <Snackbar open={!!snack} autoHideDuration={3000} onClose={() => setSnack('')} anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }} message={snack} />
    </Container>
  );
};

export default Clubs;
