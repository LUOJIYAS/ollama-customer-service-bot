import { useState, useEffect } from 'react'
import {
  Layout,
  Card,
  Input,
  Button,
  message,
  Space,
  Typography,
  Row,
  Col,
  Statistic,
  Upload,
  Modal,
  Form,
  Avatar,
  Divider,
  Popconfirm,
  Select,
  Checkbox,
  Spin,
  Tag,
  Dropdown,
  Menu,
  Collapse
} from 'antd'
import {
  PlusOutlined,
  SearchOutlined,
  UploadOutlined,
  EditOutlined,
  LinkOutlined,
  MessageOutlined,
  FileTextOutlined,
  RobotOutlined,
  UserOutlined,
  LoadingOutlined,
  DeleteOutlined,
  ClearOutlined,
  MenuOutlined,
  DownOutlined,
  FileOutlined,
  GlobalOutlined,
  BulbOutlined,
  CodeOutlined,
  SettingOutlined,
  CloseOutlined,
  CloudUploadOutlined,
  BookOutlined,
  DatabaseOutlined,
  WechatOutlined,
  ThunderboltOutlined
} from '@ant-design/icons'
import { API_ENDPOINTS, getBotEmbedCode, getBotPageUrl } from '../config/api'

const { Header, Content, Sider } = Layout
const { Title, Text, Paragraph } = Typography
const { Search } = Input
const { TextArea } = Input
const { Panel } = Collapse

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

interface ChatSession {
  id: string
  title: string
  messages: Message[]
  createdAt: Date
  lastMessageAt: Date
}

interface Stats {
  monthlyQuestions: number
  maxMonthlyQuestions: number
  knowledgeSize: number
  maxKnowledgeSize: number
}

interface CodingRule {
  id: string
  title: string
  description: string
  language: string
  category: string
  content: string
  example: string
  tags: string[]
  file_name?: string
  created_at: string
  updated_at: string
}

interface Bot {
  id: string
  name: string
  description: string
  avatar: string
  position: 'bottom-right' | 'bottom-left' | 'top-right' | 'top-left'
  size: 'small' | 'medium' | 'large'
  primary_color: string
  greeting_message: string
  knowledge_base_enabled: boolean
  created_at: string
  embed_url: string
}

