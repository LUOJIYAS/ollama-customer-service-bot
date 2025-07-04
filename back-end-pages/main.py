"""
智能客服机器人主应用

支持流式聊天、知识库管理、向量检索、编码规则管理等功能。
严格按照项目规则实现，使用Pythonic实践和完整的类型注解。
"""

from fastapi import FastAPI, HTTPException, UploadFile, File, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import json
import asyncio
from datetime import datetime
import time

from services.ollama_client import OllamaClient
from services.vector_store import VectorStore
from services.knowledge_manager import KnowledgeManager
from services.web_scraper import WebScraper
from services.coding_rules_manager import CodingRulesManager
from services.bot_manager import BotManager
from utils.logger import setup_logger

# 设置日志
logger = setup_logger(__name__)

# 创建FastAPI应用
app = FastAPI(
    title="智能客服机器人",
    description="基于Ollama和ChromaDB的智能客服系统",
    version="1.0.0"
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000", 
        "http://127.0.0.1:3000",
        "http://10.1.76.220:3000",
        "http://10.1.76.220:8000",
        "*"  # 允许所有源，便于嵌入到其他系统
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# 初始化服务
ollama_client = OllamaClient()
vector_store = VectorStore()
knowledge_manager = KnowledgeManager(vector_store, ollama_client)
coding_rules_manager = CodingRulesManager(vector_store, ollama_client)
web_scraper = WebScraper()
bot_manager = BotManager()

# 请求模型
class ChatMessage(BaseModel):
    message: str
    conversation_id: Optional[str] = None
    history: Optional[List[Dict[str, str]]] = []
    session_id: Optional[str] = None
    coding_rule: Optional[Dict[str, str]] = None

class KnowledgeItem(BaseModel):
    title: str
    content: str
    category: Optional[str] = "general"
    tags: Optional[List[str]] = []

class SearchQuery(BaseModel):
    query: str
    top_k: Optional[int] = 5

class WebUrlRequest(BaseModel):
    url: str
    category: Optional[str] = "web_content"
    auto_add_to_knowledge: Optional[bool] = False

class CodingRuleItem(BaseModel):
    title: str
    description: str
    language: str
    content: str
    example: Optional[str] = ""
    category: Optional[str] = "general"
    tags: Optional[List[str]] = []

class ApplyCodingRuleRequest(BaseModel):
    text: str
    rule_id: str

class BotCreateRequest(BaseModel):
    name: str
    description: str
    avatar: Optional[str] = "/default-bot-avatar.png"
    position: Optional[str] = "bottom-right"
    size: Optional[str] = "medium"
    primary_color: Optional[str] = "#1890ff"
    greeting_message: Optional[str] = "您好！我是您的智能助手，有什么可以帮助您的吗？"
    knowledge_base_enabled: Optional[bool] = True

class BotChatRequest(BaseModel):
    bot_id: str
    message: str
    conversation_id: Optional[str] = None
    stream: Optional[bool] = False

class BatchDeleteRequest(BaseModel):
    ids: List[str]

@app.on_event("startup")
async def startup_event():
    """应用启动时初始化服务"""
    logger.info("正在启动智能客服机器人服务...")
    try:
        await vector_store.initialize()
        logger.info("向量数据库初始化成功")
        
        # 检查Ollama连接
        health = await ollama_client.check_health()
        if health:
            logger.info("Ollama服务连接正常")
        else:
            logger.warning("Ollama服务连接失败，请检查服务状态")
            
        # 初始化机器人管理器
        global bot_manager
        bot_manager = BotManager()
        logger.info("机器人管理器初始化完成")
        
    except Exception as e:
        logger.error(f"服务初始化失败: {e}")
        raise

@app.get("/")
async def root():
    """健康检查"""
    return {"message": "智能客服机器人服务运行正常", "timestamp": datetime.now()}

@app.get("/api/health")
async def health_check():
    """详细健康检查"""
    try:
        ollama_health = await ollama_client.check_health()
        models = await ollama_client.list_models()
        running_models = await ollama_client.list_running_models()
        
        return {
            "status": "healthy",
            "ollama_connected": ollama_health,
            "available_models": len(models),
            "running_models": len(running_models),
            "chat_model": ollama_client.chat_model,
            "embedding_model": ollama_client.embedding_model,
            "timestamp": datetime.now()
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now()
        }

@app.post("/api/chat")
async def chat_stream(message: ChatMessage):
    """流式聊天接口"""
    try:
        # 如果选择了编码规则，直接进入编码规则处理模式
        if message.coding_rule:
            # 编码规则辅助模式 - 不搜索知识库
            system_prompt = f"""你是一个专业的代码分析和改进助手。用户已选择了以下编码规则：

==== 编码规则信息 ====
规则标题：{message.coding_rule.get('title', 'N/A')}
规则描述：{message.coding_rule.get('description', 'N/A')}
编程语言：{message.coding_rule.get('language', 'N/A')}
规则分类：{message.coding_rule.get('category', 'N/A')}

==== 编码规则内容 ====
{message.coding_rule.get('content', 'N/A')}

==== 编码规则示例 ====
{message.coding_rule.get('example', 'N/A')}

==== 任务要求 ====
请根据上述编码规则来分析和改进用户提供的代码。你需要：
1. 仔细学习并理解提供的编码规则
2. 分析用户的代码是否符合该规则
3. 如果不符合，提供具体的改进建议和修改后的代码
4. 解释为什么要这样修改，体现规则的价值
5. 确保修改后的代码更加规范、可读性更强
6. 使用中文进行详细说明
7. 提供完整可运行的改进后代码

请严格按照提供的编码规则来指导代码改进！"""

            # 构建用户消息
            user_content = f"""请根据已选择的编码规则来分析和改进以下代码：

{message.message}

请提供详细的分析、改进建议，并输出符合编码规则的完整代码。"""

        else:
            # 普通聊天模式 - 搜索知识库
            relevant_docs = await knowledge_manager.search_knowledge(
                message.message, top_k=3
            )
            
            system_prompt = """你是一个专业的智能客服助手。请根据提供的知识库信息回答用户问题。

回答要求：
1. 优先使用知识库中的信息
2. 保持回答准确、友好、专业
3. 如果知识库中没有相关信息，请诚实地告知用户
4. 提供具体的帮助建议
5. 使用中文回答"""

            # 构建用户消息内容（包含知识库信息）
            user_content = message.message
            if relevant_docs:
                context_info = "\n\n[相关知识库信息]\n" + "\n".join([
                    f"• {doc['title']}: {doc['content'][:300]}..." if len(doc['content']) > 300 else f"• {doc['title']}: {doc['content']}"
                    for doc in relevant_docs
                ])
                user_content += context_info

        # 构建消息列表
        messages = []
        
        # 添加历史消息（如果有）
        if message.history:
            for hist_msg in message.history[-10:]:  # 限制历史消息数量
                if hist_msg.get("role") and hist_msg.get("content"):
                    messages.append({
                        "role": hist_msg["role"],
                        "content": hist_msg["content"]
                    })
        
        # 添加当前用户消息
        messages.append({
            "role": "user", 
            "content": user_content
        })
        
        # 生成流式响应
        async def generate():
            try:
                response_content = ""
                in_thinking = False
                thinking_buffer = ""
                
                async for chunk in ollama_client.chat_stream(
                    messages=messages,
                    system=system_prompt,
                    keep_alive="10m"
                ):
                    # 检测思考标签的开始和结束
                    chunk_with_buffer = thinking_buffer + chunk
                    thinking_buffer = ""
                    
                    # 处理思考标签
                    parts = []
                    current_text = chunk_with_buffer
                    
                    # 检查是否包含思考标签
                    while "<think>" in current_text or "</think>" in current_text or in_thinking:
                        if not in_thinking and "<think>" in current_text:
                            # 找到思考开始标签
                            before_think, after_think = current_text.split("<think>", 1)
                            if before_think.strip():
                                parts.append(before_think)
                            in_thinking = True
                            current_text = after_think
                        elif in_thinking and "</think>" in current_text:
                            # 找到思考结束标签
                            thinking_content, after_think = current_text.split("</think>", 1)
                            in_thinking = False
                            current_text = after_think
                        elif in_thinking:
                            # 在思考标签内，跳过这部分内容
                            thinking_buffer = current_text
                            current_text = ""
                            break
                        else:
                            break
                    
                    # 如果不在思考状态，发送内容
                    if not in_thinking and current_text:
                        parts.append(current_text)
                    
                    # 发送非思考内容
                    for part in parts:
                        if part.strip():
                            response_content += part
                            yield f"data: {json.dumps({'content': part, 'done': False}, ensure_ascii=False)}\n\n"
                
                # 发送完成信号
                yield f"data: {json.dumps({'content': '', 'done': True}, ensure_ascii=False)}\n\n"
                
            except Exception as e:
                logger.error(f"流式响应生成失败: {e}")
                yield f"data: {json.dumps({'error': f'生成响应时出错: {str(e)}'}, ensure_ascii=False)}\n\n"
        
        return StreamingResponse(
            generate(),
            media_type="text/plain",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Content-Type": "text/plain; charset=utf-8"
            }
        )
        
    except Exception as e:
        logger.error(f"聊天接口错误: {e}")
        raise HTTPException(status_code=500, detail=f"聊天服务错误: {str(e)}")

