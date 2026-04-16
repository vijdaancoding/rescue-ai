import { useState } from 'react'
import Layout from '../components/Layout'
import Toast from '../components/Toast'
import { useToast } from '../hooks/useToast'
import { User, Bell, Shield, Globe, Moon, Volume2, Save } from 'lucide-react'

function Toggle({ checked, onChange }: { checked: boolean; onChange: (v: boolean) => void }) {
  return (
    <button
      type="button"
      onClick={() => onChange(!checked)}
      className={`relative inline-flex h-5 w-9 items-center rounded-full transition-colors duration-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-teal-500 dark:focus-visible:ring-cyan-500 ${
        checked ? 'bg-teal-500 dark:bg-cyan-500' : 'bg-slate-200 dark:bg-zinc-700'
      }`}
    >
      <span
        className={`inline-block h-3.5 w-3.5 transform rounded-full bg-white shadow transition-transform duration-200 ${
          checked ? 'translate-x-4' : 'translate-x-0.5'
        }`}
      />
    </button>
  )
}

function SectionHeader({ icon: Icon, title }: { icon: React.ElementType; title: string }) {
  return (
    <div className="flex items-center gap-2.5 mb-5 pb-4 border-b border-slate-200 dark:border-zinc-800">
      <div className="w-8 h-8 bg-slate-100 dark:bg-zinc-800 rounded-lg flex items-center justify-center">
        <Icon className="w-4 h-4 text-slate-500 dark:text-zinc-400" />
      </div>
      <h3 className="text-sm font-semibold text-slate-800 dark:text-zinc-200">{title}</h3>
    </div>
  )
}

function SettingRow({ label, description, children }: { label: string; description: string; children: React.ReactNode }) {
  return (
    <div className="flex items-center justify-between py-3.5 border-b border-slate-100 dark:border-zinc-800/60 last:border-b-0">
      <div>
        <p className="text-sm font-medium text-slate-800 dark:text-zinc-200">{label}</p>
        <p className="text-xs text-slate-400 dark:text-zinc-500 mt-0.5">{description}</p>
      </div>
      {children}
    </div>
  )
}

