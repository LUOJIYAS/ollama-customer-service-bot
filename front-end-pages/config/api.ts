/**
 * API配置文件
 * 统一管理API基础URL和相关配置
 */

// 检测当前环境，如果是开发环境使用localhost，生产环境使用指定IP
const isDevelopment = process.env.NODE_ENV === 'development'
const isLocalhost = typeof window !== 'undefined' && window.location.hostname === 'localhost'

// API基础URL配置
export const API_BASE_URL = isDevelopment && isLocalhost 
  ? 'http://localhost:8000'
  : 'http://10.1.76.220:8000'

// 前端基础URL配置（用于生成嵌入链接）
export const FRONTEND_BASE_URL = isDevelopment && isLocalhost
  ? 'http://localhost:3000'
  : 'http://10.1.76.220:3000'

// API端点配置
export const API_ENDPOINTS = {
  // 知识库相关
  KNOWLEDGE_STATS: `${API_BASE_URL}/api/knowledge/stats`,
  KNOWLEDGE_ADD: `${API_BASE_URL}/api/knowledge`,
  KNOWLEDGE_UPLOAD: `${API_BASE_URL}/api/knowledge/upload`,
  WEB_PARSE: `${API_BASE_URL}/api/web/parse`,
  
  // 聊天相关
  CHAT: `${API_BASE_URL}/api/chat`,
  BOT_CHAT: `${API_BASE_URL}/api/bot-chat`,
  
  // 编码规则相关
  CODING_RULES: `${API_BASE_URL}/api/coding-rules`,
  CODING_RULES_STATS: `${API_BASE_URL}/api/coding-rules/stats`,
  CODING_RULES_CATEGORIES: `${API_BASE_URL}/api/coding-rules/categories`,
  CODING_RULES_LANGUAGES: `${API_BASE_URL}/api/coding-rules/languages`,
  CODING_RULES_SEARCH: `${API_BASE_URL}/api/coding-rules/search`,
  CODING_RULES_UPLOAD: `${API_BASE_URL}/api/coding-rules/upload`,
  
  // 机器人相关
  BOTS: `${API_BASE_URL}/api/bots`,
  BOT_EMBED: (botId: string) => `${API_BASE_URL}/api/bot-embed/${botId}.js`,
  BOT_PAGE: (botId: string) => `${FRONTEND_BASE_URL}/bot/${botId}`,
}

/**
 * 获取机器人嵌入代码
 * @param botId 机器人ID
 * @returns 嵌入JavaScript代码
 */
export const getBotEmbedCode = (botId: string): string => {
  return `<script src="${API_ENDPOINTS.BOT_EMBED(botId)}"></script>`
}

/**
 * 获取机器人访问链接
 * @param botId 机器人ID
 * @returns 机器人页面链接
 */
export const getBotPageUrl = (botId: string): string => {
  return API_ENDPOINTS.BOT_PAGE(botId)
} 