import React, { useState, useEffect, useRef } from 'react';
import {
  Container, Typography, Box, Grid, Card, CardContent, CardMedia, CardActions,
  Button, Chip, Dialog, DialogTitle, DialogContent, DialogActions,
  TextField, FormControl, InputLabel, Select, MenuItem,
  Alert, CircularProgress, IconButton, InputAdornment, LinearProgress,
  Snackbar, Divider, Paper, Avatar, Tooltip, Fab,
} from '@mui/material';
import {
  DirectionsBike, Laptop, School, SportsSoccer, PhotoCamera,
  Build, ShoppingBag, Add, Close, Search, Delete,
  LocationOn, Phone, CloudUpload, AddAPhoto,
  ChevronLeft, ChevronRight, WhatsApp, Call,
  VerifiedUser, Person, AccessTime, CheckCircle, RadioButtonUnchecked,
  PostAdd, CalendarMonth,
} from '@mui/icons-material';
import axios from 'axios';
import { useSelector } from 'react-redux';
import { useNavigate } from 'react-router-dom';

const CATEGORIES = [
  { id: 'Bikes & Cycles',   label: 'Bikes & Cycles',  icon: <DirectionsBike />,  color: '#e65100', bg: '#fff3e0' },
  { id: 'Electronics',      label: 'Electronics',     icon: <Laptop />,          color: '#1565c0', bg: '#e3f2fd' },
  { id: 'Academic',         label: 'Academic',        icon: <School />,          color: '#2e7d32', bg: '#e8f5e9' },
  { id: 'Sports & Fitness', label: 'Sports & Fitness',icon: <SportsSoccer />,    color: '#6a1b9a', bg: '#f3e5f5' },
  { id: 'Photography',      label: 'Photography',     icon: <PhotoCamera />,     color: '#0277bd', bg: '#e1f5fe' },
  { id: 'Tools',            label: 'Tools',           icon: <Build />,           color: '#558b2f', bg: '#f1f8e9' },
  { id: 'Other',            label: 'Other',           icon: <ShoppingBag />,     color: '#455a64', bg: '#eceff1' },
];

const CAT_MAP = Object.fromEntries(CATEGORIES.map((c) => [c.id, c]));

const CONDITIONS = {
  excellent: { label: 'Excellent', color: 'success' },
  good:      { label: 'Good',      color: 'primary' },
  fair:      { label: 'Fair',      color: 'warning' },
};

const fmt = (v) => v != null ? `₹${parseFloat(v).toLocaleString('en-IN')}` : '';

const memberSince = (dateStr) => {
  if (!dateStr) return '';
  const d = new Date(dateStr);
  return d.toLocaleDateString('en-IN', { month: 'short', year: 'numeric' });
};

const cleanPhone = (raw = '') => raw.replace(/[^0-9+]/g, '');
const waLink    = (raw) => { const n = cleanPhone(raw).replace(/^\+/, ''); return `https://wa.me/${n.startsWith('91') ? n : '91' + n}`; };
const callLink  = (raw) => `tel:${cleanPhone(raw)}`;

