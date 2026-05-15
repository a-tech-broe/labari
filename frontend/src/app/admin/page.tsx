'use client'

import { useEffect, useRef, useState } from 'react'
import { createPost, deletePost, getPosts, getPresignedUrl, login, updatePost } from '@/lib/api'
import type { AuthState, Post } from '@/lib/types'

const AUTH_KEY = 'labari_auth'

function loadAuth(): AuthState | null {
  try {
    const raw = localStorage.getItem(AUTH_KEY)
    return raw ? JSON.parse(raw) : null
  } catch {
    return null
  }
}

function saveAuth(auth: AuthState) {
  localStorage.setItem(AUTH_KEY, JSON.stringify(auth))
}

function clearAuth() {
  localStorage.removeItem(AUTH_KEY)
}

// --- Login form ---

function LoginForm({ onLogin }: { onLogin: (auth: AuthState) => void }) {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setLoading(true)
    setError('')
    try {
      const auth = await login(email, password)
      onLogin(auth)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Login failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="max-w-sm mx-auto mt-20">
      <h1 className="text-2xl font-bold mb-8">Admin</h1>
      <form onSubmit={handleSubmit} className="space-y-4">
        <input
          type="email"
          placeholder="Email"
          value={email}
          onChange={e => setEmail(e.target.value)}
          required
          className="w-full px-4 py-2.5 bg-surface border border-dim rounded-lg focus:outline-none focus:border-[#444] text-sm"
        />
        <input
          type="password"
          placeholder="Password"
          value={password}
          onChange={e => setPassword(e.target.value)}
          required
          className="w-full px-4 py-2.5 bg-surface border border-dim rounded-lg focus:outline-none focus:border-[#444] text-sm"
        />
        {error && <p className="text-red-400 text-sm">{error}</p>}
        <button
          type="submit"
          disabled={loading}
          className="w-full py-2.5 bg-accent text-black font-semibold rounded-lg hover:bg-amber-400 transition-colors disabled:opacity-50"
        >
          {loading ? 'Signing in...' : 'Sign in'}
        </button>
      </form>
    </div>
  )
}

// --- Post editor ---

interface EditorProps {
  initial?: Post | null
  token: string
  onSave: () => void
  onCancel: () => void
}

function PostEditor({ initial, token, onSave, onCancel }: EditorProps) {
  const [title, setTitle] = useState(initial?.title ?? '')
  const [content, setContent] = useState(initial?.content ?? '')
  const [excerpt, setExcerpt] = useState(initial?.excerpt ?? '')
  const [coverImage, setCoverImage] = useState(initial?.cover_image ?? '')
  const [categoriesInput, setCategoriesInput] = useState((initial?.categories ?? []).join(', '))
  const [published, setPublished] = useState(initial?.published ?? false)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')
  const [uploading, setUploading] = useState(false)
  const fileRef = useRef<HTMLInputElement>(null)

  async function handleSave(e: React.FormEvent) {
    e.preventDefault()
    setSaving(true)
    setError('')
    try {
      const categories = categoriesInput.split(',').map(s => s.trim().toLowerCase()).filter(Boolean)
      const data = { title, content, excerpt, cover_image: coverImage, categories, published }
      if (initial) {
        await updatePost(initial.id, data, token)
      } else {
        await createPost(data, token)
      }
      onSave()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Save failed')
    } finally {
      setSaving(false)
    }
  }

  async function handleImageUpload(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0]
    if (!file) return
    setUploading(true)
    try {
      const { upload_url, public_url } = await getPresignedUrl(file.type, token)
      await fetch(upload_url, { method: 'PUT', body: file, headers: { 'Content-Type': file.type } })
      setCoverImage(public_url)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Upload failed')
    } finally {
      setUploading(false)
    }
  }

  return (
    <form onSubmit={handleSave} className="space-y-4 max-w-2xl">
      <div className="flex items-center justify-between mb-2">
        <h2 className="text-xl font-bold">{initial ? 'Edit post' : 'New post'}</h2>
        <button type="button" onClick={onCancel} className="text-sm text-muted hover:text-[var(--text)]">Cancel</button>
      </div>

      <input
        type="text"
        placeholder="Title"
        value={title}
        onChange={e => setTitle(e.target.value)}
        required
        className="w-full px-4 py-2.5 bg-surface border border-dim rounded-lg focus:outline-none focus:border-[#444] text-sm"
      />

      <textarea
        placeholder="Excerpt (optional)"
        value={excerpt}
        onChange={e => setExcerpt(e.target.value)}
        rows={2}
        className="w-full px-4 py-2.5 bg-surface border border-dim rounded-lg focus:outline-none focus:border-[#444] text-sm resize-none"
      />

      <textarea
        placeholder="Content (Markdown supported)"
        value={content}
        onChange={e => setContent(e.target.value)}
        required
        rows={16}
        className="w-full px-4 py-2.5 bg-surface border border-dim rounded-lg focus:outline-none focus:border-[#444] text-sm font-mono resize-y"
      />

      <input
        type="text"
        placeholder="Categories (comma-separated, e.g. aws, devops, terraform)"
        value={categoriesInput}
        onChange={e => setCategoriesInput(e.target.value)}
        className="w-full px-4 py-2.5 bg-surface border border-dim rounded-lg focus:outline-none focus:border-[#444] text-sm"
      />

      <div className="flex items-center gap-3">
        <input
          type="text"
          placeholder="Cover image URL"
          value={coverImage}
          onChange={e => setCoverImage(e.target.value)}
          className="flex-1 px-4 py-2.5 bg-surface border border-dim rounded-lg focus:outline-none focus:border-[#444] text-sm"
        />
        <button
          type="button"
          onClick={() => fileRef.current?.click()}
          disabled={uploading}
          className="px-4 py-2.5 bg-surface border border-dim rounded-lg text-sm hover:border-[#444] transition-colors disabled:opacity-50"
        >
          {uploading ? 'Uploading...' : 'Upload'}
        </button>
        <input ref={fileRef} type="file" accept="image/*" className="hidden" onChange={handleImageUpload} />
      </div>

      <label className="flex items-center gap-2 text-sm cursor-pointer">
        <input
          type="checkbox"
          checked={published}
          onChange={e => setPublished(e.target.checked)}
          className="accent-amber-500"
        />
        Publish now
      </label>

      {error && <p className="text-red-400 text-sm">{error}</p>}

      <button
        type="submit"
        disabled={saving}
        className="px-6 py-2.5 bg-accent text-black font-semibold rounded-lg hover:bg-amber-400 transition-colors disabled:opacity-50"
      >
        {saving ? 'Saving...' : 'Save post'}
      </button>
    </form>
  )
}

