'use client'

import { useEffect, useState } from 'react'
import { likePost } from '@/lib/api'

interface Props {
  postId: string
  initialCount: number
}

export default function LikeButton({ postId, initialCount }: Props) {
  const [count, setCount] = useState(initialCount)
  const [liked, setLiked] = useState(false)
  const [animating, setAnimating] = useState(false)

  useEffect(() => {
    setLiked(localStorage.getItem(`liked_${postId}`) === 'true')
  }, [postId])

  async function handleLike() {
    if (liked) return
    setAnimating(true)
    setTimeout(() => setAnimating(false), 300)
    try {
      const { like_count } = await likePost(postId)
      setCount(like_count)
      setLiked(true)
      localStorage.setItem(`liked_${postId}`, 'true')
    } catch {
      // silently ignore — count will sync on next load
    }
  }

  return (
    <button
      onClick={handleLike}
      disabled={liked}
      aria-label={liked ? 'You liked this' : 'Like this story'}
      className={`group flex items-center gap-2 px-4 py-2 rounded-full text-sm font-medium border transition-all duration-200 ${
        liked
          ? 'bg-red-500/10 border-red-500/30 text-red-400 cursor-default'
          : 'bg-surface border-dim text-muted hover:border-red-400/50 hover:text-red-400 cursor-pointer'
      }`}
    >
      <span className={`text-base transition-transform duration-300 ${animating ? 'scale-150' : liked ? 'scale-110' : 'scale-100'}`}>
        {liked ? '❤️' : '🤍'}
      </span>
      <span>{count} {count === 1 ? 'like' : 'likes'}</span>
    </button>
  )
}
