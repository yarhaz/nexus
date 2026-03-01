export interface SearchHit {
  id: string
  entity_type: string
  name: string
  description: string
  score: number
  tags: string[]
}

export interface SearchResponse {
  query: string
  total: number
  hits: SearchHit[]
}
