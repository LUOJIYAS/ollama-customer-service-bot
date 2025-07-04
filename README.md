# 智能客服机器人

基于 Ollama 0.9.3 + Next.js + FastAPI 的智能客服系统，支持知识库管理和流式对话。

## 🌟 功能特性

### 核心功能
- 🤖 **智能对话**: 基于 Ollama 的流式 AI 对话
- 📚 **知识库管理**: 可视化的知识库增删改查
- 🔍 **语义搜索**: ChromaDB 向量数据库支持的智能检索
- 📁 **文件上传**: 支持 PDF、Word、Excel、JSON 等格式
- 📊 **统计分析**: 知识库使用统计和监控

### 技术架构
- **前端**: Next.js 14 + TypeScript + Ant Design UI
- **后端**: Python FastAPI + ChromaDB
- **AI模型**: 
  - 对话模型: `deepseek-r1:latest`
  - 嵌入模型: `modelscope.cn/Qwen/Qwen3-Embedding-8B-GGUF:latest`
- **向量数据库**: ChromaDB
- **API标准**: OpenAI兼容API格式

## 🛠️ 系统要求

- **Python**: 3.8+
- **Node.js**: 16+
- **Ollama**: 0.9.3
- **操作系统**: Windows 10/11
- **内存**: 建议 16GB+（模型加载需要）

## 📦 快速开始

### 1. 克隆项目
```bash
git clone <repository-url>
cd ollama-customer-service-bot
```

### 2. 安装Ollama并拉取模型
```bash
# 安装Ollama (如果未安装)
# 从 https://ollama.com/download 下载并安装

# 启动Ollama服务
ollama serve

# 拉取所需模型
ollama pull deepseek-r1:latest
ollama pull modelscope.cn/Qwen/Qwen3-Embedding-8B-GGUF:latest
```

### 3. 系统检查
```bash
# 运行系统检查脚本
system_check.bat
```

### 4. 一键启动
```bash
# 启动所有服务
start_all.bat
```

## 🚀 手动启动

### 后端启动
```bash
cd back-end-pages
pip install -r requirements.txt
python main.py
```

### 前端启动
```bash
cd front-end-pages
npm install
npm run dev
```

## 🌐 访问地址

- **前端界面**: http://localhost:3000
- **后端API**: http://localhost:8000
- **API文档**: http://localhost:8000/docs
- **健康检查**: http://localhost:8000/health

## 📁 项目结构

```
ollama-customer-service-bot/
├── back-end-pages/              # 后端代码
│   ├── services/               # 服务层
│   │   ├── ollama_client.py   # Ollama API客户端
│   │   ├── vector_store.py    # ChromaDB向量存储
│   │   └── knowledge_manager.py # 知识库管理
│   ├── utils/                 # 工具类
│   ├── main.py               # FastAPI主应用
│   ├── config.py             # 配置管理
│   ├── requirements.txt      # Python依赖
│   └── check_ollama.py       # Ollama服务检查
├── front-end-pages/            # 前端代码
│   ├── pages/                # Next.js页面
│   ├── components/           # React组件
│   ├── services/             # API服务
│   ├── styles/               # 样式文件
│   └── package.json          # Node.js依赖
├── start_all.bat             # 一键启动脚本
├── system_check.bat          # 系统检查脚本
├── setup_frontend.bat        # 前端环境设置
└── README.md                 # 项目文档
```

## 🔧 API文档

### 聊天接口
```http
POST /api/chat
Content-Type: application/json

{
  "message": "用户消息",
  "history": [
    {"role": "user", "content": "历史消息"},
    {"role": "assistant", "content": "AI回复"}
  ]
}
```

### 知识库管理
```http
# 添加知识
POST /api/knowledge
{
  "title": "标题",
  "content": "内容",
  "category": "分类",
  "tags": ["标签1", "标签2"]
}

# 搜索知识
POST /api/knowledge/search
{
  "query": "搜索关键词",
  "top_k": 5
}

# 获取统计
GET /api/knowledge/stats
```

## 🎨 界面展示

- **现代化UI**: 基于Ant Design的专业界面设计
- **响应式布局**: 支持PC和移动端
- **实时对话**: 流式响应的聊天体验
- **知识库管理**: 直观的可视化管理界面

## ⚙️ 配置说明

### Ollama配置
```python
# back-end-pages/config.py
OLLAMA_BASE_URL = "http://localhost:11434"
CHAT_MODEL = "deepseek-r1:latest"
EMBEDDING_MODEL = "modelscope.cn/Qwen/Qwen3-Embedding-8B-GGUF:latest"
```

### 前端配置
```javascript
// front-end-pages/next.config.js
module.exports = {
  reactStrictMode: true,
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: 'http://localhost:8000/api/:path*'
      }
    ]
  }
}
```

## 🐛 常见问题

### Q: Ollama连接失败
A: 确保Ollama服务正在运行 (`ollama serve`)，并检查端口11434是否可访问

### Q: 模型加载慢
A: 首次使用时模型需要加载到内存，建议预热：`ollama run deepseek-r1:latest`

### Q: 前端依赖安装失败
A: 运行 `setup_frontend.bat` 或手动执行 `npm install --legacy-peer-deps`

### Q: 内存不足
A: 确保系统有足够内存（建议16GB+），或考虑使用更小的模型

## 📝 开发指南

### 添加新的知识源
1. 在 `knowledge_manager.py` 中添加处理逻辑
2. 更新前端上传组件支持新格式
3. 测试向量化和检索功能

### 自定义模型
1. 修改 `config.py` 中的模型配置
2. 确保模型已在Ollama中安装
3. 运行系统检查验证

### 界面定制
1. 修改 `styles/globals.css` 调整全局样式
2. 在组件中使用Ant Design主题定制
3. 参考 `style.jpg` 保持界面一致性

## 📞 技术支持

如遇问题，请：
1. 首先运行 `system_check.bat` 检查环境
2. 查看后端日志: `back-end-pages/logs/`
3. 检查Ollama服务状态: `ollama list`

## 📄 许可证

本项目遵循MIT许可证。详见LICENSE文件。

---

🚀 **立即开始**: 运行 `system_check.bat` 然后 `start_all.bat` 