// ── Image carousel ─────────────────────────────────────────────────────────
const ImageCarousel = ({ images, height = 210 }) => {
  const [idx, setIdx] = useState(0);
  const imgs = images || [];
  if (!imgs.length) {
    const cat = null;
    return (
      <Box sx={{ height, bgcolor: 'action.hover', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: 1 }}>
        <ShoppingBag sx={{ fontSize: 52, color: 'text.disabled' }} />
        <Typography variant="caption" color="text.disabled">No photos yet</Typography>
      </Box>
    );
  }
  return (
    <Box sx={{ position: 'relative', height, bgcolor: '#000', overflow: 'hidden' }}>
      <CardMedia component="img" image={imgs[idx]} alt={`Item ${idx + 1}`}
        sx={{ height, objectFit: 'cover', width: '100%', transition: 'opacity 0.25s' }} />
      {imgs.length > 1 && (
        <>
          <IconButton size="small"
            onClick={(e) => { e.stopPropagation(); setIdx((idx - 1 + imgs.length) % imgs.length); }}
            sx={{ position: 'absolute', left: 6, top: '50%', transform: 'translateY(-50%)', bgcolor: 'rgba(0,0,0,0.5)', color: 'white', p: 0.4 }}>
            <ChevronLeft fontSize="small" />
          </IconButton>
          <IconButton size="small"
            onClick={(e) => { e.stopPropagation(); setIdx((idx + 1) % imgs.length); }}
            sx={{ position: 'absolute', right: 6, top: '50%', transform: 'translateY(-50%)', bgcolor: 'rgba(0,0,0,0.5)', color: 'white', p: 0.4 }}>
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
      <Chip label={`${idx + 1}/${imgs.length}`} size="small"
        sx={{ position: 'absolute', top: 8, right: 8, bgcolor: 'rgba(0,0,0,0.55)', color: 'white', height: 20, fontSize: '0.65rem' }} />
    </Box>
  );
};

// ── Verified profile card ───────────────────────────────────────────────────
const VerifiedProfileBadge = ({ item, compact = false }) => {
  const name = item.owner_display_name || item.owner_name || 'Campus Member';
  const since = memberSince(item.owner_joined);
  const initials = name.split(' ').map((w) => w[0]).join('').toUpperCase().slice(0, 2);
  const catInfo = CAT_MAP[item.category];

  if (compact) {
    return (
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mt: 0.5 }}>
        <Avatar sx={{ width: 22, height: 22, fontSize: '0.6rem', bgcolor: catInfo?.color || 'primary.main' }}>{initials}</Avatar>
        <Typography variant="caption" color="text.secondary" noWrap>{name}</Typography>
        <Chip icon={<VerifiedUser sx={{ fontSize: '0.65rem !important' }} />} label="Verified" size="small"
          color="success" variant="outlined" sx={{ height: 16, fontSize: '0.55rem', '& .MuiChip-label': { px: 0.5 } }} />
      </Box>
    );
  }

  return (
    <Box sx={{ p: 2, borderRadius: 2, bgcolor: 'grey.50', border: '1px solid', borderColor: 'grey.200', mb: 2 }}>
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
        <Avatar sx={{ width: 52, height: 52, bgcolor: catInfo?.color || 'primary.main', fontSize: '1.1rem', fontWeight: 'bold', boxShadow: 2 }}>
          {initials}
        </Avatar>
        <Box sx={{ flexGrow: 1 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, flexWrap: 'wrap' }}>
            <Typography variant="subtitle1" fontWeight="bold">{name}</Typography>
            <Chip icon={<VerifiedUser sx={{ fontSize: '0.8rem !important' }} />} label="Campus Verified"
              color="success" size="small" variant="filled"
              sx={{ height: 22, fontSize: '0.7rem', fontWeight: 'bold' }} />
          </Box>
          {since && (
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5, mt: 0.3 }}>
              <CalendarMonth sx={{ fontSize: '0.85rem', color: 'text.secondary' }} />
              <Typography variant="caption" color="text.secondary">Member since {since}</Typography>
            </Box>
          )}
        </Box>
      </Box>
      <Divider sx={{ my: 1.5 }} />
      <Typography variant="caption" color="text.secondary" sx={{ lineHeight: 1.6 }}>
        This listing is from a verified campus member. All registered users are verified with their campus credentials.
      </Typography>
    </Box>
  );
};

// ── Contact buttons ─────────────────────────────────────────────────────────
const ContactButtons = ({ contact }) => {
  if (!contact) return null;
  return (
    <Box sx={{ display: 'flex', gap: 1.5, flexWrap: 'wrap', mt: 1.5 }}>
      <Button variant="contained" size="medium" startIcon={<WhatsApp />}
        component="a" href={waLink(contact)} target="_blank" rel="noopener"
        sx={{ borderRadius: 2, fontWeight: 'bold', bgcolor: '#25D366', '&:hover': { bgcolor: '#1ebe57' } }}>
        WhatsApp
      </Button>
      <Button variant="outlined" size="medium" startIcon={<Call />}
        component="a" href={callLink(contact)}
        sx={{ borderRadius: 2, fontWeight: 'bold' }}>
        Call Owner
      </Button>
    </Box>
  );
};

