import { ReactNode } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import { ShieldCheck, Eye, History, BarChart3, Settings, LogOut, User, Sun, Moon } from 'lucide-react'
import { useAuth } from '../context/AuthContext'
import { useTheme } from '../context/ThemeContext'

interface LayoutProps {
  children: ReactNode
  title: string
}

export default function Layout({ children, title }: LayoutProps) {
  const navigate = useNavigate()
  const location = useLocation()
  const { user, logout } = useAuth()
  const { theme, toggleTheme } = useTheme()

  const navItems = [
    { icon: Eye, label: 'Live View', path: '/dashboard' },
    { icon: History, label: 'Call History', path: '/call-history' },
    { icon: BarChart3, label: 'Analytics', path: '/analytics' },
    { icon: Settings, label: 'Settings', path: '/settings' },
  ]

  const isActive = (path: string) => location.pathname === path

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-zinc-950 flex">
      {/* Sidebar */}
      <aside className="w-60 bg-white border-r border-slate-200 dark:bg-[#050810] dark:border-white/[0.06] flex flex-col flex-shrink-0">
        {/* Logo */}
        <div className="px-5 py-5 border-b border-slate-200 dark:border-white/[0.06]">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 bg-teal-50 border border-teal-200 dark:bg-cyan-500/15 dark:border-cyan-500/30 rounded-lg flex items-center justify-center">
              <ShieldCheck className="w-4.5 h-4.5 text-teal-600 dark:text-cyan-400" style={{ width: '1.1rem', height: '1.1rem' }} />
            </div>
            <div>
              <p className="text-sm font-semibold text-slate-900 dark:text-zinc-100 tracking-wide">RESCUE AI</p>
              <p className="text-[10px] text-slate-400 dark:text-zinc-500 tracking-wider uppercase">Command Center</p>
            </div>
          </div>
        </div>

        {/* Navigation */}
        <nav className="flex-1 px-3 py-4">
          <p className="px-2 mb-3 text-[10px] font-semibold text-slate-400 dark:text-zinc-600 uppercase tracking-widest">Navigation</p>
          <ul className="space-y-0.5">
            {navItems.map((item) => {
              const Icon = item.icon
              const active = isActive(item.path)
              return (
                <li key={item.path}>
                  <button
                    onClick={() => navigate(item.path)}
                    className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition-all duration-150 ${
                      active
                        ? 'bg-teal-50 text-teal-700 border-l-2 border-teal-600 pl-[10px] dark:bg-cyan-400/10 dark:text-cyan-400 dark:border-cyan-400'
                        : 'text-slate-500 hover:text-slate-900 hover:bg-slate-100 dark:text-zinc-400 dark:hover:text-zinc-200 dark:hover:bg-zinc-800/60'
                    }`}
                  >
                    <Icon className="w-4 h-4 flex-shrink-0" />
                    <span className={active ? 'font-medium' : ''}>{item.label}</span>
                  </button>
                </li>
              )
            })}
          </ul>
        </nav>

        {/* Bottom user section */}
        <div className="border-t border-slate-200 dark:border-white/[0.06]">
          <div className="px-4 py-3 border-b border-slate-100 dark:border-white/[0.04]">
            <div className="flex items-center gap-2.5">
              <div className="w-7 h-7 bg-slate-200 dark:bg-zinc-700 rounded-full flex items-center justify-center flex-shrink-0">
                <User className="w-3.5 h-3.5 text-slate-500 dark:text-zinc-300" />
              </div>
              <div className="min-w-0">
                <p className="text-xs font-medium text-slate-700 dark:text-zinc-300 truncate">{user?.name || 'Operator'}</p>
                <p className="text-[10px] text-slate-400 dark:text-zinc-600 truncate">{user?.operatorId || 'OP-1122'}</p>
              </div>
            </div>
          </div>
          <div className="px-3 py-3">
            <button
              onClick={logout}
              className="w-full flex items-center gap-3 px-3 py-2 rounded-lg text-sm text-slate-400 hover:text-red-600 hover:bg-red-50 dark:text-zinc-500 dark:hover:text-red-400 dark:hover:bg-red-500/10 transition-all duration-150"
            >
              <LogOut className="w-4 h-4 flex-shrink-0" />
              <span>Log out</span>
            </button>
          </div>
        </div>
      </aside>

      {/* Main Content */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Top bar */}
        <header className="bg-white border-b border-slate-200 dark:bg-zinc-950 dark:border-white/[0.06] px-6 py-3.5 flex-shrink-0">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-base font-semibold text-slate-900 dark:text-zinc-100">{title}</h1>
              <p className="text-xs text-slate-400 dark:text-zinc-500 mt-0.5">
                {new Date().toLocaleDateString('en-US', {
                  weekday: 'long',
                  year: 'numeric',
                  month: 'long',
                  day: 'numeric',
                })}
              </p>
            </div>
            <div className="flex items-center gap-2">
              {/* Theme toggle */}
              <button
                onClick={toggleTheme}
                className="p-2 rounded-lg text-slate-400 hover:text-slate-700 hover:bg-slate-100 dark:text-zinc-500 dark:hover:text-zinc-200 dark:hover:bg-zinc-800 transition-all duration-150"
                title={theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'}
              >
                {theme === 'dark' ? <Sun className="w-4 h-4" /> : <Moon className="w-4 h-4" />}
              </button>
              {/* User pill */}
              <div className="flex items-center gap-2 px-3 py-1.5 bg-slate-100 border border-slate-200 dark:bg-zinc-800/60 dark:border-zinc-700/50 rounded-lg">
                <div className="w-1.5 h-1.5 bg-emerald-500 rounded-full" />
                <span className="text-xs font-medium text-slate-700 dark:text-zinc-300">
                  {user?.name?.split(' ')[0] || 'Operator'}
                </span>
              </div>
            </div>
          </div>
        </header>

        {/* Page Content */}
        <main className="flex-1 p-6 overflow-auto">
          <div className="animate-fade-in">
            {children}
          </div>
        </main>
      </div>
    </div>
  )
}