// --- Dashboard ---

export default function AdminPage() {
  const [auth, setAuth] = useState<AuthState | null>(null)
  const [posts, setPosts] = useState<Post[]>([])
  const [loading, setLoading] = useState(false)
  const [editing, setEditing] = useState<Post | null | 'new'>( null)

  useEffect(() => {
    setAuth(loadAuth())
  }, [])

  useEffect(() => {
    if (auth) loadPosts()
  }, [auth])

  async function loadPosts() {
    setLoading(true)
    try {
      setPosts(await getPosts())
    } finally {
      setLoading(false)
    }
  }

  function handleLogin(newAuth: AuthState) {
    saveAuth(newAuth)
    setAuth(newAuth)
  }

  function handleLogout() {
    clearAuth()
    setAuth(null)
    setPosts([])
  }

  async function handleDelete(id: string) {
    if (!auth || !confirm('Delete this post?')) return
    await deletePost(id, auth.token)
    setPosts(posts.filter(p => p.id !== id))
  }

  if (!auth) {
    return <LoginForm onLogin={handleLogin} />
  }

  if (editing === 'new' || (editing && typeof editing === 'object')) {
    return (
      <PostEditor
        initial={editing === 'new' ? null : editing}
        token={auth.token}
        onSave={() => { setEditing(null); loadPosts() }}
        onCancel={() => setEditing(null)}
      />
    )
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-2xl font-bold">Dashboard</h1>
          <p className="text-sm text-muted mt-1">Welcome, {auth.user.name}</p>
        </div>
        <div className="flex gap-3">
          <button
            onClick={() => setEditing('new')}
            className="px-4 py-2 bg-accent text-black font-semibold rounded-lg text-sm hover:bg-amber-400 transition-colors"
          >
            New post
          </button>
          <button
            onClick={handleLogout}
            className="px-4 py-2 bg-surface border border-dim rounded-lg text-sm hover:border-[#444] transition-colors"
          >
            Sign out
          </button>
        </div>
      </div>

      {loading && <p className="text-muted text-sm">Loading...</p>}

      {!loading && posts.length === 0 && (
        <p className="text-muted text-sm">No posts yet. Create your first one.</p>
      )}

      <div className="space-y-2">
        {posts.map(post => (
          <div
            key={post.id}
            className="flex items-center justify-between px-4 py-3 bg-surface border border-dim rounded-lg"
          >
            <div className="min-w-0 flex-1">
              <p className="font-medium truncate">{post.title}</p>
              <p className="text-xs text-muted mt-0.5">
                {post.published ? 'Published' : 'Draft'}
                {post.published_at && ` · ${new Date(post.published_at).toLocaleDateString()}`}
              </p>
            </div>
            <div className="flex gap-2 ml-4 shrink-0">
              <button
                onClick={() => setEditing(post)}
                className="px-3 py-1.5 text-xs bg-transparent border border-dim rounded hover:border-[#444] transition-colors"
              >
                Edit
              </button>
              <button
                onClick={() => handleDelete(post.id)}
                className="px-3 py-1.5 text-xs text-red-400 border border-transparent hover:border-red-900 rounded transition-colors"
              >
                Delete
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
