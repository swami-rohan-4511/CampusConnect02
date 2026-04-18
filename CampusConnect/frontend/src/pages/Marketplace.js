import React, { useState, useEffect, useRef } from 'react';
import {
  Container, Typography, Box, Grid, Card, CardContent, CardMedia, CardActions,
  Button, Chip, Dialog, DialogTitle, DialogContent, DialogActions,
  TextField, FormControl, InputLabel, Select, MenuItem,
  Alert, CircularProgress, IconButton, InputAdornment, LinearProgress,
  Snackbar, Divider, Paper, Avatar, Tooltip, Fab, Switch, FormControlLabel,
} from '@mui/material';
import {
  Laptop, MenuBook, DirectionsBike, Chair, Speaker, Checkroom,
  Kitchen, ShoppingCart, Add, Close, Search, Delete,
  LocationOn, Phone, CloudUpload, AddAPhoto,
  ChevronLeft, ChevronRight, WhatsApp, Call,
  VerifiedUser, CalendarMonth, CheckCircle, PostAdd,
  Sell, LocalOffer, Storefront,
} from '@mui/icons-material';
import axios from 'axios';
import { useSelector } from 'react-redux';
import { useNavigate } from 'react-router-dom';

const CATEGORIES = [
  { id: 'Electronics',  label: 'Electronics',  icon: <Laptop />,        color: '#1565c0', bg: '#e3f2fd' },
  { id: 'Books',        label: 'Books',         icon: <MenuBook />,      color: '#2e7d32', bg: '#e8f5e9' },
  { id: 'Bikes',        label: 'Bikes',         icon: <DirectionsBike />,color: '#e65100', bg: '#fff3e0' },
  { id: 'Furniture',    label: 'Furniture',     icon: <Chair />,         color: '#6a1b9a', bg: '#f3e5f5' },
  { id: 'Clothing',     label: 'Clothing',      icon: <Checkroom />,     color: '#00838f', bg: '#e0f7fa' },
  { id: 'Appliances',   label: 'Appliances',    icon: <Kitchen />,       color: '#558b2f', bg: '#f1f8e9' },
  { id: 'Other',        label: 'Other',         icon: <ShoppingCart />,  color: '#455a64', bg: '#eceff1' },
];
const CAT_MAP = Object.fromEntries(CATEGORIES.map((c) => [c.id, c]));

const CONDITIONS = {
  new:       { label: 'Brand New', color: 'success' },
  excellent: { label: 'Like New',  color: 'success' },
  good:      { label: 'Good',      color: 'primary' },
  used:      { label: 'Used',      color: 'warning' },
  fair:      { label: 'Fair',      color: 'warning' },
};

const fmt = (v) => v != null ? `₹${parseFloat(v).toLocaleString('en-IN')}` : '';
const memberSince = (d) => d ? new Date(d).toLocaleDateString('en-IN', { month: 'short', year: 'numeric' }) : '';
const cleanPhone = (raw = '') => raw.replace(/[^0-9+]/g, '');
const waLink    = (raw) => { const n = cleanPhone(raw).replace(/^\+/, ''); return `https://wa.me/${n.startsWith('91') ? n : '91' + n}`; };
const callLink  = (raw) => `tel:${cleanPhone(raw)}`;

// ── Image Carousel ─────────────────────────────────────────────────────────
const ImageCarousel = ({ images, height = 210 }) => {
  const [idx, setIdx] = useState(0);
  const imgs = images || [];
  if (!imgs.length) return (
    <Box sx={{ height, bgcolor: 'action.hover', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: 1 }}>
      <ShoppingCart sx={{ fontSize: 52, color: 'text.disabled' }} />
      <Typography variant="caption" color="text.disabled">No photos yet</Typography>
    </Box>
  );
  return (
    <Box sx={{ position: 'relative', height, bgcolor: '#000', overflow: 'hidden' }}>
      <CardMedia component="img" image={imgs[idx]} alt={`Product ${idx + 1}`}
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
          <Chip label={`${idx + 1}/${imgs.length}`} size="small"
            sx={{ position: 'absolute', top: 8, right: 8, bgcolor: 'rgba(0,0,0,0.55)', color: 'white', height: 20, fontSize: '0.65rem' }} />
        </>
      )}
    </Box>
  );
};

