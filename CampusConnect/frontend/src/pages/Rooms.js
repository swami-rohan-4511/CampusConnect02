import React, { useState, useEffect, useRef } from 'react';
import {
  Container, Typography, Box, Grid, Card, CardContent, CardMedia, CardActions,
  Button, Chip, Dialog, DialogTitle, DialogContent, DialogActions,
  TextField, FormControl, InputLabel, Select, MenuItem,
  Alert, CircularProgress, IconButton, InputAdornment, LinearProgress,
  Tooltip, Fab, Slider, Snackbar, Paper,
} from '@mui/material';
import {
  MeetingRoom, LocationOn, Phone, Add, Close,
  Search, Delete, Home, ChevronLeft, ChevronRight,
  CheckCircle, RadioButtonUnchecked, AddAPhoto, CloudUpload,
  Male, Female, People, WhatsApp, Call, PostAdd,
} from '@mui/icons-material';
import axios from 'axios';
import { useSelector } from 'react-redux';
import { useNavigate } from 'react-router-dom';

const ROOM_TYPES = ['single', 'double', 'shared', 'pg', 'studio', '1bhk', '2bhk'];
const ROOM_LABELS = { single: 'Single Room', double: 'Double Sharing', shared: 'Shared Room', pg: 'PG', studio: 'Studio', '1bhk': '1 BHK', '2bhk': '2 BHK' };
const ROOM_COLORS = { single: 'primary', double: 'secondary', shared: 'warning', pg: 'success', studio: 'error', '1bhk': 'info', '2bhk': 'default' };
const GENDER_ICONS = { male: <Male fontSize="small" />, female: <Female fontSize="small" />, any: <People fontSize="small" /> };
const GENDER_COLORS = { male: 'info', female: 'error', any: 'default' };
const GENDER_LABELS = { male: 'Boys Only', female: 'Girls Only', any: 'Any Gender' };
const COMMON_AMENITIES = ['AC', 'WiFi', 'Attached Bathroom', 'Common Bathroom', 'Kitchen', 'Furnished', 'Parking', 'Meals Included', 'Laundry', 'CCTV', 'Geyser', 'Power Backup', 'TV', 'Study Table', 'Wardrobe'];

const fmt = (v) => v != null ? `₹${parseFloat(v).toLocaleString('en-IN')}` : '';

const cleanPhone = (raw = '') => raw.replace(/[^0-9+]/g, '');
const waLink = (raw) => { const n = cleanPhone(raw).replace(/^\+/, ''); return `https://wa.me/${n.startsWith('91') ? n : '91' + n}`; };
const callLink = (raw) => `tel:${cleanPhone(raw)}`;

// ── Image carousel ─────────────────────────────────────────────────────────
const ImageCarousel = ({ images, height = 200 }) => {
  const [idx, setIdx] = useState(0);
  const imgs = images || [];
  if (imgs.length === 0) {
    return (
      <Box sx={{ height, bgcolor: 'action.hover', display: 'flex', alignItems: 'center', justifyContent: 'center', flexDirection: 'column', gap: 1 }}>
        <Home sx={{ fontSize: 52, color: 'text.disabled' }} />
        <Typography variant="caption" color="text.disabled">No photos yet</Typography>
      </Box>
    );
  }
  return (
    <Box sx={{ position: 'relative', height, overflow: 'hidden', bgcolor: '#000' }}>
      <CardMedia component="img" image={imgs[idx]} alt={`Room photo ${idx + 1}`}
        sx={{ height, objectFit: 'cover', width: '100%', transition: 'opacity 0.25s' }} />
      {imgs.length > 1 && (
        <>
          <IconButton size="small"
            onClick={(e) => { e.stopPropagation(); setIdx((idx - 1 + imgs.length) % imgs.length); }}
            sx={{ position: 'absolute', left: 6, top: '50%', transform: 'translateY(-50%)', bgcolor: 'rgba(0,0,0,0.5)', color: 'white', p: 0.4, '&:hover': { bgcolor: 'rgba(0,0,0,0.75)' } }}>
            <ChevronLeft fontSize="small" />
          </IconButton>
          <IconButton size="small"
            onClick={(e) => { e.stopPropagation(); setIdx((idx + 1) % imgs.length); }}
            sx={{ position: 'absolute', right: 6, top: '50%', transform: 'translateY(-50%)', bgcolor: 'rgba(0,0,0,0.5)', color: 'white', p: 0.4, '&:hover': { bgcolor: 'rgba(0,0,0,0.75)' } }}>
            <ChevronRight fontSize="small" />
          </IconButton>
          <Box sx={{ position: 'absolute', bottom: 8, left: '50%', transform: 'translateX(-50%)', display: 'flex', gap: 0.5 }}>
            {imgs.map((_, i) => (
              <Box key={i} onClick={(e) => { e.stopPropagation(); setIdx(i); }}
                sx={{ width: i === idx ? 18 : 6, height: 6, borderRadius: 3, bgcolor: i === idx ? 'white' : 'rgba(255,255,255,0.5)', cursor: 'pointer', transition: 'width 0.2s' }} />
            ))}
          </Box>
        </>
      )}
      <Chip label={`${idx + 1} / ${imgs.length}`} size="small"
        sx={{ position: 'absolute', top: 8, right: 8, bgcolor: 'rgba(0,0,0,0.55)', color: 'white', height: 20, fontSize: '0.65rem' }} />
    </Box>
  );
};

