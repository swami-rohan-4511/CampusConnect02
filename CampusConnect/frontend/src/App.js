import React, { useEffect, useMemo } from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { useDispatch, useSelector } from 'react-redux';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import { verifyToken } from './features/authSlice';
import Navbar from './components/Navbar';
import Home from './pages/Home';
import Login from './pages/Login';
import Signup from './pages/Signup';
import Meetups from './pages/Meetups';
import Marketplace from './pages/Marketplace';
import StolenFound from './pages/StolenFound';
import Rooms from './pages/Rooms';
import RentalHub from './pages/RentalHub';
import Clubs from './pages/Clubs';
import Jobs from './pages/Jobs';
import Notes from './pages/Notes';
import Food from './pages/Food';
import Profile from './pages/Profile';
import AdminPanel from './components/AdminPanel';

function App() {
  const dispatch = useDispatch();
  const themeMode = useSelector((state) => state.ui.theme);

  useEffect(() => {
    const token = localStorage.getItem('token');
    if (token) {
      dispatch(verifyToken());
    }
  }, [dispatch]);

  const theme = useMemo(
    () =>
      createTheme({
        palette: {
          mode: themeMode,
          primary: {
            main: '#1976d2',
          },
          secondary: {
            main: '#dc004e',
          },
        },
        typography: {
          fontFamily: '"Roboto", "Helvetica", "Arial", sans-serif',
          h4: { fontWeight: 600 },
          h5: { fontWeight: 600 },
          h6: { fontWeight: 600 },
        },
        components: {
          MuiButton: {
            styleOverrides: {
              root: {
                borderRadius: 8,
                textTransform: 'none',
                fontWeight: 600,
              },
            },
          },
          MuiCard: {
            styleOverrides: {
              root: {
                borderRadius: 12,
                boxShadow: '0 4px 6px rgba(0, 0, 0, 0.07)',
              },
            },
          },
        },
      }),
    [themeMode]
  );

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Router>
        <div className="App">
          <Navbar />
          <main style={{ marginTop: '64px', minHeight: 'calc(100vh - 64px)' }}>
            <Routes>
              <Route path="/" element={<Home />} />
              <Route path="/login" element={<Login />} />
              <Route path="/signup" element={<Signup />} />
              <Route path="/meetups" element={<Meetups />} />
              <Route path="/marketplace" element={<Marketplace />} />
              <Route path="/stolen-found" element={<StolenFound />} />
              <Route path="/rooms" element={<Rooms />} />
              <Route path="/rental" element={<RentalHub />} />
              <Route path="/clubs" element={<Clubs />} />
              <Route path="/jobs" element={<Jobs />} />
              <Route path="/notes" element={<Notes />} />
              <Route path="/food" element={<Food />} />
              <Route path="/profile" element={<Profile />} />
              <Route path="/admin" element={<AdminPanel />} />
            </Routes>
          </main>
        </div>
      </Router>
    </ThemeProvider>
  );
}

export default App;
