import { useState } from 'react'
import { ShieldCheck, Loader2, Eye, EyeOff } from 'lucide-react'
import { useAuth } from '../context/AuthContext'

export default function SignIn() {
  const { login } = useAuth()
  const [operatorId, setOperatorId] = useState('')
  const [password, setPassword] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState('')

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (operatorId && password) {
      setIsLoading(true)
      setError('')
      try {
        await login(operatorId, password)
      } catch {
        setError('Invalid credentials. Please try again.')
      } finally {
        setIsLoading(false)
      }
    }
  }

  const handleQuickLogin = async () => {
    setIsLoading(true)
    setError('')
    try {
      await login('dispatcher', 'rescue1122')
    } catch {
      setError('Quick login failed.')
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-zinc-950 flex items-center justify-center px-4">
      {/* Subtle background grid */}
      <div
        className="fixed inset-0 pointer-events-none opacity-[0.04] dark:opacity-[0.03]"
        style={{
          backgroundImage:
            'linear-gradient(rgba(0,0,0,0.5) 1px, transparent 1px), linear-gradient(90deg, rgba(0,0,0,0.5) 1px, transparent 1px)',
          backgroundSize: '48px 48px',
        }}
      />

      <div className="w-full max-w-sm animate-slide-in relative">
        {/* Logo mark */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-14 h-14 bg-teal-50 border border-teal-200 dark:bg-cyan-500/10 dark:border-cyan-500/25 rounded-2xl mb-4">
            <ShieldCheck className="w-7 h-7 text-teal-600 dark:text-cyan-400" />
          </div>
          <h1 className="text-2xl font-bold text-slate-900 dark:text-zinc-100 tracking-tight">RESCUE AI</h1>
          <p className="text-sm text-slate-500 dark:text-zinc-500 mt-1">Command Center — Urdu Intelligence</p>
        </div>

        {/* Form card */}
        <div className="bg-white border border-slate-200 dark:bg-zinc-900 dark:border-zinc-800 rounded-2xl p-7">
          {error && (
            <div className="mb-5 px-4 py-3 bg-red-50 border border-red-200 dark:bg-red-500/10 dark:border-red-500/20 rounded-lg text-sm text-red-700 dark:text-red-400">
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label htmlFor="operatorId" className="block text-xs font-semibold text-slate-500 dark:text-zinc-400 uppercase tracking-wider mb-2">
                Operator ID
              </label>
              <input
                id="operatorId"
                type="text"
                placeholder="Enter your operator ID"
                value={operatorId}
                onChange={(e) => setOperatorId(e.target.value)}
                className="input-field"
                disabled={isLoading}
                required
              />
            </div>

            <div>
              <label htmlFor="password" className="block text-xs font-semibold text-slate-500 dark:text-zinc-400 uppercase tracking-wider mb-2">
                Password
              </label>
              <div className="relative">
                <input
                  id="password"
                  type={showPassword ? 'text' : 'password'}
                  placeholder="Enter your password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="input-field pr-10"
                  disabled={isLoading}
                  required
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600 dark:text-zinc-500 dark:hover:text-zinc-300"
                  tabIndex={-1}
                >
                  {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
            </div>

            <button
              type="submit"
              disabled={isLoading}
              className="w-full flex items-center justify-center gap-2 py-2.5 rounded-lg font-medium text-sm mt-2 transition-all duration-200 active:scale-95
                bg-slate-900 text-white hover:bg-slate-700
                dark:bg-zinc-100 dark:text-zinc-900 dark:hover:bg-white
                disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isLoading ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  <span>Authenticating...</span>
                </>
              ) : (
                <span>Enter Command Center</span>
              )}
            </button>
          </form>

          <div className="mt-4 pt-4 border-t border-slate-100 dark:border-zinc-800 text-center">
            <button
              onClick={handleQuickLogin}
              disabled={isLoading}
              className="text-xs text-slate-400 hover:text-slate-600 dark:text-zinc-600 dark:hover:text-zinc-400 transition-colors disabled:opacity-50"
            >
              Use demo credentials →
            </button>
          </div>
        </div>

        <p className="text-center text-xs text-slate-400 dark:text-zinc-700 mt-6">
          Authorized personnel only · Rescue 1122
        </p>
      </div>
    </div>
  )
}
