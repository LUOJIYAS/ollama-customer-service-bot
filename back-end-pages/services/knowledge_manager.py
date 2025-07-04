"""
知识库管理服务
整合Ollama和ChromaDB，提供完整的知识库管理功能
"""

import os
import json
import uuid
from typing import List, Dict, Any, Optional
from datetime import datetime
from fastapi import UploadFile
import asyncio
from collections import defaultdict

# 文档处理库
import PyPDF2
import docx
import pandas as pd

from loguru import logger
from .vector_store import VectorStore
from .ollama_client import OllamaClient


class KnowledgeManager:
    """知识库管理器"""
    
    def __init__(self, vector_store: VectorStore, ollama_client: OllamaClient):
        """
        初始化知识库管理器
        
        Args:
            vector_store: 向量数据库服务
            ollama_client: Ollama客户端
        """
        self.vector_store = vector_store
        self.ollama_client = ollama_client
        
    async def add_knowledge(
        self,
        title: str,
        content: str,
        category: str = "general",
        tags: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        添加知识库条目
        
        Args:
            title: 标题
            content: 内容
            category: 分类
            tags: 标签列表
            
        Returns:
            Dict[str, Any]: 添加结果，包含ID等信息
        """
        try:
            if not content.strip():
                raise ValueError("知识内容不能为空")
            
            # 生成嵌入向量
            embeddings = await self.ollama_client.get_embeddings([content])
            if not embeddings:
                raise Exception("生成嵌入向量失败")
            
            # 准备元数据 (ChromaDB不支持list类型，需要转换为字符串)
            metadata = {
                "title": title,
                "category": category,
                "tags": ",".join(tags) if tags else "",  # 将列表转换为逗号分隔的字符串
                "content_length": len(content),
                "created_at": datetime.now().isoformat()
            }
            
            # 添加到向量数据库
            doc_id = str(uuid.uuid4())
            await self.vector_store.add_documents(
                documents=[content],
                embeddings=embeddings,
                metadatas=[metadata],
                ids=[doc_id]
            )
            
            logger.info(f"成功添加知识库条目: {title}")
            return {
                "id": doc_id,
                "title": title,
                "category": category,
                "tags": tags,
                "created_at": metadata["created_at"]
            }
            
        except Exception as e:
            logger.error(f"添加知识库条目失败: {e}")
            raise
    
    async def search_knowledge(
        self,
        query: str,
        top_k: int = 5,
        category: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        搜索知识库
        
        Args:
            query: 搜索查询
            top_k: 返回结果数量
            category: 分类过滤
            
        Returns:
            List[Dict[str, Any]]: 搜索结果
        """
        try:
            if not query.strip():
                return []
            
            # 生成查询向量
            query_embeddings = await self.ollama_client.get_embeddings([query])
            if not query_embeddings:
                logger.warning("生成查询向量失败")
                return []
            
            # 设置过滤条件
            filter_metadata = None
            if category:
                filter_metadata = {"category": category}
            
            # 执行向量搜索
            results = await self.vector_store.search_similar(
                query_embedding=query_embeddings[0],
                top_k=top_k,
                filter_metadata=filter_metadata
            )
            
            # 格式化结果
            formatted_results = []
            for result in results:
                metadata = result.get("metadata", {})
                # 将标签字符串转换回列表
                tags_str = metadata.get("tags", "")
                tags_list = tags_str.split(",") if tags_str else []
                
                # 正确计算相似度：ChromaDB返回的是距离，距离越小相似度越高
                distance = result.get("distance", 1.0)
                # 对于余弦距离，相似度 = 1 - 距离，但需要确保结果在合理范围内
                # 如果距离为负数，说明向量夹角大于90度，相似度应该较低
                if distance < 0:
                    similarity = max(0.0, 1 + distance)  # 将负距离转换为正相似度
                else:
                    similarity = max(0.0, 1 - distance)  # 标准转换，确保不小于0
                
                formatted_result = {
                    "id": result["id"],
                    "title": metadata.get("title", "无标题"),
                    "content": result["content"],
                    "category": metadata.get("category", "general"),
                    "tags": tags_list,
                    "similarity": similarity,
                    "distance": distance,  # 保留原始距离用于调试
                    "created_at": metadata.get("created_at")
                }
                formatted_results.append(formatted_result)
                
            # 按相似度从高到低排序，确保最相关的结果在前面
            formatted_results.sort(key=lambda x: x["similarity"], reverse=True)
            
            logger.info(f"知识库搜索返回 {len(formatted_results)} 个结果")
            return formatted_results
            
        except Exception as e:
            logger.error(f"搜索知识库失败: {e}")
            return []
    
    async def get_knowledge(self, knowledge_id: str) -> Optional[Dict[str, Any]]:
        """
        获取单个知识库条目
        
        Args:
            knowledge_id: 知识库条目ID
            
        Returns:
            Optional[Dict[str, Any]]: 知识库条目信息，如果不存在返回None
        """
        try:
            # 从向量数据库获取文档
            document = await self.vector_store.get_document(knowledge_id)
            if not document:
                logger.warning(f"知识库条目不存在: {knowledge_id}")
                return None
            
            # 格式化返回结果
            metadata = document.get("metadata", {})
            tags_str = metadata.get("tags", "")
            tags_list = tags_str.split(",") if tags_str else []
            
            formatted_item = {
                "id": document["id"],
                "title": metadata.get("title", "无标题"),
                "content": document["content"],
                "category": metadata.get("category", "general"),
                "tags": tags_list,
                "content_length": metadata.get("content_length", len(document["content"])),
                "created_at": metadata.get("created_at"),
                "updated_at": metadata.get("updated_at")
            }
            
            logger.info(f"成功获取知识库条目: {knowledge_id}")
            return formatted_item
            
        except Exception as e:
            logger.error(f"获取知识库条目失败: {e}")
            return None

    async def delete_knowledge(self, knowledge_id: str) -> bool:
        """
        删除知识库条目
        
        Args:
            knowledge_id: 知识库条目ID
            
        Returns:
            bool: 是否删除成功
        """
        try:
            success = await self.vector_store.delete_document(knowledge_id)
            if success:
                logger.info(f"成功删除知识库条目: {knowledge_id}")
            return success
            
        except Exception as e:
            logger.error(f"删除知识库条目失败: {e}")
            return False
    
    async def delete_knowledge_batch(self, knowledge_ids: List[str]) -> Dict[str, Any]:
        """
        批量删除知识库条目
        
        Args:
            knowledge_ids: 知识库条目ID列表
            
        Returns:
            Dict[str, Any]: 删除结果
        """
        try:
            if not knowledge_ids:
                logger.warning("尝试批量删除时提供了空的ID列表")
                return {"success": False, "deleted_count": 0, "message": "提供的ID列表为空"}
            
            result = await self.vector_store.delete_documents(knowledge_ids)
            
            if result["success"]:
                logger.info(f"成功批量删除知识库条目，数量: {result['deleted_count']}")
                return {
                    "success": True,
                    "deleted_count": result["deleted_count"],
                    "message": f"成功删除 {result['deleted_count']} 条知识"
                }
            else:
                logger.error(f"批量删除知识库条目失败: {result.get('error', '未知错误')}")
                return {
                    "success": False,
                    "deleted_count": 0,
                    "message": f"批量删除失败: {result.get('error', '未知错误')}"
                }
            
        except Exception as e:
            logger.error(f"批量删除知识库条目失败: {e}")
            return {
                "success": False,
                "deleted_count": 0,
                "message": f"批量删除失败: {str(e)}"
            }
    
    async def update_knowledge(
        self,
        knowledge_id: str,
        title: Optional[str] = None,
        content: Optional[str] = None,
        category: Optional[str] = None,
        tags: Optional[List[str]] = None
    ) -> bool:
        """
        更新知识库条目
        
        Args:
            knowledge_id: 知识库条目ID
            title: 新标题
            content: 新内容
            category: 新分类
            tags: 新标签
            
        Returns:
            bool: 是否更新成功
        """
        try:
            # 获取现有文档
            existing_doc = await self.vector_store.get_document(knowledge_id)
            if not existing_doc:
                logger.error(f"知识库条目不存在: {knowledge_id}")
                return False
            
            # 更新内容
            new_content = content or existing_doc["content"]
            existing_metadata = existing_doc["metadata"]
            
            # 更新元数据
            # 处理标签：将列表转换为逗号分隔的字符串
            existing_tags_str = existing_metadata.get("tags", "")
            existing_tags_list = existing_tags_str.split(",") if existing_tags_str else []
            final_tags = tags if tags is not None else existing_tags_list
            tags_str = ",".join(final_tags) if final_tags else ""
            
            new_metadata = {
                "title": title or existing_metadata.get("title", "无标题"),
                "category": category or existing_metadata.get("category", "general"),
                "tags": tags_str,  # 存储为逗号分隔的字符串
                "content_length": len(new_content),
                "created_at": existing_metadata.get("created_at"),
                "updated_at": datetime.now().isoformat()
            }
            
            # 如果内容改变，重新生成嵌入向量
            if content and content != existing_doc["content"]:
                new_embeddings = await self.ollama_client.get_embeddings([new_content])
                if not new_embeddings:
                    raise Exception("生成新嵌入向量失败")
                new_embedding = new_embeddings[0]
            else:
                # 如果内容未改变，使用原有向量（这里需要重新获取）
                # 为简化，我们重新生成向量
                new_embeddings = await self.ollama_client.get_embeddings([new_content])
                new_embedding = new_embeddings[0] if new_embeddings else []
            
            # 更新文档
            success = await self.vector_store.update_document(
                document_id=knowledge_id,
                document=new_content,
                embedding=new_embedding,
                metadata=new_metadata
            )
            
            if success:
                logger.info(f"成功更新知识库条目: {knowledge_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"更新知识库条目失败: {e}")
            return False
    
    async def list_knowledge(
        self,
        category: Optional[str] = None,
        page: int = 1,
        size: int = 20
    ) -> Dict[str, Any]:
        """
        获取知识库列表
        
        Args:
            category: 分类过滤
            page: 页码
            size: 页面大小
            
        Returns:
            Dict[str, Any]: 分页结果
        """
        try:
            offset = (page - 1) * size
            filter_metadata = {"category": category} if category else None
            
            # 获取文档列表
            documents = await self.vector_store.list_documents(
                limit=size,
                offset=offset,
                filter_metadata=filter_metadata
            )
            
            # 格式化结果
            formatted_docs = []
            for doc in documents:
                metadata = doc.get("metadata", {})
                formatted_doc = {
                    "id": doc["id"],
                    "title": metadata.get("title", "无标题"),
                    "content": doc["content"][:200] + "..." if len(doc["content"]) > 200 else doc["content"],
                    "category": metadata.get("category", "general"),
                    "tags": metadata.get("tags", []),
                    "content_length": metadata.get("content_length", len(doc["content"])),
                    "created_at": metadata.get("created_at"),
                    "updated_at": metadata.get("updated_at")
                }
                formatted_docs.append(formatted_doc)
            
            # 获取总数（简化实现，实际应该单独查询总数）
            stats = await self.vector_store.get_collection_stats()
            total = stats.get("total_documents", 0)
            
            return {
                "items": formatted_docs,
                "total": total,
                "page": page,
                "size": size,
                "pages": (total + size - 1) // size
            }
            
        except Exception as e:
            logger.error(f"获取知识库列表失败: {e}")
            return {
                "items": [],
                "total": 0,
                "page": page,
                "size": size,
                "pages": 0
            }
    
    async def upload_file(self, file: UploadFile) -> Dict[str, Any]:
        """
        上传知识库文件
        
        Args:
            file: 上传的文件
            
        Returns:
            Dict[str, Any]: 处理结果
        """
        try:
            if not file.filename:
                raise ValueError("文件名不能为空")
            
            # 读取文件内容
            content = await file.read()
            filename = file.filename.lower()
            
            # 根据文件类型解析内容
            texts = []
            
            if filename.endswith('.txt'):
                texts = [content.decode('utf-8')]
                
            elif filename.endswith('.pdf'):
                texts = await self._parse_pdf(content)
                
            elif filename.endswith('.docx'):
                texts = await self._parse_docx(content)
                
            elif filename.endswith(('.xlsx', '.xls')):
                texts = await self._parse_excel(content)
                
            elif filename.endswith('.json'):
                texts = await self._parse_json(content)
                
            else:
                raise ValueError(f"不支持的文件类型: {filename}")
            
            # 批量添加到知识库
            count = 0
            for i, text in enumerate(texts):
                if text.strip():
                    await self.add_knowledge(
                        title=f"{file.filename} - 片段 {i+1}",
                        content=text.strip(),
                        category="uploaded",
                        tags=["uploaded", file.filename]
                    )
                    count += 1
            
            logger.info(f"文件上传处理完成: {file.filename}, 共处理 {count} 条知识")
            return {"count": count, "filename": file.filename}
            
        except Exception as e:
            logger.error(f"文件上传处理失败: {e}")
            raise
    
    async def _parse_pdf(self, content: bytes) -> List[str]:
        """解析PDF文件"""
        try:
            import io
            pdf_file = io.BytesIO(content)
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            
            texts = []
            for page in pdf_reader.pages:
                text = page.extract_text()
                if text.strip():
                    texts.append(text)
            
            return texts
        except Exception as e:
            logger.error(f"PDF解析失败: {e}")
            return []
    
    async def _parse_docx(self, content: bytes) -> List[str]:
        """解析Word文档"""
        try:
            import io
            doc_file = io.BytesIO(content)
            doc = docx.Document(doc_file)
            
            texts = []
            for paragraph in doc.paragraphs:
                if paragraph.text.strip():
                    texts.append(paragraph.text)
            
            return texts
        except Exception as e:
            logger.error(f"Word文档解析失败: {e}")
            return []
    
    async def _parse_excel(self, content: bytes) -> List[str]:
        """解析Excel文件"""
        try:
            import io
            excel_file = io.BytesIO(content)
            df = pd.read_excel(excel_file)
            
            texts = []
            for index, row in df.iterrows():
                row_text = " | ".join([str(val) for val in row.values if pd.notna(val)])
                if row_text.strip():
                    texts.append(row_text)
            
            return texts
        except Exception as e:
            logger.error(f"Excel文件解析失败: {e}")
            return []
    
    async def _parse_json(self, content: bytes) -> List[str]:
        """解析JSON文件"""
        try:
            data = json.loads(content.decode('utf-8'))
            
            texts = []
            if isinstance(data, list):
                for item in data:
                    if isinstance(item, dict):
                        text = json.dumps(item, ensure_ascii=False, indent=2)
                        texts.append(text)
                    else:
                        texts.append(str(item))
            elif isinstance(data, dict):
                texts.append(json.dumps(data, ensure_ascii=False, indent=2))
            else:
                texts.append(str(data))
            
            return texts
        except Exception as e:
            logger.error(f"JSON文件解析失败: {e}")
            return []
    
    async def get_stats(self) -> Dict[str, Any]:
        """获取知识库统计信息"""
        try:
            # 获取基本统计
            basic_stats = await self.vector_store.get_collection_stats()
            
            # 获取分类统计
            all_docs = await self.vector_store.list_documents(limit=1000)  # 简化实现
            category_stats = defaultdict(int)
            tag_stats = defaultdict(int)
            
            for doc in all_docs:
                metadata = doc.get("metadata", {})
                category = metadata.get("category", "general")
                tags_str = metadata.get("tags", "")
                tags = tags_str.split(",") if tags_str else []
                
                category_stats[category] += 1
                for tag in tags:
                    if tag.strip():  # 避免空标签
                        tag_stats[tag.strip()] += 1
            
            return {
                "total_documents": basic_stats["total_documents"],
                "categories": dict(category_stats),
                "popular_tags": dict(sorted(tag_stats.items(), key=lambda x: x[1], reverse=True)[:10]),
                "collection_info": basic_stats
            }
            
        except Exception as e:
            logger.error(f"获取统计信息失败: {e}")
            return {
                "total_documents": 0,
                "categories": {},
                "popular_tags": {},
                "collection_info": {}
            }
    
    async def get_categories(self) -> List[str]:
        """获取所有分类"""
        try:
            all_docs = await self.vector_store.list_documents(limit=1000)  # 简化实现
            categories = set()
            
            for doc in all_docs:
                metadata = doc.get("metadata", {})
                category = metadata.get("category", "general")
                categories.add(category)
            
            return sorted(list(categories))
            
        except Exception as e:
            logger.error(f"获取分类列表失败: {e}")
            return ["general"] 