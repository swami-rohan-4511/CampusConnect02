import React, { useState, useEffect } from 'react';
import {
  Container, Typography, Box, Grid, Card, CardContent, CardActions,
  Button, Chip, Dialog, DialogTitle, DialogContent, DialogActions,
  TextField, FormControl, InputLabel, Select, MenuItem,
  Alert, CircularProgress, IconButton, InputAdornment,
  Snackbar, Divider, Paper, Tooltip, Fab,
} from '@mui/material';
import {
  Work, Laptop, Schedule, AttachMoney, LocationOn, Email,
  Add, Close, Search, Delete, PostAdd, OpenInNew,
  School, Business, AlarmOn, CheckCircle,
} from '@mui/icons-material';
import axios from 'axios';
import { useSelector } from 'react-redux';
import { useNavigate } from 'react-router-dom';

const JOB_TYPES = [
  { id: 'internship',  label: 'Internship',   color: '#1565c0', bg: '#e3f2fd' },
  { id: 'full-time',   label: 'Full-Time',    color: '#2e7d32', bg: '#e8f5e9' },
  { id: 'part-time',   label: 'Part-Time',    color: '#e65100', bg: '#fff3e0' },
  { id: 'freelance',   label: 'Freelance',    color: '#6a1b9a', bg: '#f3e5f5' },
  { id: 'research',    label: 'Research',     color: '#00838f', bg: '#e0f7fa' },
];
const TYPE_MAP = Object.fromEntries(JOB_TYPES.map((t) => [t.id, t]));

const EXP_COLORS = { entry: 'success', junior: 'primary', mid: 'warning', senior: 'error' };
const EXP_LABELS = { entry: 'Entry Level', junior: 'Junior (1-2yr)', mid: 'Mid (2-5yr)', senior: 'Senior (5yr+)' };

const daysLeft = (deadline) => {
  if (!deadline) return null;
  const diff = new Date(deadline).setHours(23, 59, 59) - Date.now();
  const days = Math.ceil(diff / 86400000);
  if (days < 0) return { label: 'Deadline passed', urgent: true };
  if (days === 0) return { label: 'Due today!', urgent: true };
  if (days <= 3) return { label: `${days} day${days > 1 ? 's' : ''} left!`, urgent: true };
  return { label: `${days} days left`, urgent: false };
};

