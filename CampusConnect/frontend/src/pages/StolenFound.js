import React, { useState, useEffect, useRef } from 'react';
import {
  Container, Typography, Box, Grid, Card, CardContent, CardActions,
  Button, Chip, Dialog, DialogTitle, DialogContent, DialogActions,
  TextField, FormControl, InputLabel, Select, MenuItem,
  Alert, CircularProgress, IconButton, InputAdornment, LinearProgress,
  Snackbar, Divider, Paper, Avatar, Tooltip, Fab, ToggleButton, ToggleButtonGroup,
} from '@mui/material';
import {
  ReportProblem, SearchOff, Add, Close, Search, Delete,
  LocationOn, Phone, CloudUpload, AddAPhoto,
  ChevronLeft, ChevronRight, WhatsApp, Call,
  VerifiedUser, CalendarMonth, CheckCircle, PostAdd,
  FindInPage, HelpOutline, Inventory,
} from '@mui/icons-material';
import axios from 'axios';
import { useSelector } from 'react-redux';
import { useNavigate } from 'react-router-dom';

const CATEGORIES = [
  'Electronics', 'Bags', 'Documents', 'Wallets', 'Books',
  'Jewellery', 'Clothing', 'Keys', 'Sports', 'Others',
];

const CATEGORY_COLORS = {
  Electronics: '#1565c0', Bags: '#6a1b9a', Documents: '#e65100',
  Wallets: '#2e7d32', Books: '#558b2f', Jewellery: '#f9a825',
  Clothing: '#00838f', Keys: '#5d4037', Sports: '#c62828', Others: '#455a64',
};

const timeSince = (dateStr) => {
  const diff = Date.now() - new Date(dateStr).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 60) return `${mins}m ago`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return `${hrs}h ago`;
  const days = Math.floor(hrs / 24);
  if (days < 7) return `${days}d ago`;
  return new Date(dateStr).toLocaleDateString('en-IN', { day: 'numeric', month: 'short' });
};

const memberSince = (d) => d ? new Date(d).toLocaleDateString('en-IN', { month: 'short', year: 'numeric' }) : '';
const cleanPhone = (raw = '') => raw.replace(/[^0-9+]/g, '');
const waLink    = (raw) => { const n = cleanPhone(raw).replace(/^\+/, ''); return `https://wa.me/${n.startsWith('91') ? n : '91' + n}`; };
const callLink  = (raw) => `tel:${cleanPhone(raw)}`;

// ── Image carousel ──────────────────────────────────────────────────────────
const ImageCarousel = ({ images, height = 220 }) => {
  const [idx, setIdx] = useState(0);
  const imgs = images || [];
  if (!imgs.length) return (
    <Box sx={{ height, bgcolor: 'action.hover', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: 1 }}>
      <Inventory sx={{ fontSize: 48, color: 'text.disabled' }} />
      <Typography variant="caption" color="text.disabled">No photo added</Typography>
    </Box>
  );
  return (
    <Box sx={{ position: 'relative', height, bgcolor: '#000', overflow: 'hidden' }}>
      <img src={imgs[idx]} alt={`Item ${idx + 1}`}
        style={{ width: '100%', height, objectFit: 'cover', transition: 'opacity 0.25s' }} />
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
    </Box>
  );
};

// ── Reporter badge ──────────────────────────────────────────────────────────
const ReporterBadge = ({ report, compact = false }) => {
  const name = report.reporter_display_name || report.reporter_name || 'Campus Member';
  const since = memberSince(report.reporter_joined);
  const initials = name.split(' ').map((w) => w[0]).join('').toUpperCase().slice(0, 2);

  if (compact) return (
    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mt: 0.5 }}>
      <Avatar sx={{ width: 22, height: 22, fontSize: '0.6rem', bgcolor: report.report_type === 'lost' ? 'error.main' : 'success.main' }}>{initials}</Avatar>
      <Typography variant="caption" color="text.secondary" noWrap>{name}</Typography>
      <Chip icon={<VerifiedUser sx={{ fontSize: '0.65rem !important' }} />} label="Verified" size="small"
        color="success" variant="outlined" sx={{ height: 16, fontSize: '0.55rem', '& .MuiChip-label': { px: 0.5 } }} />
    </Box>
  );

  return (
    <Box sx={{ p: 2, borderRadius: 2, bgcolor: 'grey.50', border: '1px solid', borderColor: 'grey.200', mb: 2 }}>
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
        <Avatar sx={{ width: 50, height: 50, bgcolor: report.report_type === 'lost' ? 'error.main' : 'success.main', fontWeight: 'bold', boxShadow: 2 }}>{initials}</Avatar>
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
        {report.report_type === 'lost'
          ? 'If you find this item, please contact the owner immediately.'
          : 'If this item belongs to you, contact to claim it.'}
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
        component="a" href={callLink(contact)} sx={{ borderRadius: 2, fontWeight: 'bold' }}>
        Call
      </Button>
    </Box>
  );
};