export default function Settings() {
  const { toasts, showToast, removeToast } = useToast()

  const [settings, setSettings] = useState({
    operatorName: 'Operator 1122',
    operatorId: 'OP-1122',
    email: 'operator1122@rescue.ai',
    soundAlerts: true,
    emailNotifications: true,
    emergencyAlerts: true,
    darkMode: true,
    language: 'english',
    volume: 75,
    microphone: true,
    twoFactorAuth: true,
    sessionTimeout: 30,
  })

  const handleSave = () => {
    showToast('Settings saved successfully', 'success')
  }

  return (
    <Layout title="Settings">
      {toasts.map(t => (
        <Toast key={t.id} message={t.message} type={t.type} onClose={() => removeToast(t.id)} />
      ))}

      <div className="max-w-2xl space-y-5">
        <div>
          <h2 className="text-base font-semibold text-slate-800 dark:text-zinc-200">Settings & Preferences</h2>
          <p className="text-xs text-slate-400 dark:text-zinc-500 mt-0.5">Customize your Rescue AI experience</p>
        </div>

        {/* Profile */}
        <div className="card">
          <SectionHeader icon={User} title="Profile Information" />
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-slate-400 dark:text-zinc-500 uppercase tracking-wider mb-2">Operator Name</label>
              <input
                type="text"
                value={settings.operatorName}
                onChange={(e) => setSettings({ ...settings, operatorName: e.target.value })}
                className="input-field"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-slate-400 dark:text-zinc-500 uppercase tracking-wider mb-2">Operator ID</label>
              <input
                type="text"
                value={settings.operatorId}
                disabled
                className="input-field opacity-50 cursor-not-allowed"
              />
            </div>
            <div className="md:col-span-2">
              <label className="block text-xs font-semibold text-slate-400 dark:text-zinc-500 uppercase tracking-wider mb-2">Email Address</label>
              <input
                type="email"
                value={settings.email}
                onChange={(e) => setSettings({ ...settings, email: e.target.value })}
                className="input-field"
              />
            </div>
          </div>
        </div>

        {/* Notifications */}
        <div className="card">
          <SectionHeader icon={Bell} title="Notifications" />
          <SettingRow label="Sound Alerts" description="Play sound for incoming calls">
            <Toggle checked={settings.soundAlerts} onChange={v => setSettings({ ...settings, soundAlerts: v })} />
          </SettingRow>
          <SettingRow label="Email Notifications" description="Receive updates via email">
            <Toggle checked={settings.emailNotifications} onChange={v => setSettings({ ...settings, emailNotifications: v })} />
          </SettingRow>
          <SettingRow label="Emergency Alerts" description="High priority emergency notifications">
            <Toggle checked={settings.emergencyAlerts} onChange={v => setSettings({ ...settings, emergencyAlerts: v })} />
          </SettingRow>
        </div>

        {/* Display */}
        <div className="card">
          <SectionHeader icon={Moon} title="Display & Language" />
          <SettingRow label="Dark Mode" description="Switch to dark theme">
            <Toggle checked={settings.darkMode} onChange={v => setSettings({ ...settings, darkMode: v })} />
          </SettingRow>
          <div className="pt-4">
            <label className="block text-xs font-semibold text-slate-400 dark:text-zinc-500 uppercase tracking-wider mb-2 flex items-center gap-2">
              <Globe className="w-3.5 h-3.5" /> Interface Language
            </label>
            <select
              value={settings.language}
              onChange={(e) => setSettings({ ...settings, language: e.target.value })}
              className="input-field"
            >
              <option value="english">English</option>
              <option value="urdu">اردو (Urdu)</option>
              <option value="punjabi">ਪੰਜਾਬੀ (Punjabi)</option>
            </select>
          </div>
        </div>

        {/* Audio */}
        <div className="card">
          <SectionHeader icon={Volume2} title="Audio Settings" />
          <div className="mb-5">
            <label className="block text-xs font-semibold text-slate-400 dark:text-zinc-500 uppercase tracking-wider mb-3">
              System Volume: <span className="text-teal-600 dark:text-cyan-400 tabular">{settings.volume}%</span>
            </label>
            <input
              type="range"
              min="0"
              max="100"
              value={settings.volume}
              onChange={(e) => setSettings({ ...settings, volume: parseInt(e.target.value) })}
              className="w-full h-1.5 bg-slate-200 dark:bg-zinc-700 rounded-full appearance-none cursor-pointer accent-teal-500 dark:accent-cyan-500"
            />
          </div>
          <SettingRow label="Microphone Access" description="Allow microphone for voice commands">
            <Toggle checked={settings.microphone} onChange={v => setSettings({ ...settings, microphone: v })} />
          </SettingRow>
        </div>

        {/* Security */}
        <div className="card">
          <SectionHeader icon={Shield} title="Security" />
          <SettingRow label="Two-Factor Authentication" description="Add an extra layer of security">
            <Toggle checked={settings.twoFactorAuth} onChange={v => setSettings({ ...settings, twoFactorAuth: v })} />
          </SettingRow>
          <div className="pt-4">
            <label className="block text-xs font-semibold text-slate-400 dark:text-zinc-500 uppercase tracking-wider mb-2">Session Timeout (minutes)</label>
            <input
              type="number"
              value={settings.sessionTimeout}
              onChange={(e) => setSettings({ ...settings, sessionTimeout: parseInt(e.target.value) })}
              className="input-field w-32"
              min="5"
              max="120"
            />
          </div>
        </div>

        {/* Save */}
        <div className="flex justify-start pb-2">
          <button
            onClick={handleSave}
            className="flex items-center gap-2 px-6 py-2.5 rounded-lg font-medium text-sm transition-all duration-200 active:scale-95
              bg-slate-900 text-white hover:bg-slate-700
              dark:bg-zinc-100 dark:text-zinc-900 dark:hover:bg-white"
          >
            <Save className="w-4 h-4" />
            Save Settings
          </button>
        </div>
      </div>
    </Layout>
  )
}