const Jobs = () => {
  const { user, token } = useSelector((s) => s.auth);
  const navigate = useNavigate();
  const isLoggedIn = !!user;
  const isAdmin = user?.role === 'admin';

  const [jobs, setJobs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [snack, setSnack] = useState('');
  const [search, setSearch] = useState('');
  const [activeType, setActiveType] = useState('all');
  const [activeExp, setActiveExp] = useState('all');
  const [detailJob, setDetailJob] = useState(null);
  const [postOpen, setPostOpen] = useState(false);
  const [form, setForm] = useState({ title: '', company_name: '', description: '', requirements: '', job_type: 'internship', location: '', salary_range: '', application_deadline: '', contact_email: '', apply_link: '', experience_level: 'entry', skills_required: '' });
  const [formError, setFormError] = useState('');
  const [submitting, setSubmitting] = useState(false);

  const fetchJobs = async () => {
    try { setLoading(true); const res = await axios.get('/jobs'); setJobs(res.data); }
    catch { setError('Failed to load jobs'); } finally { setLoading(false); }
  };

  useEffect(() => { fetchJobs(); }, []);

  const isMine = (j) => j.posted_by === user?.id;
  const canManage = (j) => isAdmin || isMine(j);

  const handlePost = async () => {
    if (!form.title.trim() || !form.company_name.trim()) { setFormError('Title and company name are required'); return; }
    setSubmitting(true); setFormError('');
    try {
      const res = await axios.post('/jobs', form, { headers: { Authorization: `Bearer ${token}` } });
      setJobs((prev) => [res.data, ...prev]);
      setPostOpen(false);
      setForm({ title: '', company_name: '', description: '', requirements: '', job_type: 'internship', location: '', salary_range: '', application_deadline: '', contact_email: '', apply_link: '', experience_level: 'entry', skills_required: '' });
      setSnack('Job posted!');
    } catch (err) { setFormError(err.response?.data?.detail || 'Failed to post'); }
    finally { setSubmitting(false); }
  };

  const handleDelete = async (id) => {
    if (!window.confirm('Close this job posting?')) return;
    try {
      await axios.delete(`/jobs/${id}`, { headers: { Authorization: `Bearer ${token}` } });
      setJobs((prev) => prev.filter((j) => j.id !== id));
      if (detailJob?.id === id) setDetailJob(null);
      setSnack('Job posting closed');
    } catch { setSnack('Failed'); }
  };

  const filtered = jobs.filter((j) => {
    if (activeType !== 'all' && j.job_type !== activeType) return false;
    if (activeExp !== 'all' && j.experience_level !== activeExp) return false;
    if (search) { const q = search.toLowerCase(); if (!j.title.toLowerCase().includes(q) && !j.company_name.toLowerCase().includes(q) && !(j.description || '').toLowerCase().includes(q) && !(j.skills_required || '').toLowerCase().includes(q)) return false; }
    return true;
  });
  const typeCounts = jobs.reduce((acc, j) => { acc[j.job_type] = (acc[j.job_type] || 0) + 1; return acc; }, {});

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      {!isLoggedIn ? (
        <Paper elevation={0} sx={{ mb: 4, p: 4, borderRadius: 3, textAlign: 'center', background: 'linear-gradient(135deg, #0d47a1 0%, #1976d2 100%)', color: 'white' }}>
          <Typography variant="h4" fontWeight="bold" gutterBottom>💼 Jobs & Internships</Typography>
          <Typography variant="body1" sx={{ mb: 3, opacity: 0.9 }}>Find campus jobs, internships, research positions, and part-time opportunities. All posted by verified members.</Typography>
          <Box sx={{ display: 'flex', gap: 2, justifyContent: 'center', flexWrap: 'wrap' }}>
            <Button variant="contained" size="large" sx={{ bgcolor: 'white', color: '#0d47a1', fontWeight: 'bold' }} onClick={() => navigate('/login')}>Log In</Button>
            <Button variant="outlined" size="large" sx={{ borderColor: 'white', color: 'white', fontWeight: 'bold' }} onClick={() => navigate('/signup')}>Sign Up Free</Button>
          </Box>
        </Paper>
      ) : (
        <Box sx={{ mb: 3, display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 2 }}>
          <Box>
            <Typography variant="h4" fontWeight="bold">💼 Jobs & Internships</Typography>
            <Typography variant="body1" color="text.secondary">{jobs.length} active listings · From internships to full-time roles</Typography>
          </Box>
          <Button variant="contained" size="large" startIcon={<PostAdd />} onClick={() => { setFormError(''); setPostOpen(true); }}
            sx={{ borderRadius: 2, fontWeight: 'bold', px: 3 }}>
            + Post a Job
          </Button>
        </Box>
      )}

      {error && <Alert severity="error" sx={{ mb: 3 }}>{error}</Alert>}

      {/* Type pills */}
      <Box sx={{ mb: 2, display: 'flex', gap: 1.5, flexWrap: 'wrap' }}>
        <Paper elevation={0} onClick={() => setActiveType('all')}
          sx={{ px: 2, py: 1, borderRadius: 3, cursor: 'pointer', display: 'flex', alignItems: 'center', gap: 1,
            border: '2px solid', borderColor: activeType === 'all' ? 'primary.main' : 'divider', bgcolor: activeType === 'all' ? 'primary.50' : 'background.paper' }}>
          <Work fontSize="small" color={activeType === 'all' ? 'primary' : 'disabled'} />
          <Typography variant="body2" fontWeight={activeType === 'all' ? 'bold' : 'normal'} color={activeType === 'all' ? 'primary.main' : 'text.secondary'}>All ({jobs.length})</Typography>
        </Paper>
        {JOB_TYPES.map((t) => {
          const active = activeType === t.id;
          const count = typeCounts[t.id] || 0;
          if (!count) return null;
          return (
            <Paper key={t.id} elevation={0} onClick={() => setActiveType(active ? 'all' : t.id)}
              sx={{ px: 2, py: 1, borderRadius: 3, cursor: 'pointer', display: 'flex', alignItems: 'center', gap: 1,
                border: '2px solid', borderColor: active ? t.color : 'divider', bgcolor: active ? t.bg : 'background.paper' }}>
              <Typography variant="body2" fontWeight={active ? 'bold' : 'normal'} sx={{ color: active ? t.color : 'text.secondary' }}>{t.label} ({count})</Typography>
            </Paper>
          );
        })}
      </Box>

      {/* Filters */}
      <Box sx={{ mb: 3, display: 'flex', gap: 2, flexWrap: 'wrap', alignItems: 'center' }}>
        <TextField placeholder="Search by title, company, skills…" value={search} onChange={(e) => setSearch(e.target.value)} size="small" sx={{ flexGrow: 1, minWidth: 220 }}
          InputProps={{ startAdornment: <InputAdornment position="start"><Search fontSize="small" /></InputAdornment> }} />
        <Box sx={{ display: 'flex', gap: 1 }}>
          {['all', 'entry', 'junior', 'mid', 'senior'].map((e) => (
            <Chip key={e} size="small" label={e === 'all' ? 'All Levels' : EXP_LABELS[e]}
              onClick={() => setActiveExp(e)}
              color={activeExp === e ? (EXP_COLORS[e] || 'primary') : 'default'}
              variant={activeExp === e ? 'filled' : 'outlined'} />
          ))}
        </Box>
        <Typography variant="body2" color="text.secondary"><b>{filtered.length}</b> listings</Typography>
      </Box>

      {loading ? <Box sx={{ display: 'flex', justifyContent: 'center', py: 10 }}><CircularProgress /></Box>
        : filtered.length === 0 ? (
          <Box sx={{ textAlign: 'center', py: 10 }}>
            <Work sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
            <Typography variant="h6" color="text.secondary">No jobs match your filters</Typography>
          </Box>
        ) : (
          <Grid container spacing={3}>
            {filtered.map((job) => {
              const typeInfo = TYPE_MAP[job.job_type] || { label: job.job_type, color: '#455a64', bg: '#eceff1' };
              const dl = daysLeft(job.application_deadline);
              return (
                <Grid item xs={12} md={6} key={job.id}>
                  <Card elevation={2} sx={{ height: '100%', display: 'flex', flexDirection: 'column', borderRadius: 3,
                    transition: 'transform 0.2s, box-shadow 0.2s', '&:hover': { transform: 'translateY(-4px)', boxShadow: 6 },
                    borderLeft: `4px solid ${typeInfo.color}` }}>
                    <CardContent sx={{ flexGrow: 1, p: 2.5 }}>
                      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 1 }}>
                        <Box sx={{ flexGrow: 1, mr: 1 }}>
                          <Typography variant="subtitle1" fontWeight="bold" sx={{ lineHeight: 1.3 }}>{job.title}</Typography>
                          <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5, mt: 0.3 }}>
                            <Business fontSize="small" color="action" />
                            <Typography variant="body2" color="text.secondary" fontWeight="bold">{job.company_name}</Typography>
                          </Box>
                        </Box>
                        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 0.5, alignItems: 'flex-end' }}>
                          <Chip label={typeInfo.label} size="small" sx={{ bgcolor: typeInfo.bg, color: typeInfo.color, fontWeight: 'bold', fontSize: '0.65rem', height: 22 }} />
                          {job.experience_level && <Chip label={EXP_LABELS[job.experience_level] || job.experience_level} size="small" color={EXP_COLORS[job.experience_level] || 'default'} sx={{ fontSize: '0.6rem', height: 20 }} />}
                        </Box>
                      </Box>

                      {job.salary_range && (
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5, mb: 0.5 }}>
                          <AttachMoney fontSize="small" color="success" />
                          <Typography variant="body2" color="success.main" fontWeight="bold">{job.salary_range}</Typography>
                        </Box>
                      )}

                      {job.location && (
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5, mb: 0.5 }}>
                          <LocationOn fontSize="small" color="action" />
                          <Typography variant="body2" color="text.secondary">{job.location}</Typography>
                        </Box>
                      )}

                      {job.description && (
                        <Typography variant="body2" color="text.secondary"
                          sx={{ mt: 0.8, display: '-webkit-box', WebkitLineClamp: 2, WebkitBoxOrient: 'vertical', overflow: 'hidden', lineHeight: 1.5 }}>
                          {job.description}
                        </Typography>
                      )}

                      {job.skills_required && (
                        <Box sx={{ mt: 1, display: 'flex', gap: 0.5, flexWrap: 'wrap' }}>
                          {job.skills_required.split(',').slice(0, 4).map((s) => (
                            <Chip key={s} label={s.trim()} size="small" variant="outlined" sx={{ height: 20, fontSize: '0.6rem', borderColor: typeInfo.color, color: typeInfo.color }} />
                          ))}
                        </Box>
                      )}

                      {dl && (
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5, mt: 1 }}>
                          <AlarmOn fontSize="small" color={dl.urgent ? 'error' : 'action'} />
                          <Typography variant="caption" color={dl.urgent ? 'error.main' : 'text.secondary'} fontWeight={dl.urgent ? 'bold' : 'normal'}>{dl.label}</Typography>
                        </Box>
                      )}
                    </CardContent>
                    <CardActions sx={{ px: 2.5, pb: 2.5, gap: 1, flexDirection: 'column', alignItems: 'stretch' }}>
                      <Button variant="contained" size="small" fullWidth sx={{ borderRadius: 2 }} onClick={() => setDetailJob(job)}>View & Apply</Button>
                      {canManage(job) && <Tooltip title="Close posting"><IconButton size="small" color="error" onClick={() => handleDelete(job.id)} sx={{ alignSelf: 'flex-end' }}><Delete fontSize="small" /></IconButton></Tooltip>}
                    </CardActions>
                  </Card>
                </Grid>
              );
            })}
          </Grid>
        )}

      {isLoggedIn && <Fab color="primary" sx={{ position: 'fixed', bottom: 32, right: 32 }} onClick={() => { setFormError(''); setPostOpen(true); }}><Add /></Fab>}

      {/* Detail dialog */}
      <Dialog open={!!detailJob} onClose={() => setDetailJob(null)} maxWidth="sm" fullWidth>
        {detailJob && (() => {
          const typeInfo = TYPE_MAP[detailJob.job_type] || { label: detailJob.job_type, color: '#455a64', bg: '#eceff1' };
          const dl = daysLeft(detailJob.application_deadline);
          return (
            <>
              <DialogTitle sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', pb: 0 }}>
                <Box sx={{ flexGrow: 1, mr: 1 }}>
                  <Typography variant="h6" fontWeight="bold">{detailJob.title}</Typography>
                  <Typography variant="subtitle1" color="text.secondary" fontWeight="bold">{detailJob.company_name}</Typography>
                  <Box sx={{ display: 'flex', gap: 1, mt: 0.5, flexWrap: 'wrap' }}>
                    <Chip label={typeInfo.label} size="small" sx={{ bgcolor: typeInfo.bg, color: typeInfo.color, fontWeight: 'bold' }} />
                    {detailJob.experience_level && <Chip label={EXP_LABELS[detailJob.experience_level] || detailJob.experience_level} size="small" color={EXP_COLORS[detailJob.experience_level] || 'default'} />}
                  </Box>
                </Box>
                <IconButton onClick={() => setDetailJob(null)}><Close /></IconButton>
              </DialogTitle>
              <DialogContent sx={{ pt: 2 }}>
                <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap', mb: 2, p: 2, borderRadius: 2, bgcolor: 'primary.50' }}>
                  {detailJob.salary_range && <Box><Typography variant="caption" color="text.secondary">Salary</Typography><Typography variant="body1" fontWeight="bold" color="success.main">{detailJob.salary_range}</Typography></Box>}
                  {detailJob.location && <Box><Typography variant="caption" color="text.secondary">Location</Typography><Typography variant="body1" fontWeight="bold">{detailJob.location}</Typography></Box>}
                  {detailJob.application_deadline && <Box><Typography variant="caption" color="text.secondary">Apply By</Typography><Typography variant="body1" fontWeight="bold" color={dl?.urgent ? 'error.main' : 'text.primary'}>{new Date(detailJob.application_deadline).toLocaleDateString('en-IN', { day: 'numeric', month: 'long', year: 'numeric' })}</Typography></Box>}
                </Box>
                {detailJob.description && <Box sx={{ mb: 2 }}><Typography variant="subtitle2" fontWeight="bold" gutterBottom>About the Role</Typography><Typography variant="body2" color="text.secondary" sx={{ lineHeight: 1.7 }}>{detailJob.description}</Typography></Box>}
                {detailJob.requirements && <Box sx={{ mb: 2 }}><Typography variant="subtitle2" fontWeight="bold" gutterBottom>Requirements</Typography><Typography variant="body2" color="text.secondary" sx={{ lineHeight: 1.7 }}>{detailJob.requirements}</Typography></Box>}
                {detailJob.skills_required && (
                  <Box sx={{ mb: 2 }}>
                    <Typography variant="subtitle2" fontWeight="bold" gutterBottom>Skills Required</Typography>
                    <Box sx={{ display: 'flex', gap: 0.8, flexWrap: 'wrap' }}>
                      {detailJob.skills_required.split(',').map((s) => <Chip key={s} label={s.trim()} size="small" color="primary" variant="outlined" />)}
                    </Box>
                  </Box>
                )}
                <Divider sx={{ my: 2 }} />
                {detailJob.contact_email && <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5, mb: 1 }}><Email fontSize="small" color="action" /><Typography variant="body2">{detailJob.contact_email}</Typography></Box>}
                {dl && <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}><AlarmOn fontSize="small" color={dl.urgent ? 'error' : 'action'} /><Typography variant="body2" color={dl.urgent ? 'error.main' : 'text.secondary'} fontWeight={dl.urgent ? 'bold' : 'normal'}>{dl.label}</Typography></Box>}
              </DialogContent>
              <DialogActions sx={{ px: 3, pb: 2, gap: 1 }}>
                {detailJob.apply_link ? (
                  <Button variant="contained" color="success" startIcon={<OpenInNew />} href={detailJob.apply_link} target="_blank" rel="noopener" component="a" sx={{ borderRadius: 2, fontWeight: 'bold' }}>Apply Now</Button>
                ) : detailJob.contact_email ? (
                  <Button variant="contained" color="primary" startIcon={<Email />} href={`mailto:${detailJob.contact_email}`} component="a" sx={{ borderRadius: 2, fontWeight: 'bold' }}>Apply via Email</Button>
                ) : null}
                {canManage(detailJob) && <Button color="error" variant="outlined" startIcon={<Delete />} onClick={() => handleDelete(detailJob.id)}>Close Posting</Button>}
              </DialogActions>
            </>
          );
        })()}
      </Dialog>

      {/* Post dialog */}
      <Dialog open={postOpen} onClose={() => setPostOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle><Typography variant="h6" fontWeight="bold">Post a Job / Internship</Typography></DialogTitle>
        <DialogContent sx={{ pt: 1 }}>
          {formError && <Alert severity="error" sx={{ mb: 2 }}>{formError}</Alert>}
          <TextField fullWidth label="Job Title *" value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })} sx={{ mb: 2, mt: 1 }} />
          <TextField fullWidth label="Company / Organisation *" value={form.company_name} onChange={(e) => setForm({ ...form, company_name: e.target.value })} sx={{ mb: 2 }}
            InputProps={{ startAdornment: <InputAdornment position="start"><Business fontSize="small" /></InputAdornment> }} />
          <Grid container spacing={2} sx={{ mb: 2 }}>
            <Grid item xs={6}>
              <FormControl fullWidth><InputLabel>Type *</InputLabel>
                <Select value={form.job_type} label="Type *" onChange={(e) => setForm({ ...form, job_type: e.target.value })}>
                  {JOB_TYPES.map((t) => <MenuItem key={t.id} value={t.id}>{t.label}</MenuItem>)}
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={6}>
              <FormControl fullWidth><InputLabel>Experience Level</InputLabel>
                <Select value={form.experience_level} label="Experience Level" onChange={(e) => setForm({ ...form, experience_level: e.target.value })}>
                  <MenuItem value="entry">Entry Level</MenuItem>
                  <MenuItem value="junior">Junior (1-2yr)</MenuItem>
                  <MenuItem value="mid">Mid (2-5yr)</MenuItem>
                  <MenuItem value="senior">Senior (5yr+)</MenuItem>
                </Select>
              </FormControl>
            </Grid>
          </Grid>
          <Grid container spacing={2} sx={{ mb: 2 }}>
            <Grid item xs={6}><TextField fullWidth label="Location / Remote" value={form.location} onChange={(e) => setForm({ ...form, location: e.target.value })} InputProps={{ startAdornment: <InputAdornment position="start"><LocationOn fontSize="small" /></InputAdornment> }} /></Grid>
            <Grid item xs={6}><TextField fullWidth label="Salary / Stipend" value={form.salary_range} onChange={(e) => setForm({ ...form, salary_range: e.target.value })} placeholder="₹15,000/month" /></Grid>
          </Grid>
          <Grid container spacing={2} sx={{ mb: 2 }}>
            <Grid item xs={6}><TextField fullWidth label="Application Deadline" type="date" value={form.application_deadline} onChange={(e) => setForm({ ...form, application_deadline: e.target.value })} InputLabelProps={{ shrink: true }} InputProps={{ startAdornment: <InputAdornment position="start"><Schedule fontSize="small" /></InputAdornment> }} /></Grid>
            <Grid item xs={6}><TextField fullWidth label="Contact Email" value={form.contact_email} onChange={(e) => setForm({ ...form, contact_email: e.target.value })} InputProps={{ startAdornment: <InputAdornment position="start"><Email fontSize="small" /></InputAdornment> }} /></Grid>
          </Grid>
          <TextField fullWidth label="Apply Link (optional)" value={form.apply_link} onChange={(e) => setForm({ ...form, apply_link: e.target.value })} sx={{ mb: 2 }} placeholder="https://company.com/careers" />
          <TextField fullWidth label="Skills Required" value={form.skills_required} onChange={(e) => setForm({ ...form, skills_required: e.target.value })} sx={{ mb: 2 }} placeholder="React, Python, SQL (comma separated)" />
          <TextField fullWidth label="Job Description" multiline rows={3} value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} sx={{ mb: 2 }} />
          <TextField fullWidth label="Requirements / Eligibility" multiline rows={2} value={form.requirements} onChange={(e) => setForm({ ...form, requirements: e.target.value })} />
        </DialogContent>
        <DialogActions sx={{ px: 3, pb: 2 }}>
          <Button onClick={() => setPostOpen(false)}>Cancel</Button>
          <Button variant="contained" onClick={handlePost} disabled={submitting} startIcon={<PostAdd />} size="large">{submitting ? 'Posting…' : 'Post Job →'}</Button>
        </DialogActions>
      </Dialog>

      <Snackbar open={!!snack} autoHideDuration={3000} onClose={() => setSnack('')} anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }} message={snack} />
    </Container>
  );
};

export default Jobs;
