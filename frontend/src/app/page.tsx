'use client'

import { useEffect, useMemo, useState } from 'react'
import PostCard from '@/components/PostCard'
import { getPosts } from '@/lib/api'
import type { Post } from '@/lib/types'

function Skeleton() {
  return (
    <div className="rounded-xl border border-dim bg-surface overflow-hidden animate-pulse">
      <div className="h-40 bg-[#1a1a1a]" />
      <div className="p-5 space-y-3">
        <div className="h-5 bg-[#1a1a1a] rounded w-3/4" />
        <div className="h-4 bg-[#1a1a1a] rounded w-full" />
        <div className="h-4 bg-[#1a1a1a] rounded w-1/3" />
      </div>
    </div>
  )
}

export default function HomePage() {
  const [posts, setPosts] = useState<Post[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [search, setSearch] = useState('')
  const [activeCategory, setActiveCategory] = useState<string | null>(null)

  async function load() {
    setLoading(true)
    setError(null)
    try {
      setPosts(await getPosts())
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to load posts')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { load() }, [])

  const allCategories = useMemo(() => {
    const set = new Set<string>()
    posts.forEach(p => p.categories?.forEach(c => set.add(c)))
    return Array.from(set).sort()
  }, [posts])

  const filtered = useMemo(() => {
    let result = posts
    if (activeCategory) {
      result = result.filter(p => p.categories?.includes(activeCategory))
    }
    if (search.trim()) {
      const q = search.toLowerCase()
      result = result.filter(p =>
        p.title.toLowerCase().includes(q) ||
        p.excerpt?.toLowerCase().includes(q) ||
        p.categories?.some(c => c.includes(q))
      )
    }
    return result
  }, [posts, activeCategory, search])

  return (
    <div>
      <div className="mb-10">
        <h1 className="text-4xl font-bold mb-2">
          Labari<span className="text-accent">.</span>
        </h1>
        <p className="text-muted text-lg">Stories worth reading.</p>
      </div>

      {/* Search */}
      <div className="mb-6">
        <input
          type="search"
          placeholder="Search stories..."
          value={search}
          onChange={e => setSearch(e.target.value)}
          className="w-full sm:max-w-sm px-4 py-2.5 bg-surface border border-dim rounded-lg focus:outline-none focus:border-[#444] text-sm placeholder:text-muted"
        />
      </div>

      {/* Category filters */}
      {allCategories.length > 0 && (
        <div className="flex flex-wrap gap-2 mb-8">
          <button
            onClick={() => setActiveCategory(null)}
            className={`px-3 py-1 rounded-full text-xs font-medium transition-colors ${
              activeCategory === null
                ? 'bg-accent text-black'
                : 'bg-surface border border-dim text-muted hover:border-[#444]'
            }`}
          >
            All
          </button>
          {allCategories.map(cat => (
            <button
              key={cat}
              onClick={() => setActiveCategory(activeCategory === cat ? null : cat)}
              className={`px-3 py-1 rounded-full text-xs font-medium transition-colors ${
                activeCategory === cat
                  ? 'bg-accent text-black'
                  : 'bg-surface border border-dim text-muted hover:border-[#444]'
              }`}
            >
              {cat}
            </button>
          ))}
        </div>
      )}

      {loading && (
        <div className="grid gap-6 sm:grid-cols-2">
          {[1, 2, 3].map(i => <Skeleton key={i} />)}
        </div>
      )}

      {error && (
        <div className="text-center py-20">
          <p className="text-muted mb-4">{error}</p>
          <button
            onClick={load}
            className="px-4 py-2 bg-surface border border-dim rounded-lg hover:border-[#444] transition-colors text-sm"
          >
            Try again
          </button>
        </div>
      )}

      {!loading && !error && filtered.length === 0 && (
        <div className="text-center py-20 text-muted">
          {posts.length === 0 ? (
            <>
              <div className="text-4xl mb-4">&#9998;</div>
              <p>No stories yet. Check back soon.</p>
            </>
          ) : (
            <p>No stories match your search.</p>
          )}
        </div>
      )}

      {!loading && !error && filtered.length > 0 && (
        <div className="grid gap-6 sm:grid-cols-2">
          {filtered.map(post => <PostCard key={post.id} post={post} />)}
        </div>
      )}
    </div>
  )
}
