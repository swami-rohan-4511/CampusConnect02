import React, { useState, useEffect, useRef } from 'react';
import {
  Container, Typography, Box, Grid, Card, CardContent, CardActions,
  CardMedia, Button, Chip, Dialog, DialogTitle, DialogContent, DialogActions,
  TextField, FormControl, InputLabel, Select, MenuItem, Switch,
  FormControlLabel, Alert, CircularProgress, Divider, IconButton,
  InputAdornment, Tabs, Tab, Tooltip, Fab, Avatar, Snackbar,
} from '@mui/material';
import {
  Restaurant, LocationOn, Phone, AccessTime, DeliveryDining,
  LocalCafe, StoreMallDirectory, Add, Close, Spa, AttachMoney,
  Search, Delete, MenuBook, Store, CloudUpload, Person, AddAPhoto,
} from '@mui/icons-material';
import axios from 'axios';
import { useSelector } from 'react-redux';

const OUTLET_TYPES = ['all', 'canteen', 'cafe', 'restaurant', 'food_court'];
const TYPE_LABELS = { canteen: 'Canteen', cafe: 'Café', restaurant: 'Restaurant', food_court: 'Food Court' };
const TYPE_COLORS = { canteen: 'primary', cafe: 'secondary', restaurant: 'error', food_court: 'success' };
const TYPE_ICONS = {
  canteen: <Restaurant fontSize="small" />,
  cafe: <LocalCafe fontSize="small" />,
  restaurant: <Restaurant fontSize="small" />,
  food_court: <StoreMallDirectory fontSize="small" />,
};