// ─── Main Component ────────────────────────────────────────────────────────
const RentalHub = () => {
  const { user, token } = useSelector((s) => s.auth);
  const navigate = useNavigate();
  const isLoggedIn = !!user;
  const isAdmin = user?.role === 'admin';

  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [snack, setSnack] = useState('');

  const [activeCategory, setActiveCategory] = useState('all');
  const [search, setSearch] = useState('');
  const [filterAvail, setFilterAvail] = useState('available');
  const [maxRate, setMaxRate] = useState(2000);

  const [detailItem, setDetailItem] = useState(null);
  const [postOpen, setPostOpen] = useState(false);

  const [form, setForm] = useState({
    name: '', description: '', category: 'Bikes & Cycles',
    daily_rate: '', weekly_rate: '', security_deposit: '',
    location: '', contact_info: '', min_rental_days: 1, condition_status: 'good',
  });
  const [formError, setFormError] = useState('');
  const [submitting, setSubmitting] = useState(false);

  const multiImgRef = useRef(null);
  const [uploadingFor, setUploadingFor] = useState(null);
  const [uploadProgress, setUploadProgress] = useState({ done: 0, total: 0 });

  const fetchItems = async () => {
    try {
      setLoading(true);
      const res = await axios.get('/rental');
      setItems(res.data);
    } catch { setError('Failed to load rental listings'); }
    finally { setLoading(false); }
  };

  useEffect(() => { fetchItems(); }, []);

  const isMine = (item) => item.owner_id === user?.id;
  const canManage = (item) => isAdmin || isMine(item);

  // ── Post listing ────────────────────────────────────────────────────────
  const handlePost = async () => {
    if (!form.name.trim() || !form.daily_rate) { setFormError('Name and daily rate are required'); return; }
    setSubmitting(true); setFormError('');
    try {
      const res = await axios.post('/rental', {
        ...form,
        daily_rate: parseFloat(form.daily_rate),
        weekly_rate: form.weekly_rate ? parseFloat(form.weekly_rate) : null,
        security_deposit: form.security_deposit ? parseFloat(form.security_deposit) : 0,
        min_rental_days: parseInt(form.min_rental_days) || 1,
      }, { headers: { Authorization: `Bearer ${token}` } });
      setItems((prev) => [res.data, ...prev]);
      setPostOpen(false);
      resetForm();
      setDetailItem(res.data);
      setSnack('Item listed! Add photos using the camera button.');
    } catch (err) {
      setFormError(err.response?.data?.detail || 'Failed to post listing');
    } finally { setSubmitting(false); }
  };

  const resetForm = () => setForm({
    name: '', description: '', category: 'Bikes & Cycles',
    daily_rate: '', weekly_rate: '', security_deposit: '',
    location: '', contact_info: '', min_rental_days: 1, condition_status: 'good',
  });

  // ── Multi-image upload ──────────────────────────────────────────────────
  const triggerUpload = (id) => { setUploadingFor(id); multiImgRef.current.click(); };

  const handleImagesSelected = async (e) => {
    const files = Array.from(e.target.files || []);
    if (!files.length || !uploadingFor) return;
    const id = uploadingFor;
    e.target.value = '';
    setUploadProgress({ done: 0, total: files.length });
    let latest = null;
    for (let i = 0; i < files.length; i++) {
      try {
        const fd = new FormData();
        fd.append('file', files[i]);
        const res = await axios.post(`/rental/${id}/image`, fd, {
          headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'multipart/form-data' },
        });
        latest = res.data;
        setUploadProgress({ done: i + 1, total: files.length });
      } catch {}
    }
    if (latest) {
      setItems((prev) => prev.map((r) => r.id === id ? { ...r, ...latest } : r));
      if (detailItem?.id === id) setDetailItem((prev) => ({ ...prev, ...latest }));
    }
    setUploadingFor(null);
    setUploadProgress({ done: 0, total: 0 });
    setSnack(`${files.length} photo${files.length > 1 ? 's' : ''} uploaded!`);
  };

  // ── Toggle availability ─────────────────────────────────────────────────
  const handleToggle = async (item) => {
    const newStatus = !item.availability_status;
    try {
      const res = await axios.patch(`/rental/${item.id}/availability`,
        { availability_status: newStatus },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      setItems((prev) => prev.map((r) => r.id === item.id ? { ...r, ...res.data } : r));
      if (detailItem?.id === item.id) setDetailItem((prev) => ({ ...prev, ...res.data }));
      setSnack(newStatus ? 'Marked as available' : 'Marked as rented out');
    } catch { setSnack('Failed to update'); }
  };

  // ── Delete ──────────────────────────────────────────────────────────────
  const handleDelete = async (id) => {
    if (!window.confirm('Remove this listing?')) return;
    try {
      await axios.delete(`/rental/${id}`, { headers: { Authorization: `Bearer ${token}` } });
      setItems((prev) => prev.filter((r) => r.id !== id));
      if (detailItem?.id === id) setDetailItem(null);
      setSnack('Listing removed');
    } catch { setSnack('Failed to delete'); }
  };

  // ── Filter ──────────────────────────────────────────────────────────────
  const filtered = items.filter((item) => {
    if (activeCategory !== 'all' && item.category !== activeCategory) return false;
    if (filterAvail === 'available' && !item.availability_status) return false;
    if (filterAvail === 'rented' && item.availability_status) return false;
    if (parseFloat(item.daily_rate) > maxRate) return false;
    if (search) {
      const q = search.toLowerCase();
      if (!item.name.toLowerCase().includes(q) &&
          !(item.description || '').toLowerCase().includes(q) &&
          !(item.location || '').toLowerCase().includes(q)) return false;
    }
    return true;
  });

  const maxRateInData = items.length ? Math.max(...items.map((r) => parseFloat(r.daily_rate) || 0), 2000) : 2000;
  const catCounts = items.reduce((acc, item) => { acc[item.category] = (acc[item.category] || 0) + 1; return acc; }, {});

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      {/* Hidden multi-image input */}
      <input ref={multiImgRef} type="file" accept="image/*" multiple style={{ display: 'none' }} onChange={handleImagesSelected} />

      {/* Upload progress bar */}
      {uploadProgress.total > 0 && (
        <Box sx={{ position: 'fixed', top: 64, left: 0, right: 0, zIndex: 9999, px: 2 }}>
          <LinearProgress variant="determinate" value={(uploadProgress.done / uploadProgress.total) * 100} sx={{ height: 4 }} />
          <Typography variant="caption" sx={{ display: 'block', textAlign: 'center', bgcolor: 'background.paper', py: 0.3 }}>
            Uploading {uploadProgress.done + 1} of {uploadProgress.total}…
          </Typography>
        </Box>
      )}

      {/* ── Page header ── */}
      {!isLoggedIn ? (
        <Paper elevation={0} sx={{
          mb: 4, p: 4, borderRadius: 3, textAlign: 'center',
          background: 'linear-gradient(135deg, #e65100 0%, #ff8f00 100%)', color: 'white',
        }}>
          <Typography variant="h4" fontWeight="bold" gutterBottom>📦 Campus Rental Hub</Typography>
          <Typography variant="body1" sx={{ mb: 3, opacity: 0.9 }}>
            Rent bikes, electronics, academic gear, sports equipment and more from verified campus members.
          </Typography>
          <Box sx={{ display: 'flex', gap: 2, justifyContent: 'center', flexWrap: 'wrap' }}>
            <Button variant="contained" size="large"
              sx={{ bgcolor: 'white', color: '#e65100', fontWeight: 'bold', '&:hover': { bgcolor: 'rgba(255,255,255,0.9)' } }}
              onClick={() => navigate('/login')}>
              Log In to Rent & List
            </Button>
            <Button variant="outlined" size="large"
              sx={{ borderColor: 'white', color: 'white', fontWeight: 'bold', '&:hover': { bgcolor: 'rgba(255,255,255,0.1)' } }}
              onClick={() => navigate('/signup')}>
              Sign Up Free
            </Button>
          </Box>
        </Paper>
      ) : (
        <Box sx={{ mb: 3, display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 2 }}>
          <Box>
            <Typography variant="h4" fontWeight="bold">📦 Campus Rental Hub</Typography>
            <Typography variant="body1" color="text.secondary">Rent and lend items with verified campus members</Typography>
          </Box>
          <Button variant="contained" size="large" startIcon={<PostAdd />}
            onClick={() => { setFormError(''); setPostOpen(true); }}
            sx={{ borderRadius: 2, fontWeight: 'bold', px: 3, py: 1.2 }}>
            + List an Item
          </Button>
        </Box>
      )}

      {error && <Alert severity="error" sx={{ mb: 3 }}>{error}</Alert>}

      {/* ── Category pills with icons ── */}
      <Box sx={{ mb: 3, display: 'flex', gap: 1.5, flexWrap: 'wrap' }}>
        <Paper elevation={0}
          onClick={() => setActiveCategory('all')}
          sx={{
            px: 2, py: 1, borderRadius: 3, cursor: 'pointer', display: 'flex', alignItems: 'center', gap: 1,
            border: '2px solid', borderColor: activeCategory === 'all' ? 'primary.main' : 'divider',
            bgcolor: activeCategory === 'all' ? 'primary.50' : 'background.paper',
            transition: 'all 0.15s',
          }}>
          <ShoppingBag fontSize="small" color={activeCategory === 'all' ? 'primary' : 'disabled'} />
          <Typography variant="body2" fontWeight={activeCategory === 'all' ? 'bold' : 'normal'}
            color={activeCategory === 'all' ? 'primary.main' : 'text.secondary'}>
            All ({items.length})
          </Typography>
        </Paper>
        {CATEGORIES.map((cat) => {
          const active = activeCategory === cat.id;
          const count = catCounts[cat.id] || 0;
          if (count === 0) return null;
          return (
            <Paper key={cat.id} elevation={0}
              onClick={() => setActiveCategory(active ? 'all' : cat.id)}
              sx={{
                px: 2, py: 1, borderRadius: 3, cursor: 'pointer', display: 'flex', alignItems: 'center', gap: 1,
                border: '2px solid', borderColor: active ? cat.color : 'divider',
                bgcolor: active ? cat.bg : 'background.paper',
                transition: 'all 0.15s',
              }}>
              <Box sx={{ color: active ? cat.color : 'text.secondary', display: 'flex', alignItems: 'center' }}>
                {React.cloneElement(cat.icon, { fontSize: 'small' })}
              </Box>
              <Typography variant="body2" fontWeight={active ? 'bold' : 'normal'}
                sx={{ color: active ? cat.color : 'text.secondary' }}>
                {cat.label} ({count})
              </Typography>
            </Paper>
          );
        })}
      </Box>

      {/* ── Filters row ── */}
      <Box sx={{ mb: 3, display: 'flex', gap: 2, flexWrap: 'wrap', alignItems: 'center' }}>
        <TextField placeholder="Search items, location..."
          value={search} onChange={(e) => setSearch(e.target.value)}
          size="small" sx={{ flexGrow: 1, minWidth: 220 }}
          InputProps={{ startAdornment: <InputAdornment position="start"><Search fontSize="small" /></InputAdornment> }} />
        <Box sx={{ display: 'flex', gap: 1 }}>
          {['available', 'rented', 'all'].map((s) => (
            <Chip key={s} size="small"
              label={s === 'available' ? 'Available' : s === 'rented' ? 'Rented Out' : 'All'}
              onClick={() => setFilterAvail(s)}
              color={filterAvail === s ? (s === 'available' ? 'success' : s === 'rented' ? 'error' : 'primary') : 'default'}
              variant={filterAvail === s ? 'filled' : 'outlined'} />
          ))}
        </Box>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, minWidth: 200 }}>
          <Typography variant="caption" color="text.secondary" noWrap>Max/day: <b>{fmt(maxRate)}</b></Typography>
          <Box component="input" type="range" min={100} max={Math.ceil(maxRateInData / 100) * 100} step={50}
            value={maxRate} onChange={(e) => setMaxRate(parseInt(e.target.value))}
            style={{ flexGrow: 1, accentColor: '#1976d2' }} />
        </Box>
      </Box>

      <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
        Showing <b>{filtered.length}</b> of {items.length} listings
      </Typography>

      {/* ── Items grid ── */}
      {loading ? (
        <Box sx={{ display: 'flex', justifyContent: 'center', py: 10 }}><CircularProgress /></Box>
      ) : filtered.length === 0 ? (
        <Box sx={{ textAlign: 'center', py: 10 }}>
          <ShoppingBag sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
          <Typography variant="h6" color="text.secondary" gutterBottom>No items match your search</Typography>
          {isLoggedIn && <Button variant="contained" startIcon={<Add />} sx={{ mt: 1 }} onClick={() => setPostOpen(true)}>List an Item</Button>}
        </Box>
      ) : (
        <Grid container spacing={3}>
          {filtered.map((item) => {
            const catInfo = CAT_MAP[item.category] || CAT_MAP['Other'];
            return (
              <Grid item xs={12} sm={6} md={4} key={item.id}>
                <Card elevation={2} sx={{
                  height: '100%', display: 'flex', flexDirection: 'column', borderRadius: 3,
                  transition: 'transform 0.2s, box-shadow 0.2s',
                  '&:hover': { transform: 'translateY(-4px)', boxShadow: 6 },
                  opacity: !item.availability_status ? 0.82 : 1,
                  outline: isMine(item) ? '2px solid' : 'none', outlineColor: 'primary.main',
                }}>
                  <Box sx={{ position: 'relative' }}>
                    <ImageCarousel images={item.images || []} height={200} />
                    {!item.availability_status && (
                      <Box sx={{ position: 'absolute', inset: 0, bgcolor: 'rgba(0,0,0,0.38)', display: 'flex', alignItems: 'center', justifyContent: 'center', pointerEvents: 'none' }}>
                        <Chip label="RENTED OUT" color="error" sx={{ fontWeight: 'bold', fontSize: '0.95rem', px: 2 }} />
                      </Box>
                    )}
                    {/* Category badge */}
                    <Chip
                      icon={React.cloneElement(catInfo.icon, { style: { color: catInfo.color, fontSize: 14 } })}
                      label={catInfo.label}
                      size="small"
                      sx={{ position: 'absolute', top: 10, left: 10, bgcolor: catInfo.bg, color: catInfo.color, fontWeight: 'bold', fontSize: '0.65rem', height: 22 }} />
                    {canManage(item) && (
                      <Tooltip title="Add photos">
                        <IconButton size="small"
                          sx={{ position: 'absolute', bottom: 8, right: 8, bgcolor: 'rgba(0,0,0,0.55)', color: 'white', '&:hover': { bgcolor: 'rgba(0,0,0,0.8)' } }}
                          onClick={(e) => { e.stopPropagation(); triggerUpload(item.id); }}>
                          <AddAPhoto fontSize="small" />
                        </IconButton>
                      </Tooltip>
                    )}
                  </Box>

                  <CardContent sx={{ flexGrow: 1, p: 2.5 }}>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 0.5 }}>
                      <Typography variant="subtitle1" fontWeight="bold" sx={{ flexGrow: 1, mr: 1, lineHeight: 1.3 }}>
                        {item.name}
                      </Typography>
                      {item.condition_status && (
                        <Chip label={CONDITIONS[item.condition_status]?.label || item.condition_status}
                          color={CONDITIONS[item.condition_status]?.color || 'default'} size="small"
                          sx={{ height: 20, fontSize: '0.6rem' }} />
                      )}
                    </Box>

                    {/* Verified owner pill */}
                    <VerifiedProfileBadge item={item} compact />

                    {item.location && (
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5, mt: 0.8, mb: 0.5 }}>
                        <LocationOn fontSize="small" color="action" />
                        <Typography variant="body2" color="text.secondary" noWrap>{item.location}</Typography>
                      </Box>
                    )}

                    {item.description && (
                      <Typography variant="body2" color="text.secondary"
                        sx={{ mb: 1, mt: 0.5, display: '-webkit-box', WebkitLineClamp: 2, WebkitBoxOrient: 'vertical', overflow: 'hidden', lineHeight: 1.5 }}>
                        {item.description}
                      </Typography>
                    )}

                    <Box sx={{ display: 'flex', gap: 2, mt: 1.5, p: 1.2, borderRadius: 2, bgcolor: 'primary.50', justifyContent: 'space-around' }}>
                      <Box sx={{ textAlign: 'center' }}>
                        <Typography variant="caption" color="text.secondary">Per Day</Typography>
                        <Typography variant="h6" fontWeight="bold" color="primary">{fmt(item.daily_rate)}</Typography>
                      </Box>
                      {item.weekly_rate && (
                        <>
                          <Divider orientation="vertical" flexItem />
                          <Box sx={{ textAlign: 'center' }}>
                            <Typography variant="caption" color="text.secondary">Per Week</Typography>
                            <Typography variant="subtitle1" fontWeight="bold" color="primary">{fmt(item.weekly_rate)}</Typography>
                          </Box>
                        </>
                      )}
                      {item.security_deposit > 0 && (
                        <>
                          <Divider orientation="vertical" flexItem />
                          <Box sx={{ textAlign: 'center' }}>
                            <Typography variant="caption" color="text.secondary">Deposit</Typography>
                            <Typography variant="subtitle2" fontWeight="bold">{fmt(item.security_deposit)}</Typography>
                          </Box>
                        </>
                      )}
                    </Box>
                  </CardContent>

                  <CardActions sx={{ px: 2.5, pb: 2.5, gap: 1, flexDirection: 'column', alignItems: 'stretch' }}>
                    <Button variant="contained" size="small" fullWidth sx={{ borderRadius: 2 }}
                      onClick={() => setDetailItem(item)}>
                      View Details & Contact
                    </Button>
                    {canManage(item) && (
                      <Box sx={{ display: 'flex', gap: 1, justifyContent: 'flex-end' }}>
                        <Tooltip title={item.availability_status ? 'Mark as rented out' : 'Mark as available'}>
                          <IconButton size="small" color={item.availability_status ? 'warning' : 'success'}
                            onClick={() => handleToggle(item)}>
                            {item.availability_status ? <CheckCircle fontSize="small" /> : <RadioButtonUnchecked fontSize="small" />}
                          </IconButton>
                        </Tooltip>
                        <Tooltip title="Remove listing">
                          <IconButton size="small" color="error" onClick={() => handleDelete(item.id)}>
                            <Delete fontSize="small" />
                          </IconButton>
                        </Tooltip>
                      </Box>
                    )}
                  </CardActions>
                </Card>
              </Grid>
            );
          })}
        </Grid>
      )}

      {isLoggedIn && (
        <Fab color="primary" sx={{ position: 'fixed', bottom: 32, right: 32 }}
          onClick={() => { setFormError(''); setPostOpen(true); }}>
          <Add />
        </Fab>
      )}

      {/* ─── Detail Dialog ─── */}
      <Dialog open={!!detailItem} onClose={() => setDetailItem(null)} maxWidth="sm" fullWidth>
        {detailItem && (() => {
          const catInfo = CAT_MAP[detailItem.category] || CAT_MAP['Other'];
          return (
            <>
              <DialogTitle sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', pb: 0 }}>
                <Box sx={{ flexGrow: 1, mr: 1 }}>
                  <Typography variant="h6" fontWeight="bold">{detailItem.name}</Typography>
                  <Box sx={{ display: 'flex', gap: 1, mt: 0.5, flexWrap: 'wrap' }}>
                    <Chip icon={React.cloneElement(catInfo.icon, { style: { color: catInfo.color, fontSize: 14 } })}
                      label={catInfo.label} size="small"
                      sx={{ bgcolor: catInfo.bg, color: catInfo.color, fontWeight: 'bold' }} />
                    {detailItem.condition_status && (
                      <Chip label={CONDITIONS[detailItem.condition_status]?.label || detailItem.condition_status}
                        color={CONDITIONS[detailItem.condition_status]?.color || 'default'} size="small" />
                    )}
                    <Chip label={detailItem.availability_status ? '✓ Available' : '✗ Rented Out'}
                      color={detailItem.availability_status ? 'success' : 'error'} size="small" />
                  </Box>
                </Box>
                <IconButton onClick={() => setDetailItem(null)}><Close /></IconButton>
              </DialogTitle>

              <DialogContent sx={{ pt: 1.5 }}>
                <Box sx={{ mx: -3, mb: 2.5 }}>
                  <ImageCarousel images={detailItem.images || []} height={270} />
                </Box>

                {canManage(detailItem) && (
                  <Box sx={{ mb: 2, display: 'flex', gap: 1, alignItems: 'center' }}>
                    <Button startIcon={<CloudUpload />} size="small" variant="outlined"
                      onClick={() => triggerUpload(detailItem.id)}>
                      Upload Photos (select multiple)
                    </Button>
                    <Typography variant="caption" color="text.secondary">
                      {(detailItem.images || []).length} photo{(detailItem.images || []).length !== 1 ? 's' : ''} added
                    </Typography>
                  </Box>
                )}

                {/* Verified owner profile card */}
                <VerifiedProfileBadge item={detailItem} compact={false} />

                {/* Pricing box */}
                <Box sx={{ display: 'flex', gap: 2, mb: 2.5, p: 2, borderRadius: 2, bgcolor: 'primary.50', border: '1px solid', borderColor: 'primary.100', flexWrap: 'wrap' }}>
                  <Box>
                    <Typography variant="caption" color="text.secondary">Per Day</Typography>
                    <Typography variant="h5" fontWeight="bold" color="primary">{fmt(detailItem.daily_rate)}</Typography>
                  </Box>
                  {detailItem.weekly_rate && (
                    <Box>
                      <Typography variant="caption" color="text.secondary">Per Week</Typography>
                      <Typography variant="h6" fontWeight="bold" color="primary">{fmt(detailItem.weekly_rate)}</Typography>
                    </Box>
                  )}
                  {detailItem.security_deposit > 0 && (
                    <Box>
                      <Typography variant="caption" color="text.secondary">Refundable Deposit</Typography>
                      <Typography variant="h6" fontWeight="bold">{fmt(detailItem.security_deposit)}</Typography>
                    </Box>
                  )}
                  {detailItem.min_rental_days > 1 && (
                    <Box>
                      <Typography variant="caption" color="text.secondary">Min. Duration</Typography>
                      <Typography variant="subtitle1" fontWeight="bold">{detailItem.min_rental_days} days</Typography>
                    </Box>
                  )}
                </Box>

                {/* Location */}
                {detailItem.location && (
                  <Box sx={{ display: 'flex', gap: 0.8, alignItems: 'center', mb: 1.5 }}>
                    <LocationOn fontSize="small" color="action" />
                    <Typography variant="body2">{detailItem.location}</Typography>
                  </Box>
                )}

                {/* Description */}
                {detailItem.description && (
                  <Box sx={{ mb: 2.5 }}>
                    <Typography variant="subtitle2" fontWeight="bold" gutterBottom>About this item</Typography>
                    <Typography variant="body2" color="text.secondary" sx={{ lineHeight: 1.7 }}>{detailItem.description}</Typography>
                  </Box>
                )}

                {/* Contact section */}
                <Box sx={{ p: 2, borderRadius: 2, bgcolor: 'success.50', border: '1px solid', borderColor: 'success.200' }}>
                  <Typography variant="subtitle2" fontWeight="bold" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                    <Phone fontSize="small" color="success" /> Contact the Owner
                  </Typography>
                  {isLoggedIn ? (
                    detailItem.contact_info ? (
                      <>
                        <Typography variant="body1" fontWeight="bold">{detailItem.contact_info}</Typography>
                        <ContactButtons contact={detailItem.contact_info} />
                      </>
                    ) : (
                      <Typography variant="body2" color="text.secondary">No contact number provided</Typography>
                    )
                  ) : (
                    <Box>
                      <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>Log in to see contact details and reach the owner.</Typography>
                      <Button variant="contained" size="small" onClick={() => { setDetailItem(null); navigate('/login'); }}>
                        Log In to Contact
                      </Button>
                    </Box>
                  )}
                </Box>
              </DialogContent>

              {canManage(detailItem) && (
                <DialogActions sx={{ px: 3, pb: 2, gap: 1 }}>
                  <Button color={detailItem.availability_status ? 'warning' : 'success'} variant="outlined" size="small"
                    onClick={() => handleToggle(detailItem)}
                    startIcon={detailItem.availability_status ? <CheckCircle /> : <RadioButtonUnchecked />}>
                    {detailItem.availability_status ? 'Mark as Rented Out' : 'Mark as Available'}
                  </Button>
                  <Button color="error" variant="outlined" size="small"
                    onClick={() => handleDelete(detailItem.id)} startIcon={<Delete />}>
                    Delete
                  </Button>
                </DialogActions>
              )}
            </>
          );
        })()}
      </Dialog>

      {/* ─── Post / List Item Dialog ─── */}
      <Dialog open={postOpen} onClose={() => setPostOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>
          <Typography variant="h6" fontWeight="bold">List an Item for Rent</Typography>
          <Typography variant="body2" color="text.secondary">Your campus-verified profile will be shown to renters</Typography>
        </DialogTitle>
        <DialogContent sx={{ pt: 1 }}>
          {formError && <Alert severity="error" sx={{ mb: 2 }}>{formError}</Alert>}

          <TextField fullWidth label="Item Name *" value={form.name}
            onChange={(e) => setForm({ ...form, name: e.target.value })} sx={{ mb: 2, mt: 1 }}
            placeholder="e.g. Honda Activa, DSLR Camera, Engineering Drawing Kit" />

          <Grid container spacing={2} sx={{ mb: 2 }}>
            <Grid item xs={6}>
              <FormControl fullWidth>
                <InputLabel>Category *</InputLabel>
                <Select value={form.category} label="Category *"
                  onChange={(e) => setForm({ ...form, category: e.target.value })}>
                  {CATEGORIES.map((c) => (
                    <MenuItem key={c.id} value={c.id}>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        <Box sx={{ color: c.color, display: 'flex', alignItems: 'center' }}>{React.cloneElement(c.icon, { fontSize: 'small' })}</Box>
                        {c.label}
                      </Box>
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={6}>
              <FormControl fullWidth>
                <InputLabel>Condition</InputLabel>
                <Select value={form.condition_status} label="Condition"
                  onChange={(e) => setForm({ ...form, condition_status: e.target.value })}>
                  <MenuItem value="excellent">Excellent</MenuItem>
                  <MenuItem value="good">Good</MenuItem>
                  <MenuItem value="fair">Fair (minor wear)</MenuItem>
                </Select>
              </FormControl>
            </Grid>
          </Grid>

          <Grid container spacing={2} sx={{ mb: 2 }}>
            <Grid item xs={4}>
              <TextField fullWidth label="Daily Rate (₹) *" type="number" value={form.daily_rate}
                onChange={(e) => setForm({ ...form, daily_rate: e.target.value })}
                InputProps={{ startAdornment: <InputAdornment position="start">₹</InputAdornment> }} />
            </Grid>
            <Grid item xs={4}>
              <TextField fullWidth label="Weekly Rate (₹)" type="number" value={form.weekly_rate}
                onChange={(e) => setForm({ ...form, weekly_rate: e.target.value })}
                InputProps={{ startAdornment: <InputAdornment position="start">₹</InputAdornment> }} />
            </Grid>
            <Grid item xs={4}>
              <TextField fullWidth label="Deposit (₹)" type="number" value={form.security_deposit}
                onChange={(e) => setForm({ ...form, security_deposit: e.target.value })}
                InputProps={{ startAdornment: <InputAdornment position="start">₹</InputAdornment> }} />
            </Grid>
          </Grid>

          <Grid container spacing={2} sx={{ mb: 2 }}>
            <Grid item xs={8}>
              <TextField fullWidth label="Pickup Location" value={form.location}
                onChange={(e) => setForm({ ...form, location: e.target.value })}
                placeholder="e.g. Hostel Block C, Room 204"
                InputProps={{ startAdornment: <InputAdornment position="start"><LocationOn fontSize="small" /></InputAdornment> }} />
            </Grid>
            <Grid item xs={4}>
              <TextField fullWidth label="Min. Days" type="number" value={form.min_rental_days}
                inputProps={{ min: 1 }}
                onChange={(e) => setForm({ ...form, min_rental_days: e.target.value })} />
            </Grid>
          </Grid>

          <TextField fullWidth label="Your Contact Number *" value={form.contact_info}
            onChange={(e) => setForm({ ...form, contact_info: e.target.value })} sx={{ mb: 2 }}
            placeholder="+91 98765 43210"
            InputProps={{ startAdornment: <InputAdornment position="start"><Phone fontSize="small" /></InputAdornment> }} />

          <TextField fullWidth label="Description" multiline rows={3} value={form.description}
            onChange={(e) => setForm({ ...form, description: e.target.value })}
            placeholder="Describe the item, its condition, any accessories included, house rules for renting, etc." />
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

export default RentalHub;
