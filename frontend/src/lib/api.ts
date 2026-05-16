import type { Comment, Post, User } from './types'

const BASE_URL = process.env.NEXT_PUBLIC_API_URL || ''

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, {
    headers: { 'Content-Type': 'application/json', ...options.headers },
    ...options,
  })

  let data: unknown
  const ct = res.headers.get('content-type') ?? ''
  if (ct.includes('application/json')) {
    data = await res.json()
  } else {
    await res.text()
    if (!res.ok) throw new Error(`Request failed: ${res.status}`)
    return undefined as unknown as T
  }

  if (!res.ok) {
    throw new Error((data as Record<string, string>).error || `Request failed: ${res.status}`)
  }

  return data as T
}

function authHeaders(token: string) {
  return { Authorization: `Bearer ${token}` }
}

export async function getPosts(category?: string): Promise<Post[]> {
  const path = category ? `/posts?category=${encodeURIComponent(category)}` : '/posts'
  const data = await request<{ posts: Post[] }>(path)
  return data.posts
}

export async function searchPosts(q: string): Promise<Post[]> {
  const data = await request<{ posts: Post[] }>(`/search?q=${encodeURIComponent(q)}`)
  return data.posts
}

export async function getPost(id: string): Promise<Post> {
  const data = await request<{ post: Post }>(`/posts/${id}`)
  return data.post
}

export async function createPost(body: Partial<Post>, token: string): Promise<Post> {
  const data = await request<{ post: Post }>('/posts', {
    method: 'POST',
    body: JSON.stringify(body),
    headers: authHeaders(token),
  })
  return data.post
}

export async function updatePost(id: string, body: Partial<Post>, token: string): Promise<void> {
  await request(`/posts/${id}`, {
    method: 'PUT',
    body: JSON.stringify(body),
    headers: authHeaders(token),
  })
}

export async function deletePost(id: string, token: string): Promise<void> {
  await request(`/posts/${id}`, {
    method: 'DELETE',
    headers: authHeaders(token),
  })
}

export async function login(email: string, password: string): Promise<{ token: string; user: User }> {
  return request('/auth/login', {
    method: 'POST',
    body: JSON.stringify({ email, password }),
  })
}

export async function register(
  email: string,
  password: string,
  name: string,
): Promise<{ token: string; user: User }> {
  return request('/auth/register', {
    method: 'POST',
    body: JSON.stringify({ email, password, name }),
  })
}

export async function likePost(id: string): Promise<{ like_count: number }> {
  return request<{ like_count: number }>(`/posts/${id}/like`, { method: 'POST' })
}

export async function getComments(postId: string): Promise<Comment[]> {
  const data = await request<{ comments: Comment[] }>(`/posts/${postId}/comments`)
  return data.comments
}

export async function createComment(
  postId: string,
  body: { author_name: string; content: string },
): Promise<Comment> {
  return request<Comment>(`/posts/${postId}/comments`, {
    method: 'POST',
    body: JSON.stringify(body),
  })
}

export async function getPresignedUrl(
  fileType: string,
  token: string,
): Promise<{ upload_url: string; key: string; public_url: string }> {
  return request('/images/upload', {
    method: 'POST',
    body: JSON.stringify({ file_type: fileType }),
    headers: authHeaders(token),
  })
}
