import React, { useState, useEffect } from 'react';
import {
  Container,
  Typography,
  Box,
  Card,
  CardContent,
  Grid,
  Tabs,
  Tab,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Chip,
  Button,
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
  AdminPanelSettings,
  People,
  Event,
  ShoppingCart,
  Report,
  Analytics,
  Settings,
  Block,
  CheckCircle,
  Delete,
} from '@mui/icons-material';
import { useSelector } from 'react-redux';
import axios from 'axios';

const AdminPanel = () => {
  const theme = useTheme();
  const { user, token } = useSelector((state) => state.auth);
  const [activeTab, setActiveTab] = useState(0);
  const [users, setUsers] = useState([]);
  const [reports, setReports] = useState([]);
  const [marketplaceItems, setMarketplaceItems] = useState([]);
  const [stats, setStats] = useState({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const API_BASE_URL = process.env.REACT_APP_API_URL || '';

  useEffect(() => {
    if (user?.role === 'admin') {
      fetchAdminData();
    }
  }, [user]);

  const fetchAdminData = async () => {
    try {
      setLoading(true);

      // Fetch users
      const usersResponse = await axios.get(`${API_BASE_URL}/auth/users`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      setUsers(usersResponse.data);

      // Fetch reports (stolen & found)
      const reportsResponse = await axios.get(`${API_BASE_URL}/stolen-found`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      setReports(reportsResponse.data);

      // Fetch marketplace items
      const marketplaceResponse = await axios.get(`${API_BASE_URL}/marketplace`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      setMarketplaceItems(marketplaceResponse.data);

      // Calculate stats
      setStats({
        totalUsers: usersResponse.data.length,
        totalReports: reportsResponse.data.length,
        totalMarketplaceItems: marketplaceResponse.data.length,
        activeReports: reportsResponse.data.filter(r => r.status === 'active').length,
        availableItems: marketplaceResponse.data.filter(i => i.status === 'available').length,
      });

    } catch (err) {
      setError('Failed to load admin data');
      console.error('Error fetching admin data:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleTabChange = (event, newValue) => {
    setActiveTab(newValue);
  };

  const handleUserAction = async (userId, action) => {
    try {
      if (action === 'delete') {
        if (!window.confirm('Delete this user? This cannot be undone.')) return;
        await axios.delete(`${API_BASE_URL}/auth/users/${userId}`, {
          headers: { Authorization: `Bearer ${token}` },
        });
        setUsers(users.filter(u => u.id !== userId));
      } else if (action === 'make_admin') {
        const updated = await axios.patch(`${API_BASE_URL}/auth/users/${userId}/role`,
          { role: 'admin' }, { headers: { Authorization: `Bearer ${token}` } });
        setUsers(users.map(u => u.id === userId ? { ...u, role: updated.data.role } : u));
      } else if (action === 'remove_admin') {
        const updated = await axios.patch(`${API_BASE_URL}/auth/users/${userId}/role`,
          { role: 'student' }, { headers: { Authorization: `Bearer ${token}` } });
        setUsers(users.map(u => u.id === userId ? { ...u, role: updated.data.role } : u));
      }
    } catch (err) {
      console.error('Error performing user action:', err);
    }
  };

  const handleReportAction = async (reportId, action) => {
    try {
      if (action === 'resolve') {
        await axios.post(`${API_BASE_URL}/stolen-found/${reportId}/mark-resolved`, {}, {
          headers: { Authorization: `Bearer ${token}` },
        });
        setReports(reports.map(r =>
          r.id === reportId ? { ...r, status: 'resolved' } : r
        ));
      }
    } catch (err) {
      console.error('Error performing report action:', err);
    }
  };

  const handleMarketplaceAction = async (itemId, action) => {
    try {
      if (action === 'remove') {
        await axios.delete(`${API_BASE_URL}/marketplace/${itemId}`, {
          headers: { Authorization: `Bearer ${token}` },
        });
        setMarketplaceItems(marketplaceItems.filter(i => i.id !== itemId));
      }
    } catch (err) {
      console.error('Error performing marketplace action:', err);
    }
  };

  if (!user || user.role !== 'admin') {
    return (
      <Container maxWidth="lg" sx={{ py: 4 }}>
        <Alert severity="error">
          Access denied. Admin privileges required.
        </Alert>
      </Container>
    );
  }

  if (loading) {
    return (
      <Container maxWidth="lg" sx={{ py: 4 }}>
        <Typography variant="h4" align="center">Loading admin panel...</Typography>
      </Container>
    );
  }

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      <Box sx={{ textAlign: 'center', mb: 4 }}>
        <AdminPanelSettings sx={{ fontSize: 64, color: 'primary.main', mb: 2 }} />
        <Typography variant="h3" component="h1" fontWeight="bold" gutterBottom>
          Admin Panel
        </Typography>
        <Typography variant="h6" color="text.secondary">
          Manage your campus community platform
        </Typography>
      </Box>

      {/* Stats Cards */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} md={3}>
          <Card>
            <CardContent sx={{ textAlign: 'center' }}>
              <People sx={{ fontSize: 48, color: 'primary.main', mb: 1 }} />
              <Typography variant="h4" fontWeight="bold">
                {stats.totalUsers || 0}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Total Users
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={3}>
          <Card>
            <CardContent sx={{ textAlign: 'center' }}>
              <Report sx={{ fontSize: 48, color: 'warning.main', mb: 1 }} />
              <Typography variant="h4" fontWeight="bold">
                {stats.activeReports || 0}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Active Reports
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={3}>
          <Card>
            <CardContent sx={{ textAlign: 'center' }}>
              <ShoppingCart sx={{ fontSize: 48, color: 'success.main', mb: 1 }} />
              <Typography variant="h4" fontWeight="bold">
                {stats.availableItems || 0}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Available Items
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={3}>
          <Card>
            <CardContent sx={{ textAlign: 'center' }}>
              <Analytics sx={{ fontSize: 48, color: 'info.main', mb: 1 }} />
              <Typography variant="h4" fontWeight="bold">
                {stats.totalReports || 0}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Total Reports
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Tabs */}
      <Paper sx={{ width: '100%' }}>
        <Tabs
          value={activeTab}
          onChange={handleTabChange}
          indicatorColor="primary"
          textColor="primary"
          centered
        >
          <Tab label="Users" />
          <Tab label="Reports" />
          <Tab label="Marketplace" />
          <Tab label="Settings" />
        </Tabs>

        {/* Users Tab */}
        {activeTab === 0 && (
          <Box sx={{ p: 3 }}>
            <Typography variant="h5" fontWeight="bold" gutterBottom>
              User Management
            </Typography>
            <TableContainer>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>ID</TableCell>
                    <TableCell>Name</TableCell>
                    <TableCell>Email</TableCell>
                    <TableCell>Role</TableCell>
                    <TableCell>Status</TableCell>
                    <TableCell>Actions</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {users.map((user) => (
                    <TableRow key={user.id}>
                      <TableCell>{user.id}</TableCell>
                      <TableCell>{user.full_name}</TableCell>
                      <TableCell>{user.email}</TableCell>
                      <TableCell>
                        <Chip
                          label={user.role}
                          color={user.role === 'admin' ? 'primary' : 'default'}
                          size="small"
                        />
                      </TableCell>
                      <TableCell>
                        <Chip
                          label={user.is_active ? 'Active' : 'Inactive'}
                          color={user.is_active ? 'success' : 'error'}
                          size="small"
                        />
                      </TableCell>
                      <TableCell>
                        <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                          {user.role !== 'admin' ? (
                            <Button size="small" color="primary" variant="outlined"
                              onClick={() => handleUserAction(user.id, 'make_admin')}>
                              Make Admin
                            </Button>
                          ) : (
                            <Button size="small" color="warning" variant="outlined"
                              onClick={() => handleUserAction(user.id, 'remove_admin')}>
                              Remove Admin
                            </Button>
                          )}
                          <Button size="small" color="error"
                            onClick={() => handleUserAction(user.id, 'delete')}>
                            Delete
                          </Button>
                        </Box>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          </Box>
        )}

        {/* Reports Tab */}
        {activeTab === 1 && (
          <Box sx={{ p: 3 }}>
            <Typography variant="h5" fontWeight="bold" gutterBottom>
              Content Moderation - Lost & Found Reports
            </Typography>
            <TableContainer>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>ID</TableCell>
                    <TableCell>Item</TableCell>
                    <TableCell>Type</TableCell>
                    <TableCell>Location</TableCell>
                    <TableCell>Status</TableCell>
                    <TableCell>Actions</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {reports.map((report) => (
                    <TableRow key={report.id}>
                      <TableCell>{report.id}</TableCell>
                      <TableCell>{report.item_name}</TableCell>
                      <TableCell>
                        <Chip
                          label={report.report_type}
                          color={report.report_type === 'lost' ? 'error' : 'success'}
                          size="small"
                        />
                      </TableCell>
                      <TableCell>{report.location || 'N/A'}</TableCell>
                      <TableCell>
                        <Chip
                          label={report.status}
                          color={report.status === 'active' ? 'warning' : 'success'}
                          size="small"
                        />
                      </TableCell>
                      <TableCell>
                        {report.status === 'active' && (
                          <Button
                            size="small"
                            color="success"
                            onClick={() => handleReportAction(report.id, 'resolve')}
                          >
                            Resolve
                          </Button>
                        )}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          </Box>
        )}

        {/* Marketplace Tab */}
        {activeTab === 2 && (
          <Box sx={{ p: 3 }}>
            <Typography variant="h5" fontWeight="bold" gutterBottom>
              Marketplace Oversight
            </Typography>
            <TableContainer>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>ID</TableCell>
                    <TableCell>Title</TableCell>
                    <TableCell>Price</TableCell>
                    <TableCell>Category</TableCell>
                    <TableCell>Status</TableCell>
                    <TableCell>Actions</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {marketplaceItems.map((item) => (
                    <TableRow key={item.id}>
                      <TableCell>{item.id}</TableCell>
                      <TableCell>{item.title}</TableCell>
                      <TableCell>${item.price}</TableCell>
                      <TableCell>
                        <Chip label={item.category} size="small" />
                      </TableCell>
                      <TableCell>
                        <Chip
                          label={item.status}
                          color={item.status === 'available' ? 'success' : 'default'}
                          size="small"
                        />
                      </TableCell>
                      <TableCell>
                        <Button
                          size="small"
                          color="error"
                          onClick={() => handleMarketplaceAction(item.id, 'remove')}
                        >
                          Remove
                        </Button>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          </Box>
        )}

        {/* Settings Tab */}
        {activeTab === 3 && (
          <Box sx={{ p: 3 }}>
            <Typography variant="h5" fontWeight="bold" gutterBottom>
              System Settings
            </Typography>
            <Alert severity="info" sx={{ mb: 3 }}>
              System configuration features will be available in future updates.
              This includes platform settings, notification preferences, and maintenance controls.
            </Alert>
            <Grid container spacing={3}>
              <Grid item xs={12} md={6}>
                <Card>
                  <CardContent>
                    <Typography variant="h6" fontWeight="bold" gutterBottom>
                      Platform Configuration
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Configure general platform settings, maintenance mode, and feature toggles.
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>
              <Grid item xs={12} md={6}>
                <Card>
                  <CardContent>
                    <Typography variant="h6" fontWeight="bold" gutterBottom>
                      Notification Settings
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Manage push notification settings and email configurations.
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>
            </Grid>
          </Box>
        )}
      </Paper>
    </Container>
  );
};

export default AdminPanel;