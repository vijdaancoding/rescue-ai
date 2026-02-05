import { createContext, useContext, useState, ReactNode } from 'react'
import { useNavigate } from 'react-router-dom'

interface User {
  id: string
  name: string
  operatorId: string
  email: string
}

interface AuthContextType {
  user: User | null
  login: (operatorId: string, password: string) => void
  logout: () => void
  isAuthenticated: boolean
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const navigate = useNavigate()

  const login = (operatorId: string, password: string) => {
    // Mock authentication - in production, this would call an API
    const mockUser: User = {
      id: '1',
      name: 'Operator Ali Khan',
      operatorId: operatorId || 'OP-1122',
      email: 'ali.khan@rescue.ai'
    }
    setUser(mockUser)
    localStorage.setItem('user', JSON.stringify(mockUser))
    navigate('/dashboard')
  }

  const logout = () => {
    setUser(null)
    localStorage.removeItem('user')
    navigate('/signin')
  }

  const isAuthenticated = user !== null

  return (
    <AuthContext.Provider value={{ user, login, logout, isAuthenticated }}>
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
