import { useState, useEffect, useRef } from 'react'
import { useRouter } from 'next/router'
import {
  Layout,
  Input,
  Button,
  message,
  Avatar,
  Typography,
  Spin,
  Card,
  Space
} from 'antd'
import {
  SendOutlined,
  LoadingOutlined,
  RobotOutlined,
  UserOutlined,
  ThunderboltOutlined,
  DownOutlined
} from '@ant-design/icons'
import { API_ENDPOINTS } from '../../config/api'

const { Content } = Layout
const { Text } = Typography

interface Message {
  id: string
  type: 'user' | 'assistant'
  content: string
  timestamp: Date
}

interface ParsedMessage {
  think?: string
  content: string
}

interface Bot {
  id: string
  name: string
  description: string
  avatar: string
  position: string
  size: string
  primary_color: string
  greeting_message: string
  knowledge_base_enabled: boolean
  created_at: string
  embed_url: string
}

export default function BotEmbedPage() {
  const router = useRouter()
  const { id: botId } = router.query
  const messagesEndRef = useRef<HTMLDivElement>(null)

  const [bot, setBot] = useState<Bot | null>(null)
  const [messages, setMessages] = useState<Message[]>([])
  const [inputMessage, setInputMessage] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [botLoading, setBotLoading] = useState(true)
  const [conversationId, setConversationId] = useState<string | null>(null)
  
  // 添加think部分展开/折叠状态
  const [expandedThinkSections, setExpandedThinkSections] = useState<Set<string>>(new Set())

  // 解析消息内容，分离think部分和正式回复
  const parseMessageContent = (content: string): ParsedMessage => {
    // 匹配<think>...</think>标签
    const thinkRegex = /<think>([\s\S]*?)<\/think>/i
    const thinkMatch = content.match(thinkRegex)
    
    if (thinkMatch) {
      const think = thinkMatch[1].trim()
      const mainContent = content.replace(thinkRegex, '').trim()
      return { think, content: mainContent }
    }
    
    return { content }
  }

  // 切换think部分展开状态
  const toggleThinkSection = (messageId: string) => {
    const newExpanded = new Set(expandedThinkSections)
    if (newExpanded.has(messageId)) {
      newExpanded.delete(messageId)
    } else {
      newExpanded.add(messageId)
    }
    setExpandedThinkSections(newExpanded)
  }

  // 渲染消息组件
  const renderMessage = (msg: Message) => {
    const parsedMessage = parseMessageContent(msg.content)
    const isThinkExpanded = expandedThinkSections.has(msg.id)
    
    return (
      <div
        key={msg.id}
        style={{
          display: 'flex',
          marginBottom: '16px',
          justifyContent: msg.type === 'user' ? 'flex-end' : 'flex-start',
          alignItems: 'flex-start',
          gap: '8px'
        }}
      >
        {/* 头像 */}
        {msg.type === 'assistant' && (
          <Avatar
            size={32}
            src={bot?.avatar}
            icon={<RobotOutlined />}
            style={{ 
              background: bot?.primary_color || '#1890ff',
              flexShrink: 0
            }}
          />
        )}
        
        <div
          style={{
            maxWidth: '70%',
            borderRadius: '12px',
            boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
            overflow: 'hidden'
          }}
        >
          {/* Think部分 - 仅对助手消息且有think内容时显示 */}
          {msg.type === 'assistant' && parsedMessage.think && (
            <div
              style={{
                background: '#f8f9fa',
                border: '1px solid #e9ecef',
                borderBottom: isThinkExpanded ? '1px solid #e9ecef' : 'none'
              }}
            >
              <div
                onClick={() => toggleThinkSection(msg.id)}
                style={{
                  padding: '8px 12px',
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  background: isThinkExpanded ? '#e9ecef' : 'transparent',
                  transition: 'background-color 0.2s'
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                  <ThunderboltOutlined style={{ color: '#6c757d', fontSize: '12px' }} />
                  <span style={{ fontSize: '12px', color: '#6c757d', fontWeight: '500' }}>
                    思考过程
                  </span>
                </div>
                <DownOutlined 
                  style={{ 
                    color: '#6c757d', 
                    fontSize: '10px',
                    transform: isThinkExpanded ? 'rotate(180deg)' : 'rotate(0deg)',
                    transition: 'transform 0.2s'
                  }} 
                />
              </div>
              
              {isThinkExpanded && (
                <div
                  style={{
                    padding: '12px',
                    fontSize: '13px',
                    color: '#495057',
                    lineHeight: '1.5',
                    whiteSpace: 'pre-wrap',
                    background: '#fff',
                    borderTop: '1px solid #e9ecef'
                  }}
                >
                  {parsedMessage.think}
                </div>
              )}
            </div>
          )}
          
          {/* 主要内容 */}
          <div
            style={{
              padding: '12px 16px',
              background: msg.type === 'user' ? (bot?.primary_color || '#1890ff') : '#f0f0f0',
              color: msg.type === 'user' ? '#fff' : '#000',
              whiteSpace: 'pre-wrap',
              ...(msg.type === 'assistant' && msg.content === '正在思考中...' ? {
                display: 'flex',
                alignItems: 'center',
                gap: '8px'
              } : {})
            }}
          >
            {/* 加载动画（仅在助手消息且内容为"正在思考中..."时显示） */}
            {msg.type === 'assistant' && msg.content === '正在思考中...' && (
              <>
                <LoadingOutlined 
                  style={{ 
                    color: bot?.primary_color || '#1890ff', 
                    fontSize: '16px'
                  }} 
                />
                <span style={{ fontSize: '14px', color: '#666' }}>
                  正在思考中...
                </span>
              </>
            )}
            
            {/* 普通消息内容 */}
            {!(msg.type === 'assistant' && msg.content === '正在思考中...') && (
              parsedMessage.content || msg.content
            )}
          </div>
        </div>
        
        {/* 用户头像 */}
        {msg.type === 'user' && (
          <Avatar
            size={32}
            icon={<UserOutlined />}
            style={{ 
              background: '#666',
              flexShrink: 0
            }}
          />
        )}
      </div>
    )
  }

  // 滚动到底部
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  // 加载机器人信息
  useEffect(() => {
    const loadBot = async () => {
      if (!botId || typeof botId !== 'string') return

      if (bot) return // 已经加载过了

      try {
        setBotLoading(true)
        const response = await fetch(`${API_ENDPOINTS.BOTS}/${botId}`)
        const data = await response.json()
        
        if (data.success && data.data) {
          setBot(data.data)
          // 添加机器人的欢迎消息
          const welcomeMessage: Message = {
            id: 'welcome',
            type: 'assistant',
            content: data.data.greeting_message || '您好！我是您的智能助手，有什么可以帮助您的吗？',
            timestamp: new Date()
          }
          setMessages([welcomeMessage])
        } else {
          message.error('机器人不存在或已被删除')
        }
      } catch (error) {
        console.error('获取机器人信息失败:', error)
        message.error('获取机器人信息失败')
      } finally {
        setBotLoading(false)
      }
    }

    loadBot()
  }, [botId, bot])

  const sendMessage = async () => {
    if (!inputMessage.trim() || !bot || isLoading) return

    setIsLoading(true)
    
    const userMessage: Message = {
      id: Date.now().toString(),
      type: 'user',
      content: inputMessage,
      timestamp: new Date()
    }

    // 立即添加用户消息
    setMessages(prev => [...prev, userMessage])

    // 添加助手消息占位符 - 显示"正在思考中..."状态
    const assistantMessageId = Date.now().toString() + '-assistant'
    const assistantMessage: Message = {
      id: assistantMessageId,
      type: 'assistant',
      content: '正在思考中...',
      timestamp: new Date()
    }

    // 立即添加"正在思考中..."的助手消息
    setMessages(prev => [...prev, assistantMessage])

    try {
      const response = await fetch(API_ENDPOINTS.BOT_CHAT, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          message: inputMessage,
          bot_id: bot.id,
          stream: true // 添加流式标识
        })
      })

      if (!response.ok) {
        throw new Error('网络请求失败')
      }

      if (!response.body) {
        throw new Error('响应体为空')
      }

      const reader = response.body.getReader()
      const decoder = new TextDecoder()
      let assistantResponse = ''

      // 读取流式响应
      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        const chunk = decoder.decode(value, { stream: true })
        const lines = chunk.split('\n')

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const data = line.slice(6)
            if (data === '[DONE]') continue
            
            try {
              const parsed = JSON.parse(data)
              if (parsed.content) {
                assistantResponse += parsed.content
                
                // 实时更新助手消息内容
                setMessages(prev => 
                  prev.map(msg => 
                    msg.id === assistantMessageId 
                      ? { ...msg, content: assistantResponse }
                      : msg
                  )
                )
              }
            } catch (e) {
              // 忽略解析错误
            }
          }
        }
      }

      // 如果没有收到任何内容，使用API的fallback逻辑
      if (!assistantResponse.trim()) {
        // 调用非流式API作为fallback
        const fallbackResponse = await fetch(API_ENDPOINTS.BOT_CHAT, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            message: inputMessage,
            bot_id: bot.id
          })
        })

        const fallbackData = await fallbackResponse.json()
        
        if (fallbackData.success) {
          assistantResponse = fallbackData.data.response
          
          setMessages(prev => 
            prev.map(msg => 
              msg.id === assistantMessageId 
                ? { ...msg, content: assistantResponse }
                : msg
            )
          )
        }
      }

    } catch (error) {
      console.error('发送消息失败:', error)
      
      // 错误时用错误消息替换"正在思考中..."
      setMessages(prev => 
        prev.map(msg => 
          msg.id === assistantMessageId 
            ? { ...msg, content: '抱歉，我暂时无法回答您的问题，请稍后再试。' }
            : msg
        )
      )
    } finally {
      setIsLoading(false)
      setInputMessage('')
    }
  }

  if (botLoading) {
    return (
      <div style={{ 
        height: '100vh', 
        display: 'flex', 
        alignItems: 'center', 
        justifyContent: 'center',
        background: '#f5f5f5'
      }}>
        <Spin size="large" />
      </div>
    )
  }

  if (!bot) {
    return (
      <div style={{ 
        height: '100vh', 
        display: 'flex', 
        alignItems: 'center', 
        justifyContent: 'center',
        background: '#f5f5f5'
      }}>
        <Card>
          <Text type="secondary">机器人不存在或已被删除</Text>
        </Card>
      </div>
    )
  }

  return (
    <Layout style={{ height: '100vh', background: '#f5f5f5' }}>
      <Content style={{ display: 'flex', flexDirection: 'column' }}>
        {/* 机器人头部信息 */}
        <div style={{
          padding: '16px 20px',
          background: bot.primary_color || '#1890ff',
          color: 'white',
          display: 'flex',
          alignItems: 'center',
          boxShadow: '0 2px 8px rgba(0,0,0,0.1)'
        }}>
          <Avatar 
            src={bot.avatar} 
            icon={<RobotOutlined />}
            size={40}
            style={{ marginRight: '12px' }}
          />
          <div>
            <div style={{ fontSize: '16px', fontWeight: 'bold' }}>
              {bot.name}
            </div>
            <div style={{ fontSize: '12px', opacity: 0.9 }}>
              {bot.description}
            </div>
          </div>
        </div>

        {/* 消息区域 */}
        <div style={{
          flex: 1,
          overflow: 'auto',
          padding: '16px',
          background: '#fff'
        }}>
          {messages.map((msg) => renderMessage(msg))}
          <div ref={messagesEndRef} />
        </div>

        {/* 输入区域 */}
        <div style={{
          padding: '16px 20px',
          borderTop: '1px solid #f0f0f0',
          background: '#fff',
          display: 'flex',
          gap: '8px'
        }}>
          <Input
            value={inputMessage}
            onChange={(e) => setInputMessage(e.target.value)}
            placeholder="请输入您的问题..."
            onPressEnter={sendMessage}
            disabled={isLoading}
            style={{ flex: 1 }}
          />
          <Button
            type="primary"
            icon={<SendOutlined />}
            onClick={sendMessage}
            loading={isLoading}
            disabled={!inputMessage.trim()}
            style={{ background: bot.primary_color, borderColor: bot.primary_color }}
          >
            发送
          </Button>
        </div>
      </Content>
    </Layout>
  )
} 