export interface Post {
  id: string
  title: string
  slug: string
  content: string
  excerpt: string
  cover_image: string
  categories: string[]
  author_id: string
  published: boolean
  published_at: string | null
  created_at: string
  updated_at: string
}

export interface User {
  id: string
  email: string
  name: string
  role: string
}

export interface AuthState {
  token: string
  user: User
}
