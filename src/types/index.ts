// Type definitions for the application

export interface User {
  id: string
  name: string
  operatorId: string
  email: string
}

export interface Call {
  id: number
  type: 'incoming' | 'blocked' | 'emergency'
  status: string
  label: string
  time?: string
  date?: string
  duration?: string
  operatorId?: string
  priority?: 'High' | 'Medium' | 'Low'
  location?: string
}

export interface SystemHealth {
  activeUnits: number
  systemLatency: string
  responseRate: string
}

export interface Stat {
  label: string
  value: string
  trend: string
  icon: any
  color: string
  bgColor: string
}

export interface NavItem {
  icon: any
  label: string
  path: string
}

export interface ToastProps {
  message: string
  type: 'success' | 'error' | 'info'
  onClose: () => void
  duration?: number
}

export interface AuthContextType {
  user: User | null
  login: (operatorId: string, password: string) => void
  logout: () => void
  isAuthenticated: boolean
}
