"""
智能客服机器人主应用
支持流式聊天、知识库管理、向量检索等功能
"""

from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import json
import asyncio
from datetime import datetime

from services.ollama_client import OllamaClient
from services.vector_store import VectorStore
from services.knowledge_manager import KnowledgeManager
from services.web_scraper import WebScraper
from services.coding_rules_manager import CodingRulesManager
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
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 初始化服务
ollama_client = OllamaClient()
vector_store = VectorStore()
knowledge_manager = KnowledgeManager(vector_store, ollama_client)
coding_rules_manager = CodingRulesManager(vector_store, ollama_client)
web_scraper = WebScraper()

# 请求模型
class ChatMessage(BaseModel):
    message: str
    conversation_id: Optional[str] = None
    history: Optional[List[Dict[str, str]]] = []

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
    """流式聊天接口（支持Ollama 0.9.3新API）"""
    try:
        # 从知识库检索相关信息
        relevant_docs = await knowledge_manager.search_knowledge(
            message.message, top_k=3
        )
        
        # 构建系统提示
        system_prompt = """你是一个专业的智能客服助手。请根据提供的知识库信息回答用户问题。

回答要求：
1. 优先使用知识库中的信息
2. 保持回答准确、友好、专业
3. 如果知识库中没有相关信息，请诚实地告知用户
4. 提供具体的帮助建议
5. 使用中文回答"""

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
        
        # 构建当前用户消息内容
        user_content = message.message
        if relevant_docs:
            context_info = "\n\n[相关知识库信息]\n" + "\n".join([
                f"• {doc['title']}: {doc['content'][:300]}..." if len(doc['content']) > 300 else f"• {doc['title']}: {doc['content']}"
                for doc in relevant_docs
            ])
            user_content += context_info
        
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
                    keep_alive="10m"  # 保持模型10分钟
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
                            _, after_think = current_text.split("</think>", 1)
                            in_thinking = False
                            current_text = after_think
                        elif in_thinking:
                            # 在思考中，丢弃这部分内容
                            break
                        else:
                            # 没有在思考中，添加剩余内容
                            if current_text.strip():
                                parts.append(current_text)
                            break
                    
                    # 如果不在思考中且没有完整的标签，保留用于输出
                    if not in_thinking and current_text and "<think>" not in current_text:
                        parts.append(current_text)
                    elif not in_thinking and current_text and "<think>" in current_text:
                        # 可能有不完整的标签，保存到缓冲区
                        thinking_buffer = current_text
                    
                    # 输出非思考部分的内容
                    for part in parts:
                        if part.strip():
                            response_content += part
                            chunk_data = {"content": part, "type": "chunk"}
                            yield f"data: {json.dumps(chunk_data, ensure_ascii=False)}\n\n"
                
                # 处理剩余的缓冲区内容（如果不在思考中）
                if thinking_buffer and not in_thinking:
                    response_content += thinking_buffer
                    chunk_data = {"content": thinking_buffer, "type": "chunk"}
                    yield f"data: {json.dumps(chunk_data, ensure_ascii=False)}\n\n"
                
                # 发送完成信号
                done_data = {
                    "type": "done", 
                    "full_response": response_content,
                    "relevant_docs": relevant_docs
                }
                yield f"data: {json.dumps(done_data, ensure_ascii=False)}\n\n"
                
            except Exception as e:
                logger.error(f"聊天流式响应错误: {e}")
                error_data = {"type": "error", "error": str(e)}
                yield f"data: {json.dumps(error_data, ensure_ascii=False)}\n\n"
        
        return StreamingResponse(
            generate(),
            media_type="text/plain",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Access-Control-Allow-Origin": "*",
            }
        )
    
    except Exception as e:
        logger.error(f"聊天接口错误: {e}")
        raise HTTPException(status_code=500, detail=str(e))



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
        return {"success": True, "id": result["id"], "message": "知识库条目添加成功"}
    except Exception as e:
        logger.error(f"添加知识库条目错误: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/knowledge/list")
async def list_knowledge(
    category: Optional[str] = None,
    page: int = 1,
    size: int = 20
):
    """获取知识库列表"""
    try:
        result = await knowledge_manager.list_knowledge(
            category=category,
            page=page,
            size=size
        )
        return result
    except Exception as e:
        logger.error(f"获取知识库列表错误: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/knowledge/{knowledge_id}")
async def delete_knowledge(knowledge_id: str):
    """删除知识库条目"""
    try:
        await knowledge_manager.delete_knowledge(knowledge_id)
        return {"success": True, "message": "知识库条目删除成功"}
    except Exception as e:
        logger.error(f"删除知识库条目错误: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/knowledge/search")
async def search_knowledge(query: SearchQuery):
    """搜索知识库"""
    try:
        results = await knowledge_manager.search_knowledge(
            query.query,
            top_k=query.top_k or 5
        )
        return {"results": results}
    except Exception as e:
        logger.error(f"搜索知识库错误: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/knowledge/upload")
async def upload_knowledge_file(file: UploadFile = File(...)):
    """上传知识库文件"""
    try:
        result = await knowledge_manager.upload_file(file)
        return {"success": True, "message": f"文件上传成功，共处理 {result['count']} 条知识"}
    except Exception as e:
        logger.error(f"上传知识库文件错误: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/knowledge/stats")
async def get_knowledge_stats():
    """获取知识库统计信息"""
    try:
        stats = await knowledge_manager.get_stats()
        return stats
    except Exception as e:
        logger.error(f"获取知识库统计错误: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/knowledge/categories")
