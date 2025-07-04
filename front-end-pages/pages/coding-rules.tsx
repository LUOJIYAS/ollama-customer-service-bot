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
  Empty,
  Pagination,
  Divider,
  Spin,
  Dropdown,
  Menu
} from 'antd'
import {
  PlusOutlined,
  SearchOutlined,
  EditOutlined,
  DeleteOutlined,
  UploadOutlined,
  FilterOutlined,
  EyeOutlined,
  ArrowLeftOutlined,
  CodeOutlined
} from '@ant-design/icons'
import Link from 'next/link'
import { API_ENDPOINTS } from '../config/api'

const { Header, Content } = Layout
const { Title, Text, Paragraph } = Typography
const { Search } = Input
const { TextArea } = Input
const { Option } = Select

interface CodingRule {
  id: string
  title: string
  description: string
  language: string
  content: string
  example: string
  category: string
  tags: string[]
  file_name?: string
  created_at: string
  updated_at: string
}

interface CodingRuleStats {
  total_rules: number
  total_languages: number
  total_categories: number
  recent_uploads: number
}

export default function CodingRulesPage() {
  const [rulesList, setRulesList] = useState<CodingRule[]>([])
  const [loading, setLoading] = useState(false)
  const [stats, setStats] = useState<CodingRuleStats | null>(null)
  const [categories, setCategories] = useState<string[]>([])
  const [languages, setLanguages] = useState<string[]>([])
  const [selectedCategory, setSelectedCategory] = useState<string>()
  const [selectedLanguage, setSelectedLanguage] = useState<string>()
  const [searchKeyword, setSearchKeyword] = useState('')
  const [currentPage, setCurrentPage] = useState(1)
  const [pageSize] = useState(10)
  const [total, setTotal] = useState(0)

  // Modal状态
  const [modalVisible, setModalVisible] = useState(false)
  const [editingItem, setEditingItem] = useState<CodingRule | null>(null)
  const [viewModalVisible, setViewModalVisible] = useState(false)
  const [viewingItem, setViewingItem] = useState<CodingRule | null>(null)
  const [uploadModalVisible, setUploadModalVisible] = useState(false)

  const [form] = Form.useForm()

  useEffect(() => {
    loadData()
  }, [currentPage, selectedCategory, selectedLanguage])

  const loadData = async () => {
    setLoading(true)
    try {
      await Promise.all([
        loadRulesList(),
        loadStats(),
        loadCategories(),
        loadLanguages()
      ])
    } catch (error) {
      message.error('加载数据失败')
    } finally {
      setLoading(false)
    }
  }

  const loadRulesList = async () => {
    try {
      const params = new URLSearchParams({
        page: currentPage.toString(),
        page_size: pageSize.toString()
      })
      
      if (selectedCategory) params.append('category', selectedCategory)
      if (selectedLanguage) params.append('language', selectedLanguage)
      
      const response = await fetch(`${API_ENDPOINTS.CODING_RULES}?${params}`)
      const data = await response.json()
      
      if (data.success && data.data && Array.isArray(data.data.items)) {
        setRulesList(data.data.items)
        setTotal(data.data.total || 0)
      } else {
        setRulesList([])
        setTotal(0)
        if (data.message) {
          message.error(data.message)
        }
      }
    } catch (error) {
      console.error('加载编码规则列表失败:', error)
      setRulesList([])
      setTotal(0)
      message.error('加载编码规则列表失败')
    }
  }

  const loadStats = async () => {
    try {
      const response = await fetch(API_ENDPOINTS.CODING_RULES_STATS)
      const data = await response.json()
      
      if (data.success) {
        setStats(data.data)
      }
    } catch (error) {
      console.error('加载统计信息失败:', error)
    }
  }

  const loadCategories = async () => {
    try {
      const response = await fetch(API_ENDPOINTS.CODING_RULES_CATEGORIES)
      const data = await response.json()
      
      if (data.success && data.data && Array.isArray(data.data.categories)) {
        setCategories(data.data.categories)
      } else {
        setCategories([])
      }
    } catch (error) {
      console.error('加载分类列表失败:', error)
      setCategories([])
    }
  }

  const loadLanguages = async () => {
    try {
      const response = await fetch(API_ENDPOINTS.CODING_RULES_LANGUAGES)
      const data = await response.json()
      
      if (data.success && data.data && Array.isArray(data.data.languages)) {
        setLanguages(data.data.languages)
      } else {
        setLanguages([])
      }
    } catch (error) {
      console.error('加载编程语言列表失败:', error)
      setLanguages([])
    }
  }

  const handleSearch = async (keyword: string) => {
    if (!keyword.trim()) {
      loadRulesList()
      return
    }

    setLoading(true)
    try {
      const response = await fetch(API_ENDPOINTS.CODING_RULES_SEARCH, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          query: keyword,
          top_k: 20
        })
      })
      const data = await response.json()
      
      if (data.success && data.data && Array.isArray(data.data.results)) {
        setRulesList(data.data.results)
        setTotal(data.data.results.length)
      } else {
        setRulesList([])
        setTotal(0)
        if (data.message) {
          message.error(data.message)
        }
      }
    } catch (error) {
      console.error('搜索失败:', error)
      setRulesList([])
      setTotal(0)
      message.error('搜索失败')
    } finally {
      setLoading(false)
    }
  }

  const handleAddOrEdit = async (values: any) => {
    try {
      // 处理tags字段：将逗号分隔的字符串转换为数组
      const processedValues = {
        ...values,
        tags: values.tags 
          ? values.tags.split(',').map((tag: string) => tag.trim()).filter((tag: string) => tag !== '')
          : []
      }
      
      const url = editingItem 
        ? `${API_ENDPOINTS.CODING_RULES}/${editingItem.id}`
        : API_ENDPOINTS.CODING_RULES
      
      const response = await fetch(url, {
        method: editingItem ? 'PUT' : 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(processedValues)
      })
      
      const data = await response.json()
      
      if (data.success) {
        message.success(editingItem ? '更新成功' : '添加成功')
        setModalVisible(false)
        form.resetFields()
        loadData()
      } else {
        message.error(data.message || (editingItem ? '更新失败' : '添加失败'))
      }
    } catch (error) {
      message.error(editingItem ? '更新失败' : '添加失败')
    }
  }

  const handleDelete = async (id: string) => {
    try {
      const response = await fetch(`${API_ENDPOINTS.CODING_RULES}/${id}`, {
        method: 'DELETE'
      })
      const data = await response.json()
      
      if (data.success) {
        message.success('删除成功')
        loadData()
      } else {
        message.error(data.message || '删除失败')
      }
    } catch (error) {
      message.error('删除失败')
    }
  }

  const handleEdit = (item: CodingRule) => {
    setEditingItem(item)
    form.setFieldsValue({
      title: item.title,
      description: item.description,
      language: item.language,
      content: item.content,
      example: item.example,
      category: item.category,
      tags: Array.isArray(item.tags) ? item.tags.join(', ') : item.tags
    })
    setModalVisible(true)
  }

  const handleView = (item: CodingRule) => {
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
      message.success(`${info.file.name} 文件上传成功，正在解析编码规则...`)
      setUploadModalVisible(false)
      loadData()
    } else if (status === 'error') {
      message.error(`${info.file.name} 文件上传失败`)
    }
  }

  const columns = [
    {
      title: '规则名称',
      dataIndex: 'title',
      key: 'title',
      width: '20%',
      render: (text: string, record: CodingRule) => (
        <Space direction="vertical" size={0}>
          <Text strong>{text}</Text>
          <Text type="secondary" style={{ fontSize: '12px' }}>
            {record.file_name && `来源: ${record.file_name}`}
          </Text>
        </Space>
      )
    },
    {
      title: '编程语言',
      dataIndex: 'language',
      key: 'language',
      width: '12%',
      render: (language: string) => (
        <Tag color="blue">{language}</Tag>
      )
    },
    {
      title: '分类',
      dataIndex: 'category',
      key: 'category',
      width: '12%',
      render: (category: string) => (
        <Tag color="green">{category}</Tag>
      )
    },
    {
      title: '描述',
      dataIndex: 'description',
      key: 'description',
      width: '25%',
      render: (text: string) => (
        <Paragraph ellipsis={{ rows: 2, expandable: false }}>
          {text}
        </Paragraph>
      )
    },
    {
      title: '标签',
      dataIndex: 'tags',
      key: 'tags',
      width: '15%',
      render: (tags: string[] | string) => {
        let tagsArray: string[] = []
        
        if (Array.isArray(tags)) {
          tagsArray = tags
        } else if (typeof tags === 'string') {
          try {
            tagsArray = JSON.parse(tags)
          } catch {
            tagsArray = tags.split(',').map(tag => tag.trim()).filter(tag => tag)
          }
        }
        
        return (
          <Space wrap>
            {(tagsArray || []).slice(0, 2).map((tag, index) => (
              <Tag key={index} color="orange" style={{ fontSize: '12px' }}>
                {tag}
              </Tag>
            ))}
            {(tagsArray || []).length > 2 && (
              <Tag color="default" style={{ fontSize: '12px' }}>
                +{(tagsArray || []).length - 2}
              </Tag>
            )}
          </Space>
        )
      }
    },
    {
      title: '操作',
      key: 'action',
      width: '16%',
      render: (_: any, record: CodingRule) => (
        <Space size="small">
          <Button
            type="text"
            icon={<EyeOutlined />}
            onClick={() => handleView(record)}
            title="查看详情"
          />
          <Button
            type="text"
            icon={<EditOutlined />}
            onClick={() => handleEdit(record)}
            title="编辑"
          />
          <Popconfirm
            title="确定要删除这个编码规则吗？"
            onConfirm={() => handleDelete(record.id)}
            okText="确定"
            cancelText="取消"
          >
            <Button
              type="text"
              danger
              icon={<DeleteOutlined />}
              title="删除"
            />
          </Popconfirm>
        </Space>
      )
    }
  ]

  const renderStatsCards = () => (
    <Row gutter={16} style={{ marginBottom: '24px' }}>
      <Col span={6}>
        <Card>
          <Statistic
            title="编码规则总数"
            value={stats?.total_rules || 0}
            prefix={<CodeOutlined />}
          />
        </Card>
      </Col>
      <Col span={6}>
        <Card>
          <Statistic
            title="支持语言"
            value={stats?.total_languages || 0}
            prefix={<CodeOutlined />}
          />
        </Card>
      </Col>
      <Col span={6}>
        <Card>
          <Statistic
            title="规则分类"
            value={stats?.total_categories || 0}
            prefix={<FilterOutlined />}
          />
        </Card>
      </Col>
      <Col span={6}>
        <Card>
          <Statistic
            title="最近上传"
            value={stats?.recent_uploads || 0}
            prefix={<UploadOutlined />}
          />
        </Card>
      </Col>
    </Row>
  )

  return (
    <Layout style={{ minHeight: '100vh', background: '#f5f5f5' }}>
      <Header style={{ background: '#fff', padding: '0 24px', boxShadow: '0 2px 8px rgba(0,0,0,0.06)' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <div style={{ display: 'flex', alignItems: 'center' }}>
            <Link href="/">
              <Button type="text" icon={<ArrowLeftOutlined />} style={{ marginRight: '16px' }}>
                返回主页
              </Button>
            </Link>
            <Title level={3} style={{ margin: 0, color: '#1890ff' }}>
              编码学习管理
            </Title>
          </div>
          <Space>
            <Button
              type="primary"
              icon={<UploadOutlined />}
              onClick={() => setUploadModalVisible(true)}
            >
              上传文件解析
            </Button>
            <Button
              type="primary"
              icon={<PlusOutlined />}
              onClick={handleAdd}
            >
              手动添加规则
            </Button>
          </Space>
        </div>
      </Header>

      <Content style={{ padding: '24px' }}>
        {renderStatsCards()}

        <Card>
          <div style={{ marginBottom: '16px' }}>
            <Row gutter={16}>
              <Col span={8}>
                <Search
                  placeholder="搜索编码规则..."
                  allowClear
                  onSearch={handleSearch}
                  style={{ width: '100%' }}
                />
              </Col>
              <Col span={4}>
                <Select
                  placeholder="选择分类"
                  allowClear
                  value={selectedCategory}
                  onChange={setSelectedCategory}
                  style={{ width: '100%' }}
                >
                  {(categories || []).map(category => (
                    <Option key={category} value={category}>{category}</Option>
                  ))}
                </Select>
              </Col>
              <Col span={4}>
                <Select
                  placeholder="选择语言"
                  allowClear
                  value={selectedLanguage}
                  onChange={setSelectedLanguage}
                  style={{ width: '100%' }}
                >
                  {(languages || []).map(language => (
                    <Option key={language} value={language}>{language}</Option>
                  ))}
                </Select>
              </Col>
            </Row>
          </div>

          <Table
            columns={columns}
            dataSource={rulesList}
            loading={loading}
            rowKey="id"
            pagination={{
              current: currentPage,
              pageSize: pageSize,
              total: total,
              onChange: setCurrentPage,
              showSizeChanger: false,
              showTotal: (total, range) => `第 ${range[0]}-${range[1]} 条，共 ${total} 条`
            }}
            locale={{
              emptyText: (
                <Empty
                  image={Empty.PRESENTED_IMAGE_SIMPLE}
                  description="暂无编码规则数据"
                >
                  <Button type="primary" onClick={handleAdd}>
                    添加第一个编码规则
                  </Button>
                </Empty>
              )
            }}
          />
        </Card>
      </Content>

      {/* 添加/编辑编码规则弹窗 */}
      <Modal
        title={editingItem ? '编辑编码规则' : '添加编码规则'}
        open={modalVisible}
        onCancel={() => setModalVisible(false)}
        footer={null}
        width={800}
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={handleAddOrEdit}
        >
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                label="规则名称"
                name="title"
                rules={[{ required: true, message: '请输入规则名称' }]}
              >
                <Input placeholder="例如：Python函数命名规范" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                label="编程语言"
                name="language"
                rules={[{ required: true, message: '请选择编程语言' }]}
              >
                <Select placeholder="选择编程语言">
                  <Option value="Python">Python</Option>
                  <Option value="JavaScript">JavaScript</Option>
                  <Option value="TypeScript">TypeScript</Option>
                  <Option value="Java">Java</Option>
                  <Option value="C++">C++</Option>
                  <Option value="Go">Go</Option>
                  <Option value="Rust">Rust</Option>
                  <Option value="其他">其他</Option>
                </Select>
              </Form.Item>
            </Col>
          </Row>
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                label="分类"
                name="category"
                rules={[{ required: true, message: '请输入分类' }]}
              >
                <Input placeholder="例如：命名规范、代码风格、设计模式" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                label="标签"
                name="tags"
                help="多个标签用逗号分隔"
              >
                <Input placeholder="例如：函数,命名,规范" />
              </Form.Item>
            </Col>
          </Row>
          <Form.Item
            label="描述"
            name="description"
            rules={[{ required: true, message: '请输入描述' }]}
          >
            <TextArea rows={3} placeholder="描述这个编码规则的作用和适用场景" />
          </Form.Item>
          <Form.Item
            label="编码规则内容"
            name="content"
            rules={[{ required: true, message: '请输入编码规则内容' }]}
          >
            <TextArea rows={6} placeholder="详细描述编码规则，包括具体要求、注意事项等" />
          </Form.Item>
          <Form.Item
            label="示例代码"
            name="example"
          >
            <TextArea rows={4} placeholder="提供示例代码，展示如何应用这个编码规则" />
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

      {/* 查看编码规则详情弹窗 */}
      <Modal
        title="编码规则详情"
        open={viewModalVisible}
        onCancel={() => setViewModalVisible(false)}
        footer={[
          <Button key="close" onClick={() => setViewModalVisible(false)}>
            关闭
          </Button>
        ]}
        width={900}
      >
        {viewingItem && (
          <div>
            <Row gutter={16} style={{ marginBottom: '16px' }}>
              <Col span={12}>
                <Text strong>规则名称：</Text>
                <Text>{viewingItem.title}</Text>
              </Col>
              <Col span={12}>
                <Text strong>编程语言：</Text>
                <Tag color="blue">{viewingItem.language}</Tag>
              </Col>
            </Row>
            <Row gutter={16} style={{ marginBottom: '16px' }}>
              <Col span={12}>
                <Text strong>分类：</Text>
                <Tag color="green">{viewingItem.category}</Tag>
              </Col>
              <Col span={12}>
                <Text strong>标签：</Text>
                <Space wrap>
                  {(() => {
                    let tagsArray: string[] = []
                    const tags = viewingItem.tags as any
                    
                    if (Array.isArray(tags)) {
                      tagsArray = tags
                    } else if (typeof tags === 'string') {
                      try {
                        if (tags.startsWith('[')) {
                          tagsArray = JSON.parse(tags)
                        } else {
                          tagsArray = tags.split(',').map((tag: string) => tag.trim()).filter((tag: string) => tag)
                        }
                      } catch {
                        tagsArray = []
                      }
                    }
                    
                    return (tagsArray || []).map((tag: string, index: number) => (
                      <Tag key={index} color="orange">{tag}</Tag>
                    ))
                  })()}
                </Space>
              </Col>
            </Row>
            <div style={{ marginBottom: '16px' }}>
              <Text strong>描述：</Text>
              <Paragraph style={{ marginTop: '8px' }}>
                {viewingItem.description}
              </Paragraph>
            </div>
            <div style={{ marginBottom: '16px' }}>
              <Text strong>编码规则内容：</Text>
              <Card style={{ marginTop: '8px', background: '#f9f9f9' }}>
                <pre style={{ whiteSpace: 'pre-wrap', margin: 0 }}>
                  {viewingItem.content}
                </pre>
              </Card>
            </div>
            {viewingItem.example && (
              <div>
                <Text strong>示例代码：</Text>
                <Card style={{ marginTop: '8px', background: '#f6f8fa' }}>
                  <pre style={{ whiteSpace: 'pre-wrap', margin: 0 }}>
                    <code>{viewingItem.example}</code>
                  </pre>
                </Card>
              </div>
            )}
          </div>
        )}
      </Modal>

      {/* 文件上传弹窗 */}
      <Modal
        title="上传文件解析编码规则"
        open={uploadModalVisible}
        onCancel={() => setUploadModalVisible(false)}
        footer={null}
        width={600}
      >
        <div style={{ marginBottom: '16px' }}>
          <Text type="secondary">
            上传代码文件或文档文件，系统将自动解析其中的编码规则和编程风格，生成可复用的编码规范。
          </Text>
        </div>
        <Upload.Dragger
          name="file"
          multiple
                        action={API_ENDPOINTS.CODING_RULES_UPLOAD}
          onChange={handleUpload}
          style={{ padding: '20px' }}
          accept=".py,.js,.ts,.java,.cpp,.go,.rs,.md,.txt,.json,.yaml,.yml"
        >
          <p className="ant-upload-drag-icon">
            <UploadOutlined style={{ fontSize: '48px', color: '#1890ff' }} />
          </p>
          <p className="ant-upload-text">点击或拖拽文件到此区域上传</p>
          <p className="ant-upload-hint">
            支持代码文件：.py, .js, .ts, .java, .cpp, .go, .rs<br/>
            支持文档文件：.md, .txt, .json, .yaml
          </p>
        </Upload.Dragger>
      </Modal>
    </Layout>
  )
} 