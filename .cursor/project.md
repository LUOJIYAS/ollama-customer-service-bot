🏗️ 技术架构

前端架构 (front-end-pages)
    框架: Next.js 13.5.6 + TypeScript 5.3.3
    UI 库: Ant Design 5.12.8 (现代化专业界面)
    特性: 响应式设计、流式对话、实时更新
页面结构:
    主聊天界面 (index.tsx)
    知识库管理 (knowledge.tsx)
    编码规则管理 (coding-rules.tsx)
    机器人管理 (bot/)
后端架构 (back-end-pages)
    框架: FastAPI (高性能异步 API)
    向量数据库: ChromaDB (持久化存储)
核心服务模块:
    ollama_client.py: Ollama API 客户端，支持流式对话和向量生成
    vector_store.py: ChromaDB 向量存储服务
    knowledge_manager.py: 知识库管理服务
    bot_manager.py: 机器人管理服务
    coding_rules_manager.py: 编码规则管理
    web_scraper.py: 网页内容抓取
🤖 AI 模型配置
    项目使用 Ollama 0.9.3 作为模型推理引擎：
    # 模型配置
        对话模型: deepseek-r1:latest # 主对话模型
        嵌入模型: modelscope.cn/Qwen/Qwen3-Embedding-8B-GGUF:latest # 向量化模型
        文本重排序: deepseek-r1:latest # 检索重排序

🔧 核心功能特性

智能对话系统
    流式响应 (Server-Sent Events)
    上下文记忆
    知识库增强回答 (RAG)
    OpenAI 兼容 API 格式
知识库管理
    支持 PDF、Word、Excel、JSON 文件上传
    网页内容抓取
    向量化存储和语义搜索
    分类标签管理
多机器人支持
    独立机器人实例
    可嵌入式部署
    自定义外观和行为
