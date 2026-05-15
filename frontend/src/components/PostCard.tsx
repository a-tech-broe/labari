import Link from 'next/link'
import type { Post } from '@/lib/types'

function formatDate(iso: string | null) {
  if (!iso) return ''
  return new Date(iso).toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' })
}

function gradientFromTitle(title: string) {
  const hue = title.charCodeAt(0) % 360
  return `linear-gradient(135deg, hsl(${hue},60%,20%), hsl(${(hue + 60) % 360},60%,15%))`
}

export default function PostCard({ post }: { post: Post }) {
  return (
    <Link href={`/post?id=${post.id}`} className="group block">
      <article className="rounded-xl border border-dim bg-surface overflow-hidden hover:border-[#444] transition-all duration-200 hover:-translate-y-0.5 hover:shadow-xl hover:shadow-black/40">
        <div className="h-40 overflow-hidden">
          {post.cover_image ? (
            <img
              src={post.cover_image}
              alt={post.title}
              className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
            />
          ) : (
            <div
              className="w-full h-full flex items-center justify-center text-4xl font-bold text-white/20"
              style={{ background: gradientFromTitle(post.title) }}
            >
              {post.title.charAt(0).toUpperCase()}
            </div>
          )}
        </div>
        <div className="p-5">
          <h2 className="font-semibold text-lg leading-snug mb-2 group-hover:text-accent transition-colors">
            {post.title}
          </h2>
          <p className="text-sm text-muted line-clamp-2 mb-3">{post.excerpt}</p>
          <div className="flex items-center justify-between gap-2">
            <time className="text-xs text-muted">{formatDate(post.published_at)}</time>
            {post.categories?.length > 0 && (
              <div className="flex gap-1 flex-wrap justify-end">
                {post.categories.slice(0, 3).map(cat => (
                  <span key={cat} className="text-[10px] px-2 py-0.5 rounded-full bg-[#1a1a1a] border border-dim text-muted">
                    {cat}
                  </span>
                ))}
              </div>
            )}
          </div>
        </div>
      </article>
    </Link>
  )
}
