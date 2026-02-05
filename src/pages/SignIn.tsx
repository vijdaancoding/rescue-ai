import { useState } from 'react'
import { ShieldCheck, Loader2 } from 'lucide-react'
import { useAuth } from '../context/AuthContext'

export default function SignIn() {
  const { login } = useAuth()
  const [operatorId, setOperatorId] = useState('')
  const [password, setPassword] = useState('')
  const [isLoading, setIsLoading] = useState(false)

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (operatorId && password) {
      setIsLoading(true)
      // Simulate API call delay
      setTimeout(() => {
        login(operatorId, password)
        setIsLoading(false)
      }, 1000)
    }
  }

  const handleQuickLogin = () => {
    setIsLoading(true)
    setTimeout(() => {
      login('OP-1122', 'demo')
      setIsLoading(false)
    }, 1000)
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-teal-50 via-white to-blue-50 flex flex-col">
      {/* Header */}
      <header className="bg-white/80 backdrop-blur-md border-b border-gray-200 px-6 py-4 shadow-sm">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-gradient-to-br from-teal-500 to-teal-600 rounded-xl flex items-center justify-center shadow-md">
            <ShieldCheck className="w-6 h-6 text-white" />
          </div>
          <div>
            <span className="font-bold text-gray-900 text-lg">Rescue AI</span>
            <p className="text-xs text-gray-600">Urdu Intelligence System</p>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-1 flex items-center justify-center px-4 py-12">
        <div className="w-full max-w-md animate-slide-in">
          {/* Welcome Section */}
          <div className="text-center mb-12">
            <div className="inline-block p-4 bg-gradient-to-br from-teal-500 to-teal-600 rounded-2xl shadow-xl mb-6">
              <ShieldCheck className="w-16 h-16 text-white" />
            </div>
            <h1 className="text-4xl font-bold text-gray-900 mb-3 bg-gradient-to-r from-teal-600 to-blue-600 bg-clip-text text-transparent">
              Welcome to Rescue AI
            </h1>
            <p className="text-gray-600 mb-6 text-lg">
              Secure Login to Access the Command Center
            </p>
            <button
              onClick={handleQuickLogin}
              disabled={isLoading}
              className="btn btn-secondary inline-flex items-center gap-2"
            >
              {isLoading ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  <span>Authenticating...</span>
                </>
              ) : (
                <span>Quick Access (Demo)</span>
              )}
            </button>
          </div>

          {/* Login Form */}
          <div className="bg-white/80 backdrop-blur-md rounded-2xl shadow-2xl border border-gray-200 p-8">
            <h2 className="text-2xl font-bold text-gray-900 mb-2">
              Login Information
            </h2>
            <p className="text-gray-600 mb-6">Please enter your credentials.</p>

            <form onSubmit={handleSubmit} className="space-y-5">
              {/* Operator ID */}
              <div>
                <label htmlFor="operatorId" className="block text-sm font-semibold text-gray-700 mb-2">
                  Operator ID
                </label>
                <input
                  id="operatorId"
                  type="text"
                  placeholder="Enter your Operator ID"
                  value={operatorId}
                  onChange={(e) => setOperatorId(e.target.value)}
                  className="input-field"
                  disabled={isLoading}
                  required
                />
              </div>

              {/* Password */}
              <div>
                <label htmlFor="password" className="block text-sm font-semibold text-gray-700 mb-2">
                  Password
                </label>
                <input
                  id="password"
                  type="password"
                  placeholder="Enter your password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="input-field"
                  disabled={isLoading}
                  required
                />
              </div>

              {/* Submit Button */}
              <button
                type="submit"
                disabled={isLoading}
                className="btn btn-primary w-full flex items-center justify-center gap-2"
              >
                {isLoading ? (
                  <>
                    <Loader2 className="w-5 h-5 animate-spin" />
                    <span>Authenticating...</span>
                  </>
                ) : (
                  <span>Enter Command Center</span>
                )}
              </button>
            </form>
          </div>

          {/* Footer */}
          <p className="text-center text-sm text-gray-600 mt-8 font-medium">
            🔒 Authorized Personnel Only - Rescue 1122 / Police Access
          </p>

          {/* Portal Info */}
          <div className="mt-6 glass rounded-xl p-6 text-center shadow-lg">
            <p className="text-sm text-gray-700 font-medium">
              This is a secure portal designed for authorized emergency response personnel.
            </p>
          </div>
        </div>
      </main>
    </div>
  )
}