# 知识库管理接口
@app.post("/api/knowledge")
async def add_knowledge(item: KnowledgeItem):
    """添加知识库条目"""
    try:
        result = await knowledge_manager.add_knowledge(
            title=item.title,
            content=item.content,
            category=item.category or "general",
            tags=item.tags or []
        )
        return {"success": True, "data": result}
    except Exception as e:
        logger.error(f"添加知识库条目失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/knowledge")
async def list_knowledge(
    page: int = 1, 
    page_size: int = 10, 
    category: Optional[str] = None
):
    """获取知识库列表"""
    try:
        result = await knowledge_manager.list_knowledge(
            page=page, 
            size=page_size, 
            category=category
        )
        return {"success": True, "data": result}
    except Exception as e:
        logger.error(f"获取知识库列表失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/knowledge/stats")
async def get_knowledge_stats():
    """获取知识库统计信息"""
    try:
        stats = await knowledge_manager.get_stats()
        return {"success": True, "data": stats}
    except Exception as e:
        logger.error(f"获取知识库统计失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/knowledge/categories")
async def get_knowledge_categories():
    """获取知识库分类列表"""
    try:
        categories = await knowledge_manager.get_categories()
        return {"success": True, "data": {"categories": categories}}
    except Exception as e:
        logger.error(f"获取知识库分类失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/knowledge/{item_id}")
