import { Suspense } from 'react'
import PostDetail from './PostDetail'

function LoadingSkeleton() {
  return (
    <div className="animate-pulse space-y-4">
      <div className="h-8 bg-surface rounded w-2/3" />
      <div className="h-4 bg-surface rounded w-1/4" />
      <div className="h-64 bg-surface rounded" />
    </div>
  )
}

export default function PostPage() {
  return (
    <Suspense fallback={<LoadingSkeleton />}>
      <PostDetail />
    </Suspense>
  )
}
