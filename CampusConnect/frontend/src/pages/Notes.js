import React, { useState, useEffect, useRef } from 'react';
import {
  Container, Typography, Box, Grid, Card, CardContent, CardActions,
  Button, Chip, Dialog, DialogTitle, DialogContent, DialogActions,
  TextField, FormControl, InputLabel, Select, MenuItem,
  Alert, CircularProgress, IconButton, InputAdornment, LinearProgress,
  Snackbar, Divider, Avatar, Tooltip, Fab, Paper,
} from '@mui/material';
import {
  MenuBook, PictureAsPdf, CloudUpload, Add, Close, Search, Delete,
  ThumbUp, Download, Visibility, School, PostAdd, Person, CalendarToday,
  Label,
} from '@mui/icons-material';
import axios from 'axios';
import { useSelector } from 'react-redux';
import { useNavigate } from 'react-router-dom';

const BRANCHES = ['All Branches', 'CSE', 'ECE', 'Mechanical', 'Civil', 'Chemical', 'Electrical', 'IT', 'Other'];
const SEMESTERS = [1, 2, 3, 4, 5, 6, 7, 8];

const getInitials = (name = '') => name.split(' ').map((w) => w[0]).join('').toUpperCase().slice(0, 2);
const fmt = (d) => d ? new Date(d).toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' }) : '';

