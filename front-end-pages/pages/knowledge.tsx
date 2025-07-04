import { useState, useEffect } from 'react'
import {
  Layout,
  Card,
  Table,
  Button,
  Input,
  Modal,
  Form,
  Select,
  Space,
  Typography,
  Tag,
  Popconfirm,
  message,
  Upload,
  Row,
  Col,
  Statistic,
  Tabs,
  Empty,
  Spin
} from 'antd'
import {
  PlusOutlined,
  SearchOutlined,
  EditOutlined,
  DeleteOutlined,
  UploadOutlined,
  DownloadOutlined,
  FilterOutlined,
  EyeOutlined,
  ArrowLeftOutlined,
  LinkOutlined
} from '@ant-design/icons'
import { KnowledgeService } from '../services/knowledgeService'
import type { KnowledgeItem, KnowledgeStats } from '../services/knowledgeService'
import Link from 'next/link'
import { API_ENDPOINTS } from '../config/api'

const { Header, Content } = Layout
const { Title, Text, Paragraph } = Typography
const { Search } = Input
const { TextArea } = Input
const { Option } = Select
const { TabPane } = Tabs

export default function KnowledgePage() {
  const [knowledgeList, setKnowledgeList] = useState<KnowledgeItem[]>([])
  const [loading, setLoading] = useState(false)
  const [stats, setStats] = useState<KnowledgeStats | null>(null)
  const [categories, setCategories] = useState<string[]>([])
  const [selectedCategory, setSelectedCategory] = useState<string>()
  const [searchKeyword, setSearchKeyword] = useState('')
  const [currentPage, setCurrentPage] = useState(1)
  const [pageSize] = useState(10)
  const [total, setTotal] = useState(0)
  const [selectedRowKeys, setSelectedRowKeys] = useState<React.Key[]>([])
  const [batchDeleteLoading, setBatchDeleteLoading] = useState(false)

  // Modal状态
  const [modalVisible, setModalVisible] = useState(false)
  const [editingItem, setEditingItem] = useState<KnowledgeItem | null>(null)
  const [viewModalVisible, setViewModalVisible] = useState(false)
  const [viewingItem, setViewingItem] = useState<KnowledgeItem | null>(null)
  const [uploadModalVisible, setUploadModalVisible] = useState(false)
  const [webUrlModalVisible, setWebUrlModalVisible] = useState(false)
  const [webUrlLoading, setWebUrlLoading] = useState(false)

  const [form] = Form.useForm()
  const knowledgeService = new KnowledgeService()

  useEffect(() => {
    loadData()
    // 当页面或分类变化时，清除行选择
    setSelectedRowKeys([])
  }, [currentPage, selectedCategory])

  const loadData = async () => {
    setLoading(true)
    // 清除选择
    setSelectedRowKeys([])
    try {
      await Promise.all([
        loadKnowledgeList(),
        loadStats(),
        loadCategories()
      ])
    } catch (error) {
      message.error('加载数据失败')
    } finally {
      setLoading(false)
    }
  }

  const loadKnowledgeList = async () => {
    try {
      const response = await knowledgeService.getKnowledgeList(
        selectedCategory,
        currentPage,
        pageSize
      )
      setKnowledgeList(response.items)
      setTotal(response.total)
    } catch (error) {
      message.error('加载知识库列表失败')
    }
  }

  const loadStats = async () => {
    try {
      const statsData = await knowledgeService.getStats()
      setStats(statsData)
    } catch (error) {
      console.error('加载统计信息失败:', error)
    }
  }

  const loadCategories = async () => {
    try {
      const response = await knowledgeService.getCategories()
      setCategories(response.categories)
    } catch (error) {
      console.error('加载分类列表失败:', error)
    }
  }

  const handleSearch = async (keyword: string) => {
    if (!keyword.trim()) {
      loadKnowledgeList()
      return
    }

    setLoading(true)
    try {
      const response = await knowledgeService.searchKnowledge({
        query: keyword,
        top_k: 20
      })
      setKnowledgeList(response.results || [])
      setTotal((response.results || []).length)
    } catch (error) {
      message.error('搜索失败')
    } finally {
      setLoading(false)
    }
  }

  const handleAddOrEdit = async (values: any) => {
    try {
      if (editingItem) {
        // 更新知识库条目
        await knowledgeService.updateKnowledge(editingItem.id, values)
        message.success('更新成功')
      } else {
        // 添加新的知识库条目
        await knowledgeService.addKnowledge(values)
        message.success('添加成功')
      }
      setModalVisible(false)
      form.resetFields()
      setEditingItem(null)
      loadData()
    } catch (error) {
      console.error('操作失败:', error)
      message.error(editingItem ? '更新失败' : '添加失败')
    }
  }

  const handleDelete = async (id: string) => {
    try {
      await knowledgeService.deleteKnowledge(id)
      message.success('删除成功')
      loadData()
    } catch (error) {
      message.error('删除失败')
    }
  }

  const handleBatchDelete = async () => {
    if (selectedRowKeys.length === 0) {
      message.warning('请先选择要删除的条目')
      return
    }

    setBatchDeleteLoading(true)
    try {
      const result = await knowledgeService.batchDeleteKnowledge(selectedRowKeys as string[])
      if (result.success) {
        message.success(`成功删除 ${result.deleted_count} 条知识`)
        setSelectedRowKeys([]) // 清空选择
        loadData() // 重新加载数据
      } else {
        message.error(result.message || '批量删除失败')
      }
    } catch (error) {
      message.error('批量删除失败')
      console.error('批量删除错误:', error)
    } finally {
      setBatchDeleteLoading(false)
    }
  }

  const handleEdit = (item: KnowledgeItem) => {
    setEditingItem(item)
    form.setFieldsValue({
      title: item.title,
      content: item.content,
      category: item.category,
      tags: item.tags
    })
    setModalVisible(true)
  }

  const handleView = (item: KnowledgeItem) => {
    setViewingItem(item)
    setViewModalVisible(true)
  }

  const handleAdd = () => {
    setEditingItem(null)
    form.resetFields()
    setModalVisible(true)
  }

  const handleUpload = async (info: any) => {
    const { status } = info.file
    if (status === 'done') {
      message.success(`${info.file.name} 文件上传成功`)
      setUploadModalVisible(false)
      loadData()
    } else if (status === 'error') {
      message.error(`${info.file.name} 文件上传失败`)
    }
  }

  const handleWebUrlImport = async (values: any) => {
    setWebUrlLoading(true)
    try {
      await knowledgeService.importWebUrl({
        url: values.url,
        category: values.category || 'web_content',
        auto_add_to_knowledge: true
      })
      message.success('网页内容导入成功')
      setWebUrlModalVisible(false)
      form.resetFields()
      loadData()
    } catch (error) {
      message.error('网页内容导入失败')
    } finally {
      setWebUrlLoading(false)
    }
  }

  const columns = [
    {
      title: '标题',
      dataIndex: 'title',
      key: 'title',
      ellipsis: true,
      render: (text: string, record: KnowledgeItem) => (
        <Button type="link" onClick={() => handleView(record)}>
          {text}
        </Button>
      ),
    },
    {
      title: '分类',
      dataIndex: 'category',
      key: 'category',
      width: 120,
      render: (category: string) => (
        <Tag color="blue">{category}</Tag>
      ),
    },
    {
      title: '标签',
      dataIndex: 'tags',
      key: 'tags',
      width: 200,
      render: (tags: string[] | string | null | undefined) => {
        // 处理不同的tags数据格式
        let tagArray: string[] = []
        
        if (Array.isArray(tags)) {
          tagArray = tags
        } else if (typeof tags === 'string') {
          // 如果是字符串，尝试解析为数组
          try {
            tagArray = JSON.parse(tags)
          } catch {
            // 如果解析失败，按逗号分割
            tagArray = tags.split(',').map(tag => tag.trim()).filter(tag => tag)
          }
        }
        
        return (
          <Space wrap>
            {tagArray.map(tag => (
              <Tag key={tag} color="orange">
                {tag}
              </Tag>
            ))}
          </Space>
        )
      },
    },
    {
      title: '内容预览',
      dataIndex: 'content',
      key: 'content',
      ellipsis: true,
      render: (content: string) => (
        <Text type="secondary">
          {content.length > 50 ? content.substring(0, 50) + '...' : content}
        </Text>
      ),
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 180,
      render: (date: string) => new Date(date).toLocaleString(),
    },
    {
      title: '操作',
      key: 'actions',
      width: 150,
      render: (_: any, record: KnowledgeItem) => (
        <Space>
          <Button
            type="text"
            icon={<EyeOutlined />}
            onClick={() => handleView(record)}
          />
          <Button
            type="text"
            icon={<EditOutlined />}
            onClick={() => handleEdit(record)}
          />
          <Popconfirm
            title="确定要删除这条知识吗？"
            onConfirm={() => handleDelete(record.id)}
            okText="确定"
            cancelText="取消"
          >
            <Button type="text" danger icon={<DeleteOutlined />} />
          </Popconfirm>
        </Space>
      ),
    },
  ]

  return (
    <Layout style={{ minHeight: '100vh', background: '#f5f5f5' }}>
      {/* 头部导航 */}
      <Header style={{ background: '#fff', padding: '0 24px', boxShadow: '0 2px 8px rgba(0,0,0,0.1)' }}>
        <div style={{ display: 'flex', alignItems: 'center', height: '100%' }}>
          <Link href="/">
            <Button type="text" icon={<ArrowLeftOutlined />}>
              返回首页
            </Button>
          </Link>
          <Title level={3} style={{ margin: '0 0 0 16px', color: '#1890ff' }}>
            知识库管理
          </Title>
        </div>
      </Header>

      <Content style={{ padding: '24px' }}>
        {/* 统计卡片 */}
        {stats && (
          <Row gutter={16} style={{ marginBottom: '24px' }}>
            <Col span={6}>
              <Card>
                <Statistic
                  title="知识条目总数"
                  value={stats?.total_count || 0}
                  valueStyle={{ color: '#1890ff' }}
                />
              </Card>
            </Col>
            <Col span={6}>
              <Card>
                <Statistic
                  title="总查询次数"
                  value={stats?.total_queries || 0}
                  valueStyle={{ color: '#52c41a' }}
                />
              </Card>
            </Col>
            <Col span={6}>
              <Card>
                <Statistic
                  title="数据库大小"
                  value={Math.round((stats?.total_size || 0) / (1024 * 1024))}
                  suffix="MB"
                  valueStyle={{ color: '#fa8c16' }}
                />
              </Card>
            </Col>
            <Col span={6}>
              <Card>
                <Statistic
                  title="分类数量"
                  value={stats?.categories?.length || 0}
                  valueStyle={{ color: '#722ed1' }}
                />
              </Card>
            </Col>
          </Row>
        )}

        {/* 主要内容卡片 */}
        <Card>
          {/* 操作栏 */}
          <div style={{ marginBottom: '16px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <Space>
              <Button
                type="primary"
                icon={<PlusOutlined />}
                onClick={handleAdd}
              >
                添加知识
              </Button>
              <Button
                icon={<UploadOutlined />}
                onClick={() => setUploadModalVisible(true)}
              >
                批量上传
              </Button>
              <Button
                icon={<LinkOutlined />}
                onClick={() => setWebUrlModalVisible(true)}
              >
                导入网页
              </Button>
              <Popconfirm
                title={`确定要删除选中的 ${selectedRowKeys.length} 条知识吗？`}
                onConfirm={handleBatchDelete}
                okText="确定"
                cancelText="取消"
                disabled={selectedRowKeys.length === 0}
              >
                <Button
                  danger
                  icon={<DeleteOutlined />}
                  disabled={selectedRowKeys.length === 0}
                  loading={batchDeleteLoading}
                >
                  批量删除
                </Button>
              </Popconfirm>
              {selectedRowKeys.length > 0 && (
                <Button 
                  icon={<FilterOutlined />}
                  onClick={() => setSelectedRowKeys([])}
                >
                  清除选择 ({selectedRowKeys.length})
                </Button>
              )}
            </Space>

            <Space>
              <Select
                placeholder="选择分类"
                style={{ width: 150 }}
                allowClear
                value={selectedCategory}
                onChange={(value) => {
                  setSelectedCategory(value)
                  setCurrentPage(1)
                }}
              >
                {(categories || []).map(category => (
                  <Option key={category} value={category}>
                    {category}
                  </Option>
                ))}
              </Select>
              <Search
                placeholder="搜索知识库..."
                style={{ width: 300 }}
                onSearch={handleSearch}
                enterButton={<SearchOutlined />}
              />
            </Space>
          </div>

          {/* 知识库表格 */}
          <Table
            columns={columns}
            dataSource={knowledgeList}
            rowKey="id"
            loading={loading}
            rowSelection={{
              selectedRowKeys,
              onChange: (selectedKeys) => setSelectedRowKeys(selectedKeys),
              selections: [
                Table.SELECTION_ALL,
                Table.SELECTION_INVERT,
                Table.SELECTION_NONE
              ]
            }}
            pagination={{
              current: currentPage,
              pageSize: pageSize,
              total: total,
              showSizeChanger: false,
              showQuickJumper: true,
              showTotal: (total, range) =>
                `第 ${range[0]}-${range[1]} 条，共 ${total} 条`,
              onChange: (page) => setCurrentPage(page),
            }}
            locale={{
              emptyText: (
                <Empty
                  description="暂无知识库数据"
                  image={Empty.PRESENTED_IMAGE_SIMPLE}
                />
              ),
            }}
          />
        </Card>

        {/* 添加/编辑弹窗 */}
        <Modal
          title={editingItem ? '编辑知识' : '添加知识'}
          open={modalVisible}
          onCancel={() => {
            setModalVisible(false)
            setEditingItem(null)
            form.resetFields()
          }}
          footer={null}
          width={800}
        >
          <Form form={form} layout="vertical" onFinish={handleAddOrEdit}>
            <Form.Item
              label="标题"
              name="title"
              rules={[{ required: true, message: '请输入知识标题' }]}
            >
              <Input placeholder="请输入知识标题" />
            </Form.Item>

            <Form.Item
              label="分类"
              name="category"
              rules={[{ required: true, message: '请选择或输入分类' }]}
            >
                          <Select
              placeholder="选择分类或输入新分类"
              showSearch
              allowClear
            >
                {(categories || []).map(category => (
                  <Option key={category} value={category}>
                    {category}
                  </Option>
                ))}
              </Select>
            </Form.Item>

            <Form.Item
              label="内容"
              name="content"
              rules={[{ required: true, message: '请输入知识内容' }]}
            >
              <TextArea
                rows={8}
                placeholder="请输入知识内容，支持Markdown格式"
              />
            </Form.Item>

            <Form.Item
              label="标签"
              name="tags"
            >
              <Select
                mode="tags"
                placeholder="输入标签，按回车添加"
                style={{ width: '100%' }}
              />
            </Form.Item>

            <Form.Item>
              <Space>
                <Button type="primary" htmlType="submit">
                  {editingItem ? '更新' : '添加'}
                </Button>
                <Button onClick={() => setModalVisible(false)}>
                  取消
                </Button>
              </Space>
            </Form.Item>
          </Form>
        </Modal>

        {/* 查看详情弹窗 */}
        <Modal
          title="知识详情"
          open={viewModalVisible}
          onCancel={() => setViewModalVisible(false)}
          footer={[
            <Button key="edit" type="primary" onClick={() => {
              setViewModalVisible(false)
              handleEdit(viewingItem!)
            }}>
              编辑
            </Button>,
            <Button key="close" onClick={() => setViewModalVisible(false)}>
              关闭
            </Button>
          ]}
          width={800}
        >
          {viewingItem && (
            <div>
              <Title level={4}>{viewingItem.title}</Title>
              <Space style={{ marginBottom: '16px' }}>
                <Tag color="blue">{viewingItem.category}</Tag>
                {(() => {
                  // 处理不同的tags数据格式
                  let tagArray: string[] = []
                  const tags = viewingItem.tags as string[] | string | null | undefined
                  
                  if (Array.isArray(tags)) {
                    tagArray = tags
                  } else if (typeof tags === 'string') {
                    // 如果是字符串，尝试解析为数组
                    try {
                      const parsed = JSON.parse(tags)
                      tagArray = Array.isArray(parsed) ? parsed : []
                    } catch {
                      // 如果解析失败，按逗号分割
                      tagArray = tags.split(',').map((tag: string) => tag.trim()).filter((tag: string) => tag)
                    }
                  }
                  
                  return tagArray.map((tag: string) => (
                    <Tag key={tag} color="orange">{tag}</Tag>
                  ))
                })()}
              </Space>
              <Paragraph>
                <Text strong>创建时间：</Text>
                {new Date(viewingItem.created_at).toLocaleString()}
              </Paragraph>
              <Paragraph>
                <Text strong>内容：</Text>
              </Paragraph>
              <div style={{ 
                background: '#fafafa', 
                padding: '16px', 
                borderRadius: '8px',
                maxHeight: '400px',
                overflowY: 'auto'
              }}>
                <pre style={{ 
                  whiteSpace: 'pre-wrap', 
                  fontFamily: 'inherit',
                  margin: 0
                }}>
                  {viewingItem.content}
                </pre>
              </div>
            </div>
          )}
        </Modal>

        {/* 批量上传弹窗 */}
        <Modal
          title="批量上传知识库文件"
          open={uploadModalVisible}
          onCancel={() => setUploadModalVisible(false)}
          footer={null}
          width={600}
        >
          <Upload.Dragger
            name="file"
            multiple
                          action={API_ENDPOINTS.KNOWLEDGE_UPLOAD}
            onChange={handleUpload}
            style={{ padding: '20px' }}
          >
            <p className="ant-upload-drag-icon">
              <UploadOutlined style={{ fontSize: '48px', color: '#1890ff' }} />
            </p>
            <p className="ant-upload-text">点击或拖拽文件到此区域上传</p>
            <p className="ant-upload-hint">
              支持 docx, csv, ppt, md, txt, xlsx 等格式的批量上传
            </p>
          </Upload.Dragger>
        </Modal>

        {/* 网页链接导入弹窗 */}
        <Modal
          title="导入网页链接"
          open={webUrlModalVisible}
          onCancel={() => {
            setWebUrlModalVisible(false)
            form.resetFields()
          }}
          footer={null}
          width={600}
        >
          <Form form={form} layout="vertical" onFinish={handleWebUrlImport}>
            <Form.Item
              label="网页链接"
              name="url"
              rules={[
                { required: true, message: '请输入网页链接' },
                { type: 'url', message: '请输入有效的网页链接' }
              ]}
            >
              <Input
                placeholder="请输入要导入的网页链接，如：https://example.com"
                prefix={<LinkOutlined />}
              />
            </Form.Item>

            <Form.Item
              label="分类"
              name="category"
              initialValue="web_content"
            >
              <Select placeholder="选择分类">
                <Option value="web_content">网页内容</Option>
                {(categories || []).map(category => (
                  <Option key={category} value={category}>
                    {category}
                  </Option>
                ))}
              </Select>
            </Form.Item>

            <Form.Item>
              <Space>
                <Button 
                  type="primary" 
                  htmlType="submit"
                  loading={webUrlLoading}
                >
                  导入网页内容
                </Button>
                <Button onClick={() => {
                  setWebUrlModalVisible(false)
                  form.resetFields()
                }}>
                  取消
                </Button>
              </Space>
            </Form.Item>
          </Form>

          <div style={{ 
            background: '#f0f9ff', 
            padding: '12px', 
            borderRadius: '6px',
            marginTop: '16px' 
          }}>
            <Text type="secondary">
              💡 提示：导入的网页内容将自动解析标题、正文，并生成向量化数据用于智能检索。
            </Text>
          </div>
        </Modal>
      </Content>
    </Layout>
  )
} 