/**
 * 知识库服务 - 处理与后端API的通信
 */

const API_BASE_URL = 'http://localhost:8000'

export interface KnowledgeItem {
  id: string
  title: string
  content: string
  category: string
  tags: string[]
  created_at: string
  similarity?: number
}

export interface KnowledgeStats {
  total_count: number
  total_size: number
  total_queries: number
  categories: string[]
}

export interface CreateKnowledgeRequest {
  title: string
  content: string
  category?: string
  tags?: string[]
}

export interface SearchKnowledgeRequest {
  query: string
  top_k?: number
}

export interface KnowledgeListResponse {
  items: KnowledgeItem[]
  total: number
  page: number
  size: number
}

export interface SearchKnowledgeResponse {
  results: KnowledgeItem[]
}

export interface CategoriesResponse {
  categories: string[]
}

export interface WebUrlImportRequest {
  url: string
  category?: string
  auto_add_to_knowledge?: boolean
}

export interface WebUrlImportResponse {
  success: boolean
  data: {
    title: string
    url: string
    content: string
    description: string
    domain: string
  }
  message: string
}

export class KnowledgeService {
  private apiUrl: string

  constructor(apiUrl: string = API_BASE_URL) {
    this.apiUrl = apiUrl
  }

  /**
   * 添加知识库条目
   */
  async addKnowledge(knowledge: CreateKnowledgeRequest): Promise<{ success: boolean; id: string; message: string }> {
    const response = await fetch(`${this.apiUrl}/api/knowledge`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(knowledge),
    })

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`)
    }

    const result = await response.json()
    return { success: result.success, ...result.data }
  }

  /**
   * 获取知识库列表
   */
  async getKnowledgeList(
    category?: string,
    page: number = 1,
    size: number = 20
  ): Promise<KnowledgeListResponse> {
    const params = new URLSearchParams({
      page: page.toString(),
      page_size: size.toString(),
    })

    if (category) {
      params.append('category', category)
    }

    const response = await fetch(`${this.apiUrl}/api/knowledge?${params}`)

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`)
    }

    const result = await response.json()
    return result.data
  }

  /**
   * 获取单个知识库条目
   */
  async getKnowledge(id: string): Promise<KnowledgeItem> {
    const response = await fetch(`${this.apiUrl}/api/knowledge/${id}`)

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`)
    }

    const result = await response.json()
    return result.data
  }

  /**
   * 更新知识库条目
   */
  async updateKnowledge(id: string, knowledge: CreateKnowledgeRequest): Promise<{ success: boolean; data: KnowledgeItem }> {
    const response = await fetch(`${this.apiUrl}/api/knowledge/${id}`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(knowledge),
    })

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`)
    }

    const result = await response.json()
    return { success: result.success, data: result.data }
  }

  /**
   * 删除知识库条目
   */
  async deleteKnowledge(id: string): Promise<{ success: boolean; message: string }> {
    const response = await fetch(`${this.apiUrl}/api/knowledge/${id}`, {
      method: 'DELETE',
    })

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`)
    }

    const result = await response.json()
    return { success: result.success, ...result.data }
  }

  /**
   * 批量删除知识库条目
   */
  async batchDeleteKnowledge(ids: string[]): Promise<{ success: boolean; deleted_count: number; message: string }> {
    const response = await fetch(`${this.apiUrl}/api/knowledge/batch-delete`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ ids }),
    })

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`)
    }

    const result = await response.json()
    return { success: result.success, ...result.data }
  }

  /**
   * 搜索知识库
   */
  async searchKnowledge(request: SearchKnowledgeRequest): Promise<SearchKnowledgeResponse> {
    const response = await fetch(`${this.apiUrl}/api/knowledge/search`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(request),
    })

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`)
    }

    const result = await response.json()
    return result.data
  }

  /**
   * 上传文件
   */
  async uploadFile(file: File): Promise<{ success: boolean; message: string; count?: number }> {
    const formData = new FormData()
    formData.append('file', file)

    const response = await fetch(`${this.apiUrl}/api/knowledge/upload`, {
      method: 'POST',
      body: formData,
    })

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`)
    }

    const result = await response.json()
    return { success: result.success, ...result.data }
  }

  /**
   * 获取统计信息
   */
  async getStats(): Promise<KnowledgeStats> {
    const response = await fetch(`${this.apiUrl}/api/knowledge/stats`)

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`)
    }

    const result = await response.json()
    return result.data
  }

  /**
   * 获取分类列表
   */
  async getCategories(): Promise<CategoriesResponse> {
    const response = await fetch(`${this.apiUrl}/api/knowledge/categories`)

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`)
    }

    const result = await response.json()
    return result.data
  }

  /**
   * 导入网页链接
   */
  async importWebUrl(request: WebUrlImportRequest): Promise<WebUrlImportResponse> {
    const response = await fetch(`${this.apiUrl}/api/knowledge/web`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(request),
    })

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`)
    }

    const result = await response.json()
    return result.data
  }

  /**
   * 健康检查
   */
  async healthCheck(): Promise<any> {
    const response = await fetch(`${this.apiUrl}/api/health`)

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`)
    }

    return response.json()
  }
} 