const Notes = () => {
  const { user, token } = useSelector((s) => s.auth);
  const navigate = useNavigate();
  const isLoggedIn = !!user;
  const isAdmin = user?.role === 'admin';

  const [notes, setNotes] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [snack, setSnack] = useState('');
  const [search, setSearch] = useState('');
  const [filterBranch, setFilterBranch] = useState('all');
  const [filterSem, setFilterSem] = useState('all');
  const [detailNote, setDetailNote] = useState(null);
  const [postOpen, setPostOpen] = useState(false);
  const [form, setForm] = useState({ title: '', subject: '', description: '', file_type: 'pdf', semester: '', branch: '', tags: '' });
  const [formError, setFormError] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [uploadingFor, setUploadingFor] = useState(null);
  const [uploading, setUploading] = useState(false);
  const fileRef = useRef(null);

  const fetchNotes = async () => {
    try { setLoading(true); const res = await axios.get('/notes'); setNotes(res.data); }
    catch { setError('Failed to load notes'); } finally { setLoading(false); }
  };

  useEffect(() => { fetchNotes(); }, []);

  const isMine = (n) => n.uploaded_by === user?.id;
  const canManage = (n) => isAdmin || isMine(n);

  const handlePost = async () => {
    if (!form.title.trim() || !form.subject.trim()) { setFormError('Title and subject are required'); return; }
    setSubmitting(true); setFormError('');
    try {
      const tags = form.tags ? form.tags.split(',').map((t) => t.trim()).filter(Boolean) : [];
      const res = await axios.post('/notes', { ...form, semester: form.semester ? parseInt(form.semester) : null, tags },
        { headers: { Authorization: `Bearer ${token}` } });
      setNotes((prev) => [res.data, ...prev]);
      setPostOpen(false);
      setForm({ title: '', subject: '', description: '', file_type: 'pdf', semester: '', branch: '', tags: '' });
      setUploadingFor(res.data.id);
      fileRef.current.click();
    } catch (err) { setFormError(err.response?.data?.detail || 'Failed to post'); }
    finally { setSubmitting(false); }
  };

  const handleFileSelected = async (e) => {
    const file = e.target.files?.[0];
    if (!file || !uploadingFor) return;
    e.target.value = '';
    setUploading(true);
    try {
      const fd = new FormData();
      fd.append('file', file);
      const res = await axios.post(`/notes/${uploadingFor}/file`, fd, {
        headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'multipart/form-data' },
      });
      setNotes((prev) => prev.map((n) => n.id === uploadingFor ? { ...n, ...res.data } : n));
      setSnack('Note uploaded! 🎉');
    } catch { setSnack('Failed to upload file'); }
    finally { setUploading(false); setUploadingFor(null); }
  };

  const handleUpvote = async (noteId) => {
    if (!isLoggedIn) { navigate('/login'); return; }
    try {
      const res = await axios.post(`/notes/${noteId}/upvote`, {}, { headers: { Authorization: `Bearer ${token}` } });
      setNotes((prev) => prev.map((n) => n.id === noteId ? { ...n, upvotes: res.data.upvotes } : n));
      if (detailNote?.id === noteId) setDetailNote((prev) => ({ ...prev, upvotes: res.data.upvotes }));
    } catch {}
  };

  const handleDownload = async (note) => {
    if (!note.file_url) { setSnack('No file uploaded for this note yet'); return; }
    await axios.post(`/notes/${note.id}/view`).catch(() => {});
    window.open(note.file_url, '_blank');
    setNotes((prev) => prev.map((n) => n.id === note.id ? { ...n, download_count: (n.download_count || 0) + 1 } : n));
  };

  const handleDelete = async (id) => {
    if (!window.confirm('Delete this note?')) return;
    try {
      await axios.delete(`/notes/${id}`, { headers: { Authorization: `Bearer ${token}` } });
      setNotes((prev) => prev.filter((n) => n.id !== id));
      if (detailNote?.id === id) setDetailNote(null);
      setSnack('Note deleted');
    } catch { setSnack('Failed'); }
  };

  const filtered = notes.filter((n) => {
    if (filterBranch !== 'all' && n.branch !== filterBranch) return false;
    if (filterSem !== 'all' && String(n.semester) !== String(filterSem)) return false;
    if (search) { const q = search.toLowerCase(); if (!n.title.toLowerCase().includes(q) && !n.subject.toLowerCase().includes(q) && !(n.description || '').toLowerCase().includes(q) && !(n.tags || []).some((t) => t.toLowerCase().includes(q))) return false; }
    return true;
  });

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      <input ref={fileRef} type="file" accept=".pdf,.doc,.docx,.ppt,.pptx,.zip,.png,.jpg" style={{ display: 'none' }} onChange={handleFileSelected} />
      {uploading && <Box sx={{ position: 'fixed', top: 64, left: 0, right: 0, zIndex: 9999 }}><LinearProgress /><Typography variant="caption" sx={{ display: 'block', textAlign: 'center', bgcolor: 'background.paper', py: 0.3 }}>Uploading file…</Typography></Box>}

      {!isLoggedIn ? (
        <Paper elevation={0} sx={{ mb: 4, p: 4, borderRadius: 3, textAlign: 'center', background: 'linear-gradient(135deg, #1a237e 0%, #3949ab 100%)', color: 'white' }}>
          <Typography variant="h4" fontWeight="bold" gutterBottom>📚 Notes & Study Material</Typography>
          <Typography variant="body1" sx={{ mb: 3, opacity: 0.9 }}>Download notes, PYQs, cheatsheets, and study guides. Share your own notes with the campus.</Typography>
          <Box sx={{ display: 'flex', gap: 2, justifyContent: 'center', flexWrap: 'wrap' }}>
            <Button variant="contained" size="large" sx={{ bgcolor: 'white', color: '#1a237e', fontWeight: 'bold' }} onClick={() => navigate('/login')}>Log In to Download</Button>
            <Button variant="outlined" size="large" sx={{ borderColor: 'white', color: 'white', fontWeight: 'bold' }} onClick={() => navigate('/signup')}>Sign Up Free</Button>
          </Box>
        </Paper>
      ) : (
        <Box sx={{ mb: 3, display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 2 }}>
          <Box>
            <Typography variant="h4" fontWeight="bold">📚 Notes & Study Material</Typography>
            <Typography variant="body1" color="text.secondary">{notes.length} notes shared · Upload yours and help the campus</Typography>
          </Box>
          <Button variant="contained" size="large" startIcon={<PostAdd />} onClick={() => { setFormError(''); setPostOpen(true); }}
            sx={{ borderRadius: 2, fontWeight: 'bold', px: 3, bgcolor: '#1a237e', '&:hover': { bgcolor: '#283593' } }}>
            + Upload Notes
          </Button>
        </Box>
      )}

      {error && <Alert severity="error" sx={{ mb: 3 }}>{error}</Alert>}

      {/* Filters */}
      <Box sx={{ mb: 3, display: 'flex', gap: 2, flexWrap: 'wrap', alignItems: 'center' }}>
        <TextField placeholder="Search by title, subject, tags…" value={search} onChange={(e) => setSearch(e.target.value)} size="small" sx={{ flexGrow: 1, minWidth: 220 }}
          InputProps={{ startAdornment: <InputAdornment position="start"><Search fontSize="small" /></InputAdornment> }} />
        <FormControl size="small" sx={{ minWidth: 130 }}>
          <InputLabel>Branch</InputLabel>
          <Select value={filterBranch} label="Branch" onChange={(e) => setFilterBranch(e.target.value)}>
            <MenuItem value="all">All Branches</MenuItem>
            {BRANCHES.filter((b) => b !== 'All Branches').map((b) => <MenuItem key={b} value={b}>{b}</MenuItem>)}
          </Select>
        </FormControl>
        <FormControl size="small" sx={{ minWidth: 110 }}>
          <InputLabel>Semester</InputLabel>
          <Select value={filterSem} label="Semester" onChange={(e) => setFilterSem(e.target.value)}>
            <MenuItem value="all">All Sems</MenuItem>
            {SEMESTERS.map((s) => <MenuItem key={s} value={s}>Sem {s}</MenuItem>)}
          </Select>
        </FormControl>
        <Typography variant="body2" color="text.secondary"><b>{filtered.length}</b> notes</Typography>
      </Box>

      {loading ? <Box sx={{ display: 'flex', justifyContent: 'center', py: 10 }}><CircularProgress /></Box>
        : filtered.length === 0 ? (
          <Box sx={{ textAlign: 'center', py: 10 }}>
            <MenuBook sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
            <Typography variant="h6" color="text.secondary">No notes match your search</Typography>
            {isLoggedIn && <Button variant="contained" startIcon={<Add />} sx={{ mt: 2, bgcolor: '#1a237e' }} onClick={() => setPostOpen(true)}>Upload Notes</Button>}
          </Box>
        ) : (
          <Grid container spacing={3}>
            {filtered.map((note) => {
              const uploaderName = note.uploader_display || note.uploader_name || 'Campus Member';
              return (
                <Grid item xs={12} sm={6} md={4} key={note.id}>
                  <Card elevation={2} sx={{ height: '100%', display: 'flex', flexDirection: 'column', borderRadius: 3,
                    transition: 'transform 0.2s, box-shadow 0.2s', '&:hover': { transform: 'translateY(-4px)', boxShadow: 6 },
                    borderTop: '4px solid #1a237e' }}>
                    <CardContent sx={{ flexGrow: 1, p: 2.5 }}>
                      <Box sx={{ display: 'flex', gap: 1.5, mb: 1.5 }}>
                        <Box sx={{ width: 44, height: 44, borderRadius: 2, bgcolor: '#e8eaf6', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
                          <PictureAsPdf sx={{ color: '#c62828', fontSize: 28 }} />
                        </Box>
                        <Box>
                          <Typography variant="subtitle1" fontWeight="bold" sx={{ lineHeight: 1.3 }}>{note.title}</Typography>
                          <Typography variant="body2" color="primary" fontWeight="bold">{note.subject}</Typography>
                        </Box>
                      </Box>

                      <Box sx={{ display: 'flex', gap: 1, mb: 1, flexWrap: 'wrap' }}>
                        {note.branch && <Chip label={note.branch} size="small" icon={<School sx={{ fontSize: '12px !important' }} />} sx={{ height: 20, fontSize: '0.6rem', bgcolor: '#e8eaf6', color: '#1a237e' }} />}
                        {note.semester && <Chip label={`Sem ${note.semester}`} size="small" sx={{ height: 20, fontSize: '0.6rem', bgcolor: '#e8f5e9', color: '#2e7d32' }} />}
                      </Box>

                      {/* Uploader */}
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                        <Avatar sx={{ width: 20, height: 20, fontSize: '0.6rem', bgcolor: '#1a237e' }}>{getInitials(uploaderName)}</Avatar>
                        <Typography variant="caption" color="text.secondary">{uploaderName}</Typography>
                      </Box>

                      {note.description && (
                        <Typography variant="body2" color="text.secondary"
                          sx={{ mb: 1, display: '-webkit-box', WebkitLineClamp: 2, WebkitBoxOrient: 'vertical', overflow: 'hidden', lineHeight: 1.5 }}>
                          {note.description}
                        </Typography>
                      )}

                      {(note.tags || []).length > 0 && (
                        <Box sx={{ display: 'flex', gap: 0.5, flexWrap: 'wrap', mt: 0.5 }}>
                          {(note.tags || []).slice(0, 4).map((t) => <Chip key={t} label={t} size="small" icon={<Label sx={{ fontSize: '10px !important' }} />} sx={{ height: 18, fontSize: '0.58rem', bgcolor: '#f3e5f5', color: '#6a1b9a' }} />)}
                        </Box>
                      )}

                      <Box sx={{ display: 'flex', gap: 2, mt: 1.5 }}>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}><ThumbUp sx={{ fontSize: 14, color: 'text.secondary' }} /><Typography variant="caption" color="text.secondary">{note.upvotes || 0}</Typography></Box>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}><Download sx={{ fontSize: 14, color: 'text.secondary' }} /><Typography variant="caption" color="text.secondary">{note.download_count || 0} downloads</Typography></Box>
                      </Box>
                    </CardContent>

                    <CardActions sx={{ px: 2.5, pb: 2.5, gap: 1, flexWrap: 'wrap' }}>
                      <Button variant="contained" size="small" startIcon={<Download />} sx={{ borderRadius: 2, flexGrow: 1, bgcolor: '#1a237e', '&:hover': { bgcolor: '#283593' } }}
                        disabled={!note.file_url} onClick={() => handleDownload(note)}>
                        {note.file_url ? 'Download' : 'No File Yet'}
                      </Button>
                      <Button variant="outlined" size="small" startIcon={<ThumbUp />} sx={{ borderRadius: 2 }} onClick={() => handleUpvote(note.id)}>
                        {note.upvotes || 0}
                      </Button>
                      {canManage(note) && (
                        <>
                          {!note.file_url && <Tooltip title="Upload file"><IconButton size="small" color="primary" onClick={() => { setUploadingFor(note.id); fileRef.current.click(); }}><CloudUpload fontSize="small" /></IconButton></Tooltip>}
                          <Tooltip title="Delete note"><IconButton size="small" color="error" onClick={() => handleDelete(note.id)}><Delete fontSize="small" /></IconButton></Tooltip>
                        </>
                      )}
                    </CardActions>
                  </Card>
                </Grid>
              );
            })}
          </Grid>
        )}

      {isLoggedIn && <Fab sx={{ position: 'fixed', bottom: 32, right: 32, bgcolor: '#1a237e', color: 'white', '&:hover': { bgcolor: '#283593' } }} onClick={() => { setFormError(''); setPostOpen(true); }}><Add /></Fab>}

      {/* Detail dialog */}
      <Dialog open={!!detailNote} onClose={() => setDetailNote(null)} maxWidth="sm" fullWidth>
        {detailNote && (
          <>
            <DialogTitle sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', pb: 0 }}>
              <Box sx={{ flexGrow: 1, mr: 1 }}>
                <Typography variant="h6" fontWeight="bold">{detailNote.title}</Typography>
                <Typography variant="subtitle1" color="primary" fontWeight="bold">{detailNote.subject}</Typography>
                <Box sx={{ display: 'flex', gap: 1, mt: 0.5, flexWrap: 'wrap' }}>
                  {detailNote.branch && <Chip label={detailNote.branch} size="small" icon={<School sx={{ fontSize: '12px !important' }} />} sx={{ bgcolor: '#e8eaf6', color: '#1a237e' }} />}
                  {detailNote.semester && <Chip label={`Semester ${detailNote.semester}`} size="small" color="success" />}
                </Box>
              </Box>
              <IconButton onClick={() => setDetailNote(null)}><Close /></IconButton>
            </DialogTitle>
            <DialogContent sx={{ pt: 2 }}>
              <Box sx={{ display: 'flex', gap: 3, mb: 2.5, p: 2, borderRadius: 2, bgcolor: 'primary.50' }}>
                <Box sx={{ textAlign: 'center' }}><Typography variant="caption" color="text.secondary">Upvotes</Typography><Typography variant="h6" fontWeight="bold" color="primary">{detailNote.upvotes || 0}</Typography></Box>
                <Box sx={{ textAlign: 'center' }}><Typography variant="caption" color="text.secondary">Downloads</Typography><Typography variant="h6" fontWeight="bold">{detailNote.download_count || 0}</Typography></Box>
                <Box sx={{ textAlign: 'center' }}><Typography variant="caption" color="text.secondary">Uploaded</Typography><Typography variant="body2" fontWeight="bold">{fmt(detailNote.created_at)}</Typography></Box>
              </Box>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5, mb: 2, p: 1.5, borderRadius: 2, bgcolor: 'grey.50' }}>
                <Avatar sx={{ width: 40, height: 40, bgcolor: '#1a237e' }}>{getInitials(detailNote.uploader_display || detailNote.uploader_name || 'U')}</Avatar>
                <Box>
                  <Typography variant="body2" fontWeight="bold">{detailNote.uploader_display || detailNote.uploader_name || 'Campus Member'}</Typography>
                  <Typography variant="caption" color="text.secondary">Campus Verified Member</Typography>
                </Box>
              </Box>
              {detailNote.description && <Box sx={{ mb: 2 }}><Typography variant="subtitle2" fontWeight="bold" gutterBottom>About these notes</Typography><Typography variant="body2" color="text.secondary" sx={{ lineHeight: 1.7 }}>{detailNote.description}</Typography></Box>}
              {(detailNote.tags || []).length > 0 && (
                <Box sx={{ mb: 2 }}>
                  <Typography variant="subtitle2" fontWeight="bold" gutterBottom>Tags</Typography>
                  <Box sx={{ display: 'flex', gap: 0.8, flexWrap: 'wrap' }}>
                    {(detailNote.tags || []).map((t) => <Chip key={t} label={t} size="small" sx={{ bgcolor: '#f3e5f5', color: '#6a1b9a' }} />)}
                  </Box>
                </Box>
              )}
            </DialogContent>
            <DialogActions sx={{ px: 3, pb: 2, gap: 1 }}>
              <Button variant="contained" startIcon={<Download />} onClick={() => handleDownload(detailNote)} disabled={!detailNote.file_url}
                sx={{ borderRadius: 2, bgcolor: '#1a237e', '&:hover': { bgcolor: '#283593' } }}>
                {detailNote.file_url ? 'Download PDF' : 'No File Yet'}
              </Button>
              <Button variant="outlined" startIcon={<ThumbUp />} onClick={() => handleUpvote(detailNote.id)}>Upvote</Button>
              {canManage(detailNote) && <Button color="error" variant="outlined" startIcon={<Delete />} onClick={() => handleDelete(detailNote.id)}>Delete</Button>}
            </DialogActions>
          </>
        )}
      </Dialog>

      {/* Post dialog */}
      <Dialog open={postOpen} onClose={() => setPostOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>
          <Typography variant="h6" fontWeight="bold">Upload Study Material</Typography>
          <Typography variant="body2" color="text.secondary">You can attach the file after filling in the details</Typography>
        </DialogTitle>
        <DialogContent sx={{ pt: 1 }}>
          {formError && <Alert severity="error" sx={{ mb: 2 }}>{formError}</Alert>}
          <TextField fullWidth label="Title *" value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })} sx={{ mb: 2, mt: 1 }} placeholder="e.g. Data Structures Complete Notes" />
          <TextField fullWidth label="Subject *" value={form.subject} onChange={(e) => setForm({ ...form, subject: e.target.value })} sx={{ mb: 2 }} placeholder="e.g. Data Structures & Algorithms" />
          <Grid container spacing={2} sx={{ mb: 2 }}>
            <Grid item xs={6}>
              <FormControl fullWidth><InputLabel>Branch</InputLabel>
                <Select value={form.branch} label="Branch" onChange={(e) => setForm({ ...form, branch: e.target.value })}>
                  <MenuItem value="">Any Branch</MenuItem>
                  {BRANCHES.filter((b) => b !== 'All Branches').map((b) => <MenuItem key={b} value={b}>{b}</MenuItem>)}
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={6}>
              <FormControl fullWidth><InputLabel>Semester</InputLabel>
                <Select value={form.semester} label="Semester" onChange={(e) => setForm({ ...form, semester: e.target.value })}>
                  <MenuItem value="">Any Semester</MenuItem>
                  {SEMESTERS.map((s) => <MenuItem key={s} value={s}>Semester {s}</MenuItem>)}
                </Select>
              </FormControl>
            </Grid>
          </Grid>
          <TextField fullWidth label="Tags (comma separated)" value={form.tags} onChange={(e) => setForm({ ...form, tags: e.target.value })} sx={{ mb: 2 }} placeholder="DSA, Trees, Exam Prep, GATE" />
          <TextField fullWidth label="Description" multiline rows={3} value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} placeholder="What do these notes cover? Any special features?" />
        </DialogContent>
        <DialogActions sx={{ px: 3, pb: 2 }}>
          <Button onClick={() => setPostOpen(false)}>Cancel</Button>
          <Button variant="contained" onClick={handlePost} disabled={submitting} startIcon={<CloudUpload />} size="large" sx={{ bgcolor: '#1a237e', '&:hover': { bgcolor: '#283593' } }}>
            {submitting ? 'Saving…' : 'Save & Upload File →'}
          </Button>
        </DialogActions>
      </Dialog>

      <Snackbar open={!!snack} autoHideDuration={3000} onClose={() => setSnack('')} anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }} message={snack} />
    </Container>
  );
};

export default Notes;
