import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider } from './context/AuthContext'
import ProtectedRoute from './components/ProtectedRoute'
import SignIn from './pages/SignIn'
import Dashboard from './pages/Dashboard'
import Analytics from './pages/Analytics'
import LiveCall from './pages/LiveCall'
import CallHistory from './pages/CallHistory'
import Settings from './pages/Settings'
import TestCaller from './pages/TestCaller'

function App() {
  return (
    <Router>
      <AuthProvider>
        <Routes>
          <Route path="/" element={<Navigate to="/signin" replace />} />
          <Route path="/signin" element={<SignIn />} />
          <Route path="/dashboard" element={
            <ProtectedRoute>
              <Dashboard />
            </ProtectedRoute>
          } />
          <Route path="/analytics" element={
            <ProtectedRoute>
              <Analytics />
            </ProtectedRoute>
          } />
          <Route path="/live" element={
            <ProtectedRoute>
              <LiveCall />
            </ProtectedRoute>
          } />
          <Route path="/call-history" element={
            <ProtectedRoute>
              <CallHistory />
            </ProtectedRoute>
          } />
          <Route path="/settings" element={
            <ProtectedRoute>
              <Settings />
            </ProtectedRoute>
          } />
          {/* No auth required — accessed via URL params from the live call page */}
          <Route path="/test-caller" element={<TestCaller />} />
        </Routes>
      </AuthProvider>
    </Router>
  )
}

export default App
