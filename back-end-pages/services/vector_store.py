"""
ChromaDB 向量数据库服务
用于存储和检索知识库向量数据
"""

import chromadb
from chromadb.config import Settings
from typing import List, Dict, Any, Optional
import uuid
from datetime import datetime
from loguru import logger


class VectorStore:
    """ChromaDB向量数据库服务"""
    
    def __init__(self, persist_directory: str = "./data/chroma_db"):
        """
        初始化向量数据库
        
        Args:
            persist_directory: 数据库持久化目录
        """
        self.persist_directory = persist_directory
        self.client = None
        self.collection = None
        self.collection_name = "knowledge_base"
        
    async def initialize(self):
        """初始化数据库连接和集合"""
        try:
            # 创建ChromaDB客户端
            self.client = chromadb.PersistentClient(
                path=self.persist_directory,
                settings=Settings(
                    anonymized_telemetry=False,
                    allow_reset=True
                )
            )
            
            # 获取或创建集合
            try:
                self.collection = self.client.get_collection(
                    name=self.collection_name
                )
                logger.info(f"已连接到现有集合: {self.collection_name}")
            except:
                self.collection = self.client.create_collection(
                    name=self.collection_name,
                    metadata={"description": "智能客服知识库向量集合"}
                )
                logger.info(f"已创建新集合: {self.collection_name}")
                
        except Exception as e:
            logger.error(f"向量数据库初始化失败: {e}")
            raise
    
    async def add_documents(
        self,
        documents: List[str],
        embeddings: List[List[float]],
        metadatas: List[Dict[str, Any]],
        ids: Optional[List[str]] = None
    ) -> List[str]:
        """
        添加文档到向量数据库
        
        Args:
            documents: 文档内容列表
            embeddings: 嵌入向量列表
            metadatas: 元数据列表
            ids: 文档ID列表，如果为None会自动生成
            
        Returns:
            List[str]: 文档ID列表
        """
        try:
            if not self.collection:
                raise Exception("向量数据库未初始化")
            
            # 生成ID（如果未提供）
            if ids is None:
                ids = [str(uuid.uuid4()) for _ in documents]
            
            # 添加创建时间到元数据
            for metadata in metadatas:
                metadata["created_at"] = datetime.now().isoformat()
            
            # 添加文档到集合
            self.collection.add(
                documents=documents,
                embeddings=embeddings,  # type: ignore
                metadatas=metadatas,  # type: ignore
                ids=ids
            )
            
            logger.info(f"成功添加 {len(documents)} 个文档到向量数据库")
            return ids
            
        except Exception as e:
            logger.error(f"添加文档到向量数据库失败: {e}")
            raise
    
    async def search_similar(
        self,
        query_embedding: List[float],
        top_k: int = 5,
        filter_metadata: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        搜索相似文档
        
        Args:
            query_embedding: 查询向量
            top_k: 返回结果数量
            filter_metadata: 元数据过滤条件
            
        Returns:
            List[Dict[str, Any]]: 搜索结果列表
        """
        try:
            if not self.collection:
                raise Exception("向量数据库未初始化")
            
            # 执行向量搜索
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k,
                where=filter_metadata
            )
            
            # 格式化结果
            formatted_results = []
            if results["documents"] and results["documents"][0]:
                for i in range(len(results["documents"][0])):
                    result = {
                        "id": results["ids"][0][i],
                        "content": results["documents"][0][i],
                        "metadata": results["metadatas"][0][i] if results["metadatas"] else {},
                        "distance": results["distances"][0][i] if results["distances"] else 0
                    }
                    formatted_results.append(result)
            
            logger.info(f"向量搜索返回 {len(formatted_results)} 个结果")
            return formatted_results
            
        except Exception as e:
            logger.error(f"向量搜索失败: {e}")
            raise
    
    async def delete_document(self, document_id: str) -> bool:
        """
        删除文档
        
        Args:
            document_id: 文档ID
            
        Returns:
            bool: 是否删除成功
        """
        try:
            if not self.collection:
                raise Exception("向量数据库未初始化")
            
            self.collection.delete(ids=[document_id])
            logger.info(f"成功删除文档: {document_id}")
            return True
            
        except Exception as e:
            logger.error(f"删除文档失败: {e}")
            return False
    
    async def delete_documents(self, document_ids: List[str]) -> Dict[str, Any]:
        """
        批量删除文档
        
        Args:
            document_ids: 文档ID列表
            
        Returns:
            Dict[str, Any]: 删除结果，包含成功删除数量
        """
        try:
            if not self.collection:
                raise Exception("向量数据库未初始化")
            
            if not document_ids:
                logger.warning("尝试批量删除时提供了空的ID列表")
                return {"success": False, "deleted_count": 0, "error": "提供的ID列表为空"}
            
            self.collection.delete(ids=document_ids)
            logger.info(f"成功批量删除文档，数量: {len(document_ids)}")
            return {"success": True, "deleted_count": len(document_ids)}
            
        except Exception as e:
            logger.error(f"批量删除文档失败: {e}")
            return {"success": False, "deleted_count": 0, "error": str(e)}
    
    async def update_document(
        self,
        document_id: str,
        document: str,
        embedding: List[float],
        metadata: Dict[str, Any]
    ) -> bool:
        """
        更新文档
        
        Args:
            document_id: 文档ID
            document: 新文档内容
            embedding: 新嵌入向量
            metadata: 新元数据
            
        Returns:
            bool: 是否更新成功
        """
        try:
            if not self.collection:
                raise Exception("向量数据库未初始化")
            
            # 添加更新时间
            metadata["updated_at"] = datetime.now().isoformat()
            
            # 更新文档
            self.collection.update(
                ids=[document_id],
                documents=[document],
                embeddings=[embedding],
                metadatas=[metadata]
            )
            
            logger.info(f"成功更新文档: {document_id}")
            return True
            
        except Exception as e:
            logger.error(f"更新文档失败: {e}")
            return False
    
    async def get_document(self, document_id: str) -> Optional[Dict[str, Any]]:
        """
        获取单个文档
        
        Args:
            document_id: 文档ID
            
        Returns:
            Optional[Dict[str, Any]]: 文档信息，如果不存在返回None
        """
        try:
            if not self.collection:
                raise Exception("向量数据库未初始化")
            
            results = self.collection.get(ids=[document_id])
            
            if results["documents"] and results["documents"][0]:
                return {
                    "id": results["ids"][0],
                    "content": results["documents"][0],
                    "metadata": results["metadatas"][0] if results["metadatas"] else {}
                }
            
            return None
            
        except Exception as e:
            logger.error(f"获取文档失败: {e}")
            return None
    
    async def list_documents(
        self,
        limit: int = 100,
        offset: int = 0,
        filter_metadata: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        列出文档
        
        Args:
            limit: 限制数量
            offset: 偏移量
            filter_metadata: 元数据过滤条件
            
        Returns:
            List[Dict[str, Any]]: 文档列表
        """
        try:
            if not self.collection:
                raise Exception("向量数据库未初始化")
            
            results = self.collection.get(
                where=filter_metadata,
                limit=limit,
                offset=offset
            )
            
            documents = []
            if results["documents"]:
                for i in range(len(results["documents"])):
                    doc = {
                        "id": results["ids"][i],
                        "content": results["documents"][i],
                        "metadata": results["metadatas"][i] if results["metadatas"] else {}
                    }
                    documents.append(doc)
            
            return documents
            
        except Exception as e:
            logger.error(f"列出文档失败: {e}")
            return []
    
    async def get_collection_stats(self) -> Dict[str, Any]:
        """
        获取集合统计信息
        
        Returns:
            Dict[str, Any]: 统计信息
        """
        try:
            if not self.collection:
                raise Exception("向量数据库未初始化")
            
            count = self.collection.count()
            
            return {
                "total_documents": count,
                "collection_name": self.collection_name,
                "persist_directory": self.persist_directory
            }
            
        except Exception as e:
            logger.error(f"获取集合统计失败: {e}")
            return {
                "total_documents": 0,
                "collection_name": self.collection_name,
                "persist_directory": self.persist_directory
            }
    
    async def reset_collection(self) -> bool:
        """
        重置集合（删除所有数据）
        
        Returns:
            bool: 是否重置成功
        """
        try:
            if not self.collection:
                raise Exception("向量数据库未初始化")
            
            # 删除现有集合
            if self.client:
                self.client.delete_collection(name=self.collection_name)
                
                # 重新创建集合
                self.collection = self.client.create_collection(
                    name=self.collection_name,
                    metadata={"description": "智能客服知识库向量集合"}
                )
            
            logger.info(f"成功重置集合: {self.collection_name}")
            return True
            
        except Exception as e:
            logger.error(f"重置集合失败: {e}")
            return False 