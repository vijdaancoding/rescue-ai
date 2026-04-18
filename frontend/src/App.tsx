import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider } from './context/AuthContext'
import { ThemeProvider } from './context/ThemeContext'
import ProtectedRoute from './components/ProtectedRoute'
import SignIn from './pages/SignIn'
import Dashboard from './pages/Dashboard'
import Analytics from './pages/Analytics'
import LiveCall from './pages/LiveCall'
import CallHistory from './pages/CallHistory'
import Settings from './pages/Settings'
import TestCaller from './pages/TestCaller'
import Dispatch from './pages/Dispatch'
import Health from './pages/Health'
import CallListener from './pages/CallListener'
import TestCall from './pages/TestCall'

function App() {
  return (
    <ThemeProvider>
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
            <Route path="/health" element={
              <ProtectedRoute>
                <Health />
              </ProtectedRoute>
            } />
            <Route path="/dispatch/:callId" element={
              <ProtectedRoute>
                <Dispatch />
              </ProtectedRoute>
            } />
            <Route path="/listen/:callId" element={
              <ProtectedRoute>
                <CallListener />
              </ProtectedRoute>
            } />
            <Route path="/test-call" element={
              <ProtectedRoute>
                <TestCall />
              </ProtectedRoute>
            } />
            <Route path="/test-caller" element={<TestCaller />} />
          </Routes>
        </AuthProvider>
      </Router>
    </ThemeProvider>
  )
}

export default App