const Food = () => {
  const { user, token } = useSelector((state) => state.auth);
  const isAdmin = user?.role === 'admin';
  const isLoggedIn = !!user;

  const [outlets, setOutlets] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [filterType, setFilterType] = useState('all');
  const [searchText, setSearchText] = useState('');
  const [snackMsg, setSnackMsg] = useState('');

  // Menu dialog
  const [menuDialogOpen, setMenuDialogOpen] = useState(false);
  const [selectedOutlet, setSelectedOutlet] = useState(null);
  const [menuItems, setMenuItems] = useState([]);
  const [menuLoading, setMenuLoading] = useState(false);
  const [menuFilter, setMenuFilter] = useState('all');

  // Add stall dialog
  const [addOutletOpen, setAddOutletOpen] = useState(false);
  const [outletForm, setOutletForm] = useState({
    name: '', type: 'food_court', description: '', location: '',
    contact_info: '', operating_hours: '', delivery_available: false,
  });
  const [stallImageFile, setStallImageFile] = useState(null);
  const [stallImagePreview, setStallImagePreview] = useState('');
  const stallImageRef = useRef(null);

  // Add menu item dialog
  const [addMenuOpen, setAddMenuOpen] = useState(false);
  const [menuForm, setMenuForm] = useState({
    item_name: '', description: '', price: '', category: '',
    is_vegetarian: true, is_available: true,
  });
  const [menuImageFile, setMenuImageFile] = useState(null);
  const [menuImagePreview, setMenuImagePreview] = useState('');
  const menuImageRef = useRef(null);

  // Per-item image upload (existing items)
  const [uploadingFor, setUploadingFor] = useState(null);
  const existingItemImageRef = useRef(null);

  const [submitting, setSubmitting] = useState(false);
  const [formError, setFormError] = useState('');

  const fetchOutlets = async () => {
    try {
      setLoading(true);
      const res = await axios.get('/food');
      setOutlets(res.data);
    } catch {
      setError('Failed to load food outlets');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchOutlets(); }, []);

  const isOutletMine = (outlet) => outlet.owner_id === user?.id;
  const canManage = (outlet) => isAdmin || isOutletMine(outlet);

  const openMenu = async (outlet) => {
    setSelectedOutlet(outlet);
    setMenuDialogOpen(true);
    setMenuLoading(true);
    setMenuFilter('all');
    setMenuItems([]);
    try {
      const res = await axios.get(`/food/${outlet.id}/menu`);
      setMenuItems(res.data);
    } catch {
      setMenuItems([]);
    } finally {
      setMenuLoading(false);
    }
  };

  // ── Create stall ──────────────────────────────────────────────────────────
  const handleAddOutlet = async () => {
    if (!outletForm.name.trim()) { setFormError('Stall name is required'); return; }
    setSubmitting(true); setFormError('');
    try {
      const res = await axios.post('/food', outletForm, {
        headers: { Authorization: `Bearer ${token}` },
      });
      const newOutlet = res.data;

      // Upload cover image if picked
      if (stallImageFile) {
        try {
          const fd = new FormData();
          fd.append('file', stallImageFile);
          const imgRes = await axios.post(`/food/${newOutlet.id}/image`, fd, {
            headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'multipart/form-data' },
          });
          newOutlet.image_url = imgRes.data.image_url;
        } catch { /* image upload failed silently */ }
      }

      setAddOutletOpen(false);
      setOutletForm({ name: '', type: 'food_court', description: '', location: '', contact_info: '', operating_hours: '', delivery_available: false });
      setStallImageFile(null); setStallImagePreview('');
      setOutlets((prev) => [...prev, newOutlet]);
      // Immediately open menu so owner can add items
      openMenu(newOutlet);
      setSnackMsg('Stall listed! Now add your menu items below.');
    } catch (err) {
      setFormError(err.response?.data?.detail || 'Failed to list stall');
    } finally {
      setSubmitting(false);
    }
  };

  // ── Add menu item ─────────────────────────────────────────────────────────
  const handleAddMenuItem = async () => {
    if (!menuForm.item_name.trim() || !menuForm.price) {
      setFormError('Item name and price are required'); return;
    }
    setSubmitting(true); setFormError('');
    try {
      const res = await axios.post(`/food/${selectedOutlet.id}/menu`, {
        ...menuForm, price: parseFloat(menuForm.price),
      }, { headers: { Authorization: `Bearer ${token}` } });

      let newItem = res.data;

      if (menuImageFile) {
        try {
          const fd = new FormData();
          fd.append('file', menuImageFile);
          const imgRes = await axios.post(
            `/food/${selectedOutlet.id}/menu/${newItem.id}/image`, fd,
            { headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'multipart/form-data' } }
          );
          newItem = imgRes.data;
        } catch { /* image upload failed silently */ }
      }

      setMenuItems((prev) => [...prev, newItem]);
      setAddMenuOpen(false);
      setMenuForm({ item_name: '', description: '', price: '', category: '', is_vegetarian: true, is_available: true });
      setMenuImageFile(null); setMenuImagePreview('');
      setSnackMsg('Item added!');
    } catch (err) {
      setFormError(err.response?.data?.detail || 'Failed to add item');
    } finally {
      setSubmitting(false);
    }
  };

  // ── Upload image for an existing menu item ────────────────────────────────
  const triggerExistingItemUpload = (itemId) => {
    setUploadingFor(itemId);
    existingItemImageRef.current.click();
  };

  const handleExistingItemImage = async (e) => {
    const file = e.target.files[0];
    if (!file || uploadingFor === null) return;
    const itemId = uploadingFor;
    e.target.value = '';
    try {
      const fd = new FormData();
      fd.append('file', file);
      const res = await axios.post(
        `/food/${selectedOutlet.id}/menu/${itemId}/image`, fd,
        { headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'multipart/form-data' } }
      );
      setMenuItems((prev) => prev.map((m) => m.id === itemId ? res.data : m));
      setSnackMsg('Photo uploaded!');
    } catch {
      setSnackMsg('Image upload failed');
    } finally {
      setUploadingFor(null);
    }
  };

  // ── Upload cover image for a stall card (from card button) ────────────────
  const stallCoverRef = useRef(null);
  const [coverUploadingFor, setCoverUploadingFor] = useState(null);

  const triggerCoverUpload = (outletId) => {
    setCoverUploadingFor(outletId);
    stallCoverRef.current.click();
  };

  const handleCoverUpload = async (e) => {
    const file = e.target.files[0];
    if (!file || !coverUploadingFor) return;
    const outletId = coverUploadingFor;
    e.target.value = '';
    try {
      const fd = new FormData();
      fd.append('file', file);
      const res = await axios.post(`/food/${outletId}/image`, fd, {
        headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'multipart/form-data' },
      });
      setOutlets((prev) => prev.map((o) => o.id === outletId ? { ...o, image_url: res.data.image_url } : o));
      setSnackMsg('Stall photo updated!');
    } catch {
      setSnackMsg('Cover upload failed');
    } finally {
      setCoverUploadingFor(null);
    }
  };

  const handleDeleteOutlet = async (outletId) => {
    if (!window.confirm('Delete this stall and all its menu items?')) return;
    try {
      await axios.delete(`/food/${outletId}`, { headers: { Authorization: `Bearer ${token}` } });
      setOutlets((prev) => prev.filter((o) => o.id !== outletId));
    } catch { alert('Failed to delete stall'); }
  };

  const handleDeleteMenuItem = async (itemId) => {
    try {
      await axios.delete(`/food/${selectedOutlet.id}/menu/${itemId}`, { headers: { Authorization: `Bearer ${token}` } });
      setMenuItems((prev) => prev.filter((m) => m.id !== itemId));
    } catch { alert('Failed to delete item'); }
  };

  // ── Filter / group helpers ────────────────────────────────────────────────
  const filteredOutlets = outlets.filter((o) => {
    const matchType = filterType === 'all' || o.type === filterType;
    const matchSearch = !searchText ||
      o.name.toLowerCase().includes(searchText.toLowerCase()) ||
      (o.location || '').toLowerCase().includes(searchText.toLowerCase());
    return matchType && matchSearch;
  });

  const menuCategories = ['all', ...new Set(menuItems.map((m) => m.category).filter(Boolean))];
  const filteredMenu = menuFilter === 'all' ? menuItems : menuItems.filter((m) => m.category === menuFilter);
  const groupedMenu = filteredMenu.reduce((acc, item) => {
    const cat = item.category || 'Other';
    if (!acc[cat]) acc[cat] = [];
    acc[cat].push(item);
    return acc;
  }, {});

  // ── Render ────────────────────────────────────────────────────────────────
  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      {/* Hidden file inputs */}
      <input ref={existingItemImageRef} type="file" accept="image/*" style={{ display: 'none' }} onChange={handleExistingItemImage} />
      <input ref={stallCoverRef} type="file" accept="image/*" style={{ display: 'none' }} onChange={handleCoverUpload} />

      {/* Header */}
      <Box sx={{ mb: 4, display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: 2 }}>
        <Box>
          <Typography variant="h4" fontWeight="bold" gutterBottom>🍽️ Campus Food</Typography>
          <Typography variant="body1" color="text.secondary">Discover eateries, cafes, and food stalls on campus</Typography>
        </Box>
        {isLoggedIn && (
          <Button variant="contained" startIcon={<Store />}
            onClick={() => { setFormError(''); setStallImageFile(null); setStallImagePreview(''); setAddOutletOpen(true); }}
            sx={{ borderRadius: 2, fontWeight: 'bold' }}>
            List My Stall
          </Button>
        )}
      </Box>

      {error && <Alert severity="error" sx={{ mb: 3 }}>{error}</Alert>}

      {/* Search + Filter */}
      <Box sx={{ display: 'flex', gap: 2, mb: 3, flexWrap: 'wrap', alignItems: 'center' }}>
        <TextField
          placeholder="Search by name or location..."
          value={searchText} onChange={(e) => setSearchText(e.target.value)}
          size="small" sx={{ flexGrow: 1, minWidth: 220 }}
          InputProps={{ startAdornment: <InputAdornment position="start"><Search fontSize="small" /></InputAdornment> }}
        />
        <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
          {OUTLET_TYPES.map((type) => (
            <Chip key={type}
              label={type === 'all' ? `All (${outlets.length})` : TYPE_LABELS[type]}
              onClick={() => setFilterType(type)}
              color={filterType === type ? 'primary' : 'default'}
              variant={filterType === type ? 'filled' : 'outlined'}
              size="small" icon={type !== 'all' ? TYPE_ICONS[type] : undefined} />
          ))}
        </Box>
      </Box>

      {/* Outlet grid */}
      {loading ? (
        <Box sx={{ display: 'flex', justifyContent: 'center', py: 8 }}><CircularProgress /></Box>
      ) : filteredOutlets.length === 0 ? (
        <Box sx={{ textAlign: 'center', py: 8 }}>
          <Restaurant sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
          <Typography variant="h6" color="text.secondary">
            {outlets.length === 0 ? 'No food stalls yet — be the first to list yours!' : 'No stalls match your search'}
          </Typography>
          {isLoggedIn && <Button variant="contained" sx={{ mt: 2 }} onClick={() => setAddOutletOpen(true)} startIcon={<Add />}>List My Stall</Button>}
        </Box>
      ) : (
        <Grid container spacing={3}>
          {filteredOutlets.map((outlet) => (
            <Grid item xs={12} sm={6} md={4} key={outlet.id}>
              <Card elevation={2} sx={{
                height: '100%', display: 'flex', flexDirection: 'column', borderRadius: 3,
                transition: 'transform 0.2s, box-shadow 0.2s',
                '&:hover': { transform: 'translateY(-4px)', boxShadow: 6 },
                outline: isOutletMine(outlet) ? '2px solid' : 'none',
                outlineColor: 'primary.main',
              }}>
                {/* Cover image */}
                {outlet.image_url ? (
                  <Box sx={{ position: 'relative' }}>
                    <CardMedia component="img" height="160" image={outlet.image_url} alt={outlet.name}
                      sx={{ objectFit: 'cover' }} />
                    {canManage(outlet) && (
                      <Tooltip title="Change cover photo">
                        <IconButton size="small"
                          sx={{ position: 'absolute', bottom: 8, right: 8, bgcolor: 'rgba(0,0,0,0.55)', color: 'white', '&:hover': { bgcolor: 'rgba(0,0,0,0.75)' } }}
                          onClick={() => triggerCoverUpload(outlet.id)}>
                          {coverUploadingFor === outlet.id ? <CircularProgress size={16} sx={{ color: 'white' }} /> : <AddAPhoto fontSize="small" />}
                        </IconButton>
                      </Tooltip>
                    )}
                  </Box>
                ) : (
                  <Box sx={{ position: 'relative', height: 8, bgcolor: `${TYPE_COLORS[outlet.type] || 'primary'}.main` }}>
                    {canManage(outlet) && (
                      <Tooltip title="Add cover photo">
                        <Button size="small" startIcon={<AddAPhoto />} variant="text"
                          sx={{ position: 'absolute', right: 4, top: 4, fontSize: '0.7rem', color: 'text.secondary', bgcolor: 'background.paper', boxShadow: 1, borderRadius: 2, px: 1, minHeight: 28 }}
                          onClick={() => triggerCoverUpload(outlet.id)}>
                          {coverUploadingFor === outlet.id ? 'Uploading…' : 'Add Photo'}
                        </Button>
                      </Tooltip>
                    )}
                  </Box>
                )}

                <CardContent sx={{ flexGrow: 1, p: 2.5 }}>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 1 }}>
                    <Box sx={{ flexGrow: 1, mr: 1 }}>
                      <Typography variant="h6" fontWeight="bold" sx={{ lineHeight: 1.3 }}>{outlet.name}</Typography>
                      {isOutletMine(outlet) && (
                        <Chip label="Your Stall" size="small" color="primary" variant="outlined" sx={{ mt: 0.5, height: 20, fontSize: '0.65rem' }} />
                      )}
                    </Box>
                    <Chip label={TYPE_LABELS[outlet.type] || outlet.type}
                      color={TYPE_COLORS[outlet.type] || 'default'} size="small"
                      icon={TYPE_ICONS[outlet.type]} />
                  </Box>

                  {outlet.description && (
                    <Typography variant="body2" color="text.secondary" sx={{ mb: 1.5, lineHeight: 1.5 }}>
                      {outlet.description}
                    </Typography>
                  )}

                  <Box sx={{ display: 'flex', flexDirection: 'column', gap: 0.8 }}>
                    {outlet.location && <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.8 }}>
                      <LocationOn fontSize="small" color="action" />
                      <Typography variant="body2" color="text.secondary">{outlet.location}</Typography>
                    </Box>}
                    {outlet.contact_info && <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.8 }}>
                      <Phone fontSize="small" color="action" />
                      <Typography variant="body2" color="text.secondary">{outlet.contact_info}</Typography>
                    </Box>}
                    {outlet.operating_hours && <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.8 }}>
                      <AccessTime fontSize="small" color="action" />
                      <Typography variant="body2" color="text.secondary">{outlet.operating_hours}</Typography>
                    </Box>}
                    {outlet.owner_name && <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.8 }}>
                      <Person fontSize="small" color="action" />
                      <Typography variant="body2" color="text.secondary">Listed by {outlet.owner_name}</Typography>
                    </Box>}
                  </Box>

                  {outlet.delivery_available && (
                    <Chip icon={<DeliveryDining />} label="Delivery Available" color="success" size="small" variant="outlined" sx={{ mt: 1.5 }} />
                  )}
                </CardContent>

                <CardActions sx={{ px: 2.5, pb: 2, gap: 1 }}>
                  <Button variant="contained" size="small" startIcon={<MenuBook />}
                    onClick={() => openMenu(outlet)} sx={{ borderRadius: 2, flexGrow: 1 }}>
                    View Menu
                  </Button>
                  {canManage(outlet) && (
                    <Tooltip title="Delete stall">
                      <IconButton size="small" color="error" onClick={() => handleDeleteOutlet(outlet.id)}>
                        <Delete fontSize="small" />
                      </IconButton>
                    </Tooltip>
                  )}
                </CardActions>
              </Card>
            </Grid>
          ))}
        </Grid>
      )}

      {isAdmin && (
        <Fab color="primary" sx={{ position: 'fixed', bottom: 32, right: 32 }}
          onClick={() => { setFormError(''); setStallImageFile(null); setStallImagePreview(''); setAddOutletOpen(true); }}>
          <Add />
        </Fab>
      )}

      {/* ─── Menu Dialog ─── */}
      <Dialog open={menuDialogOpen} onClose={() => setMenuDialogOpen(false)} maxWidth="md" fullWidth>
        <DialogTitle sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', pb: 1 }}>
          <Box>
            <Typography variant="h6" fontWeight="bold">{selectedOutlet?.name}</Typography>
            <Typography variant="body2" color="text.secondary">Menu</Typography>
          </Box>
          <Box sx={{ display: 'flex', gap: 1 }}>
            {selectedOutlet && canManage(selectedOutlet) && (
              <Button size="small" variant="contained" startIcon={<Add />}
                onClick={() => { setFormError(''); setMenuImageFile(null); setMenuImagePreview(''); setAddMenuOpen(true); }}>
                Add Item
              </Button>
            )}
            <IconButton onClick={() => setMenuDialogOpen(false)}><Close /></IconButton>
          </Box>
        </DialogTitle>

        {menuCategories.length > 2 && (
          <Box sx={{ px: 3, pb: 1 }}>
            <Tabs value={menuFilter} onChange={(_, v) => setMenuFilter(v)} variant="scrollable" scrollButtons="auto"
              sx={{ borderBottom: 1, borderColor: 'divider' }}>
              {menuCategories.map((cat) => (
                <Tab key={cat} label={cat === 'all' ? 'All Items' : cat} value={cat} />
              ))}
            </Tabs>
          </Box>
        )}

        <DialogContent sx={{ pt: 2, minHeight: 200 }}>
          {menuLoading ? (
            <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}><CircularProgress /></Box>
          ) : menuItems.length === 0 ? (
            <Box sx={{ textAlign: 'center', py: 6 }}>
              <Restaurant sx={{ fontSize: 48, color: 'text.secondary', mb: 1.5 }} />
              <Typography color="text.secondary" gutterBottom>No items in the menu yet.</Typography>
              {selectedOutlet && canManage(selectedOutlet) && (
                <Button variant="contained" sx={{ mt: 1 }} startIcon={<Add />}
                  onClick={() => { setFormError(''); setMenuImageFile(null); setMenuImagePreview(''); setAddMenuOpen(true); }}>
                  Add First Item
                </Button>
              )}
            </Box>
          ) : (
            Object.entries(groupedMenu).map(([category, items]) => (
              <Box key={category} sx={{ mb: 3 }}>
                {menuFilter === 'all' && (
                  <>
                    <Typography variant="subtitle1" fontWeight="bold" color="primary" sx={{ mb: 1 }}>{category}</Typography>
                    <Divider sx={{ mb: 1.5 }} />
                  </>
                )}
                <Grid container spacing={2}>
                  {items.map((item) => (
                    <Grid item xs={12} sm={6} key={item.id}>
                      <Card variant="outlined" sx={{ borderRadius: 2, overflow: 'hidden', display: 'flex', flexDirection: 'column' }}>
                        {/* Product image */}
                        {item.image_url ? (
                          <Box sx={{ position: 'relative' }}>
                            <CardMedia component="img" height="160" image={item.image_url} alt={item.item_name} sx={{ objectFit: 'cover' }} />
                            {selectedOutlet && canManage(selectedOutlet) && (
                              <Tooltip title="Change photo">
                                <IconButton size="small"
                                  sx={{ position: 'absolute', bottom: 6, right: 6, bgcolor: 'rgba(0,0,0,0.55)', color: 'white', '&:hover': { bgcolor: 'rgba(0,0,0,0.75)' } }}
                                  onClick={() => triggerExistingItemUpload(item.id)}>
                                  {uploadingFor === item.id ? <CircularProgress size={16} sx={{ color: 'white' }} /> : <AddAPhoto fontSize="small" />}
                                </IconButton>
                              </Tooltip>
                            )}
                          </Box>
                        ) : selectedOutlet && canManage(selectedOutlet) ? (
                          <Box
                            onClick={() => triggerExistingItemUpload(item.id)}
                            sx={{
                              height: 110, bgcolor: 'action.hover', display: 'flex',
                              alignItems: 'center', justifyContent: 'center',
                              flexDirection: 'column', gap: 0.5, cursor: 'pointer',
                              '&:hover': { bgcolor: 'action.selected' },
                            }}>
                            {uploadingFor === item.id
                              ? <CircularProgress size={24} />
                              : <><CloudUpload color="action" /><Typography variant="caption" color="text.secondary">Add Photo</Typography></>}
                          </Box>
                        ) : null}

                        <CardContent sx={{ p: 1.5 }}>
                          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                            <Box sx={{ flexGrow: 1, mr: 1 }}>
                              <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5, mb: 0.3 }}>
                                {item.is_vegetarian && <Spa fontSize="small" sx={{ color: 'green', fontSize: 14 }} />}
                                <Typography variant="body2" fontWeight="bold">{item.item_name}</Typography>
                              </Box>
                              {item.description && (
                                <Typography variant="caption" color="text.secondary" sx={{ lineHeight: 1.3, display: 'block' }}>
                                  {item.description}
                                </Typography>
                              )}
                            </Box>
                            <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5, flexShrink: 0 }}>
                              <Typography variant="body2" fontWeight="bold" color="primary">
                                ₹{parseFloat(item.price).toFixed(2)}
                              </Typography>
                              {selectedOutlet && canManage(selectedOutlet) && (
                                <IconButton size="small" color="error" onClick={() => handleDeleteMenuItem(item.id)} sx={{ p: 0.3 }}>
                                  <Delete sx={{ fontSize: 16 }} />
                                </IconButton>
                              )}
                            </Box>
                          </Box>
                        </CardContent>
                      </Card>
                    </Grid>
                  ))}
                </Grid>
              </Box>
            ))
          )}
        </DialogContent>
      </Dialog>

      {/* ─── List My Stall Dialog ─── */}
      <Dialog open={addOutletOpen} onClose={() => setAddOutletOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>
          <Typography variant="h6" fontWeight="bold">List Your Food Stall</Typography>
          <Typography variant="body2" color="text.secondary">After listing, you can add your menu items straight away</Typography>
        </DialogTitle>
        <DialogContent sx={{ pt: 1 }}>
          {formError && <Alert severity="error" sx={{ mb: 2 }}>{formError}</Alert>}

          {/* Cover image picker */}
          <Box
            onClick={() => stallImageRef.current.click()}
            sx={{
              mb: 2, mt: 1, height: 150, borderRadius: 2, border: '2px dashed', borderColor: 'divider',
              display: 'flex', alignItems: 'center', justifyContent: 'center', cursor: 'pointer',
              overflow: 'hidden', bgcolor: 'action.hover', position: 'relative',
              '&:hover': { borderColor: 'primary.main', bgcolor: 'action.selected' },
            }}>
            {stallImagePreview ? (
              <>
                <Box component="img" src={stallImagePreview} alt="preview"
                  sx={{ width: '100%', height: '100%', objectFit: 'cover', position: 'absolute' }} />
                <Box sx={{ position: 'absolute', bgcolor: 'rgba(0,0,0,0.45)', inset: 0, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                  <Typography variant="body2" sx={{ color: 'white' }}>Click to change</Typography>
                </Box>
              </>
            ) : (
              <Box sx={{ textAlign: 'center' }}>
                <AddAPhoto sx={{ fontSize: 36, color: 'text.secondary', mb: 0.5 }} />
                <Typography variant="body2" color="text.secondary">Add a cover photo for your stall</Typography>
                <Typography variant="caption" color="text.disabled">(optional)</Typography>
              </Box>
            )}
          </Box>
          <input ref={stallImageRef} type="file" accept="image/*" style={{ display: 'none' }}
            onChange={(e) => {
              const f = e.target.files[0];
              if (f) { setStallImageFile(f); setStallImagePreview(URL.createObjectURL(f)); }
            }} />

          <TextField fullWidth label="Stall / Outlet Name *" value={outletForm.name}
            onChange={(e) => setOutletForm({ ...outletForm, name: e.target.value })} sx={{ mb: 2 }} />
          <FormControl fullWidth sx={{ mb: 2 }}>
            <InputLabel>Type *</InputLabel>
            <Select value={outletForm.type} label="Type *"
              onChange={(e) => setOutletForm({ ...outletForm, type: e.target.value })}>
              <MenuItem value="canteen">Canteen</MenuItem>
              <MenuItem value="cafe">Café</MenuItem>
              <MenuItem value="restaurant">Restaurant</MenuItem>
              <MenuItem value="food_court">Food Court / Stall</MenuItem>
            </Select>
          </FormControl>
          <TextField fullWidth label="Description" multiline rows={2} value={outletForm.description}
            onChange={(e) => setOutletForm({ ...outletForm, description: e.target.value })} sx={{ mb: 2 }} />
          <TextField fullWidth label="Location on Campus" value={outletForm.location}
            onChange={(e) => setOutletForm({ ...outletForm, location: e.target.value })}
            placeholder="e.g. Near Gate 3, Block B Ground Floor" sx={{ mb: 2 }}
            InputProps={{ startAdornment: <InputAdornment position="start"><LocationOn fontSize="small" /></InputAdornment> }} />
          <TextField fullWidth label="Contact / WhatsApp" value={outletForm.contact_info}
            onChange={(e) => setOutletForm({ ...outletForm, contact_info: e.target.value })} sx={{ mb: 2 }}
            InputProps={{ startAdornment: <InputAdornment position="start"><Phone fontSize="small" /></InputAdornment> }} />
          <TextField fullWidth label="Operating Hours (e.g. 8am – 6pm)" value={outletForm.operating_hours}
            onChange={(e) => setOutletForm({ ...outletForm, operating_hours: e.target.value })} sx={{ mb: 2 }}
            InputProps={{ startAdornment: <InputAdornment position="start"><AccessTime fontSize="small" /></InputAdornment> }} />
          <FormControlLabel
            control={<Switch checked={outletForm.delivery_available}
              onChange={(e) => setOutletForm({ ...outletForm, delivery_available: e.target.checked })} />}
            label="I offer delivery / takeaway" />
        </DialogContent>
        <DialogActions sx={{ px: 3, pb: 2 }}>
          <Button onClick={() => setAddOutletOpen(false)}>Cancel</Button>
          <Button variant="contained" onClick={handleAddOutlet} disabled={submitting} startIcon={<Store />}>
            {submitting ? 'Listing…' : 'List Stall & Add Menu →'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* ─── Add Menu Item Dialog ─── */}
      <Dialog open={addMenuOpen} onClose={() => setAddMenuOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>
          <Typography variant="h6" fontWeight="bold">Add Menu Item</Typography>
          <Typography variant="body2" color="text.secondary">{selectedOutlet?.name}</Typography>
        </DialogTitle>
        <DialogContent sx={{ pt: 1 }}>
          {formError && <Alert severity="error" sx={{ mb: 2 }}>{formError}</Alert>}

          {/* Product image picker */}
          <Box
            onClick={() => menuImageRef.current.click()}
            sx={{
              mb: 2, mt: 1, height: 130, borderRadius: 2, border: '2px dashed', borderColor: 'divider',
              display: 'flex', alignItems: 'center', justifyContent: 'center', cursor: 'pointer',
              overflow: 'hidden', bgcolor: 'action.hover', position: 'relative',
              '&:hover': { borderColor: 'primary.main', bgcolor: 'action.selected' },
            }}>
            {menuImagePreview ? (
              <>
                <Box component="img" src={menuImagePreview} alt="preview"
                  sx={{ width: '100%', height: '100%', objectFit: 'cover', position: 'absolute' }} />
                <Box sx={{ position: 'absolute', bgcolor: 'rgba(0,0,0,0.4)', inset: 0, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                  <Typography variant="body2" sx={{ color: 'white' }}>Click to change</Typography>
                </Box>
              </>
            ) : (
              <Box sx={{ textAlign: 'center' }}>
                <CloudUpload sx={{ fontSize: 32, color: 'text.secondary', mb: 0.5 }} />
                <Typography variant="body2" color="text.secondary">Upload a product photo</Typography>
                <Typography variant="caption" color="text.disabled">(optional)</Typography>
              </Box>
            )}
          </Box>
          <input ref={menuImageRef} type="file" accept="image/*" style={{ display: 'none' }}
            onChange={(e) => {
              const f = e.target.files[0];
              if (f) { setMenuImageFile(f); setMenuImagePreview(URL.createObjectURL(f)); }
            }} />

          <TextField fullWidth label="Item Name *" value={menuForm.item_name}
            onChange={(e) => setMenuForm({ ...menuForm, item_name: e.target.value })} sx={{ mb: 2 }} />
          <TextField fullWidth label="Description" value={menuForm.description}
            onChange={(e) => setMenuForm({ ...menuForm, description: e.target.value })} sx={{ mb: 2 }} />
          <Grid container spacing={2} sx={{ mb: 2 }}>
            <Grid item xs={6}>
              <TextField fullWidth label="Price (₹) *" type="number" value={menuForm.price}
                onChange={(e) => setMenuForm({ ...menuForm, price: e.target.value })}
                InputProps={{ startAdornment: <InputAdornment position="start"><AttachMoney fontSize="small" /></InputAdornment> }} />
            </Grid>
            <Grid item xs={6}>
              <TextField fullWidth label="Category" value={menuForm.category}
                onChange={(e) => setMenuForm({ ...menuForm, category: e.target.value })}
                placeholder="e.g. Mains, Drinks" />
            </Grid>
          </Grid>
          <Box sx={{ display: 'flex', gap: 2 }}>
            <FormControlLabel
              control={<Switch checked={menuForm.is_vegetarian}
                onChange={(e) => setMenuForm({ ...menuForm, is_vegetarian: e.target.checked })} />}
              label="Vegetarian" />
            <FormControlLabel
              control={<Switch checked={menuForm.is_available}
                onChange={(e) => setMenuForm({ ...menuForm, is_available: e.target.checked })} />}
              label="Available now" />
          </Box>
        </DialogContent>
        <DialogActions sx={{ px: 3, pb: 2 }}>
          <Button onClick={() => setAddMenuOpen(false)}>Cancel</Button>
          <Button variant="contained" onClick={handleAddMenuItem} disabled={submitting}>
            {submitting ? 'Adding…' : 'Add to Menu'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Snackbar feedback */}
      <Snackbar open={!!snackMsg} autoHideDuration={3000} onClose={() => setSnackMsg('')}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
        message={snackMsg} />
    </Container>
  );
};

export default Food;