async def get_categories():
    """获取知识库分类列表"""
    try:
        categories = await knowledge_manager.get_categories()
        return {"categories": categories}
    except Exception as e:
        logger.error(f"获取分类列表错误: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/web/parse")
async def parse_web_url(request: WebUrlRequest):
    """解析网页URL并提取内容"""
    try:
        # 验证URL格式
        if not web_scraper.validate_url(request.url):
            raise HTTPException(status_code=400, detail="无效的URL格式")
        
        # 抓取网页内容
        scraped_data = await web_scraper.scrape_url(request.url)
        
        # 如果选择自动添加到知识库
        if request.auto_add_to_knowledge:
            await knowledge_manager.add_knowledge(
                title=scraped_data['title'],
                content=f"来源：{scraped_data['url']}\n\n{scraped_data['description']}\n\n{scraped_data['content']}",
                category=request.category or "web_content",
                tags=[scraped_data['domain'], "网页内容"]
            )
            
        return {
            "success": True,
            "data": scraped_data,
            "message": "网页解析成功" + ("，已添加到知识库" if request.auto_add_to_knowledge else "")
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"网页解析错误: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ===== 编码规则管理 API =====

@app.post("/api/coding-rules")
async def add_coding_rule(item: CodingRuleItem):
    """添加编码规则"""
    try:
        rule_id = await coding_rules_manager.add_coding_rule(
            title=item.title,
            description=item.description,
            language=item.language,
            content=item.content,
            example=item.example or "",
            category=item.category or "general",
            tags=item.tags or []
        )
        return {"success": True, "data": {"id": rule_id}, "message": "编码规则添加成功"}
    except Exception as e:
        logger.error(f"添加编码规则错误: {e}")
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
        result = await coding_rules_manager.get_coding_rules(
            page=page,
            page_size=page_size,
            category=category,
            language=language
        )
        return {"success": True, "data": result}
    except Exception as e:
        logger.error(f"获取编码规则列表错误: {e}")
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
        
        # 更新编码规则（通过删除再添加的方式）
        await coding_rules_manager.delete_coding_rule(rule_id)
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

@app.post("/api/coding-rules/search")
async def search_coding_rules(query: SearchQuery):
    """搜索编码规则"""
    try:
        results = await coding_rules_manager.search_coding_rules(
            query.query,
            top_k=query.top_k or 10
        )
        return {"success": True, "data": {"results": results}}
    except Exception as e:
        logger.error(f"搜索编码规则错误: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/coding-rules/stats")
async def get_coding_rules_stats():
    """获取编码规则统计信息"""
    try:
        stats = await coding_rules_manager.get_statistics()
        return {"success": True, "data": stats}
    except Exception as e:
        logger.error(f"获取编码规则统计错误: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/coding-rules/categories")
async def get_coding_rules_categories():
    """获取编码规则分类列表"""
    try:
        categories = await coding_rules_manager.get_categories()
        return {"success": True, "data": {"categories": categories}}
    except Exception as e:
        logger.error(f"获取编码规则分类错误: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/coding-rules/languages")
async def get_coding_rules_languages():
    """获取编码规则编程语言列表"""
    try:
        languages = await coding_rules_manager.get_languages()
        return {"success": True, "data": {"languages": languages}}
    except Exception as e:
        logger.error(f"获取编程语言列表错误: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/coding-rules/upload")
async def upload_coding_rules_file(file: UploadFile = File(...)):
    """上传文件解析编码规则"""
    try:
        # 保存上传的文件
        import tempfile
        import os
        
        # 检查文件类型
        allowed_extensions = {'.py', '.js', '.ts', '.java', '.cpp', '.go', '.rs', '.md', '.txt', '.json', '.yaml', '.yml'}
        file_ext = os.path.splitext(file.filename)[1].lower()
        
        if file_ext not in allowed_extensions:
            raise HTTPException(status_code=400, detail="不支持的文件格式")
        
        # 创建临时文件
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_file_path = temp_file.name
        
        try:
            # 解析文件中的编码规则
            rules = await coding_rules_manager.parse_file_for_coding_rules(temp_file_path, file.filename)
            
            # 添加解析出的规则到数据库
            added_count = 0
            for rule in rules:
                try:
                    await coding_rules_manager.add_coding_rule(
                        title=rule['title'],
                        description=rule['description'],
                        language=rule['language'],
                        content=rule['content'],
                        example=rule['example'],
                        category=rule['category'],
                        tags=rule['tags'],
                        file_name=file.filename
                    )
                    added_count += 1
                except Exception as e:
                    logger.warning(f"添加规则失败: {rule['title']}, 错误: {e}")
            
            return {
                "success": True,
                "data": {
                    "parsed_rules": len(rules),
                    "added_rules": added_count,
                    "rules": rules
                },
                "message": f"文件解析完成，共解析出 {len(rules)} 个编码规则，成功添加 {added_count} 个"
            }
            
        finally:
            # 清理临时文件
            os.unlink(temp_file_path)
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"上传编码规则文件错误: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/coding-rules/apply")
async def apply_coding_rule(request: ApplyCodingRuleRequest):
    """将编码规则应用到文本上"""
    try:
        result = await coding_rules_manager.apply_coding_rule_to_text(
            text=request.text,
            rule_id=request.rule_id
        )
        return {"success": True, "data": {"result": result}, "message": "编码规则应用成功"}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"应用编码规则错误: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info") 