// ─── Main Component ────────────────────────────────────────────────────────
const StolenFound = () => {
  const { user, token } = useSelector((s) => s.auth);
  const navigate = useNavigate();
  const isLoggedIn = !!user;
  const isAdmin = user?.role === 'admin';

  const [reports, setReports] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [snack, setSnack] = useState('');

  const [typeFilter, setTypeFilter] = useState('all');
  const [categoryFilter, setCategoryFilter] = useState('all');
  const [statusFilter, setStatusFilter] = useState('active');
  const [search, setSearch] = useState('');

  const [detailReport, setDetailReport] = useState(null);
  const [postOpen, setPostOpen] = useState(false);
  const [postType, setPostType] = useState('lost');

  const [form, setForm] = useState({ item_name: '', description: '', category: 'Electronics', location: '', contact_info: '' });
  const [formError, setFormError] = useState('');
  const [submitting, setSubmitting] = useState(false);

  const multiImgRef = useRef(null);
  const [uploadingFor, setUploadingFor] = useState(null);
  const [uploadProgress, setUploadProgress] = useState({ done: 0, total: 0 });

  const fetchReports = async () => {
    try {
      setLoading(true);
      const res = await axios.get('/stolen-found');
      setReports(res.data);
    } catch { setError('Failed to load reports'); }
    finally { setLoading(false); }
  };

  useEffect(() => { fetchReports(); }, []);

  const isMine = (r) => r.reported_by === user?.id;
  const canManage = (r) => isAdmin || isMine(r);

  const handlePost = async () => {
    if (!form.item_name.trim()) { setFormError('Item name is required'); return; }
    setSubmitting(true); setFormError('');
    try {
      const res = await axios.post('/stolen-found', { ...form, report_type: postType },
        { headers: { Authorization: `Bearer ${token}` } });
      setReports((prev) => [res.data, ...prev]);
      setPostOpen(false);
      setForm({ item_name: '', description: '', category: 'Electronics', location: '', contact_info: '' });
      setDetailReport(res.data);
      setSnack(`${postType === 'lost' ? 'Lost item' : 'Found item'} report posted! Add a photo to help others identify it.`);
    } catch (err) {
      setFormError(err.response?.data?.detail || 'Failed to post report');
    } finally { setSubmitting(false); }
  };

  // Multi-image upload
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
        const res = await axios.post(`/stolen-found/${id}/image`, fd, {
          headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'multipart/form-data' },
        });
        latest = res.data;
        setUploadProgress({ done: i + 1, total: files.length });
      } catch {}
    }
    if (latest) {
      setReports((prev) => prev.map((r) => r.id === id ? { ...r, ...latest } : r));
      if (detailReport?.id === id) setDetailReport((prev) => ({ ...prev, ...latest }));
    }
    setUploadingFor(null);
    setUploadProgress({ done: 0, total: 0 });
    setSnack(`${files.length} photo${files.length > 1 ? 's' : ''} uploaded!`);
  };

  const handleStatusChange = async (report, newStatus) => {
    try {
      const res = await axios.patch(`/stolen-found/${report.id}/status`, { status: newStatus },
        { headers: { Authorization: `Bearer ${token}` } });
      setReports((prev) => prev.map((r) => r.id === report.id ? { ...r, ...res.data } : r));
      if (detailReport?.id === report.id) setDetailReport((prev) => ({ ...prev, ...res.data }));
      setSnack(newStatus === 'resolved' ? '✓ Marked as resolved!' : 'Status updated');
    } catch { setSnack('Failed to update'); }
  };

  const handleDelete = async (id) => {
    if (!window.confirm('Remove this report?')) return;
    try {
      await axios.delete(`/stolen-found/${id}`, { headers: { Authorization: `Bearer ${token}` } });
      setReports((prev) => prev.filter((r) => r.id !== id));
      if (detailReport?.id === id) setDetailReport(null);
      setSnack('Report removed');
    } catch { setSnack('Failed to delete'); }
  };

  const filtered = reports.filter((r) => {
    if (typeFilter !== 'all' && r.report_type !== typeFilter) return false;
    if (categoryFilter !== 'all' && r.category !== categoryFilter) return false;
    if (statusFilter !== 'all' && r.status !== statusFilter) return false;
    if (search) {
      const q = search.toLowerCase();
      if (!r.item_name.toLowerCase().includes(q) &&
          !(r.description || '').toLowerCase().includes(q) &&
          !(r.location || '').toLowerCase().includes(q)) return false;
    }
    return true;
  });

  const lostCount   = reports.filter((r) => r.report_type === 'lost'  && r.status === 'active').length;
  const foundCount  = reports.filter((r) => r.report_type === 'found' && r.status === 'active').length;

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

      {/* ── Header ── */}
      {!isLoggedIn ? (
        <Paper elevation={0} sx={{
          mb: 4, p: 4, borderRadius: 3, textAlign: 'center',
          background: 'linear-gradient(135deg, #b71c1c 0%, #ef5350 100%)', color: 'white',
        }}>
          <Typography variant="h4" fontWeight="bold" gutterBottom>🔍 Lost & Found</Typography>
          <Typography variant="body1" sx={{ mb: 3, opacity: 0.9 }}>
            Lost something? Found something? Post here and help reunite items with their owners.
          </Typography>
          <Box sx={{ display: 'flex', gap: 2, justifyContent: 'center', flexWrap: 'wrap' }}>
            <Button variant="contained" size="large"
              sx={{ bgcolor: 'white', color: '#b71c1c', fontWeight: 'bold', '&:hover': { bgcolor: 'rgba(255,255,255,0.9)' } }}
              onClick={() => navigate('/login')}>
              Log In to Report
            </Button>
            <Button variant="outlined" size="large"
              sx={{ borderColor: 'white', color: 'white', fontWeight: 'bold', '&:hover': { bgcolor: 'rgba(255,255,255,0.1)' } }}
              onClick={() => navigate('/signup')}>
              Sign Up Free
            </Button>
          </Box>
        </Paper>
      ) : (
        <Box sx={{ mb: 3 }}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: 2, mb: 2 }}>
            <Box>
              <Typography variant="h4" fontWeight="bold">🔍 Lost & Found</Typography>
              <Typography variant="body1" color="text.secondary">Help reunite lost items with their owners</Typography>
            </Box>
            <Box sx={{ display: 'flex', gap: 1.5 }}>
              <Button variant="outlined" size="large" startIcon={<SearchOff />} color="error"
                onClick={() => { setPostType('lost'); setFormError(''); setPostOpen(true); }}
                sx={{ borderRadius: 2, fontWeight: 'bold' }}>
                Report Lost
              </Button>
              <Button variant="contained" size="large" startIcon={<FindInPage />} color="success"
                onClick={() => { setPostType('found'); setFormError(''); setPostOpen(true); }}
                sx={{ borderRadius: 2, fontWeight: 'bold' }}>
                Report Found
              </Button>
            </Box>
          </Box>

          {/* Stats pills */}
          <Box sx={{ display: 'flex', gap: 1.5, flexWrap: 'wrap' }}>
            <Chip icon={<ReportProblem />} label={`${lostCount} Items Lost`} color="error" variant="outlined" />
            <Chip icon={<FindInPage />} label={`${foundCount} Items Found`} color="success" variant="outlined" />
            <Chip icon={<CheckCircle />} label={`${reports.filter((r) => r.status === 'resolved').length} Reunited`} color="primary" variant="outlined" />
          </Box>
        </Box>
      )}

      {error && <Alert severity="error" sx={{ mb: 3 }}>{error}</Alert>}

      {/* ── Filters ── */}
      <Box sx={{ mb: 3, display: 'flex', gap: 2, flexWrap: 'wrap', alignItems: 'center' }}>
        <ToggleButtonGroup value={typeFilter} exclusive onChange={(_, v) => v && setTypeFilter(v)} size="small">
          <ToggleButton value="all" sx={{ px: 2 }}>All</ToggleButton>
          <ToggleButton value="lost" sx={{ px: 2, color: 'error.main', '&.Mui-selected': { bgcolor: 'error.50', color: 'error.main', borderColor: 'error.main' } }}>
            Lost
          </ToggleButton>
          <ToggleButton value="found" sx={{ px: 2, color: 'success.main', '&.Mui-selected': { bgcolor: 'success.50', color: 'success.main', borderColor: 'success.main' } }}>
            Found
          </ToggleButton>
        </ToggleButtonGroup>

        <TextField placeholder="Search items, description, location…"
          value={search} onChange={(e) => setSearch(e.target.value)}
          size="small" sx={{ flexGrow: 1, minWidth: 200 }}
          InputProps={{ startAdornment: <InputAdornment position="start"><Search fontSize="small" /></InputAdornment> }} />

        <FormControl size="small" sx={{ minWidth: 130 }}>
          <InputLabel>Category</InputLabel>
          <Select value={categoryFilter} label="Category" onChange={(e) => setCategoryFilter(e.target.value)}>
            <MenuItem value="all">All Categories</MenuItem>
            {CATEGORIES.map((c) => <MenuItem key={c} value={c}>{c}</MenuItem>)}
          </Select>
        </FormControl>

        <Box sx={{ display: 'flex', gap: 1 }}>
          {['active', 'resolved', 'all'].map((s) => (
            <Chip key={s} size="small"
              label={s === 'active' ? 'Active' : s === 'resolved' ? 'Resolved' : 'All'}
              onClick={() => setStatusFilter(s)}
              color={statusFilter === s ? (s === 'active' ? 'warning' : s === 'resolved' ? 'success' : 'primary') : 'default'}
              variant={statusFilter === s ? 'filled' : 'outlined'} />
          ))}
        </Box>
      </Box>

      <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
        Showing <b>{filtered.length}</b> of {reports.length} reports
      </Typography>

      {/* ── Reports grid ── */}
      {loading ? (
        <Box sx={{ display: 'flex', justifyContent: 'center', py: 10 }}><CircularProgress /></Box>
      ) : filtered.length === 0 ? (
        <Box sx={{ textAlign: 'center', py: 10 }}>
          <HelpOutline sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
          <Typography variant="h6" color="text.secondary">No reports match your filters</Typography>
          {isLoggedIn && (
            <Box sx={{ display: 'flex', gap: 2, justifyContent: 'center', mt: 2 }}>
              <Button variant="outlined" color="error" startIcon={<SearchOff />} onClick={() => { setPostType('lost'); setPostOpen(true); }}>Report Lost</Button>
              <Button variant="contained" color="success" startIcon={<FindInPage />} onClick={() => { setPostType('found'); setPostOpen(true); }}>Report Found</Button>
            </Box>
          )}
        </Box>
      ) : (
        <Grid container spacing={3}>
          {filtered.map((report) => {
            const isLost = report.report_type === 'lost';
            const isResolved = report.status === 'resolved';
            const catColor = CATEGORY_COLORS[report.category] || '#455a64';
            return (
              <Grid item xs={12} sm={6} md={4} key={report.id}>
                <Card elevation={2} sx={{
                  height: '100%', display: 'flex', flexDirection: 'column', borderRadius: 3,
                  transition: 'transform 0.2s, box-shadow 0.2s',
                  '&:hover': { transform: 'translateY(-4px)', boxShadow: 6 },
                  opacity: isResolved ? 0.75 : 1,
                  borderLeft: '4px solid',
                  borderColor: isResolved ? 'success.main' : isLost ? 'error.main' : 'success.main',
                  outline: isMine(report) ? '1px solid' : 'none', outlineColor: 'primary.light',
                }}>
                  <Box sx={{ position: 'relative' }}>
                    <ImageCarousel images={report.images || []} height={180} />
                    {/* Type badge */}
                    <Chip
                      icon={isLost ? <ReportProblem sx={{ fontSize: '14px !important' }} /> : <FindInPage sx={{ fontSize: '14px !important' }} />}
                      label={isLost ? 'LOST' : 'FOUND'}
                      size="small"
                      sx={{
                        position: 'absolute', top: 10, left: 10, fontWeight: 'bold', fontSize: '0.7rem',
                        bgcolor: isLost ? 'error.main' : 'success.main', color: 'white',
                      }} />
                    {isResolved && (
                      <Chip icon={<CheckCircle sx={{ fontSize: '14px !important' }} />}
                        label="RESOLVED" size="small" color="success"
                        sx={{ position: 'absolute', top: 10, right: 10, fontWeight: 'bold', fontSize: '0.65rem' }} />
                    )}
                    {canManage(report) && (
                      <Tooltip title="Add photos">
                        <IconButton size="small"
                          sx={{ position: 'absolute', bottom: 8, right: 8, bgcolor: 'rgba(0,0,0,0.55)', color: 'white' }}
                          onClick={(e) => { e.stopPropagation(); triggerUpload(report.id); }}>
                          <AddAPhoto fontSize="small" />
                        </IconButton>
                      </Tooltip>
                    )}
                  </Box>

                  <CardContent sx={{ flexGrow: 1, p: 2.5 }}>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 0.5 }}>
                      <Typography variant="subtitle1" fontWeight="bold" sx={{ flexGrow: 1, mr: 1, lineHeight: 1.3 }}>
                        {report.item_name}
                      </Typography>
                      <Chip label={report.category} size="small"
                        sx={{ height: 20, fontSize: '0.6rem', bgcolor: catColor + '22', color: catColor, fontWeight: 'bold' }} />
                    </Box>

                    <ReporterBadge report={report} compact />

                    {report.location && (
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5, mt: 0.8 }}>
                        <LocationOn fontSize="small" color="action" />
                        <Typography variant="body2" color="text.secondary" noWrap>{report.location}</Typography>
                      </Box>
                    )}

                    {report.description && (
                      <Typography variant="body2" color="text.secondary"
                        sx={{ mt: 0.5, display: '-webkit-box', WebkitLineClamp: 2, WebkitBoxOrient: 'vertical', overflow: 'hidden', lineHeight: 1.5 }}>
                        {report.description}
                      </Typography>
                    )}

                    <Typography variant="caption" color="text.disabled" sx={{ display: 'block', mt: 1 }}>
                      {timeSince(report.created_at)}
                    </Typography>
                  </CardContent>

                  <CardActions sx={{ px: 2.5, pb: 2.5, flexDirection: 'column', gap: 1, alignItems: 'stretch' }}>
                    <Button variant={isLost ? 'outlined' : 'contained'} color={isLost ? 'error' : 'success'}
                      size="small" fullWidth sx={{ borderRadius: 2 }}
                      onClick={() => setDetailReport(report)}>
                      {isLost ? 'I Found This!' : 'This Is Mine!'}
                    </Button>
                    {canManage(report) && !isResolved && (
                      <Box sx={{ display: 'flex', gap: 1, justifyContent: 'flex-end' }}>
                        <Tooltip title="Mark as resolved / item found">
                          <Chip label="Resolve" size="small" color="success" variant="outlined" sx={{ cursor: 'pointer', height: 22, fontSize: '0.65rem' }}
                            onClick={() => handleStatusChange(report, 'resolved')} />
                        </Tooltip>
                        <Tooltip title="Remove report">
                          <IconButton size="small" color="error" onClick={() => handleDelete(report.id)}>
                            <Delete fontSize="small" />
                          </IconButton>
                        </Tooltip>
                      </Box>
                    )}
                    {canManage(report) && isResolved && (
                      <Box sx={{ display: 'flex', gap: 1, justifyContent: 'flex-end' }}>
                        <Chip label="Re-activate" size="small" variant="outlined" sx={{ cursor: 'pointer', height: 22, fontSize: '0.65rem' }}
                          onClick={() => handleStatusChange(report, 'active')} />
                        <IconButton size="small" color="error" onClick={() => handleDelete(report.id)}>
                          <Delete fontSize="small" />
                        </IconButton>
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
        <Fab color="error" sx={{ position: 'fixed', bottom: 32, right: 32 }}
          onClick={() => { setPostType('lost'); setFormError(''); setPostOpen(true); }}>
          <Add />
        </Fab>
      )}

      {/* ─── Detail Dialog ─── */}
      <Dialog open={!!detailReport} onClose={() => setDetailReport(null)} maxWidth="sm" fullWidth>
        {detailReport && (() => {
          const isLost = detailReport.report_type === 'lost';
          const isResolved = detailReport.status === 'resolved';
          const catColor = CATEGORY_COLORS[detailReport.category] || '#455a64';
          return (
            <>
              <DialogTitle sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', pb: 0 }}>
                <Box sx={{ flexGrow: 1, mr: 1 }}>
                  <Typography variant="h6" fontWeight="bold">{detailReport.item_name}</Typography>
                  <Box sx={{ display: 'flex', gap: 1, mt: 0.5, flexWrap: 'wrap' }}>
                    <Chip
                      icon={isLost ? <ReportProblem sx={{ fontSize: '14px !important' }} /> : <FindInPage sx={{ fontSize: '14px !important' }} />}
                      label={isLost ? 'LOST' : 'FOUND'} size="small"
                      sx={{ bgcolor: isLost ? 'error.main' : 'success.main', color: 'white', fontWeight: 'bold' }} />
                    <Chip label={detailReport.category} size="small"
                      sx={{ bgcolor: catColor + '22', color: catColor, fontWeight: 'bold' }} />
                    <Chip label={isResolved ? 'Resolved' : 'Active'}
                      color={isResolved ? 'success' : 'warning'} size="small" />
                  </Box>
                </Box>
                <IconButton onClick={() => setDetailReport(null)}><Close /></IconButton>
              </DialogTitle>

              <DialogContent sx={{ pt: 1.5 }}>
                <Box sx={{ mx: -3, mb: 2.5 }}>
                  <ImageCarousel images={detailReport.images || []} height={260} />
                </Box>

                {canManage(detailReport) && (
                  <Box sx={{ mb: 2, display: 'flex', gap: 1, alignItems: 'center' }}>
                    <Button startIcon={<CloudUpload />} size="small" variant="outlined"
                      onClick={() => triggerUpload(detailReport.id)}>
                      Upload Photos (multiple)
                    </Button>
                    <Typography variant="caption" color="text.secondary">
                      {(detailReport.images || []).length} photo{(detailReport.images || []).length !== 1 ? 's' : ''} added
                    </Typography>
                  </Box>
                )}

                <ReporterBadge report={detailReport} compact={false} />

                {detailReport.location && (
                  <Box sx={{ display: 'flex', gap: 0.8, alignItems: 'center', mb: 1.5 }}>
                    <LocationOn fontSize="small" color="action" />
                    <Box>
                      <Typography variant="caption" color="text.secondary">{isLost ? 'Last seen at' : 'Found at'}</Typography>
                      <Typography variant="body1" fontWeight="bold">{detailReport.location}</Typography>
                    </Box>
                  </Box>
                )}

                {detailReport.description && (
                  <Box sx={{ mb: 2.5 }}>
                    <Typography variant="subtitle2" fontWeight="bold" gutterBottom>Description</Typography>
                    <Typography variant="body2" color="text.secondary" sx={{ lineHeight: 1.7 }}>{detailReport.description}</Typography>
                  </Box>
                )}

                {/* Contact section */}
                <Box sx={{ p: 2, borderRadius: 2, bgcolor: isLost ? 'error.50' : 'success.50', border: '1px solid', borderColor: isLost ? 'error.200' : 'success.200' }}>
                  <Typography variant="subtitle2" fontWeight="bold" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                    <Phone fontSize="small" color={isLost ? 'error' : 'success'} />
                    {isLost ? 'Contact the Owner' : 'Contact the Finder'}
                  </Typography>
                  {isLoggedIn ? (
                    detailReport.contact_info ? (
                      <>
                        <Typography variant="body1" fontWeight="bold">{detailReport.contact_info}</Typography>
                        <ContactButtons contact={detailReport.contact_info} />
                      </>
                    ) : <Typography variant="body2" color="text.secondary">No contact number provided</Typography>
                  ) : (
                    <Box>
                      <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>Log in to see contact details.</Typography>
                      <Button variant="contained" size="small" onClick={() => { setDetailReport(null); navigate('/login'); }}>Log In to Contact</Button>
                    </Box>
                  )}
                </Box>
              </DialogContent>

              {canManage(detailReport) && (
                <DialogActions sx={{ px: 3, pb: 2, gap: 1 }}>
                  {!isResolved ? (
                    <Button color="success" variant="contained" size="small"
                      startIcon={<CheckCircle />} onClick={() => handleStatusChange(detailReport, 'resolved')}>
                      ✓ Mark as Resolved
                    </Button>
                  ) : (
                    <Button variant="outlined" size="small" onClick={() => handleStatusChange(detailReport, 'active')}>Re-activate</Button>
                  )}
                  <Button color="error" variant="outlined" size="small" startIcon={<Delete />} onClick={() => handleDelete(detailReport.id)}>Delete</Button>
                </DialogActions>
              )}
            </>
          );
        })()}
      </Dialog>

      {/* ─── Post Report Dialog ─── */}
      <Dialog open={postOpen} onClose={() => setPostOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle sx={{ pb: 1 }}>
          <Box sx={{ display: 'flex', gap: 1.5, mb: 1 }}>
            <Button variant={postType === 'lost' ? 'contained' : 'outlined'} color="error" size="small"
              startIcon={<SearchOff />} onClick={() => setPostType('lost')} sx={{ borderRadius: 2, fontWeight: 'bold' }}>
              I Lost Something
            </Button>
            <Button variant={postType === 'found' ? 'contained' : 'outlined'} color="success" size="small"
              startIcon={<FindInPage />} onClick={() => setPostType('found')} sx={{ borderRadius: 2, fontWeight: 'bold' }}>
              I Found Something
            </Button>
          </Box>
          <Typography variant="h6" fontWeight="bold">
            {postType === 'lost' ? '😰 Report a Lost Item' : '🎉 Report a Found Item'}
          </Typography>
          <Typography variant="body2" color="text.secondary">Your verified campus profile will be attached to this report</Typography>
        </DialogTitle>
        <DialogContent sx={{ pt: 1 }}>
          {formError && <Alert severity="error" sx={{ mb: 2 }}>{formError}</Alert>}

          <TextField fullWidth label="Item Name *" value={form.item_name}
            onChange={(e) => setForm({ ...form, item_name: e.target.value })} sx={{ mb: 2, mt: 1 }}
            placeholder={postType === 'lost' ? 'e.g. Black Backpack, iPhone 13, ID Card' : 'e.g. Blue Water Bottle, Casio Calculator'} />

          <FormControl fullWidth sx={{ mb: 2 }}>
            <InputLabel>Category *</InputLabel>
            <Select value={form.category} label="Category *"
              onChange={(e) => setForm({ ...form, category: e.target.value })}>
              {CATEGORIES.map((c) => <MenuItem key={c} value={c}>{c}</MenuItem>)}
            </Select>
          </FormControl>

          <TextField fullWidth label={postType === 'lost' ? 'Last Seen Location' : 'Where Did You Find It?'}
            value={form.location} onChange={(e) => setForm({ ...form, location: e.target.value })} sx={{ mb: 2 }}
            placeholder="e.g. Main Canteen, Library Entrance, Sports Ground"
            InputProps={{ startAdornment: <InputAdornment position="start"><LocationOn fontSize="small" /></InputAdornment> }} />

          <TextField fullWidth label="Your Contact Number *" value={form.contact_info}
            onChange={(e) => setForm({ ...form, contact_info: e.target.value })} sx={{ mb: 2 }}
            placeholder="+91 98765 43210"
            InputProps={{ startAdornment: <InputAdornment position="start"><Phone fontSize="small" /></InputAdornment> }} />

          <TextField fullWidth label="Description" multiline rows={3} value={form.description}
            onChange={(e) => setForm({ ...form, description: e.target.value })}
            placeholder={postType === 'lost'
              ? 'Describe the item in detail — colour, brand, what was inside, any identifying features...'
              : 'Describe the item found — where exactly, condition, any details that help identify the owner...'} />
        </DialogContent>
        <DialogActions sx={{ px: 3, pb: 2 }}>
          <Button onClick={() => setPostOpen(false)}>Cancel</Button>
          <Button variant="contained" color={postType === 'lost' ? 'error' : 'success'} onClick={handlePost}
            disabled={submitting} startIcon={<PostAdd />} size="large">
            {submitting ? 'Posting…' : `Post ${postType === 'lost' ? 'Lost' : 'Found'} Report →`}
          </Button>
        </DialogActions>
      </Dialog>

      <Snackbar open={!!snack} autoHideDuration={3500} onClose={() => setSnack('')}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }} message={snack} />
    </Container>
  );
};

export default StolenFound;
