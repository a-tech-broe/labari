'use client'

import { useEffect, useState } from 'react'
import { createComment, getComments } from '@/lib/api'
import type { Comment } from '@/lib/types'

function timeAgo(iso: string) {
  const diff = Date.now() - new Date(iso).getTime()
  const mins = Math.floor(diff / 60000)
  if (mins < 1) return 'just now'
  if (mins < 60) return `${mins}m ago`
  const hrs = Math.floor(mins / 60)
  if (hrs < 24) return `${hrs}h ago`
  const days = Math.floor(hrs / 24)
  if (days < 30) return `${days}d ago`
  return new Date(iso).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
}

function Avatar({ name }: { name: string }) {
  const initials = name.split(' ').map(w => w[0]).join('').slice(0, 2).toUpperCase()
  const hue = name.charCodeAt(0) % 360
  return (
    <div
      className="w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold text-white shrink-0"
      style={{ background: `hsl(${hue},50%,35%)` }}
    >
      {initials}
    </div>
  )
}

export default function CommentSection({ postId }: { postId: string }) {
  const [comments, setComments] = useState<Comment[]>([])
  const [loading, setLoading] = useState(true)
  const [name, setName] = useState('')
  const [content, setContent] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState(false)

  useEffect(() => {
    getComments(postId)
      .then(setComments)
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [postId])

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setSubmitting(true)
    setError('')
    setSuccess(false)
    try {
      const comment = await createComment(postId, { author_name: name.trim(), content: content.trim() })
      setComments(prev => [...prev, comment])
      setContent('')
      setSuccess(true)
      setTimeout(() => setSuccess(false), 3000)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to post comment')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <section className="mt-16 border-t border-dim pt-10">
      <h2 className="text-lg font-semibold mb-6">
        {loading ? 'Comments' : `${comments.length} ${comments.length === 1 ? 'comment' : 'comments'}`}
      </h2>

      {/* Comment list */}
      {loading ? (
        <div className="space-y-3 mb-10">
          {[1, 2].map(i => <div key={i} className="animate-pulse h-16 bg-surface rounded-lg" />)}
        </div>
      ) : comments.length > 0 ? (
        <div className="space-y-4 mb-10">
          {comments.map(c => (
            <div key={c.id} className="flex gap-3">
              <Avatar name={c.author_name} />
              <div className="flex-1 min-w-0">
                <div className="flex items-baseline gap-2 mb-1">
                  <span className="text-sm font-medium">{c.author_name}</span>
                  <span className="text-xs text-muted">{timeAgo(c.created_at)}</span>
                </div>
                <p className="text-sm text-muted leading-relaxed whitespace-pre-wrap">{c.content}</p>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <p className="text-muted text-sm mb-10">No comments yet. Be the first to share your thoughts.</p>
      )}

      {/* Comment form */}
      <form onSubmit={handleSubmit} className="space-y-3">
        <p className="text-xs text-muted uppercase tracking-widest font-medium">Leave a comment</p>
        <input
          type="text"
          placeholder="Your name"
          value={name}
          onChange={e => setName(e.target.value)}
          required
          maxLength={80}
          className="w-full px-4 py-2.5 bg-surface border border-dim rounded-lg focus:outline-none focus:border-[#555] text-sm transition-colors"
        />
        <textarea
          placeholder="Share your thoughts..."
          value={content}
          onChange={e => setContent(e.target.value)}
          required
          rows={4}
          maxLength={2000}
          className="w-full px-4 py-2.5 bg-surface border border-dim rounded-lg focus:outline-none focus:border-[#555] text-sm resize-none transition-colors"
        />
        <div className="flex items-center gap-3">
          <button
            type="submit"
            disabled={submitting}
            className="px-5 py-2.5 bg-accent text-black font-semibold rounded-lg text-sm hover:bg-amber-400 transition-colors disabled:opacity-50"
          >
            {submitting ? 'Posting...' : 'Post comment'}
          </button>
          {error && <p className="text-red-400 text-sm">{error}</p>}
          {success && <p className="text-green-400 text-sm">Comment posted!</p>}
        </div>
      </form>
    </section>
  )
}