async def get_knowledge(item_id: str):
    """获取单个知识库条目"""
    try:
        result = await knowledge_manager.get_knowledge(item_id)
        if not result:
            raise HTTPException(status_code=404, detail="知识库条目不存在")
        return {"success": True, "data": result}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取知识库条目失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/knowledge/{item_id}")
async def update_knowledge(item_id: str, item: KnowledgeItem):
    """更新知识库条目"""
    try:
        success = await knowledge_manager.update_knowledge(
            knowledge_id=item_id,
            title=item.title,
            content=item.content,
            category=item.category,
            tags=item.tags
        )
        if not success:
            raise HTTPException(status_code=404, detail="知识库条目不存在或更新失败")
        
        # 返回更新后的数据
        updated_item = await knowledge_manager.get_knowledge(item_id)
        return {"success": True, "data": updated_item}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新知识库条目失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/knowledge/{item_id}")
async def delete_knowledge(item_id: str):
    """删除知识库条目"""
    try:
        result = await knowledge_manager.delete_knowledge(item_id)
        return {"success": True, "data": result}
    except Exception as e:
        logger.error(f"删除知识库条目失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/knowledge/batch-delete")
async def batch_delete_knowledge(request: BatchDeleteRequest):
    """批量删除知识库条目"""
    try:
        result = await knowledge_manager.delete_knowledge_batch(request.ids)
        return {"success": result["success"], "data": result}
    except Exception as e:
        logger.error(f"批量删除知识库条目失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/knowledge/search")