// ── Seller verified badge ───────────────────────────────────────────────────
const SellerBadge = ({ item, compact = false }) => {
  const name = item.seller_display_name || item.seller_name || 'Campus Member';
  const since = memberSince(item.seller_joined);
  const initials = name.split(' ').map((w) => w[0]).join('').toUpperCase().slice(0, 2);

  if (compact) return (
    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mt: 0.5 }}>
      <Avatar sx={{ width: 22, height: 22, fontSize: '0.6rem', bgcolor: 'primary.main' }}>{initials}</Avatar>
      <Typography variant="caption" color="text.secondary" noWrap>{name}</Typography>
      <Chip icon={<VerifiedUser sx={{ fontSize: '0.65rem !important' }} />} label="Verified" size="small"
        color="success" variant="outlined" sx={{ height: 16, fontSize: '0.55rem', '& .MuiChip-label': { px: 0.5 } }} />
    </Box>
  );

  return (
    <Box sx={{ p: 2, borderRadius: 2, bgcolor: 'grey.50', border: '1px solid', borderColor: 'grey.200', mb: 2 }}>
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
        <Avatar sx={{ width: 50, height: 50, bgcolor: 'primary.main', fontWeight: 'bold', boxShadow: 2 }}>{initials}</Avatar>
        <Box>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, flexWrap: 'wrap' }}>
            <Typography variant="subtitle1" fontWeight="bold">{name}</Typography>
            <Chip icon={<VerifiedUser sx={{ fontSize: '0.8rem !important' }} />} label="Campus Verified"
              color="success" size="small" sx={{ height: 22, fontSize: '0.7rem', fontWeight: 'bold' }} />
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
      <Typography variant="caption" color="text.secondary">
        Verified campus member. Always meet in a safe public location for handover.
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
        Call Seller
      </Button>
    </Box>
  );
};

