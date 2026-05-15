'use client'

import { useEffect, useState } from 'react'
import Link from 'next/link'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { getPost } from '@/lib/api'
import type { Post } from '@/lib/types'

function formatDate(iso: string | null) {
  if (!iso) return ''
  return new Date(iso).toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' })
}

export default function PostPage({ params }: { params: { slug: string } }) {
  const [post, setPost] = useState<Post | null>(null)
  const [loading, setLoading] = useState(true)
  const [notFound, setNotFound] = useState(false)

  useEffect(() => {
    // params.slug is the post ID — we use IDs in URLs since slugs aren't unique-enforced
    getPost(params.slug)
      .then(setPost)
      .catch(() => setNotFound(true))
      .finally(() => setLoading(false))
  }, [params.slug])

  if (loading) {
    return (
      <div className="animate-pulse space-y-4">
        <div className="h-8 bg-surface rounded w-2/3" />
        <div className="h-4 bg-surface rounded w-1/4" />
        <div className="h-64 bg-surface rounded" />
      </div>
    )
  }

  if (notFound || !post) {
    return (
      <div className="text-center py-20">
        <p className="text-2xl font-bold mb-2">Story not found</p>
        <p className="text-muted mb-6">This post may have been removed or the link is incorrect.</p>
        <Link href="/" className="text-accent hover:underline">Back to home</Link>
      </div>
    )
  }

  return (
    <article className="max-w-2xl mx-auto">
      <Link href="/" className="text-sm text-muted hover:text-accent transition-colors inline-block mb-8">
        &larr; All stories
      </Link>

      {post.cover_image && (
        <img
          src={post.cover_image}
          alt={post.title}
          className="w-full h-64 object-cover rounded-xl mb-8"
        />
      )}

      <h1 className="text-3xl font-bold leading-tight mb-3">{post.title}</h1>

      {post.published_at && (
        <time className="text-sm text-muted block mb-10">{formatDate(post.published_at)}</time>
      )}

      <div className="prose prose-invert prose-amber max-w-none">
        <ReactMarkdown remarkPlugins={[remarkGfm]}>
          {post.content}
        </ReactMarkdown>
      </div>
    </article>
  )
}