export default function Home() {
  // 添加CSS动画样式
  const addSpinAnimation = () => {
    if (typeof document !== 'undefined' && !document.getElementById('spin-animation')) {
      const style = document.createElement('style')
      style.id = 'spin-animation'
      style.textContent = `
        @keyframes spin {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }
        
        @keyframes pulse {
          0%, 100% { opacity: 1; }
          50% { opacity: 0.5; }
        }
      `
      document.head.appendChild(style)
    }
  }

  // 确保在组件挂载时添加动画样式并加载历史记录
  useEffect(() => {
    addSpinAnimation()
    
    // 加载历史聊天记录
    const savedSessions = loadChatSessionsFromStorage()
    if (savedSessions.length > 0) {
      setChatSessions(savedSessions)
      // 设置最近的会话为当前会话
      const mostRecentSession = savedSessions.sort((a, b) => 
        new Date(b.lastMessageAt).getTime() - new Date(a.lastMessageAt).getTime()
      )[0]
      setCurrentSessionId(mostRecentSession.id)
    }
    
    // 加载机器人列表
    fetchBotList()
  }, [])
  const [activeView, setActiveView] = useState('dashboard')
  const [stats, setStats] = useState<Stats>({
    monthlyQuestions: 0,
    maxMonthlyQuestions: 30,
    knowledgeSize: 0,
    maxKnowledgeSize: 30
  })
  const [chatSessions, setChatSessions] = useState<ChatSession[]>([])
  const [currentSessionId, setCurrentSessionId] = useState<string | null>(null)
  const [inputMessage, setInputMessage] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [chatModalVisible, setChatModalVisible] = useState(false)
  const [uploadModalVisible, setUploadModalVisible] = useState(false)
  const [textModalVisible, setTextModalVisible] = useState(false)
  const [linkModalVisible, setLinkModalVisible] = useState(false)

  // 编码规则相关状态
  const [codingRules, setCodingRules] = useState<CodingRule[]>([])
  const [selectedCodingRule, setSelectedCodingRule] = useState<CodingRule | null>(null)
  const [applyingRule, setApplyingRule] = useState(false)

  // 机器人创建相关状态
  const [botCreateModalVisible, setBotCreateModalVisible] = useState(false)
  const [botList, setBotList] = useState<Bot[]>([])
  const [creatingBot, setCreatingBot] = useState(false)
  const [botForm] = Form.useForm()

  // 机器人编辑相关状态
  const [botEditModalVisible, setBotEditModalVisible] = useState(false)
  const [editingBot, setEditingBot] = useState<Bot | null>(null)
  const [updatingBot, setUpdatingBot] = useState(false)
  const [botDetailsModalVisible, setBotDetailsModalVisible] = useState(false)
  const [selectedBot, setSelectedBot] = useState<Bot | null>(null)
  const [botEditForm] = Form.useForm()

  const [form] = Form.useForm()

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
        }}
      >
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
              background: msg.type === 'user' ? '#1890ff' : '#f0f0f0',
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
                    color: '#1890ff', 
                    fontSize: '16px',
                    animation: 'spin 1s linear infinite' 
                  }} 
                />
                <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
                  <span style={{ fontSize: '14px', color: '#666', fontWeight: '500' }}>
                    正在思考中...
                  </span>
                  <span style={{ fontSize: '12px', color: '#999' }}>
                    正在匹配知识库并生成回答
                  </span>
                </div>
              </>
            )}
            
            {/* 普通消息内容 */}
            {!(msg.type === 'assistant' && msg.content === '正在思考中...') && (
              parsedMessage.content || msg.content
            )}
          </div>
        </div>
      </div>
    )
  }

  // 获取当前会话
  const getCurrentSession = (): ChatSession | null => {
    return chatSessions.find(session => session.id === currentSessionId) || null
  }

  // 获取当前会话的消息
  const getCurrentMessages = (): Message[] => {
    return getCurrentSession()?.messages || []
  }

  // 创建新的聊天会话
  const createNewSession = (): string => {
    const newSessionId = Date.now().toString()
    const newSession: ChatSession = {
      id: newSessionId,
      title: `对话 ${chatSessions.length + 1}`,
      messages: [],
      createdAt: new Date(),
      lastMessageAt: new Date()
    }
    setChatSessions(prev => {
      const newSessions = [...prev, newSession]
      // 保存到本地存储
      saveChatSessionsToStorage(newSessions)
      return newSessions
    })
    setCurrentSessionId(newSessionId)
    return newSessionId
  }

  // 清除所有聊天记录
  const clearAllChatHistory = () => {
    setChatSessions([])
    setCurrentSessionId(null)
    try {
      localStorage.removeItem('chatSessions')
      message.success('聊天记录已清除')
    } catch (error) {
      console.error('清除聊天记录失败:', error)
      message.error('清除聊天记录失败')
    }
  }

  // 删除单个会话
  const deleteSession = (sessionId: string) => {
    setChatSessions(prev => {
      const newSessions = prev.filter(session => session.id !== sessionId)
      // 保存到本地存储
      saveChatSessionsToStorage(newSessions)
      
      // 如果删除的是当前会话，清除当前会话ID
      if (sessionId === currentSessionId) {
        setCurrentSessionId(newSessions.length > 0 ? newSessions[0].id : null)
      }
      
      return newSessions
    })
  }

  // 保存会话到本地存储
  const saveChatSessionsToStorage = (sessions: ChatSession[]) => {
    try {
      localStorage.setItem('chatSessions', JSON.stringify(sessions))
    } catch (error) {
      console.error('保存聊天记录失败:', error)
    }
  }

  // 从本地存储读取会话
  const loadChatSessionsFromStorage = (): ChatSession[] => {
    try {
      const stored = localStorage.getItem('chatSessions')
      if (stored) {
        const sessions = JSON.parse(stored)
        // 转换日期字符串为Date对象
        return sessions.map((session: any) => ({
          ...session,
          createdAt: new Date(session.createdAt),
          lastMessageAt: new Date(session.lastMessageAt),
          messages: session.messages.map((msg: any) => ({
            ...msg,
            timestamp: new Date(msg.timestamp)
          }))
        }))
      }
    } catch (error) {
      console.error('读取聊天记录失败:', error)
    }
    return []
  }

  // 更新会话消息
  const updateSessionMessages = (sessionId: string, messages: Message[]) => {
    setChatSessions(prev => {
      const newSessions = prev.map(session => 
        session.id === sessionId 
          ? { ...session, messages, lastMessageAt: new Date() }
          : session
      )
      // 保存到本地存储
      saveChatSessionsToStorage(newSessions)
      return newSessions
    })
  }

  // 更新会话标题
  const updateSessionTitle = (sessionId: string, title: string) => {
    setChatSessions(prev => {
      const newSessions = prev.map(session => 
        session.id === sessionId 
          ? { ...session, title }
          : session
      )
      // 保存到本地存储
      saveChatSessionsToStorage(newSessions)
      return newSessions
    })
  }

  useEffect(() => {
    loadChatSessionsFromStorage()
    fetchCodingRules()
    fetchBotList()
  }, [])

  const fetchStats = async () => {
    try {
      const response = await fetch(API_ENDPOINTS.KNOWLEDGE_STATS)
      const data = await response.json()
      setStats({
        monthlyQuestions: data.monthly_questions || 0,
        maxMonthlyQuestions: data.max_monthly_questions || 1000,
        knowledgeSize: data.knowledge_size || 0,
        maxKnowledgeSize: data.max_knowledge_size || 100
      })
    } catch (error) {
      console.error('获取统计信息失败:', error)
    }
  }

  const handleFileUpload = async (info: any) => {
    const { status } = info.file
    if (status === 'done') {
      message.success(`${info.file.name} 文件上传成功`)
      fetchStats()
    } else if (status === 'error') {
      message.error(`${info.file.name} 文件上传失败`)
    }
  }

  const handleTextSubmit = async (values: any) => {
    try {
      const response = await fetch(API_ENDPOINTS.KNOWLEDGE_ADD, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          title: values.title,
          content: values.content,
          category: values.category || 'manual'
        })
      })

      const data = await response.json()
      if (data.success) {
        message.success('知识添加成功！')
        setTextModalVisible(false)
        form.resetFields()
      } else {
        message.error(data.message || '添加失败')
      }
    } catch (error) {
      console.error('文本提交失败:', error)
      message.error('提交失败')
    }
  }

  const handleLinkSubmit = async (values: any) => {
    try {
      const response = await fetch(API_ENDPOINTS.WEB_PARSE, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          url: values.url,
          category: values.category || 'web_content',
          auto_add: values.auto_add !== false
        })
      })

      const data = await response.json()
      if (data.success) {
        message.success('网页解析成功！')
        setLinkModalVisible(false)
        form.resetFields()
      } else {
        message.error(data.message || '解析失败')
      }
    } catch (error) {
      console.error('链接提交失败:', error)
      message.error('解析失败')
    }
  }

  const startChat = () => {
    // 如果没有当前会话，创建一个新会话
    if (!currentSessionId) {
      createNewSession()
    }
    setChatModalVisible(true)
    
    // 加载编码规则列表
    fetchCodingRules()
  }

  const sendMessage = async () => {
    if (!inputMessage.trim() || isLoading) return

    setIsLoading(true)
    
    // 如果没有当前会话，创建新会话
    const sessionId = currentSessionId || createNewSession()
    
    const userMessage: Message = {
      id: Date.now().toString(),
      type: 'user',
      content: inputMessage,
      timestamp: new Date()
    }

    // 获取当前会话的消息
    const currentMessages = getCurrentMessages()
    const newMessages = [...currentMessages, userMessage]
    
    // 立即更新用户消息到会话
    updateSessionMessages(sessionId, newMessages)

    // 添加助手消息占位符 - 显示"正在思考中..."状态
    const assistantMessageId = Date.now().toString() + '-assistant'
    const assistantMessage: Message = {
      id: assistantMessageId,
      type: 'assistant',
      content: '正在思考中...',
      timestamp: new Date()
    }

    // 立即添加"正在思考中..."的助手消息到会话
    const messagesWithAssistant = [...newMessages, assistantMessage]
    updateSessionMessages(sessionId, messagesWithAssistant)

    try {
      // 构建请求体，包含编码规则信息
      const requestBody: any = {
        message: inputMessage,
        session_id: sessionId
      }

      // 如果选择了编码规则，添加规则信息
      if (selectedCodingRule) {
        requestBody.coding_rule = {
          id: selectedCodingRule.id,
          title: selectedCodingRule.title,
          description: selectedCodingRule.description,
          content: selectedCodingRule.content,
          example: selectedCodingRule.example,
          language: selectedCodingRule.language,
          category: selectedCodingRule.category
        }
      }

      const response = await fetch(API_ENDPOINTS.CHAT, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(requestBody)
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
                const updatedMessages = messagesWithAssistant.map(msg => 
                  msg.id === assistantMessageId 
                    ? { ...msg, content: assistantResponse }
                    : msg
                )
                updateSessionMessages(sessionId, updatedMessages)
              }
            } catch (e) {
              // 忽略解析错误
            }
          }
        }
      }

      // 如果是新会话的第一条消息，更新会话标题
      if (newMessages.length <= 2) {
        const title = inputMessage.length > 20 ? inputMessage.substring(0, 20) + '...' : inputMessage
        updateSessionTitle(sessionId, title)
      }

    } catch (error) {
      console.error('发送消息失败:', error)
      message.error('发送消息失败，请重试')
      
      // 错误时移除"正在思考中..."消息
      updateSessionMessages(sessionId, newMessages)
    } finally {
      setIsLoading(false)
      setInputMessage('')
      // 使用编码规则后清除选择（可选行为）
      if (selectedCodingRule) {
        setSelectedCodingRule(null)
      }
    }
  }

  // 加载编码规则列表
  const fetchCodingRules = async () => {
    try {
      const response = await fetch(API_ENDPOINTS.CODING_RULES)
      const data = await response.json()
      if (data.success) {
        setCodingRules(data.data.items || [])
      }
    } catch (error) {
      console.error('获取编码规则失败:', error)
    }
  }

  // 机器人创建相关函数
  const handleCreateBot = () => {
    setBotCreateModalVisible(true)
  }

  const handleBotFormSubmit = async (values: any) => {
    setCreatingBot(true)
    try {
      const response = await fetch(API_ENDPOINTS.BOTS, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          name: values.name,
          description: values.description,
          avatar: values.avatar || "/default-bot-avatar.png",
          position: values.position || "bottom-right",
          size: values.size || "medium",
          primary_color: values.primary_color || "#1890ff",
          greeting_message: values.greeting_message || "您好！我是您的智能助手，有什么可以帮助您的吗？",
          knowledge_base_enabled: values.knowledge_base_enabled !== false
        })
      })

      const data = await response.json()
      if (data.success) {
        message.success('机器人创建成功！')
        setBotCreateModalVisible(false)
        botForm.resetFields()
        
        // 显示创建成功的信息
        const bot = data.data
        
        Modal.success({
          title: '机器人创建成功！',
          width: 600,
          content: (
            <div style={{ marginTop: '16px' }}>
              <p><strong>机器人名称：</strong>{bot.name}</p>
              <p><strong>访问链接：</strong></p>
              <Input 
                value={getBotPageUrl(bot.id)}
                readOnly 
                style={{ marginBottom: '8px' }}
              />
              <p><strong>嵌入代码：</strong></p>
              <Input.TextArea 
                value={getBotEmbedCode(bot.id)}
                readOnly 
                rows={2}
              />
            </div>
          )
        })
        
        // 刷新机器人列表
        fetchBotList()
      } else {
        message.error(data.message || '创建失败')
      }
    } catch (error) {
      console.error('创建机器人失败:', error)
      message.error('创建机器人失败')
    } finally {
      setCreatingBot(false)
    }
  }

  const fetchBotList = async () => {
    try {
      const response = await fetch(API_ENDPOINTS.BOTS)
      const data = await response.json()
      if (data.success) {
        setBotList(data.data.items || [])
      }
    } catch (error) {
      console.error('获取机器人列表失败:', error)
    }
  }

  // 编辑机器人
  const handleEditBot = (bot: Bot) => {
    setEditingBot(bot)
    botEditForm.setFieldsValue({
      name: bot.name,
      description: bot.description,
      avatar: bot.avatar,
      position: bot.position,
      size: bot.size,
      primary_color: bot.primary_color,
      greeting_message: bot.greeting_message,
      knowledge_base_enabled: bot.knowledge_base_enabled
    })
    setBotEditModalVisible(true)
  }

  // 提交编辑
  const handleBotEditSubmit = async (values: any) => {
    if (!editingBot) return
    
    setUpdatingBot(true)
    try {
      const response = await fetch(`${API_ENDPOINTS.BOTS}/${editingBot.id}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          name: values.name,
          description: values.description,
          avatar: values.avatar || "/default-bot-avatar.png",
          position: values.position || "bottom-right",
          size: values.size || "medium",
          primary_color: values.primary_color || "#1890ff",
          greeting_message: values.greeting_message || "您好！我是您的智能助手，有什么可以帮助您的吗？",
          knowledge_base_enabled: values.knowledge_base_enabled !== false
        })
      })

      const data = await response.json()
      if (data.success) {
        message.success('机器人更新成功！')
        setBotEditModalVisible(false)
        botEditForm.resetFields()
        setEditingBot(null)
        
        // 刷新机器人列表
        fetchBotList()
      } else {
        message.error(data.message || '更新失败')
      }
    } catch (error) {
      console.error('更新机器人失败:', error)
      message.error('更新机器人失败')
    } finally {
      setUpdatingBot(false)
    }
  }

  // 删除机器人
  const handleDeleteBot = async (bot: Bot) => {
    try {
      const response = await fetch(`${API_ENDPOINTS.BOTS}/${bot.id}`, {
        method: 'DELETE'
      })

      const data = await response.json()
      if (data.success) {
        message.success('机器人删除成功！')
        
        // 刷新机器人列表
        fetchBotList()
      } else {
        message.error(data.message || '删除失败')
      }
    } catch (error) {
      console.error('删除机器人失败:', error)
      message.error('删除机器人失败')
    }
  }

  // 查看机器人详情
  const handleViewBot = (bot: Bot) => {
    setSelectedBot(bot)
    setBotDetailsModalVisible(true)
  }

  // 复制嵌入代码
  const copyEmbedCode = (bot: Bot) => {
    const embedCode = getBotEmbedCode(bot.id)
    navigator.clipboard.writeText(embedCode).then(() => {
      message.success('嵌入代码已复制到剪贴板')
    }).catch(() => {
      message.error('复制失败')
    })
  }

  // 复制访问链接
  const copyBotLink = (bot: Bot) => {
    const botLink = getBotPageUrl(bot.id)
    navigator.clipboard.writeText(botLink).then(() => {
      message.success('访问链接已复制到剪贴板')
    }).catch(() => {
      message.error('复制失败')
    })
  }

  const renderDashboard = () => (
    <div style={{ padding: '24px' }}>
      <Row gutter={[24, 24]}>
        {/* 上传文件卡片 */}
        <Col xs={24} md={12}>
          <Card
            hoverable
            style={{ height: '280px', borderRadius: '12px' }}
            bodyStyle={{ padding: '24px', height: '100%', display: 'flex', flexDirection: 'column' }}
            onClick={() => setUploadModalVisible(true)}
          >
            <div style={{ textAlign: 'center', flex: 1, display: 'flex', flexDirection: 'column', justifyContent: 'center' }}>
              <UploadOutlined style={{ fontSize: '48px', color: '#1890ff', marginBottom: '16px' }} />
              <Title level={4} style={{ margin: '0 0 8px 0' }}>上传文件</Title>
              <Text type="secondary" style={{ fontSize: '14px', lineHeight: '1.6' }}>
                支持 docx, csv, ppt, md, txt, xlsx等文件上传解析
              </Text>
            </div>
          </Card>
        </Col>

        {/* 文本录入卡片 */}
        <Col xs={24} md={12}>
          <Card
            hoverable
            style={{ height: '280px', borderRadius: '12px' }}
            bodyStyle={{ padding: '24px', height: '100%', display: 'flex', flexDirection: 'column' }}
            onClick={() => setTextModalVisible(true)}
          >
            <div style={{ textAlign: 'center', flex: 1, display: 'flex', flexDirection: 'column', justifyContent: 'center' }}>
              <EditOutlined style={{ fontSize: '48px', color: '#52c41a', marginBottom: '16px' }} />
              <Title level={4} style={{ margin: '0 0 8px 0' }}>文本录入</Title>
              <Text type="secondary" style={{ fontSize: '14px', lineHeight: '1.6' }}>
                支持直接输入的提问和解析
              </Text>
            </div>
          </Card>
        </Col>

        {/* 导入网页链接卡片 */}
        <Col xs={24} md={12}>
          <Card
            hoverable
            style={{ height: '280px', borderRadius: '12px' }}
            bodyStyle={{ padding: '24px', height: '100%', display: 'flex', flexDirection: 'column' }}
            onClick={() => setLinkModalVisible(true)}
          >
            <div style={{ textAlign: 'center', flex: 1, display: 'flex', flexDirection: 'column', justifyContent: 'center' }}>
              <LinkOutlined style={{ fontSize: '48px', color: '#722ed1', marginBottom: '16px' }} />
              <Title level={4} style={{ margin: '0 0 8px 0' }}>导入网页链接</Title>
              <Text type="secondary" style={{ fontSize: '14px', lineHeight: '1.6' }}>
                支持上传网页URL链接并快速解析网页内容并解析
              </Text>
            </div>
          </Card>
        </Col>

        {/* 一对一咨询卡片 */}
        <Col xs={24} md={12}>
          <Card
            hoverable
            style={{ height: '280px', borderRadius: '12px' }}
            bodyStyle={{ padding: '24px', height: '100%', display: 'flex', flexDirection: 'column' }}
            onClick={startChat}
          >
            <div style={{ textAlign: 'center', flex: 1, display: 'flex', flexDirection: 'column', justifyContent: 'center' }}>
              <MessageOutlined style={{ fontSize: '48px', color: '#fa8c16', marginBottom: '16px' }} />
              <Title level={4} style={{ margin: '0 0 8px 0' }}>一对一咨询</Title>
              <Text type="secondary" style={{ fontSize: '14px', lineHeight: '1.6' }}>
                任何机器人问题，一对一的问题对话
              </Text>
            </div>
          </Card>
        </Col>
      </Row>
    </div>
  )

  const renderSidebar = () => (
    <div style={{ padding: '16px' }}>
      {/* 标题和头像 */}
      <div style={{ textAlign: 'center', marginBottom: '24px' }}>
        <Avatar 
          size={48} 
          style={{ backgroundColor: '#1890ff', marginBottom: '12px' }}
          icon={<RobotOutlined />}
        />
        <Title level={4} style={{ margin: 0, color: '#1890ff' }}>智能客服</Title>
      </div>

      {/* 创建机器人按钮 */}
      <Button 
        type="primary" 
        icon={<RobotOutlined />} 
        block 
        style={{ marginBottom: '16px', borderRadius: '8px' }}
        onClick={handleCreateBot}
      >
        创建机器人
      </Button>

      {/* 开始对话按钮 */}
      <Button 
        icon={<MessageOutlined />} 
        block 
        style={{ marginBottom: '16px', borderRadius: '8px' }}
        onClick={startChat}
      >
        开始对话
      </Button>

      {/* 知识库管理按钮 */}
      <Button 
        icon={<FileTextOutlined />} 
        block 
        style={{ marginBottom: '16px', borderRadius: '8px' }}
        onClick={() => window.open('/knowledge', '_blank')}
      >
        知识库管理
      </Button>

      {/* 编码学习管理按钮 */}
      <Button 
        icon={<EditOutlined />} 
        block 
        style={{ marginBottom: '16px', borderRadius: '8px' }}
        onClick={() => window.open('/coding-rules', '_blank')}
      >
        编码学习管理
      </Button>

      {/* 搜索框 */}
      <Search
        placeholder="请输入关键词..."
        style={{ marginBottom: '24px' }}
        onSearch={(value) => {
          if (value.trim()) {
            message.info(`搜索: ${value}`)
          }
        }}
      />

      <Divider />

      {/* 机器人历史记录 */}
      <div style={{ marginTop: 'auto' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
          <Title level={5} style={{ color: '#666', margin: 0 }}>创建的机器人</Title>
          <Text type="secondary" style={{ fontSize: '12px' }}>
            {botList.length} 个
          </Text>
        </div>
        
        <div style={{ maxHeight: '300px', overflow: 'auto' }}>
          {botList.length === 0 ? (
            <div style={{ textAlign: 'center', padding: '20px 0', color: '#999' }}>
              <RobotOutlined style={{ fontSize: '24px', marginBottom: '8px', display: 'block' }} />
              <Text type="secondary" style={{ fontSize: '12px' }}>
                暂无机器人
              </Text>
            </div>
          ) : (
            botList.map((bot) => (
              <Card
                key={bot.id}
                size="small"
                style={{ 
                  marginBottom: '8px',
                  cursor: 'pointer',
                  border: `1px solid ${bot.primary_color}20`,
                  borderRadius: '8px'
                }}
                bodyStyle={{ padding: '8px 12px' }}
                onClick={() => handleViewBot(bot)}
                hoverable
              >
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div style={{ 
                      display: 'flex', 
                      alignItems: 'center', 
                      marginBottom: '4px' 
                    }}>
                      <Avatar 
                        src={bot.avatar} 
                        icon={<RobotOutlined />} 
                        size={20}
                        style={{ marginRight: '6px', backgroundColor: bot.primary_color }}
                      />
                      <Text 
                        strong 
                        style={{ 
                          fontSize: '12px',
                          overflow: 'hidden',
                          textOverflow: 'ellipsis',
                          whiteSpace: 'nowrap',
                          color: bot.primary_color
                        }}
                      >
                        {bot.name}
                      </Text>
                    </div>
                    <Text 
                      type="secondary" 
                      style={{ 
                        fontSize: '10px',
                        display: 'block',
                        overflow: 'hidden',
                        textOverflow: 'ellipsis',
                        whiteSpace: 'nowrap'
                      }}
                    >
                      {bot.description}
                    </Text>
                  </div>
                  
                  <div style={{ display: 'flex', gap: '4px', marginLeft: '8px' }}>
                    <Button
                      type="text"
                      size="small"
                      icon={<EditOutlined />}
                      onClick={(e) => {
                        e.stopPropagation()
                        handleEditBot(bot)
                      }}
                      style={{ padding: '2px 4px', height: 'auto' }}
                      title="编辑机器人"
                    />
                    <Popconfirm
                      title="删除机器人"
                      description="确定要删除这个机器人吗？此操作不可恢复。"
                      onConfirm={(e) => {
                        e?.stopPropagation()
                        handleDeleteBot(bot)
                      }}
                      okText="确定"
                      cancelText="取消"
                    >
                      <Button
                        type="text"
                        size="small"
                        icon={<DeleteOutlined />}
                        onClick={(e) => e.stopPropagation()}
                        style={{ padding: '2px 4px', height: 'auto', color: '#ff4d4f' }}
                        title="删除机器人"
                      />
                    </Popconfirm>
                  </div>
                </div>
              </Card>
            ))
          )}
        </div>
      </div>
    </div>
  )

  return (
    <Layout style={{ height: '100vh', background: '#f5f5f5' }}>
      {/* 左侧边栏 */}
      <Sider 
        width={280} 
        style={{ 
          background: '#fff', 
          boxShadow: '2px 0 8px rgba(0,0,0,0.1)',
          height: '100vh',
          display: 'flex',
          flexDirection: 'column'
        }}
      >
        {renderSidebar()}
      </Sider>

      {/* 主内容区域 */}
      <Layout>
        <Content style={{ padding: '24px', background: '#f5f5f5' }}>
          {renderDashboard()}
        </Content>
      </Layout>

      {/* 文件上传弹窗 */}
      <Modal
        title="上传文件"
        open={uploadModalVisible}
        onCancel={() => setUploadModalVisible(false)}
        footer={null}
        width={600}
      >
        <Upload.Dragger
          name="file"
          multiple
          action={API_ENDPOINTS.KNOWLEDGE_UPLOAD}
          onChange={handleFileUpload}
          style={{ padding: '20px' }}
        >
          <p className="ant-upload-drag-icon">
            <UploadOutlined style={{ fontSize: '48px', color: '#1890ff' }} />
          </p>
          <p className="ant-upload-text">点击或拖拽文件到此区域上传</p>
          <p className="ant-upload-hint">
            支持 docx, csv, ppt, md, txt, xlsx 等格式
          </p>
        </Upload.Dragger>
      </Modal>

      {/* 文本录入弹窗 */}
      <Modal
        title="文本录入"
        open={textModalVisible}
        onCancel={() => setTextModalVisible(false)}
        footer={null}
        width={600}
      >
        <Form form={form} onFinish={handleTextSubmit} layout="vertical">
          <Form.Item
            label="标题"
            name="title"
            rules={[{ required: true, message: '请输入标题' }]}
          >
            <Input placeholder="请输入知识标题" />
          </Form.Item>
          <Form.Item
            label="内容"
            name="content"
            rules={[{ required: true, message: '请输入内容' }]}
          >
            <TextArea rows={6} placeholder="请输入知识内容" />
          </Form.Item>
          <Form.Item
            label="分类"
            name="category"
          >
            <Input placeholder="请输入分类（可选）" />
          </Form.Item>
          <Form.Item>
            <Space>
              <Button type="primary" htmlType="submit">
                提交
              </Button>
              <Button onClick={() => setTextModalVisible(false)}>
                取消
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>

      {/* 网页链接弹窗 */}
      <Modal
        title="导入网页链接"
        open={linkModalVisible}
        onCancel={() => setLinkModalVisible(false)}
        footer={null}
        width={600}
      >
        <Form form={form} onFinish={handleLinkSubmit} layout="vertical" initialValues={{ auto_add: true }}>
          <Form.Item
            label="网页URL"
            name="url"
            rules={[
              { required: true, message: '请输入网页URL' },
              { type: 'url', message: '请输入有效的URL' }
            ]}
          >
            <Input placeholder="https://example.com" />
          </Form.Item>
          <Form.Item
            label="分类"
            name="category"
          >
            <Input placeholder="web_content" />
          </Form.Item>
          <Form.Item
            name="auto_add"
            valuePropName="checked"
          >
            <span>
              <input type="checkbox" style={{ marginRight: '8px' }} />
              自动添加到知识库
            </span>
          </Form.Item>
          <Form.Item>
            <Space>
              <Button type="primary" htmlType="submit">
                解析网页
              </Button>
              <Button onClick={() => setLinkModalVisible(false)}>
                取消
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>

      {/* 聊天弹窗 */}
      <Modal
        title={
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <div style={{ display: 'flex', alignItems: 'center' }}>
              <RobotOutlined style={{ marginRight: '8px', color: '#1890ff' }} />
              智能客服对话
            </div>
            <Button 
              type="primary" 
              size="small"
              icon={<PlusOutlined />}
              onClick={() => {
                createNewSession()
              }}
            >
              新对话
            </Button>
          </div>
        }
        open={chatModalVisible}
        onCancel={() => setChatModalVisible(false)}
        footer={null}
        width={1000}
        styles={{ body: { height: '600px', padding: 0 } }}
      >
        <div style={{ height: '100%', display: 'flex' }}>
          {/* 会话列表侧边栏 */}
          <div style={{ 
            width: '250px', 
            borderRight: '1px solid #f0f0f0',
            background: '#fafafa',
            padding: '16px 0'
          }}>
            <div style={{ padding: '0 16px', marginBottom: '16px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <Text strong>会话历史</Text>
              <Popconfirm
                title="清除所有聊天记录"
                description="确定要清除所有聊天记录吗？此操作不可恢复。"
                onConfirm={clearAllChatHistory}
                okText="确定"
                cancelText="取消"
              >
                <Button 
                  type="text" 
                  size="small"
                  icon={<ClearOutlined />}
                  title="清除所有聊天记录"
                  style={{ color: '#ff4d4f' }}
                />
              </Popconfirm>
            </div>
            <div style={{ height: 'calc(100% - 50px)', overflow: 'auto' }}>
              {chatSessions.length === 0 ? (
                <div style={{ textAlign: 'center', padding: '20px', color: '#999' }}>
                  <Text type="secondary">暂无会话记录</Text>
                </div>
              ) : (
                chatSessions.map((session) => (
                  <div
                    key={session.id}
                    style={{
                      padding: '12px 16px',
                      cursor: 'pointer',
                      background: session.id === currentSessionId ? '#e6f7ff' : 'transparent',
                      borderLeft: session.id === currentSessionId ? '3px solid #1890ff' : '3px solid transparent',
                      position: 'relative'
                    }}
                    onMouseEnter={(e) => {
                      const deleteBtn = e.currentTarget.querySelector('.delete-session-btn') as HTMLElement
                      if (deleteBtn) deleteBtn.style.display = 'block'
                    }}
                    onMouseLeave={(e) => {
                      const deleteBtn = e.currentTarget.querySelector('.delete-session-btn') as HTMLElement
                      if (deleteBtn) deleteBtn.style.display = 'none'
                    }}
                  >
                    <div onClick={() => setCurrentSessionId(session.id)}>
                      <div style={{ fontSize: '14px', fontWeight: '500', marginBottom: '4px', paddingRight: '20px' }}>
                        {session.title}
                      </div>
                      <div style={{ fontSize: '12px', color: '#999' }}>
                        {session.messages.length} 条消息
                      </div>
                      <div style={{ fontSize: '12px', color: '#999' }}>
                        {session.lastMessageAt.toLocaleString()}
                      </div>
                    </div>
                    <Popconfirm
                      title="删除会话"
                      description="确定要删除这个会话吗？此操作不可恢复。"
                      onConfirm={() => deleteSession(session.id)}
                      okText="确定"
                      cancelText="取消"
                    >
                      <Button
                        className="delete-session-btn"
                        type="text"
                        size="small"
                        icon={<DeleteOutlined />}
                        onClick={(e) => e.stopPropagation()}
                        style={{
                          position: 'absolute',
                          top: '8px',
                          right: '8px',
                          color: '#ff4d4f',
                          display: 'none'
                        }}
                        title="删除此会话"
                      />
                    </Popconfirm>
                  </div>
                ))
              )}
            </div>
          </div>

          {/* 聊天内容区域 */}
          <div style={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
            {/* 聊天消息区域 */}
            <div style={{ 
              flex: 1, 
              overflow: 'auto', 
              padding: '16px',
              background: '#fff'
            }}>
              {getCurrentMessages().length === 0 ? (
                <div style={{ textAlign: 'center', padding: '60px 0', color: '#999' }}>
                  <RobotOutlined style={{ fontSize: '48px', marginBottom: '16px' }} />
                  <p>您好！我是智能客服助手，有什么可以帮助您的吗？</p>
                  <p style={{ fontSize: '12px', color: '#ccc' }}>
                    您可以点击右上角"新对话"按钮创建新的聊天会话
                  </p>
                </div>
              ) : (
                getCurrentMessages().map((msg: Message) => 
                  renderMessage(msg)
                )
              )}
            </div>

            {/* 输入区域 */}
            <div style={{ padding: '16px', borderTop: '1px solid #f0f0f0', background: '#fff' }}>
              {/* 编码规则选择器 */}
              {codingRules.length > 0 && (
                <div style={{ marginBottom: '12px' }}>
                  <Text type="secondary" style={{ fontSize: '12px', marginBottom: '4px', display: 'block' }}>
                    编码规则辅助（可选）：
                  </Text>
                  <Select
                    style={{ width: '100%' }}
                    placeholder="选择编码规则来改进您的代码..."
                    allowClear
                    value={selectedCodingRule?.id}
                    onChange={(value) => {
                      const rule = codingRules.find(r => r.id === value)
                      setSelectedCodingRule(rule || null)
                    }}
                    size="small"
                    loading={applyingRule}
                  >
                    {codingRules.map((rule) => (
                      <Select.Option key={rule.id} value={rule.id}>
                        <div style={{ padding: '4px 0' }}>
                          <div style={{ 
                            fontWeight: '500',
                            lineHeight: '1.2',
                            wordBreak: 'break-word'
                          }}>
                            {rule.title}
                          </div>
                        </div>
                      </Select.Option>
                    ))}
                  </Select>
                  {selectedCodingRule && (
                    <div style={{ 
                      marginTop: '8px', 
                      padding: '8px 12px', 
                      background: '#f6f8fa', 
                      borderRadius: '6px',
                      fontSize: '12px',
                      color: '#666',
                      border: '1px solid #e1e4e8',
                      lineHeight: '1.4'
                    }}>
                      <div style={{ 
                        fontWeight: '500', 
                        marginBottom: '4px',
                        color: '#24292e',
                        wordBreak: 'break-word'
                      }}>
                        已选择：{selectedCodingRule.title}
                      </div>
                      <div style={{ 
                        maxHeight: '60px', 
                        overflow: 'hidden',
                        textOverflow: 'ellipsis',
                        wordBreak: 'break-word',
                        whiteSpace: 'normal',
                        lineHeight: '1.3'
                      }}>
                        {selectedCodingRule.description}
                      </div>
                    </div>
                  )}
                </div>
              )}
              
              <div style={{ display: 'flex', gap: '8px' }}>
                <Input
                  value={inputMessage}
                  onChange={(e) => setInputMessage(e.target.value)}
                  placeholder={selectedCodingRule ? "输入您的代码，我将根据选择的编码规则为您改进..." : "请输入您的问题..."}
                  onPressEnter={sendMessage}
                  disabled={isLoading || applyingRule}
                />
                <Button
                  type="primary"
                  icon={<MessageOutlined />}
                  onClick={sendMessage}
                  loading={isLoading || applyingRule}
                  disabled={!currentSessionId}
                >
                  {selectedCodingRule ? '应用规则' : '发送'}
                </Button>
              </div>
            </div>
          </div>
        </div>
      </Modal>

      {/* 机器人创建弹窗 */}
      <Modal
        title={
          <div style={{ display: 'flex', alignItems: 'center' }}>
            <RobotOutlined style={{ marginRight: '8px', color: '#1890ff' }} />
            创建智能机器人
          </div>
        }
        open={botCreateModalVisible}
        onCancel={() => {
          setBotCreateModalVisible(false)
          botForm.resetFields()
        }}
        footer={null}
        width={800}
      >
        <Form
          form={botForm}
          layout="vertical"
          onFinish={handleBotFormSubmit}
          initialValues={{
            position: 'bottom-right',
            size: 'medium',
            primary_color: '#1890ff',
            knowledge_base_enabled: true
          }}
        >
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                label="机器人名称"
                name="name"
                rules={[{ required: true, message: '请输入机器人名称' }]}
              >
                <Input placeholder="例如：智能客服小助手" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                label="主色调"
                name="primary_color"
              >
                <Input type="color" style={{ width: '100%', height: '32px' }} />
              </Form.Item>
            </Col>
          </Row>

          <Form.Item
            label="机器人描述"
            name="description"
            rules={[{ required: true, message: '请输入机器人描述' }]}
          >
            <TextArea rows={3} placeholder="描述机器人的功能和特点..." />
          </Form.Item>

          <Form.Item
            label="头像图片"
            name="avatar"
            extra="请输入图片URL，留空将使用默认头像"
          >
            <Input placeholder="https://example.com/avatar.png" />
          </Form.Item>

          <Form.Item
            label="欢迎语"
            name="greeting_message"
          >
            <TextArea rows={2} placeholder="您好！我是您的智能助手，有什么可以帮助您的吗？" />
          </Form.Item>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                label="显示位置"
                name="position"
              >
                <Select>
                  <Select.Option value="bottom-right">右下角</Select.Option>
                  <Select.Option value="bottom-left">左下角</Select.Option>
                  <Select.Option value="top-right">右上角</Select.Option>
                  <Select.Option value="top-left">左上角</Select.Option>
                </Select>
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                label="机器人大小"
                name="size"
              >
                <Select>
                  <Select.Option value="small">小号</Select.Option>
                  <Select.Option value="medium">中号</Select.Option>
                  <Select.Option value="large">大号</Select.Option>
                </Select>
              </Form.Item>
            </Col>
          </Row>

          <Form.Item
            name="knowledge_base_enabled"
            valuePropName="checked"
          >
            <span>
              <input type="checkbox" style={{ marginRight: '8px' }} />
              启用知识库回答功能
            </span>
          </Form.Item>

          <Form.Item style={{ marginBottom: 0, textAlign: 'right' }}>
            <Space>
              <Button onClick={() => {
                setBotCreateModalVisible(false)
                botForm.resetFields()
              }}>
                取消
              </Button>
              <Button type="primary" htmlType="submit" loading={creatingBot}>
                创建机器人
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>

      {/* 机器人编辑弹窗 */}
      <Modal
        title={
          <div style={{ display: 'flex', alignItems: 'center' }}>
            <EditOutlined style={{ marginRight: '8px', color: '#1890ff' }} />
            编辑机器人
          </div>
        }
        open={botEditModalVisible}
        onCancel={() => {
          setBotEditModalVisible(false)
          botEditForm.resetFields()
          setEditingBot(null)
        }}
        footer={null}
        width={800}
      >
        <Form
          form={botEditForm}
          layout="vertical"
          onFinish={handleBotEditSubmit}
        >
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                label="机器人名称"
                name="name"
                rules={[{ required: true, message: '请输入机器人名称' }]}
              >
                <Input placeholder="例如：智能客服小助手" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                label="主色调"
                name="primary_color"
              >
                <Input type="color" style={{ width: '100%', height: '32px' }} />
              </Form.Item>
            </Col>
          </Row>

          <Form.Item
            label="机器人描述"
            name="description"
            rules={[{ required: true, message: '请输入机器人描述' }]}
          >
            <TextArea rows={3} placeholder="描述机器人的功能和特点..." />
          </Form.Item>

          <Form.Item
            label="头像图片"
            name="avatar"
            extra="请输入图片URL，留空将使用默认头像"
          >
            <Input placeholder="https://example.com/avatar.png" />
          </Form.Item>

          <Form.Item
            label="欢迎语"
            name="greeting_message"
          >
            <TextArea rows={2} placeholder="您好！我是您的智能助手，有什么可以帮助您的吗？" />
          </Form.Item>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                label="显示位置"
                name="position"
              >
                <Select>
                  <Select.Option value="bottom-right">右下角</Select.Option>
                  <Select.Option value="bottom-left">左下角</Select.Option>
                  <Select.Option value="top-right">右上角</Select.Option>
                  <Select.Option value="top-left">左上角</Select.Option>
                </Select>
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                label="机器人大小"
                name="size"
              >
                <Select>
                  <Select.Option value="small">小号</Select.Option>
                  <Select.Option value="medium">中号</Select.Option>
                  <Select.Option value="large">大号</Select.Option>
                </Select>
              </Form.Item>
            </Col>
          </Row>

          <Form.Item
            name="knowledge_base_enabled"
            valuePropName="checked"
          >
            <span>
              <input type="checkbox" style={{ marginRight: '8px' }} />
              启用知识库回答功能
            </span>
          </Form.Item>

          <Form.Item style={{ marginBottom: 0, textAlign: 'right' }}>
            <Space>
              <Button onClick={() => {
                setBotEditModalVisible(false)
                botEditForm.resetFields()
                setEditingBot(null)
              }}>
                取消
              </Button>
              <Button type="primary" htmlType="submit" loading={updatingBot}>
                更新机器人
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>

      {/* 机器人详情查看弹窗 */}
      <Modal
        title={
          <div style={{ display: 'flex', alignItems: 'center' }}>
            <RobotOutlined style={{ marginRight: '8px', color: selectedBot?.primary_color || '#1890ff' }} />
            {selectedBot?.name || '机器人详情'}
          </div>
        }
        open={botDetailsModalVisible}
        onCancel={() => {
          setBotDetailsModalVisible(false)
          setSelectedBot(null)
        }}
        footer={
          <Space>
            <Button onClick={() => copyEmbedCode(selectedBot!)}>
              <LinkOutlined /> 复制嵌入代码
            </Button>
            <Button onClick={() => copyBotLink(selectedBot!)}>
              <LinkOutlined /> 复制访问链接
            </Button>
            <Button 
              type="primary" 
              onClick={() => {
                setBotDetailsModalVisible(false)
                handleEditBot(selectedBot!)
              }}
            >
              <EditOutlined /> 编辑机器人
            </Button>
          </Space>
        }
        width={700}
      >
        {selectedBot && (
          <div>
            <Row gutter={24}>
              <Col span={8}>
                <div style={{ textAlign: 'center', marginBottom: '20px' }}>
                  <Avatar 
                    src={selectedBot.avatar} 
                    icon={<RobotOutlined />}
                    size={80}
                    style={{ backgroundColor: selectedBot.primary_color }}
                  />
                  <div style={{ marginTop: '12px' }}>
                    <Text strong style={{ fontSize: '16px', color: selectedBot.primary_color }}>
                      {selectedBot.name}
                    </Text>
                  </div>
                </div>
              </Col>
              <Col span={16}>
                <div style={{ marginBottom: '16px' }}>
                  <Text strong>描述：</Text>
                  <div style={{ marginTop: '4px' }}>
                    <Text>{selectedBot.description}</Text>
                  </div>
                </div>
                
                <div style={{ marginBottom: '16px' }}>
                  <Text strong>欢迎语：</Text>
                  <div style={{ marginTop: '4px' }}>
                    <Text>{selectedBot.greeting_message}</Text>
                  </div>
                </div>

                <Row gutter={16}>
                  <Col span={12}>
                    <div style={{ marginBottom: '12px' }}>
                      <Text strong>显示位置：</Text>
                      <div style={{ marginTop: '4px' }}>
                        <Text>
                          {selectedBot.position === 'bottom-right' ? '右下角' : 
                           selectedBot.position === 'bottom-left' ? '左下角' :
                           selectedBot.position === 'top-right' ? '右上角' : '左上角'}
                        </Text>
                      </div>
                    </div>
                  </Col>
                  <Col span={12}>
                    <div style={{ marginBottom: '12px' }}>
                      <Text strong>大小：</Text>
                      <div style={{ marginTop: '4px' }}>
                        <Text>
                          {selectedBot.size === 'small' ? '小号' : 
                           selectedBot.size === 'medium' ? '中号' : '大号'}
                        </Text>
                      </div>
                    </div>
                  </Col>
                </Row>

                <Row gutter={16}>
                  <Col span={12}>
                    <div style={{ marginBottom: '12px' }}>
                      <Text strong>主色调：</Text>
                      <div style={{ marginTop: '4px', display: 'flex', alignItems: 'center' }}>
                        <div 
                          style={{ 
                            width: '20px', 
                            height: '20px', 
                            backgroundColor: selectedBot.primary_color,
                            borderRadius: '4px',
                            marginRight: '8px',
                            border: '1px solid #d9d9d9'
                          }}
                        />
                        <Text>{selectedBot.primary_color}</Text>
                      </div>
                    </div>
                  </Col>
                  <Col span={12}>
                    <div style={{ marginBottom: '12px' }}>
                      <Text strong>知识库功能：</Text>
                      <div style={{ marginTop: '4px' }}>
                        <Text style={{ color: selectedBot.knowledge_base_enabled ? '#52c41a' : '#ff4d4f' }}>
                          {selectedBot.knowledge_base_enabled ? '已启用' : '已禁用'}
                        </Text>
                      </div>
                    </div>
                  </Col>
                </Row>

                <div style={{ marginBottom: '16px' }}>
                  <Text strong>创建时间：</Text>
                  <div style={{ marginTop: '4px' }}>
                    <Text>{new Date(selectedBot.created_at).toLocaleString()}</Text>
                  </div>
                </div>
              </Col>
            </Row>

            <Divider />

            <div>
              <Text strong>使用方式：</Text>
              <div style={{ marginTop: '8px' }}>
                <Text type="secondary">嵌入代码（复制到其他网站HTML中）：</Text>
                <Input.TextArea
                  value={getBotEmbedCode(selectedBot.id)}
                  rows={2}
                  readOnly
                  style={{ marginTop: '4px', marginBottom: '8px' }}
                />
                
                <Text type="secondary">直接访问链接：</Text>
                <Input
                  value={getBotPageUrl(selectedBot.id)}
                  readOnly
                  style={{ marginTop: '4px' }}
                  addonAfter={
                    <Button 
                      type="link" 
                      size="small"
                      onClick={() => window.open(getBotPageUrl(selectedBot.id), '_blank')}
                    >
                      访问
                    </Button>
                  }
                />
              </div>
            </div>
          </div>
        )}
      </Modal>
    </Layout>
  )
}