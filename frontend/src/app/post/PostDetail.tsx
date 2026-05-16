'use client'

import { useEffect, useState } from 'react'
import { useSearchParams } from 'next/navigation'
import Link from 'next/link'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { getPost } from '@/lib/api'
import type { Post } from '@/lib/types'
import LikeButton from '@/components/LikeButton'
import CommentSection from '@/components/CommentSection'

function formatDate(iso: string | null) {
  if (!iso) return ''
  return new Date(iso).toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' })
}

function gradientFromTitle(title: string) {
  const hue = title.charCodeAt(0) % 360
  return `linear-gradient(135deg, hsl(${hue},60%,20%), hsl(${(hue + 60) % 360},60%,15%))`
}

export default function PostDetail() {
  const searchParams = useSearchParams()
  const id = searchParams.get('id')
  const [post, setPost] = useState<Post | null>(null)
  const [loading, setLoading] = useState(true)
  const [notFound, setNotFound] = useState(false)

  useEffect(() => {
    if (!id) { setLoading(false); setNotFound(true); return }
    getPost(id)
      .then(setPost)
      .catch(() => setNotFound(true))
      .finally(() => setLoading(false))
  }, [id])

  if (loading) {
    return (
      <div className="max-w-2xl mx-auto animate-pulse space-y-6">
        <div className="h-4 bg-surface rounded w-16" />
        <div className="h-64 bg-surface rounded-xl" />
        <div className="h-8 bg-surface rounded w-3/4" />
        <div className="h-4 bg-surface rounded w-1/4" />
        <div className="space-y-3">
          <div className="h-4 bg-surface rounded" />
          <div className="h-4 bg-surface rounded w-5/6" />
          <div className="h-4 bg-surface rounded w-4/6" />
        </div>
      </div>
    )
  }

  if (notFound || !post) {
    return (
      <div className="text-center py-24">
        <p className="text-5xl mb-4">📭</p>
        <p className="text-2xl font-bold mb-2">Story not found</p>
        <p className="text-muted mb-6">This post may have been removed or the link is incorrect.</p>
        <Link href="/" className="text-accent hover:underline">← Back to home</Link>
      </div>
    )
  }

  return (
    <article className="max-w-2xl mx-auto">
      <Link href="/" className="text-sm text-muted hover:text-accent transition-colors inline-flex items-center gap-1 mb-8">
        ← All stories
      </Link>

      {post.cover_image ? (
        <img
          src={post.cover_image}
          alt={post.title}
          className="w-full h-72 object-cover rounded-xl mb-8"
        />
      ) : (
        <div
          className="w-full h-48 rounded-xl mb-8 flex items-center justify-center text-6xl font-bold text-white/10"
          style={{ background: gradientFromTitle(post.title) }}
        >
          {post.title.charAt(0).toUpperCase()}
        </div>
      )}

      {post.categories?.length > 0 && (
        <div className="flex flex-wrap gap-2 mb-4">
          {post.categories.map(cat => (
            <span key={cat} className="text-xs px-2.5 py-1 rounded-full bg-[#1a1a1a] border border-dim text-muted">
              {cat}
            </span>
          ))}
        </div>
      )}

      <h1 className="text-3xl sm:text-4xl font-bold leading-tight mb-3">{post.title}</h1>

      {post.published_at && (
        <time className="text-sm text-muted block mb-10">{formatDate(post.published_at)}</time>
      )}

      <div className="prose prose-invert prose-amber max-w-none">
        <ReactMarkdown remarkPlugins={[remarkGfm]}>
          {post.content}
        </ReactMarkdown>
      </div>

      <div className="mt-10 pt-8 border-t border-dim">
        <LikeButton postId={post.id} initialCount={post.like_count ?? 0} />
      </div>

      <CommentSection postId={post.id} />
    </article>
  )
}