// ─── Main Component ────────────────────────────────────────────────────────
const Marketplace = () => {
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
  const [filterStatus, setFilterStatus] = useState('available');
  const [maxPrice, setMaxPrice] = useState(50000);

  const [detailItem, setDetailItem] = useState(null);
  const [postOpen, setPostOpen] = useState(false);

  const [form, setForm] = useState({
    title: '', description: '', price: '', category: 'Electronics',
    condition_status: 'good', location: '', contact_info: '', is_negotiable: true,
  });
  const [formError, setFormError] = useState('');
  const [submitting, setSubmitting] = useState(false);

  const multiImgRef = useRef(null);
  const [uploadingFor, setUploadingFor] = useState(null);
  const [uploadProgress, setUploadProgress] = useState({ done: 0, total: 0 });

  const fetchItems = async () => {
    try {
      setLoading(true);
      const res = await axios.get('/marketplace');
      setItems(res.data);
    } catch { setError('Failed to load listings'); }
    finally { setLoading(false); }
  };

  useEffect(() => { fetchItems(); }, []);

  const isMine = (item) => item.seller_id === user?.id;
  const canManage = (item) => isAdmin || isMine(item);

  // ── Post item ─────────────────────────────────────────────────────────────
  const handlePost = async () => {
    if (!form.title.trim() || !form.price) { setFormError('Title and price are required'); return; }
    setSubmitting(true); setFormError('');
    try {
      const res = await axios.post('/marketplace', {
        ...form, price: parseFloat(form.price),
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
    title: '', description: '', price: '', category: 'Electronics',
    condition_status: 'good', location: '', contact_info: '', is_negotiable: true,
  });

  // ── Multi-image upload ────────────────────────────────────────────────────
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
        const res = await axios.post(`/marketplace/${id}/image`, fd, {
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

  // ── Status update ─────────────────────────────────────────────────────────
  const handleStatusChange = async (item, newStatus) => {
    try {
      const res = await axios.patch(`/marketplace/${item.id}/status`, { status: newStatus }, {
        headers: { Authorization: `Bearer ${token}` },
      });
      setItems((prev) => prev.map((r) => r.id === item.id ? { ...r, ...res.data } : r));
      if (detailItem?.id === item.id) setDetailItem((prev) => ({ ...prev, ...res.data }));
      setSnack(`Marked as ${newStatus}`);
    } catch { setSnack('Failed to update status'); }
  };

  // ── Delete ────────────────────────────────────────────────────────────────
  const handleDelete = async (id) => {
    if (!window.confirm('Remove this listing?')) return;
    try {
      await axios.delete(`/marketplace/${id}`, { headers: { Authorization: `Bearer ${token}` } });
      setItems((prev) => prev.filter((r) => r.id !== id));
      if (detailItem?.id === id) setDetailItem(null);
      setSnack('Listing removed');
    } catch { setSnack('Failed to delete'); }
  };

  // ── Filter ────────────────────────────────────────────────────────────────
  const filtered = items.filter((item) => {
    if (activeCategory !== 'all' && item.category !== activeCategory) return false;
    if (filterStatus !== 'all' && item.status !== filterStatus) return false;
    if (parseFloat(item.price) > maxPrice) return false;
    if (search) {
      const q = search.toLowerCase();
      if (!item.title.toLowerCase().includes(q) &&
          !(item.description || '').toLowerCase().includes(q) &&
          !(item.location || '').toLowerCase().includes(q)) return false;
    }
    return true;
  });

  const maxPriceInData = items.length ? Math.max(...items.map((r) => parseFloat(r.price) || 0), 50000) : 50000;
  const catCounts = items.reduce((acc, i) => { acc[i.category] = (acc[i.category] || 0) + 1; return acc; }, {});

  const statusColors = { available: 'success', sold: 'error', reserved: 'warning' };

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      <input ref={multiImgRef} type="file" accept="image/*" multiple style={{ display: 'none' }} onChange={handleImagesSelected} />

      {uploadProgress.total > 0 && (
        <Box sx={{ position: 'fixed', top: 64, left: 0, right: 0, zIndex: 9999 }}>
          <LinearProgress variant="determinate" value={(uploadProgress.done / uploadProgress.total) * 100} sx={{ height: 4 }} />
          <Typography variant="caption" sx={{ display: 'block', textAlign: 'center', bgcolor: 'background.paper', py: 0.3 }}>
            Uploading {uploadProgress.done + 1} of {uploadProgress.total}…
          </Typography>
        </Box>
      )}

      {/* ── Hero / Header ── */}
      {!isLoggedIn ? (
        <Paper elevation={0} sx={{
          mb: 4, p: 4, borderRadius: 3, textAlign: 'center',
          background: 'linear-gradient(135deg, #1b5e20 0%, #43a047 100%)', color: 'white',
        }}>
          <Typography variant="h4" fontWeight="bold" gutterBottom>🛒 Campus Marketplace</Typography>
          <Typography variant="body1" sx={{ mb: 3, opacity: 0.9 }}>
            Buy and sell textbooks, electronics, furniture, bikes and more with verified campus members.
          </Typography>
          <Box sx={{ display: 'flex', gap: 2, justifyContent: 'center', flexWrap: 'wrap' }}>
            <Button variant="contained" size="large"
              sx={{ bgcolor: 'white', color: '#2e7d32', fontWeight: 'bold', '&:hover': { bgcolor: 'rgba(255,255,255,0.9)' } }}
              onClick={() => navigate('/login')}>
              Log In to Buy & Sell
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
            <Typography variant="h4" fontWeight="bold">🛒 Campus Marketplace</Typography>
            <Typography variant="body1" color="text.secondary">Buy and sell with verified campus members</Typography>
          </Box>
          <Button variant="contained" size="large" startIcon={<Sell />}
            onClick={() => { setFormError(''); setPostOpen(true); }}
            sx={{ borderRadius: 2, fontWeight: 'bold', px: 3, py: 1.2 }}>
            + Sell an Item
          </Button>
        </Box>
      )}

      {error && <Alert severity="error" sx={{ mb: 3 }}>{error}</Alert>}

      {/* ── Category pills ── */}
      <Box sx={{ mb: 3, display: 'flex', gap: 1.5, flexWrap: 'wrap' }}>
        <Paper elevation={0} onClick={() => setActiveCategory('all')}
          sx={{ px: 2, py: 1, borderRadius: 3, cursor: 'pointer', display: 'flex', alignItems: 'center', gap: 1,
            border: '2px solid', borderColor: activeCategory === 'all' ? 'primary.main' : 'divider',
            bgcolor: activeCategory === 'all' ? 'primary.50' : 'background.paper', transition: 'all 0.15s' }}>
          <Storefront fontSize="small" color={activeCategory === 'all' ? 'primary' : 'disabled'} />
          <Typography variant="body2" fontWeight={activeCategory === 'all' ? 'bold' : 'normal'}
            color={activeCategory === 'all' ? 'primary.main' : 'text.secondary'}>
            All ({items.length})
          </Typography>
        </Paper>
        {CATEGORIES.map((cat) => {
          const active = activeCategory === cat.id;
          const count = catCounts[cat.id] || 0;
          if (!count) return null;
          return (
            <Paper key={cat.id} elevation={0} onClick={() => setActiveCategory(active ? 'all' : cat.id)}
              sx={{ px: 2, py: 1, borderRadius: 3, cursor: 'pointer', display: 'flex', alignItems: 'center', gap: 1,
                border: '2px solid', borderColor: active ? cat.color : 'divider',
                bgcolor: active ? cat.bg : 'background.paper', transition: 'all 0.15s' }}>
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

      {/* ── Filters ── */}
      <Box sx={{ mb: 3, display: 'flex', gap: 2, flexWrap: 'wrap', alignItems: 'center' }}>
        <TextField placeholder="Search items, location…"
          value={search} onChange={(e) => setSearch(e.target.value)}
          size="small" sx={{ flexGrow: 1, minWidth: 220 }}
          InputProps={{ startAdornment: <InputAdornment position="start"><Search fontSize="small" /></InputAdornment> }} />
        <Box sx={{ display: 'flex', gap: 1 }}>
          {['available', 'sold', 'reserved', 'all'].map((s) => (
            <Chip key={s} size="small"
              label={s === 'all' ? 'All' : s.charAt(0).toUpperCase() + s.slice(1)}
              onClick={() => setFilterStatus(s)}
              color={filterStatus === s ? (statusColors[s] || 'primary') : 'default'}
              variant={filterStatus === s ? 'filled' : 'outlined'} />
          ))}
        </Box>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, minWidth: 200 }}>
          <Typography variant="caption" color="text.secondary" noWrap>Max: <b>{fmt(maxPrice)}</b></Typography>
          <Box component="input" type="range" min={100} max={Math.ceil(maxPriceInData / 1000) * 1000} step={500}
            value={maxPrice} onChange={(e) => setMaxPrice(parseInt(e.target.value))}
            style={{ flexGrow: 1, accentColor: '#2e7d32' }} />
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
          <ShoppingCart sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
          <Typography variant="h6" color="text.secondary">No items match your search</Typography>
          {isLoggedIn && <Button variant="contained" startIcon={<Add />} sx={{ mt: 2 }} onClick={() => setPostOpen(true)}>Sell an Item</Button>}
        </Box>
      ) : (
        <Grid container spacing={3}>
          {filtered.map((item) => {
            const catInfo = CAT_MAP[item.category] || CAT_MAP['Other'];
            const condInfo = CONDITIONS[item.condition_status] || { label: item.condition_status, color: 'default' };
            const isSold = item.status === 'sold';
            const isReserved = item.status === 'reserved';
            return (
              <Grid item xs={12} sm={6} md={4} key={item.id}>
                <Card elevation={2} sx={{
                  height: '100%', display: 'flex', flexDirection: 'column', borderRadius: 3,
                  transition: 'transform 0.2s, box-shadow 0.2s',
                  '&:hover': { transform: 'translateY(-4px)', boxShadow: 6 },
                  opacity: isSold ? 0.78 : 1,
                  outline: isMine(item) ? '2px solid' : 'none', outlineColor: 'primary.main',
                }}>
                  <Box sx={{ position: 'relative' }}>
                    <ImageCarousel images={item.images || []} height={200} />
                    {(isSold || isReserved) && (
                      <Box sx={{ position: 'absolute', inset: 0, bgcolor: 'rgba(0,0,0,0.35)', display: 'flex', alignItems: 'center', justifyContent: 'center', pointerEvents: 'none' }}>
                        <Chip label={isSold ? 'SOLD' : 'RESERVED'} color={isSold ? 'error' : 'warning'} sx={{ fontWeight: 'bold', fontSize: '1rem', px: 2 }} />
                      </Box>
                    )}
                    <Chip
                      icon={React.cloneElement(catInfo.icon, { style: { color: catInfo.color, fontSize: 14 } })}
                      label={catInfo.label} size="small"
                      sx={{ position: 'absolute', top: 10, left: 10, bgcolor: catInfo.bg, color: catInfo.color, fontWeight: 'bold', fontSize: '0.65rem', height: 22 }} />
                    {item.is_negotiable && (
                      <Chip label="Negotiable" size="small" icon={<LocalOffer sx={{ fontSize: '12px !important' }} />}
                        sx={{ position: 'absolute', top: 10, right: 10, bgcolor: 'rgba(255,193,7,0.9)', color: '#333', fontWeight: 'bold', fontSize: '0.6rem', height: 20 }} />
                    )}
                    {canManage(item) && (
                      <Tooltip title="Add photos">
                        <IconButton size="small"
                          sx={{ position: 'absolute', bottom: 8, right: 8, bgcolor: 'rgba(0,0,0,0.55)', color: 'white' }}
                          onClick={(e) => { e.stopPropagation(); triggerUpload(item.id); }}>
                          <AddAPhoto fontSize="small" />
                        </IconButton>
                      </Tooltip>
                    )}
                  </Box>

                  <CardContent sx={{ flexGrow: 1, p: 2.5 }}>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 0.5 }}>
                      <Typography variant="subtitle1" fontWeight="bold" sx={{ flexGrow: 1, mr: 1, lineHeight: 1.3 }}>
                        {item.title}
                      </Typography>
                      <Chip label={condInfo.label} color={condInfo.color} size="small" sx={{ height: 20, fontSize: '0.6rem' }} />
                    </Box>

                    <SellerBadge item={item} compact />

                    <Typography variant="h5" color="success.main" fontWeight="bold" sx={{ mt: 1.2, mb: 0.5 }}>
                      {fmt(item.price)}
                    </Typography>

                    {item.location && (
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5, mb: 0.5 }}>
                        <LocationOn fontSize="small" color="action" />
                        <Typography variant="body2" color="text.secondary" noWrap>{item.location}</Typography>
                      </Box>
                    )}

                    {item.description && (
                      <Typography variant="body2" color="text.secondary"
                        sx={{ display: '-webkit-box', WebkitLineClamp: 2, WebkitBoxOrient: 'vertical', overflow: 'hidden', lineHeight: 1.5, mt: 0.5 }}>
                        {item.description}
                      </Typography>
                    )}
                  </CardContent>

                  <CardActions sx={{ px: 2.5, pb: 2.5, flexDirection: 'column', gap: 1, alignItems: 'stretch' }}>
                    <Button variant="contained" size="small" fullWidth sx={{ borderRadius: 2 }}
                      onClick={() => setDetailItem(item)}>
                      View Details & Contact
                    </Button>
                    {canManage(item) && (
                      <Box sx={{ display: 'flex', gap: 1, justifyContent: 'flex-end' }}>
                        {item.status === 'available' && (
                          <>
                            <Tooltip title="Mark as reserved">
                              <Chip label="Reserve" size="small" color="warning" variant="outlined" sx={{ cursor: 'pointer', height: 22, fontSize: '0.65rem' }}
                                onClick={() => handleStatusChange(item, 'reserved')} />
                            </Tooltip>
                            <Tooltip title="Mark as sold">
                              <Chip label="Mark Sold" size="small" color="error" variant="outlined" sx={{ cursor: 'pointer', height: 22, fontSize: '0.65rem' }}
                                onClick={() => handleStatusChange(item, 'sold')} />
                            </Tooltip>
                          </>
                        )}
                        {item.status !== 'available' && (
                          <Chip label="Re-list" size="small" color="success" variant="outlined" sx={{ cursor: 'pointer', height: 22, fontSize: '0.65rem' }}
                            onClick={() => handleStatusChange(item, 'available')} />
                        )}
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
          const condInfo = CONDITIONS[detailItem.condition_status] || { label: detailItem.condition_status, color: 'default' };
          return (
            <>
              <DialogTitle sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', pb: 0 }}>
                <Box sx={{ flexGrow: 1, mr: 1 }}>
                  <Typography variant="h6" fontWeight="bold">{detailItem.title}</Typography>
                  <Box sx={{ display: 'flex', gap: 1, mt: 0.5, flexWrap: 'wrap' }}>
                    <Chip icon={React.cloneElement(catInfo.icon, { style: { color: catInfo.color, fontSize: 14 } })}
                      label={catInfo.label} size="small"
                      sx={{ bgcolor: catInfo.bg, color: catInfo.color, fontWeight: 'bold' }} />
                    <Chip label={condInfo.label} color={condInfo.color} size="small" />
                    <Chip label={detailItem.status.toUpperCase()} color={statusColors[detailItem.status] || 'default'} size="small" />
                    {detailItem.is_negotiable && <Chip label="Negotiable" size="small" icon={<LocalOffer sx={{ fontSize: '12px !important' }} />} color="warning" />}
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
                      Upload Photos (multiple)
                    </Button>
                    <Typography variant="caption" color="text.secondary">
                      {(detailItem.images || []).length} photo{(detailItem.images || []).length !== 1 ? 's' : ''} added
                    </Typography>
                  </Box>
                )}

                <SellerBadge item={detailItem} compact={false} />

                {/* Price */}
                <Box sx={{ p: 2, borderRadius: 2, bgcolor: 'success.50', border: '1px solid', borderColor: 'success.100', mb: 2.5, display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                  <Box>
                    <Typography variant="caption" color="text.secondary">Asking Price</Typography>
                    <Typography variant="h4" fontWeight="bold" color="success.main">{fmt(detailItem.price)}</Typography>
                    {detailItem.is_negotiable && (
                      <Typography variant="caption" color="success.main" fontWeight="bold">Price is negotiable</Typography>
                    )}
                  </Box>
                </Box>

                {detailItem.location && (
                  <Box sx={{ display: 'flex', gap: 0.8, alignItems: 'center', mb: 1.5 }}>
                    <LocationOn fontSize="small" color="action" />
                    <Typography variant="body2">{detailItem.location}</Typography>
                  </Box>
                )}

                {detailItem.description && (
                  <Box sx={{ mb: 2.5 }}>
                    <Typography variant="subtitle2" fontWeight="bold" gutterBottom>Description</Typography>
                    <Typography variant="body2" color="text.secondary" sx={{ lineHeight: 1.7 }}>{detailItem.description}</Typography>
                  </Box>
                )}

                {/* Contact */}
                <Box sx={{ p: 2, borderRadius: 2, bgcolor: 'success.50', border: '1px solid', borderColor: 'success.200' }}>
                  <Typography variant="subtitle2" fontWeight="bold" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                    <Phone fontSize="small" color="success" /> Contact Seller
                  </Typography>
                  {isLoggedIn ? (
                    detailItem.contact_info ? (
                      <>
                        <Typography variant="body1" fontWeight="bold">{detailItem.contact_info}</Typography>
                        <ContactButtons contact={detailItem.contact_info} />
                      </>
                    ) : <Typography variant="body2" color="text.secondary">No contact number provided</Typography>
                  ) : (
                    <Box>
                      <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>Log in to see the seller's contact details.</Typography>
                      <Button variant="contained" size="small" onClick={() => { setDetailItem(null); navigate('/login'); }}>Log In to Contact</Button>
                    </Box>
                  )}
                </Box>
              </DialogContent>

              {canManage(detailItem) && (
                <DialogActions sx={{ px: 3, pb: 2, gap: 1, flexWrap: 'wrap' }}>
                  {detailItem.status === 'available' ? (
                    <>
                      <Button color="warning" variant="outlined" size="small" onClick={() => handleStatusChange(detailItem, 'reserved')}>Mark Reserved</Button>
                      <Button color="error" variant="outlined" size="small" onClick={() => handleStatusChange(detailItem, 'sold')} startIcon={<CheckCircle />}>Mark Sold</Button>
                    </>
                  ) : (
                    <Button color="success" variant="outlined" size="small" onClick={() => handleStatusChange(detailItem, 'available')}>Re-list as Available</Button>
                  )}
                  <Button color="error" variant="outlined" size="small" onClick={() => handleDelete(detailItem.id)} startIcon={<Delete />}>Delete</Button>
                </DialogActions>
              )}
            </>
          );
        })()}
      </Dialog>

      {/* ─── Post / Sell Dialog ─── */}
      <Dialog open={postOpen} onClose={() => setPostOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>
          <Typography variant="h6" fontWeight="bold">Sell an Item</Typography>
          <Typography variant="body2" color="text.secondary">Your verified campus profile will be shown to buyers</Typography>
        </DialogTitle>
        <DialogContent sx={{ pt: 1 }}>
          {formError && <Alert severity="error" sx={{ mb: 2 }}>{formError}</Alert>}

          <TextField fullWidth label="Item Title *" value={form.title}
            onChange={(e) => setForm({ ...form, title: e.target.value })} sx={{ mb: 2, mt: 1 }}
            placeholder="e.g. HP Laptop 15-inch, HC Verma Vol 1, Cycle" />

          <Grid container spacing={2} sx={{ mb: 2 }}>
            <Grid item xs={6}>
              <FormControl fullWidth>
                <InputLabel>Category *</InputLabel>
                <Select value={form.category} label="Category *"
                  onChange={(e) => setForm({ ...form, category: e.target.value })}>
                  {CATEGORIES.map((c) => (
                    <MenuItem key={c.id} value={c.id}>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        <Box sx={{ color: c.color, display: 'flex' }}>{React.cloneElement(c.icon, { fontSize: 'small' })}</Box>
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
                  <MenuItem value="new">Brand New</MenuItem>
                  <MenuItem value="excellent">Like New</MenuItem>
                  <MenuItem value="good">Good</MenuItem>
                  <MenuItem value="used">Used</MenuItem>
                  <MenuItem value="fair">Fair</MenuItem>
                </Select>
              </FormControl>
            </Grid>
          </Grid>

          <Grid container spacing={2} sx={{ mb: 2 }}>
            <Grid item xs={6}>
              <TextField fullWidth label="Asking Price (₹) *" type="number" value={form.price}
                onChange={(e) => setForm({ ...form, price: e.target.value })}
                InputProps={{ startAdornment: <InputAdornment position="start">₹</InputAdornment> }} />
            </Grid>
            <Grid item xs={6} sx={{ display: 'flex', alignItems: 'center' }}>
              <FormControlLabel
                control={<Switch checked={form.is_negotiable} onChange={(e) => setForm({ ...form, is_negotiable: e.target.checked })} color="warning" />}
                label={<Typography variant="body2">Price Negotiable</Typography>} />
            </Grid>
          </Grid>

          <TextField fullWidth label="Location / Pickup Point" value={form.location}
            onChange={(e) => setForm({ ...form, location: e.target.value })} sx={{ mb: 2 }}
            placeholder="e.g. Hostel A Block, Room 105"
            InputProps={{ startAdornment: <InputAdornment position="start"><LocationOn fontSize="small" /></InputAdornment> }} />

          <TextField fullWidth label="Your Contact Number *" value={form.contact_info}
            onChange={(e) => setForm({ ...form, contact_info: e.target.value })} sx={{ mb: 2 }}
            placeholder="+91 98765 43210"
            InputProps={{ startAdornment: <InputAdornment position="start"><Phone fontSize="small" /></InputAdornment> }} />

          <TextField fullWidth label="Description" multiline rows={3} value={form.description}
            onChange={(e) => setForm({ ...form, description: e.target.value })}
            placeholder="Describe the item — age, condition, accessories included, reason for selling, etc." />
        </DialogContent>
        <DialogActions sx={{ px: 3, pb: 2 }}>
          <Button onClick={() => setPostOpen(false)}>Cancel</Button>
          <Button variant="contained" onClick={handlePost} disabled={submitting} startIcon={<PostAdd />} size="large" color="success">
            {submitting ? 'Posting…' : 'Post Listing →'}
          </Button>
        </DialogActions>
      </Dialog>

      <Snackbar open={!!snack} autoHideDuration={3500} onClose={() => setSnack('')}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }} message={snack} />
    </Container>
  );
};

export default Marketplace;
