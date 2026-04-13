import { createContext, useContext, useState, useEffect, ReactNode } from 'react'
import { useNavigate } from 'react-router-dom'

interface User {
  id: string
  name: string
  operatorId: string
  email: string
}

interface AuthContextType {
  user: User | null
  token: string | null
  login: (operatorId: string, password: string) => Promise<void>
  logout: () => void
  isAuthenticated: boolean
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [token, setToken] = useState<string | null>(null)
  const navigate = useNavigate()

  // Restore session from localStorage on mount
  useEffect(() => {
    const savedToken = localStorage.getItem('auth_token')
    const savedUser = localStorage.getItem('user')
    if (savedToken && savedUser) {
      setToken(savedToken)
      setUser(JSON.parse(savedUser))
    }
  }, [])

  const login = async (operatorId: string, password: string) => {
    const formData = new URLSearchParams()
    formData.append('username', operatorId)
    formData.append('password', password)

    const res = await fetch(`${API_URL}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: formData.toString(),
    })

    if (!res.ok) {
      throw new Error('Invalid credentials')
    }

    const data = await res.json()
    const accessToken: string = data.access_token

    const loggedInUser: User = {
      id: '1',
      name: operatorId,
      operatorId: operatorId,
      email: `${operatorId}@rescue.ai`,
    }

    setToken(accessToken)
    setUser(loggedInUser)
    localStorage.setItem('auth_token', accessToken)
    localStorage.setItem('user', JSON.stringify(loggedInUser))
    navigate('/dashboard')
  }

  const logout = () => {
    setUser(null)
    setToken(null)
    localStorage.removeItem('auth_token')
    localStorage.removeItem('user')
    navigate('/signin')
  }

  const isAuthenticated = user !== null

  return (
    <AuthContext.Provider value={{ user, token, login, logout, isAuthenticated }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}
