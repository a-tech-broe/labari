import PostPageClient from './PostPageClient'

export function generateStaticParams() {
  return []
}

export default function PostPage({ params }: { params: { slug: string } }) {
  return <PostPageClient slug={params.slug} />
}
