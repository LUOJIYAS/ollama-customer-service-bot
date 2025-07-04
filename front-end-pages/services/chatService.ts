/**
 * 聊天服务类
 * 处理与后端智能客服API的通信
 * 支持Ollama 0.9.3新API格式
 */

export interface ChatMessage {
  role: 'user' | 'assistant' | 'system'
  content: string
  timestamp?: number
}

export interface StreamChunk {
  content?: string
  type: 'chunk' | 'done' | 'error'
  full_response?: string
  relevant_docs?: any[]
  error?: string
}

export interface ChatResponse {
  response: string
  relevant_docs?: any[]
  model?: string
  timestamp?: string
}

export interface HealthStatus {
  status: 'healthy' | 'unhealthy'
  ollama_connected?: boolean
  available_models?: number
  running_models?: number
  chat_model?: string
  embedding_model?: string
  error?: string
  timestamp?: string
}

export class ChatService {
  private baseUrl = '/api'

  /**
   * 发送消息并接收流式响应
   * @param message 用户消息
   * @param history 对话历史
   * @param onChunk 接收到数据块时的回调函数
   * @param onComplete 完成时的回调函数
   */
  async sendMessage(
    message: string, 
    history: ChatMessage[] = [],
    onChunk: (chunk: string) => void,
    onComplete?: (fullResponse: string, relevantDocs?: any[]) => void
  ): Promise<void> {
    try {
      const response = await fetch(`${this.baseUrl}/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ 
          message,
          history: history.map(msg => ({ role: msg.role, content: msg.content }))
        }),
      })

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      const reader = response.body?.getReader()
      if (!reader) {
        throw new Error('无法获取响应流')
      }

      const decoder = new TextDecoder()
      let fullResponse = ''

      while (true) {
        const { done, value } = await reader.read()
        
        if (done) break

        const chunk = decoder.decode(value, { stream: true })
        const lines = chunk.split('\n')

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data: StreamChunk = JSON.parse(line.slice(6))
              
              if (data.type === 'chunk' && data.content) {
                fullResponse += data.content
                onChunk(data.content)
              }
              
              if (data.type === 'done') {
                onComplete?.(data.full_response || fullResponse, data.relevant_docs)
                return
              }
              
              if (data.type === 'error' && data.error) {
                throw new Error(data.error)
              }
            } catch (parseError) {
              // 忽略解析错误，继续处理下一行
              console.warn('解析SSE数据失败:', parseError)
            }
          }
        }
      }
    } catch (error) {
      console.error('发送消息失败:', error)
      throw error
    }
  }

  /**
   * 发送简单的非流式消息
   * @param message 用户消息
   * @param history 对话历史
   */
  async sendSimpleMessage(
    message: string, 
    history: ChatMessage[] = []
  ): Promise<ChatResponse> {
    try {
      const response = await fetch(`${this.baseUrl}/chat/simple`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ 
          message,
          history: history.map(msg => ({ role: msg.role, content: msg.content }))
        }),
      })

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      return await response.json()
    } catch (error) {
      console.error('发送简单消息失败:', error)
      throw error
    }
  }

  /**
   * 检查服务健康状态
   */
  async checkHealth(): Promise<boolean> {
    try {
      const response = await fetch(`${this.baseUrl.replace('/api', '')}/`)
      return response.ok
    } catch (error) {
      console.error('健康检查失败:', error)
      return false
    }
  }

  /**
   * 获取详细健康状态
   */
  async getHealthStatus(): Promise<HealthStatus> {
    try {
      const response = await fetch(`${this.baseUrl}/health`)
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      return await response.json()
    } catch (error) {
      console.error('获取健康状态失败:', error)
      return {
        status: 'unhealthy',
        error: error instanceof Error ? error.message : 'Unknown error'
      }
    }
  }

  /**
   * 创建聊天消息对象
   */
  createMessage(role: 'user' | 'assistant' | 'system', content: string): ChatMessage {
    return {
      role,
      content,
      timestamp: Date.now()
    }
  }

  /**
   * 格式化消息历史为显示用
   */
  formatHistory(messages: ChatMessage[]): string {
    return messages
      .map(msg => `${msg.role === 'user' ? '用户' : '助手'}: ${msg.content}`)
      .join('\n\n')
  }
} 