async def search_knowledge(query: SearchQuery):
    """搜索知识库"""
    try:
        results = await knowledge_manager.search_knowledge(
            query.query, top_k=query.top_k or 5
        )
        return {"success": True, "data": results}
    except Exception as e:
        logger.error(f"搜索知识库失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/knowledge/upload")
async def upload_knowledge_file(file: UploadFile = File(...), category: str = "upload"):
    """上传文件到知识库"""
    try:
        result = await knowledge_manager.upload_file(file)
        return {"success": True, "data": result}
    except Exception as e:
        logger.error(f"上传文件失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/knowledge/web")
async def add_web_content(request: WebUrlRequest):
    """从网页添加内容到知识库"""
    try:
        # 抓取网页内容
        content = await web_scraper.scrape_url(request.url)
        
        # 如果设置了自动添加到知识库
        if request.auto_add_to_knowledge:
            result = await knowledge_manager.add_knowledge(
                title=content.get("title", "网页内容"),
                content=content.get("content", ""),
                category=request.category or "web_content",
                tags=["web_content"]
            )
            return {"success": True, "data": {"content": content, "knowledge_added": result}}
        else:
            return {"success": True, "data": {"content": content}}
            
    except Exception as e:
        logger.error(f"处理网页内容失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# 网页解析接口 - 首页导入网络链接使用
@app.post("/api/web/parse")
async def parse_web_url(request: WebUrlRequest):
    """解析网页URL并提取内容，支持自动添加到知识库"""
    try:
        # 验证URL格式
        if not web_scraper.validate_url(request.url):
            raise HTTPException(status_code=400, detail="无效的URL格式")
        
        # 抓取网页内容
        scraped_data = await web_scraper.scrape_url(request.url)
        
        knowledge_id = None
        
        # 如果选择自动添加到知识库
        if request.auto_add_to_knowledge:
            try:
                # 构建更好的格式化内容，确保类型安全
                title = scraped_data.get("title", "网页内容")
                title = title if isinstance(title, str) else "网页内容"
                
                description = scraped_data.get("description", "")
                description = description if isinstance(description, str) else ""
                
                web_content = scraped_data.get("content", "")
                web_content = web_content if isinstance(web_content, str) else ""
                
                keywords = scraped_data.get("keywords", "")
                keywords = keywords if isinstance(keywords, str) else ""
                
                url = scraped_data.get("url", request.url)
                domain = scraped_data.get("domain", "")
                
                # 构建格式化的内容
                formatted_content_parts = []
                
                # 添加来源信息
                formatted_content_parts.append(f"📄 来源：{url}")
                
                # 添加描述（如果有）
                if description:
                    formatted_content_parts.append(f"📝 摘要：{description}")
                
                # 添加关键词（如果有）
                if keywords:
                    formatted_content_parts.append(f"🔖 关键词：{keywords}")
                
                # 添加分隔线
                formatted_content_parts.append("=" * 50)
                
                # 添加主要内容
                if web_content:
                    formatted_content_parts.append(web_content)
                else:
                    # 如果网页内容为空，至少保留基本信息
                    formatted_content_parts.append("该网页暂无可提取的文本内容，但已保存基本信息供参考。")
                
                # 组合最终内容
                final_content = "\n\n".join(formatted_content_parts)
                
                # 准备标签
                tags = ["网页内容"]
                if domain:
                    tags.append(domain)
                if request.category and request.category != "web_content":
                    tags.append(request.category)
                
                # 添加到知识库
                result = await knowledge_manager.add_knowledge(
                    title=title if title != "网页内容" else f"网页内容 - {domain}",
                    content=final_content,
                    category=request.category or "web_content",
                    tags=tags
                )
                
                knowledge_id = result["id"]
                logger.info(f"成功将网页内容添加到知识库: {title}, URL: {url}, ID: {knowledge_id}")
                
            except Exception as ke:
                logger.error(f"添加网页内容到知识库失败: {ke}")
                return {
                    "success": True,
                    "data": scraped_data,
                    "message": f"网页解析成功，但添加到知识库失败: {str(ke)}",
                    "error": {"type": "knowledge_add_failed", "detail": str(ke)}
                }
        
        # 返回结果
        response_data = {
            "success": True,
            "data": scraped_data,
            "message": "网页解析成功" + ("，已添加到知识库" if request.auto_add_to_knowledge and knowledge_id else "")
        }
        
        # 如果成功添加到知识库，包含知识库信息
        if knowledge_id:
            response_data["knowledge_id"] = knowledge_id
            
        return response_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"网页解析错误: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# 编码规则管理接口
# 注意：更具体的路由必须在更通用的路由之前定义

@app.get("/api/coding-rules/stats")
async def get_coding_rules_stats():
    """获取编码规则统计信息"""
    try:
        stats = await coding_rules_manager.get_stats()
        # 转换为前端期望的格式
        formatted_stats = {
            "total_rules": stats.get("total_rules", 0),
            "total_languages": len(stats.get("languages", [])),
            "total_categories": len(stats.get("categories", [])),
            "recent_uploads": 0  # 这里可以根据实际需求计算
        }
        return {"success": True, "data": formatted_stats}
    except Exception as e:
        logger.error(f"获取编码规则统计失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/coding-rules/categories")
async def get_coding_rules_categories():
    """获取编码规则分类列表"""
    try:
        categories = await coding_rules_manager.get_categories()
        return {"success": True, "data": {"categories": categories}}
    except Exception as e:
        logger.error(f"获取编码规则分类失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/coding-rules/languages")
async def get_coding_rules_languages():
    """获取编程语言列表"""
    try:
        languages = await coding_rules_manager.get_languages()
        return {"success": True, "data": {"languages": languages}}
    except Exception as e:
        logger.error(f"获取编程语言列表失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/coding-rules/search")
async def search_coding_rules(query: SearchQuery):
    """搜索编码规则"""
    try:
        # 简单的基于标题和描述的搜索实现
        search_term = query.query.lower()
        
        # 获取所有编码规则进行搜索
        all_rules = await coding_rules_manager.list_coding_rules(page=1, page_size=1000)
        
        results = []
        for rule in all_rules.get('items', []):
            # 检查标题、描述、内容中是否包含搜索词
            if (search_term in rule.get('title', '').lower() or 
                search_term in rule.get('description', '').lower() or
                search_term in rule.get('content', '').lower() or
                search_term in rule.get('language', '').lower() or
                search_term in rule.get('category', '').lower()):
                results.append(rule)
                
        # 限制结果数量
        max_results = query.top_k or 10
        results = results[:max_results]
        
        return {"success": True, "data": {"results": results}}
    except Exception as e:
        logger.error(f"搜索编码规则错误: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/coding-rules/apply")
async def apply_coding_rule(request: ApplyCodingRuleRequest):
    """应用编码规则到文本"""
    try:
        result = await coding_rules_manager.apply_rule(
            text=request.text,
            rule_id=request.rule_id
        )
        return {"success": True, "data": result}
    except Exception as e:
        logger.error(f"应用编码规则失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/coding-rules/upload")
async def upload_coding_rule_file(file: UploadFile = File(...), category: str = "upload"):
    """上传文件解析编码规则"""
    try:
        content = await file.read()
        result = await coding_rules_manager.process_file(
            file_content=content,
            filename=file.filename or "unknown",
            category=category
        )
        return {"success": True, "data": result}
    except Exception as e:
        logger.error(f"解析编码规则文件失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/coding-rules")
async def add_coding_rule(item: CodingRuleItem):
    """添加编码规则"""
    try:
        result = await coding_rules_manager.add_coding_rule(
            title=item.title,
            description=item.description,
            language=item.language,
            content=item.content,
            example=item.example or "",
            category=item.category or "general",
            tags=item.tags or []
        )
        return {"success": True, "data": result}
    except Exception as e:
        logger.error(f"添加编码规则失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/coding-rules/{rule_id}")
async def get_coding_rule(rule_id: str):
    """根据ID获取编码规则"""
    try:
        rule = await coding_rules_manager.get_coding_rule_by_id(rule_id)
        if not rule:
            raise HTTPException(status_code=404, detail="编码规则不存在")
        return {"success": True, "data": rule}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取编码规则错误: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/coding-rules/{rule_id}")
async def update_coding_rule(rule_id: str, item: CodingRuleItem):
    """更新编码规则"""
    try:
        # 先检查规则是否存在
        existing_rule = await coding_rules_manager.get_coding_rule_by_id(rule_id)
        if not existing_rule:
            raise HTTPException(status_code=404, detail="编码规则不存在")
        
        # 删除旧规则并添加新规则（作为更新的替代方案）
        success = await coding_rules_manager.delete_coding_rule(rule_id)
        if not success:
            raise HTTPException(status_code=404, detail="编码规则不存在")
        
        # 添加更新后的规则
        new_rule_id = await coding_rules_manager.add_coding_rule(
            title=item.title,
            description=item.description,
            language=item.language,
            content=item.content,
            example=item.example or "",
            category=item.category or "general",
            tags=item.tags or []
        )
        
        return {"success": True, "data": {"id": new_rule_id}, "message": "编码规则更新成功"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新编码规则错误: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/coding-rules/{rule_id}")
async def delete_coding_rule(rule_id: str):
    """删除编码规则"""
    try:
        success = await coding_rules_manager.delete_coding_rule(rule_id)
        if not success:
            raise HTTPException(status_code=404, detail="编码规则不存在")
        return {"success": True, "message": "编码规则删除成功"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除编码规则错误: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/coding-rules")
async def list_coding_rules(
    page: int = 1,
    page_size: int = 10,
    category: Optional[str] = None,
    language: Optional[str] = None
):
    """获取编码规则列表"""
    try:
        result = await coding_rules_manager.list_coding_rules(
            page=page, 
            page_size=page_size, 
            category=category,
            language=language
        )
        return {"success": True, "data": result}
    except Exception as e:
        logger.error(f"获取编码规则列表失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# 机器人管理API端点

@app.post("/api/bots")
async def create_bot(item: BotCreateRequest):
    """创建机器人"""
    try:
        bot = await bot_manager.create_bot(
            name=item.name,
            description=item.description,
            avatar=item.avatar or "/default-bot-avatar.png",
            position=item.position or "bottom-right",
            size=item.size or "medium",
            primary_color=item.primary_color or "#1890ff",
            greeting_message=item.greeting_message or "您好！我是您的智能助手，有什么可以帮助您的吗？",
            knowledge_base_enabled=item.knowledge_base_enabled if item.knowledge_base_enabled is not None else True
        )
        return {"success": True, "data": bot}
    except Exception as e:
        logger.error(f"创建机器人失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/bots")
async def list_bots(page: int = 1, page_size: int = 10):
    """获取机器人列表"""
    try:
        result = await bot_manager.list_bots(page=page, page_size=page_size)
        return {"success": True, "data": result}
    except Exception as e:
        logger.error(f"获取机器人列表失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/bots/{bot_id}")
async def get_bot(bot_id: str):
    """获取单个机器人详情"""
    try:
        bot = await bot_manager.get_bot_by_id(bot_id)
        if not bot:
            raise HTTPException(status_code=404, detail="机器人不存在")
        return {"success": True, "data": bot}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取机器人失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/bots/{bot_id}")
async def delete_bot(bot_id: str):
    """删除机器人"""
    try:
        success = await bot_manager.delete_bot(bot_id)
        if not success:
            raise HTTPException(status_code=404, detail="机器人不存在")
        return {"success": True, "message": "机器人删除成功"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除机器人失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/bots/{bot_id}")
async def update_bot(bot_id: str, item: BotCreateRequest):
    """更新机器人"""
    try:
        # 检查机器人是否存在
        existing_bot = await bot_manager.get_bot_by_id(bot_id)
        if not existing_bot:
            raise HTTPException(status_code=404, detail="机器人不存在")
        
        # 更新机器人信息
        updated_bot = await bot_manager.update_bot(
            bot_id=bot_id,
            name=item.name,
            description=item.description,
            avatar=item.avatar or "/default-bot-avatar.png",
            position=item.position or "bottom-right",
            size=item.size or "medium",
            primary_color=item.primary_color or "#1890ff",
            greeting_message=item.greeting_message or "您好！我是您的智能助手，有什么可以帮助您的吗？",
            knowledge_base_enabled=item.knowledge_base_enabled if item.knowledge_base_enabled is not None else True
        )
        
        if not updated_bot:
            raise HTTPException(status_code=404, detail="机器人不存在")
        
        return {"success": True, "data": updated_bot}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新机器人失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/bot-embed/{bot_id}.js")
async def get_bot_embed_script(bot_id: str, request: Request):
    """获取机器人嵌入脚本"""
    try:
        # 检查机器人是否存在
        bot = await bot_manager.get_bot_by_id(bot_id)
        if not bot:
            raise HTTPException(status_code=404, detail="机器人不存在")
        
        # 获取基础URL
        base_url = f"{request.url.scheme}://{request.headers.get('host', 'localhost:8000')}"
        
        # 生成嵌入脚本
        script = bot_manager.generate_embed_script(bot_id, base_url)
        
        return Response(
            content=script,
            media_type="application/javascript",
            headers={"Content-Disposition": f"inline; filename=\"bot-{bot_id}.js\""}
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取嵌入脚本失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/bots/stats")
async def get_bot_stats():
    """获取机器人统计信息"""
    try:
        stats = await bot_manager.get_stats()
        return {"success": True, "data": stats}
    except Exception as e:
        logger.error(f"获取机器人统计失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/bot-chat")
async def bot_chat(item: BotChatRequest):
    """机器人对话接口"""
    try:
        # 检查机器人是否存在
        bot = await bot_manager.get_bot_by_id(item.bot_id)
        if not bot:
            raise HTTPException(status_code=404, detail="机器人不存在")
        
        # 如果请求流式响应
        if item.stream:
            # 如果机器人启用了知识库功能，则调用知识库问答
            if bot.get('knowledge_base_enabled', True):
                # 从知识库检索相关信息
                relevant_docs = await knowledge_manager.search_knowledge(
                    item.message, top_k=3
                )
                
                # 构建系统提示
                system_prompt = f"""你是{bot.get('name', '智能助手')}。{bot.get('description', '')}

回答要求：
1. 优先使用知识库中的信息
2. 保持回答准确、友好、专业
3. 如果知识库中没有相关信息，请诚实地告知用户
4. 提供具体的帮助建议
5. 使用中文回答
6. 对于复杂问题，可以在<think></think>标签中展示思考过程"""

                # 构建用户消息内容
                user_content = item.message
                if relevant_docs:
                    context_info = "\n\n[相关知识库信息]\n" + "\n".join([
                        f"• {doc['title']}: {doc['content'][:300]}..." if len(doc['content']) > 300 else f"• {doc['title']}: {doc['content']}"
                        for doc in relevant_docs
                    ])
                    user_content += context_info
                
                # 构建消息列表
                messages = [{"role": "user", "content": user_content}]
                
                # 流式响应生成器
                async def generate():
                    try:
                        async for chunk in ollama_client.chat_stream(
                            messages=messages,
                            system=system_prompt,
                            keep_alive="10m"
                        ):
                            # 对于机器人聊天，保留think部分不过滤
                            if chunk:
                                yield f"data: {json.dumps({'content': chunk})}\n\n"
                        
                        yield "data: [DONE]\n\n"
                        
                    except Exception as e:
                        logger.error(f"生成机器人回答失败: {e}")
                        error_message = "抱歉，我暂时无法回答您的问题，请稍后再试。"
                        yield f"data: {json.dumps({'content': error_message})}\n\n"
                        yield "data: [DONE]\n\n"
                
                return StreamingResponse(
                    generate(),
                    media_type="text/plain",
                    headers={
                        "Cache-Control": "no-cache",
                        "Connection": "keep-alive",
                        "Access-Control-Allow-Origin": "*",
                        "Access-Control-Allow-Methods": "POST",
                        "Access-Control-Allow-Headers": "Content-Type"
                    }
                )
            else:
                # 简单回复的流式响应
                async def generate_simple():
                    simple_responses = [
                        f"感谢您使用{bot.get('name', '智能助手')}！",
                        "这是一个很好的问题。",
                        "我正在为您查找相关信息。",
                        "请问还有其他问题吗？",
                        f"很高兴为您服务！我是{bot.get('name', '智能助手')}。"
                    ]
                    
                    import random
                    response = random.choice(simple_responses)
                    
                    yield f"data: {json.dumps({'content': response})}\n\n"
                    yield "data: [DONE]\n\n"
                
                return StreamingResponse(
                    generate_simple(),
                    media_type="text/plain",
                    headers={
                        "Cache-Control": "no-cache",
                        "Connection": "keep-alive",
                        "Access-Control-Allow-Origin": "*",
                        "Access-Control-Allow-Methods": "POST",
                        "Access-Control-Allow-Headers": "Content-Type"
                    }
                )
        
        # 非流式响应（保持兼容性）
        else:
            # 如果机器人启用了知识库功能，则调用知识库问答
            if bot.get('knowledge_base_enabled', True):
                # 从知识库检索相关信息
                relevant_docs = await knowledge_manager.search_knowledge(
                    item.message, top_k=3
                )
                
                # 构建系统提示
                system_prompt = f"""你是{bot.get('name', '智能助手')}。{bot.get('description', '')}

回答要求：
1. 优先使用知识库中的信息
2. 保持回答准确、友好、专业
3. 如果知识库中没有相关信息，请诚实地告知用户
4. 提供具体的帮助建议
5. 使用中文回答"""

                # 构建用户消息内容
                user_content = item.message
                if relevant_docs:
                    context_info = "\n\n[相关知识库信息]\n" + "\n".join([
                        f"• {doc['title']}: {doc['content'][:300]}..." if len(doc['content']) > 300 else f"• {doc['title']}: {doc['content']}"
                        for doc in relevant_docs
                    ])
                    user_content += context_info
                
                # 构建消息列表
                messages = [{"role": "user", "content": user_content}]
                
                # 生成回答
                response_content = ""
                try:
                    async for chunk in ollama_client.chat_stream(
                        messages=messages,
                        system=system_prompt,
                        keep_alive="10m"
                    ):
                        # 过滤思考标签
                        if "<think>" not in chunk and "</think>" not in chunk:
                            response_content += chunk
                    
                    # 如果没有生成内容，提供默认回复
                    if not response_content.strip():
                        response_content = "抱歉，我暂时无法回答您的问题，请稍后再试。"
                        
                except Exception as e:
                    logger.error(f"生成回答失败: {e}")
                    response_content = "抱歉，我暂时无法回答您的问题，请稍后再试。"
                
                return {
                    "success": True, 
                    "data": {
                        "response": response_content.strip(),
                        "conversation_id": item.conversation_id or f"conv_{int(time.time())}"
                    }
                }
            else:
                # 简单的回复逻辑
                simple_responses = [
                    f"感谢您使用{bot.get('name', '智能助手')}！",
                    "这是一个很好的问题。",
                    "我正在为您查找相关信息。",
                    "请问还有其他问题吗？",
                    f"很高兴为您服务！我是{bot.get('name', '智能助手')}。"
                ]
                
                import random
                response = random.choice(simple_responses)
                
                return {
                    "success": True,
                    "data": {
                        "response": response,
                        "conversation_id": item.conversation_id or f"conv_{int(time.time())}"
                    }
                }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"机器人对话失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info") 