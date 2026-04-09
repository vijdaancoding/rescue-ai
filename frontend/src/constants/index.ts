// Application constants

export const APP_NAME = 'Rescue AI'
export const APP_DESCRIPTION = 'Emergency Dispatcher Dashboard with Urdu Intelligence'
export const APP_VERSION = '1.0.0'

export const ROUTES = {
  SIGNIN: '/signin',
  DASHBOARD: '/dashboard',
  ANALYTICS: '/analytics',
  LIVE: '/live',
  CALL_HISTORY: '/call-history',
  SETTINGS: '/settings',
} as const

export const TOAST_DURATION = 3000

export const CALL_TYPES = {
  INCOMING: 'incoming',
  BLOCKED: 'blocked',
  EMERGENCY: 'emergency',
} as const

export const PRIORITY_LEVELS = {
  HIGH: 'High',
  MEDIUM: 'Medium',
  LOW: 'Low',
} as const

export const STORAGE_KEYS = {
  USER: 'user',
  AUTH_TOKEN: 'authToken',
} as const