// ── Contact buttons ────────────────────────────────────────────────────────
const ContactButtons = ({ contact, size = 'medium' }) => {
  if (!contact) return null;
  return (
    <Box sx={{ display: 'flex', gap: 1.5, flexWrap: 'wrap', mt: 1 }}>
      <Button variant="contained" color="success" size={size}
        startIcon={<WhatsApp />} component="a"
        href={waLink(contact)} target="_blank" rel="noopener noreferrer"
        sx={{ borderRadius: 2, fontWeight: 'bold', bgcolor: '#25D366', '&:hover': { bgcolor: '#1ebe57' } }}>
        WhatsApp
      </Button>
      <Button variant="outlined" size={size}
        startIcon={<Call />} component="a"
        href={callLink(contact)}
        sx={{ borderRadius: 2, fontWeight: 'bold', borderColor: 'primary.main' }}>
        Call
      </Button>
    </Box>
  );
};

const Rooms = () => {
  const { user, token } = useSelector((s) => s.auth);
  const navigate = useNavigate();
  const isLoggedIn = !!user;
  const isAdmin = user?.role === 'admin';

  const [rooms, setRooms] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [snack, setSnack] = useState('');

  // Filters
  const [search, setSearch] = useState('');
  const [filterType, setFilterType] = useState('all');
  const [filterGender, setFilterGender] = useState('all');
  const [filterStatus, setFilterStatus] = useState('available');
  const [maxRent, setMaxRent] = useState(20000);

  // Detail dialog
  const [detailRoom, setDetailRoom] = useState(null);

  // Post dialog
  const [postOpen, setPostOpen] = useState(false);
  const [form, setForm] = useState({
    title: '', description: '', location: '', rent_amount: '', deposit_amount: '',
    room_type: 'single', gender_preference: 'any', amenities: [], contact_info: '',
  });
  const [formError, setFormError] = useState('');
  const [submitting, setSubmitting] = useState(false);

  // Multi-image upload
  const multiImageRef = useRef(null);
  const [uploadingFor, setUploadingFor] = useState(null);
  const [uploadProgress, setUploadProgress] = useState({ done: 0, total: 0 });

  const fetchRooms = async () => {
    try {
      setLoading(true);
      const res = await axios.get('/rooms');
      setRooms(res.data);
    } catch { setError('Failed to load rooms'); }
    finally { setLoading(false); }
  };

  useEffect(() => { fetchRooms(); }, []);

  const isMine = (room) => room.owner_id === user?.id;
  const canManage = (room) => isAdmin || isMine(room);

  // ── Post Room ─────────────────────────────────────────────────────────────
  const handlePost = async () => {
    if (!form.title.trim() || !form.location.trim() || !form.rent_amount) {
      setFormError('Title, location and rent are required'); return;
    }
    setSubmitting(true); setFormError('');
    try {
      const res = await axios.post('/rooms', {
        ...form,
        rent_amount: parseFloat(form.rent_amount),
        deposit_amount: form.deposit_amount ? parseFloat(form.deposit_amount) : 0,
      }, { headers: { Authorization: `Bearer ${token}` } });
      setRooms((prev) => [res.data, ...prev]);
      setPostOpen(false);
      resetForm();
      setDetailRoom(res.data);
      setSnack('Room posted! Add photos using the camera button.');
    } catch (err) {
      setFormError(err.response?.data?.detail || 'Failed to post room');
    } finally { setSubmitting(false); }
  };

  const resetForm = () => setForm({
    title: '', description: '', location: '', rent_amount: '', deposit_amount: '',
    room_type: 'single', gender_preference: 'any', amenities: [], contact_info: '',
  });

  const toggleAmenity = (a) => setForm((f) => ({
    ...f, amenities: f.amenities.includes(a) ? f.amenities.filter((x) => x !== a) : [...f.amenities, a],
  }));

  // ── Multi-image upload ────────────────────────────────────────────────────
  const triggerUpload = (roomId) => {
    setUploadingFor(roomId);
    multiImageRef.current.click();
  };

  const handleMultiImageUpload = async (e) => {
    const files = Array.from(e.target.files || []);
    if (!files.length || !uploadingFor) return;
    const roomId = uploadingFor;
    e.target.value = '';
    setUploadProgress({ done: 0, total: files.length });

    let latestRoom = null;
    for (let i = 0; i < files.length; i++) {
      try {
        const fd = new FormData();
        fd.append('file', files[i]);
        const res = await axios.post(`/rooms/${roomId}/image`, fd, {
          headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'multipart/form-data' },
        });
        latestRoom = res.data;
        setUploadProgress({ done: i + 1, total: files.length });
      } catch { /* skip failed file */ }
    }

    if (latestRoom) {
      setRooms((prev) => prev.map((r) => r.id === roomId ? latestRoom : r));
      if (detailRoom?.id === roomId) setDetailRoom(latestRoom);
    }
    setUploadingFor(null);
    setUploadProgress({ done: 0, total: 0 });
    setSnack(`${files.length} photo${files.length > 1 ? 's' : ''} uploaded!`);
  };

  // ── Toggle status ─────────────────────────────────────────────────────────
  const handleToggleStatus = async (room) => {
    const newStatus = room.status === 'available' ? 'taken' : 'available';
    try {
      const res = await axios.patch(`/rooms/${room.id}/status`, { status: newStatus }, {
        headers: { Authorization: `Bearer ${token}` },
      });
      setRooms((prev) => prev.map((r) => r.id === room.id ? res.data : r));
      if (detailRoom?.id === room.id) setDetailRoom(res.data);
      setSnack(`Marked as ${newStatus}`);
    } catch { setSnack('Failed to update status'); }
  };

  // ── Delete ────────────────────────────────────────────────────────────────
  const handleDelete = async (roomId) => {
    if (!window.confirm('Delete this room listing?')) return;
    try {
      await axios.delete(`/rooms/${roomId}`, { headers: { Authorization: `Bearer ${token}` } });
      setRooms((prev) => prev.filter((r) => r.id !== roomId));
      if (detailRoom?.id === roomId) setDetailRoom(null);
      setSnack('Room deleted');
    } catch { setSnack('Failed to delete'); }
  };

  // ── Filter ────────────────────────────────────────────────────────────────
  const filtered = rooms.filter((r) => {
    if (filterType !== 'all' && r.room_type !== filterType) return false;
    if (filterGender !== 'all' && r.gender_preference !== filterGender) return false;
    if (filterStatus !== 'all' && r.status !== filterStatus) return false;
    if (parseFloat(r.rent_amount) > maxRent) return false;
    if (search) {
      const q = search.toLowerCase();
      if (!r.title.toLowerCase().includes(q) && !(r.location || '').toLowerCase().includes(q) && !(r.description || '').toLowerCase().includes(q)) return false;
    }
    return true;
  });

  const maxRentInData = rooms.length ? Math.max(...rooms.map((r) => parseFloat(r.rent_amount) || 0), 20000) : 20000;

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      {/* Hidden multi-image input */}
      <input ref={multiImageRef} type="file" accept="image/*" multiple style={{ display: 'none' }} onChange={handleMultiImageUpload} />

      {/* Upload progress bar */}
      {uploadProgress.total > 0 && (
        <Box sx={{ position: 'fixed', top: 64, left: 0, right: 0, zIndex: 9999, px: 2 }}>
          <LinearProgress variant="determinate" value={(uploadProgress.done / uploadProgress.total) * 100} sx={{ height: 4 }} />
          <Typography variant="caption" sx={{ display: 'block', textAlign: 'center', bgcolor: 'background.paper', py: 0.3 }}>
            Uploading photo {uploadProgress.done + 1} of {uploadProgress.total}…
          </Typography>
        </Box>
      )}

      {/* ── Hero / CTA Banner ── */}
      {!isLoggedIn ? (
        <Paper elevation={0} sx={{
          mb: 4, p: 4, borderRadius: 3, textAlign: 'center',
          background: 'linear-gradient(135deg, #1976d2 0%, #42a5f5 100%)',
          color: 'white',
        }}>
          <Typography variant="h4" fontWeight="bold" gutterBottom>🏠 Find Your Perfect Room</Typography>
          <Typography variant="body1" sx={{ mb: 3, opacity: 0.9 }}>Browse rooms, PGs, and flats near campus. Log in to contact owners and post your own listing.</Typography>
          <Box sx={{ display: 'flex', gap: 2, justifyContent: 'center', flexWrap: 'wrap' }}>
            <Button variant="contained" size="large"
              sx={{ bgcolor: 'white', color: 'primary.main', fontWeight: 'bold', '&:hover': { bgcolor: 'rgba(255,255,255,0.9)' } }}
              onClick={() => navigate('/login')}>
              Log In to Contact Owners
            </Button>
            <Button variant="outlined" size="large"
              sx={{ borderColor: 'white', color: 'white', fontWeight: 'bold', '&:hover': { bgcolor: 'rgba(255,255,255,0.1)' } }}
              onClick={() => navigate('/signup')}>
              Sign Up Free
            </Button>
          </Box>
        </Paper>
      ) : (
        <Box sx={{ mb: 4, display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 2 }}>
          <Box>
            <Typography variant="h4" fontWeight="bold" gutterBottom>🏠 Rooms & Accommodation</Typography>
            <Typography variant="body1" color="text.secondary">Find rooms, PGs, and flats near campus</Typography>
          </Box>
          <Button variant="contained" size="large" startIcon={<PostAdd />}
            onClick={() => { setFormError(''); setPostOpen(true); }}
            sx={{ borderRadius: 2, fontWeight: 'bold', px: 3, py: 1.2 }}>
            + List Your Room
          </Button>
        </Box>
      )}

      {!isLoggedIn && (
        <Box sx={{ mb: 3, display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 2 }}>
          <Box>
            <Typography variant="h5" fontWeight="bold">🏠 Rooms & Accommodation</Typography>
            <Typography variant="body2" color="text.secondary">Find rooms, PGs, and flats near campus</Typography>
          </Box>
        </Box>
      )}

      {error && <Alert severity="error" sx={{ mb: 3 }}>{error}</Alert>}

      {/* ── Filters ── */}
      <Box sx={{ mb: 3, display: 'flex', flexDirection: 'column', gap: 2 }}>
        <TextField placeholder="Search by title, location or description..."
          value={search} onChange={(e) => setSearch(e.target.value)}
          size="small" fullWidth
          InputProps={{ startAdornment: <InputAdornment position="start"><Search fontSize="small" /></InputAdornment> }} />

        <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap', alignItems: 'center' }}>
          <Typography variant="body2" color="text.secondary" sx={{ mr: 0.5 }}>Type:</Typography>
          {['all', ...ROOM_TYPES].map((t) => (
            <Chip key={t} label={t === 'all' ? 'All' : ROOM_LABELS[t]}
              onClick={() => setFilterType(t)}
              color={filterType === t ? ROOM_COLORS[t] || 'primary' : 'default'}
              variant={filterType === t ? 'filled' : 'outlined'} size="small" />
          ))}
        </Box>

        <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap', alignItems: 'center' }}>
          <Box sx={{ display: 'flex', gap: 1, alignItems: 'center' }}>
            <Typography variant="body2" color="text.secondary">Gender:</Typography>
            {['all', 'any', 'male', 'female'].map((g) => (
              <Chip key={g} size="small"
                label={g === 'all' ? 'All' : GENDER_LABELS[g]}
                icon={g !== 'all' ? GENDER_ICONS[g] : undefined}
                onClick={() => setFilterGender(g)}
                color={filterGender === g ? GENDER_COLORS[g] || 'primary' : 'default'}
                variant={filterGender === g ? 'filled' : 'outlined'} />
            ))}
          </Box>
          <Box sx={{ display: 'flex', gap: 1, alignItems: 'center' }}>
            <Typography variant="body2" color="text.secondary">Status:</Typography>
            {['available', 'taken', 'all'].map((s) => (
              <Chip key={s} size="small" label={s === 'all' ? 'All' : s.charAt(0).toUpperCase() + s.slice(1)}
                onClick={() => setFilterStatus(s)}
                color={filterStatus === s ? (s === 'available' ? 'success' : s === 'taken' ? 'error' : 'primary') : 'default'}
                variant={filterStatus === s ? 'filled' : 'outlined'} />
            ))}
          </Box>
        </Box>

        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, maxWidth: 420 }}>
          <Typography variant="body2" color="text.secondary" sx={{ whiteSpace: 'nowrap' }}>
            Max rent: <b>{fmt(maxRent)}</b>/mo
          </Typography>
          <Slider value={maxRent} min={1000} max={Math.ceil(maxRentInData / 1000) * 1000}
            step={500} onChange={(_, v) => setMaxRent(v)} size="small" sx={{ flexGrow: 1 }} />
        </Box>

        <Typography variant="body2" color="text.secondary">
          Showing <b>{filtered.length}</b> of {rooms.length} listings
        </Typography>
      </Box>

      {/* ── Room grid ── */}
      {loading ? (
        <Box sx={{ display: 'flex', justifyContent: 'center', py: 8 }}><CircularProgress /></Box>
      ) : filtered.length === 0 ? (
        <Box sx={{ textAlign: 'center', py: 8 }}>
          <MeetingRoom sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
          <Typography variant="h6" color="text.secondary">No rooms match your filters</Typography>
          {isLoggedIn && <Button variant="contained" sx={{ mt: 2 }} onClick={() => setPostOpen(true)} startIcon={<Add />}>Post a Room</Button>}
        </Box>
      ) : (
        <Grid container spacing={3}>
          {filtered.map((room) => (
            <Grid item xs={12} sm={6} md={4} key={room.id}>
              <Card elevation={2} sx={{
                height: '100%', display: 'flex', flexDirection: 'column', borderRadius: 3,
                transition: 'transform 0.2s, box-shadow 0.2s',
                '&:hover': { transform: 'translateY(-4px)', boxShadow: 6 },
                opacity: room.status === 'taken' ? 0.82 : 1,
                outline: isMine(room) ? '2px solid' : 'none',
                outlineColor: 'primary.main',
              }}>
                {/* Carousel */}
                <Box sx={{ position: 'relative' }}>
                  <ImageCarousel images={room.images || []} height={200} />
                  {room.status === 'taken' && (
                    <Box sx={{ position: 'absolute', inset: 0, bgcolor: 'rgba(0,0,0,0.38)', display: 'flex', alignItems: 'center', justifyContent: 'center', pointerEvents: 'none' }}>
                      <Chip label="TAKEN" color="error" sx={{ fontWeight: 'bold', fontSize: '1rem', px: 2 }} />
                    </Box>
                  )}
                  {canManage(room) && (
                    <Tooltip title="Add photos">
                      <IconButton size="small"
                        sx={{ position: 'absolute', bottom: 8, right: 8, bgcolor: 'rgba(0,0,0,0.55)', color: 'white', '&:hover': { bgcolor: 'rgba(0,0,0,0.75)' } }}
                        onClick={(e) => { e.stopPropagation(); triggerUpload(room.id); }}>
                        <AddAPhoto fontSize="small" />
                      </IconButton>
                    </Tooltip>
                  )}
                </Box>

                <CardContent sx={{ flexGrow: 1, p: 2.5 }}>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 1 }}>
                    <Box sx={{ flexGrow: 1, mr: 1 }}>
                      <Typography variant="subtitle1" fontWeight="bold" sx={{ lineHeight: 1.3 }}>{room.title}</Typography>
                      {isMine(room) && <Chip label="Your Listing" size="small" color="primary" variant="outlined" sx={{ mt: 0.5, height: 18, fontSize: '0.6rem' }} />}
                    </Box>
                    <Chip label={ROOM_LABELS[room.room_type] || room.room_type}
                      color={ROOM_COLORS[room.room_type] || 'default'} size="small" />
                  </Box>

                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5, mb: 0.8 }}>
                    <LocationOn fontSize="small" color="action" />
                    <Typography variant="body2" color="text.secondary" noWrap>{room.location}</Typography>
                  </Box>

                  {room.description && (
                    <Typography variant="body2" color="text.secondary"
                      sx={{ mb: 1, display: '-webkit-box', WebkitLineClamp: 2, WebkitBoxOrient: 'vertical', overflow: 'hidden', lineHeight: 1.5 }}>
                      {room.description}
                    </Typography>
                  )}

                  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
                    <Box>
                      <Typography variant="h6" color="primary" fontWeight="bold" sx={{ lineHeight: 1.2 }}>
                        {fmt(room.rent_amount)}<Typography component="span" variant="caption" color="text.secondary">/mo</Typography>
                      </Typography>
                      {room.deposit_amount > 0 && <Typography variant="caption" color="text.secondary">Deposit: {fmt(room.deposit_amount)}</Typography>}
                    </Box>
                    <Chip icon={GENDER_ICONS[room.gender_preference] || <People fontSize="small" />}
                      label={GENDER_LABELS[room.gender_preference] || room.gender_preference}
                      color={GENDER_COLORS[room.gender_preference] || 'default'} size="small" variant="outlined" />
                  </Box>

                  {(room.amenities || []).length > 0 && (
                    <Box sx={{ display: 'flex', gap: 0.5, flexWrap: 'wrap' }}>
                      {(room.amenities || []).slice(0, 4).map((a) => (
                        <Chip key={a} label={a} size="small" variant="outlined" sx={{ height: 20, fontSize: '0.65rem', borderColor: 'divider' }} />
                      ))}
                      {(room.amenities || []).length > 4 && (
                        <Chip label={`+${room.amenities.length - 4} more`} size="small" sx={{ height: 20, fontSize: '0.65rem', bgcolor: 'action.hover' }} />
                      )}
                    </Box>
                  )}
                </CardContent>

                <CardActions sx={{ px: 2.5, pb: 2.5, gap: 1, flexDirection: 'column', alignItems: 'stretch' }}>
                  <Button variant="contained" size="small" fullWidth sx={{ borderRadius: 2 }}
                    onClick={() => setDetailRoom(room)}>
                    View Details & Contact
                  </Button>
                  {canManage(room) && (
                    <Box sx={{ display: 'flex', gap: 1, justifyContent: 'flex-end' }}>
                      <Tooltip title={room.status === 'available' ? 'Mark as taken' : 'Mark as available'}>
                        <IconButton size="small" color={room.status === 'available' ? 'warning' : 'success'} onClick={() => handleToggleStatus(room)}>
                          {room.status === 'available' ? <CheckCircle fontSize="small" /> : <RadioButtonUnchecked fontSize="small" />}
                        </IconButton>
                      </Tooltip>
                      <Tooltip title="Delete listing">
                        <IconButton size="small" color="error" onClick={() => handleDelete(room.id)}>
                          <Delete fontSize="small" />
                        </IconButton>
                      </Tooltip>
                    </Box>
                  )}
                </CardActions>
              </Card>
            </Grid>
          ))}
        </Grid>
      )}

      {isLoggedIn && (
        <Fab color="primary" sx={{ position: 'fixed', bottom: 32, right: 32 }}
          onClick={() => { setFormError(''); setPostOpen(true); }}>
          <Add />
        </Fab>
      )}

      {/* ─── Room Detail Dialog ─── */}
      <Dialog open={!!detailRoom} onClose={() => setDetailRoom(null)} maxWidth="sm" fullWidth>
        {detailRoom && (
          <>
            <DialogTitle sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', pb: 0 }}>
              <Box sx={{ flexGrow: 1, mr: 1 }}>
                <Typography variant="h6" fontWeight="bold">{detailRoom.title}</Typography>
                <Box sx={{ display: 'flex', gap: 1, mt: 0.5, flexWrap: 'wrap' }}>
                  <Chip label={ROOM_LABELS[detailRoom.room_type] || detailRoom.room_type}
                    color={ROOM_COLORS[detailRoom.room_type] || 'default'} size="small" />
                  <Chip label={detailRoom.status === 'available' ? '✓ Available' : '✗ Taken'}
                    color={detailRoom.status === 'available' ? 'success' : 'error'} size="small" />
                  <Chip icon={GENDER_ICONS[detailRoom.gender_preference] || <People />}
                    label={GENDER_LABELS[detailRoom.gender_preference] || detailRoom.gender_preference}
                    color={GENDER_COLORS[detailRoom.gender_preference] || 'default'} size="small" variant="outlined" />
                </Box>
              </Box>
              <IconButton onClick={() => setDetailRoom(null)}><Close /></IconButton>
            </DialogTitle>

            <DialogContent sx={{ pt: 1 }}>
              {/* Full image carousel */}
              <Box sx={{ mx: -3, mb: 2 }}>
                <ImageCarousel images={detailRoom.images || []} height={260} />
              </Box>

              {/* Owner: add photos button */}
              {canManage(detailRoom) && (
                <Box sx={{ mb: 2, display: 'flex', gap: 1, alignItems: 'center' }}>
                  <Button startIcon={<CloudUpload />} size="small" variant="outlined"
                    onClick={() => triggerUpload(detailRoom.id)}>
                    Upload Photos (select multiple)
                  </Button>
                  <Typography variant="caption" color="text.secondary">
                    {(detailRoom.images || []).length} photo{(detailRoom.images || []).length !== 1 ? 's' : ''} uploaded
                  </Typography>
                </Box>
              )}

              {/* Price box */}
              <Box sx={{ display: 'flex', gap: 3, mb: 2.5, p: 2, borderRadius: 2, bgcolor: 'primary.50', border: '1px solid', borderColor: 'primary.100' }}>
                <Box>
                  <Typography variant="caption" color="text.secondary">Monthly Rent</Typography>
                  <Typography variant="h5" fontWeight="bold" color="primary">{fmt(detailRoom.rent_amount)}</Typography>
                </Box>
                {detailRoom.deposit_amount > 0 && (
                  <Box>
                    <Typography variant="caption" color="text.secondary">Security Deposit</Typography>
                    <Typography variant="h6" fontWeight="bold">{fmt(detailRoom.deposit_amount)}</Typography>
                  </Box>
                )}
              </Box>

              {/* Location */}
              <Box sx={{ display: 'flex', gap: 0.8, alignItems: 'center', mb: 1.5 }}>
                <LocationOn fontSize="small" color="action" />
                <Typography variant="body2">{detailRoom.location}</Typography>
              </Box>

              {/* Description */}
              {detailRoom.description && (
                <Box sx={{ mb: 2 }}>
                  <Typography variant="subtitle2" fontWeight="bold" gutterBottom>About this room</Typography>
                  <Typography variant="body2" color="text.secondary" sx={{ lineHeight: 1.7 }}>{detailRoom.description}</Typography>
                </Box>
              )}

              {/* Amenities */}
              {(detailRoom.amenities || []).length > 0 && (
                <Box sx={{ mb: 2.5 }}>
                  <Typography variant="subtitle2" fontWeight="bold" gutterBottom>Amenities</Typography>
                  <Box sx={{ display: 'flex', gap: 0.8, flexWrap: 'wrap' }}>
                    {(detailRoom.amenities || []).map((a) => (
                      <Chip key={a} label={a} size="small" color="primary" variant="outlined" />
                    ))}
                  </Box>
                </Box>
              )}

              {/* Contact section */}
              <Box sx={{ p: 2, borderRadius: 2, bgcolor: 'success.50', border: '1px solid', borderColor: 'success.200' }}>
                <Typography variant="subtitle2" fontWeight="bold" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                  <Phone fontSize="small" color="success" /> Contact Owner
                </Typography>
                {isLoggedIn ? (
                  detailRoom.contact_info ? (
                    <>
                      <Typography variant="body1" fontWeight="bold" sx={{ mb: 1 }}>{detailRoom.contact_info}</Typography>
                      <ContactButtons contact={detailRoom.contact_info} />
                    </>
                  ) : (
                    <Typography variant="body2" color="text.secondary">No contact number provided</Typography>
                  )
                ) : (
                  <Box>
                    <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>Log in to see contact details and reach out to the owner.</Typography>
                    <Button variant="contained" size="small" onClick={() => { setDetailRoom(null); navigate('/login'); }}>
                      Log In to Contact
                    </Button>
                  </Box>
                )}
              </Box>
            </DialogContent>

            {canManage(detailRoom) && (
              <DialogActions sx={{ px: 3, pb: 2, gap: 1 }}>
                <Button color={detailRoom.status === 'available' ? 'warning' : 'success'}
                  variant="outlined" size="small"
                  onClick={() => handleToggleStatus(detailRoom)}
                  startIcon={detailRoom.status === 'available' ? <CheckCircle /> : <RadioButtonUnchecked />}>
                  {detailRoom.status === 'available' ? 'Mark as Taken' : 'Mark as Available'}
                </Button>
                <Button color="error" variant="outlined" size="small"
                  onClick={() => handleDelete(detailRoom.id)} startIcon={<Delete />}>
                  Delete
                </Button>
              </DialogActions>
            )}
          </>
        )}
      </Dialog>

      {/* ─── Post Room Dialog ─── */}
      <Dialog open={postOpen} onClose={() => setPostOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>
          <Typography variant="h6" fontWeight="bold">List Your Room</Typography>
          <Typography variant="body2" color="text.secondary">Fill in the details — you can add photos right after</Typography>
        </DialogTitle>
        <DialogContent sx={{ pt: 1 }}>
          {formError && <Alert severity="error" sx={{ mb: 2 }}>{formError}</Alert>}

          <TextField fullWidth label="Listing Title *" value={form.title}
            onChange={(e) => setForm({ ...form, title: e.target.value })} sx={{ mb: 2, mt: 1 }}
            placeholder="e.g. Single AC Room near Main Gate" />

          <Grid container spacing={2} sx={{ mb: 2 }}>
            <Grid item xs={6}>
              <FormControl fullWidth>
                <InputLabel>Room Type *</InputLabel>
                <Select value={form.room_type} label="Room Type *"
                  onChange={(e) => setForm({ ...form, room_type: e.target.value })}>
                  {ROOM_TYPES.map((t) => <MenuItem key={t} value={t}>{ROOM_LABELS[t]}</MenuItem>)}
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={6}>
              <FormControl fullWidth>
                <InputLabel>Suitable For</InputLabel>
                <Select value={form.gender_preference} label="Suitable For"
                  onChange={(e) => setForm({ ...form, gender_preference: e.target.value })}>
                  <MenuItem value="any">Any Gender</MenuItem>
                  <MenuItem value="male">Boys Only</MenuItem>
                  <MenuItem value="female">Girls Only</MenuItem>
                </Select>
              </FormControl>
            </Grid>
          </Grid>

          <TextField fullWidth label="Location *" value={form.location}
            onChange={(e) => setForm({ ...form, location: e.target.value })}
            placeholder="e.g. Sector 14, Near Main Gate" sx={{ mb: 2 }}
            InputProps={{ startAdornment: <InputAdornment position="start"><LocationOn fontSize="small" /></InputAdornment> }} />

          <Grid container spacing={2} sx={{ mb: 2 }}>
            <Grid item xs={6}>
              <TextField fullWidth label="Monthly Rent (₹) *" type="number" value={form.rent_amount}
                onChange={(e) => setForm({ ...form, rent_amount: e.target.value })}
                InputProps={{ startAdornment: <InputAdornment position="start">₹</InputAdornment> }} />
            </Grid>
            <Grid item xs={6}>
              <TextField fullWidth label="Security Deposit (₹)" type="number" value={form.deposit_amount}
                onChange={(e) => setForm({ ...form, deposit_amount: e.target.value })}
                InputProps={{ startAdornment: <InputAdornment position="start">₹</InputAdornment> }} />
            </Grid>
          </Grid>

          <TextField fullWidth label="Your Contact Number *" value={form.contact_info}
            onChange={(e) => setForm({ ...form, contact_info: e.target.value })} sx={{ mb: 2 }}
            placeholder="e.g. +91 98765 43210"
            InputProps={{ startAdornment: <InputAdornment position="start"><Phone fontSize="small" /></InputAdornment> }} />

          <TextField fullWidth label="Description" multiline rows={3} value={form.description}
            onChange={(e) => setForm({ ...form, description: e.target.value })} sx={{ mb: 2 }}
            placeholder="Describe the room, surroundings, nearby landmarks, house rules, etc." />

          <Typography variant="body2" fontWeight="bold" sx={{ mb: 1 }}>Amenities (tap to select)</Typography>
          <Box sx={{ display: 'flex', gap: 0.8, flexWrap: 'wrap' }}>
            {COMMON_AMENITIES.map((a) => (
              <Chip key={a} label={a} size="small"
                onClick={() => toggleAmenity(a)}
                color={form.amenities.includes(a) ? 'primary' : 'default'}
                variant={form.amenities.includes(a) ? 'filled' : 'outlined'}
                sx={{ cursor: 'pointer' }} />
            ))}
          </Box>
        </DialogContent>
        <DialogActions sx={{ px: 3, pb: 2 }}>
          <Button onClick={() => setPostOpen(false)}>Cancel</Button>
          <Button variant="contained" onClick={handlePost} disabled={submitting} startIcon={<PostAdd />} size="large">
            {submitting ? 'Posting…' : 'Post Listing →'}
          </Button>
        </DialogActions>
      </Dialog>

      <Snackbar open={!!snack} autoHideDuration={3500} onClose={() => setSnack('')}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }} message={snack} />
    </Container>
  );
};

export default Rooms;
