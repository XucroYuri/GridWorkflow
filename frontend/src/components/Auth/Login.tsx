import { useState } from 'react'
import { supabase } from '../../lib/supabase'

export default function Login() {
  const [loading, setLoading] = useState(false)
  const [email, setEmail] = useState('')

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    const { error } = await supabase.auth.signInWithOtp({ email })

    if (error) {
      alert(error.message)
    } else {
      alert('Check your email for the login link!')
    }
    setLoading(false)
  }

  return (
    <div className="flex flex-col items-center justify-center h-screen bg-gray-900 text-white">
      <div className="p-8 bg-gray-800 rounded-lg shadow-lg w-96">
        <h1 className="text-2xl font-bold mb-4 text-center">Sign In</h1>
        <p className="mb-4 text-gray-400 text-center">Sign in via Magic Link with your email below</p>
        <form onSubmit={handleLogin} className="flex flex-col gap-4">
          <input
            className="p-2 rounded bg-gray-700 border border-gray-600 focus:border-blue-500 focus:outline-none"
            type="email"
            placeholder="Your email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
          />
          <button
            className="p-2 rounded bg-blue-600 hover:bg-blue-500 font-semibold disabled:opacity-50 transition-colors"
            disabled={loading}
          >
            {loading ? 'Sending magic link...' : 'Send Magic Link'}
          </button>
        </form>
      </div>
    </div>
  )
}

