import React, { useState, useEffect } from 'react';
import { 
  Button, 
  Modal, 
  Table, 
  Tag, 
  Space, 
  Tooltip, 
  message, 
  Card, 
  Statistic, 
  Row, 
  Col,
  Tabs,
  Select,
  Checkbox,
  List,
  Typography,
  Divider,
  Progress,
  Spin
} from 'antd';
import { 
  DownloadOutlined, 
  FileOutlined, 
  FolderOutlined,
  StarOutlined,
  StarFilled,
  DeleteOutlined,
  EyeOutlined,
  PackageOutlined,
  AnalysisOutlined,
  ReloadOutlined
} from '@ant-design/icons';
import type { Session } from '../../types/datamodel';

const { Text, Title } = Typography;
const { TabPane } = Tabs;

interface ConversationFile {
  id: string;
  filename: string;
  file_type: string;
  size: number;
  created_at: string;
  created_by: string;
  description?: string;
  is_deliverable: boolean;
  is_intermediate: boolean;
  tags: string[];
  relative_path: string;
  download_url: string;
}

interface FileStats {
  session_id: number;
  total_files: number;
  deliverable_files: number;
  intermediate_files: number;
  file_types: Record<string, number>;
  agent_statistics: Record<string, any>;
  storage_path: string;
  created_at?: string;
  last_updated?: string;
}

interface DeliverableRecommendation {
  file_id: string;
  filename: string;
  file_type: string;
  relevance_score: number;
  delivery_priority: number;
  recommendation_reason: string;
  suggested_filename?: string;
  customer_description?: string;
  file_size: number;
  created_by: string;
  created_at: string;
  download_url: string;
}

interface DeliverableAnalysis {
  session_id: number;
  task_goal: string;
  recommended_files: DeliverableRecommendation[];
  delivery_summary: string;
  total_files_analyzed: number;
  analysis_timestamp: string;
}

interface FileManagerProps {
  session: Session;
  visible: boolean;
  onClose: () => void;
  taskDescription?: string;
}

const FileManager: React.FC<FileManagerProps> = ({ 
  session, 
  visible, 
  onClose, 
  taskDescription = "用户任务"
}) => {
  const [files, setFiles] = useState<ConversationFile[]>([]);
  const [stats, setStats] = useState<FileStats | null>(null);
  const [analysis, setAnalysis] = useState<DeliverableAnalysis | null>(null);
  const [loading, setLoading] = useState(false);
  const [analyzing, setAnalyzing] = useState(false);
  const [selectedFiles, setSelectedFiles] = useState<Set<string>>(new Set());
  const [filterType, setFilterType] = useState<string>('all');
  const [filterAgent, setFilterAgent] = useState<string>('all');
  const [activeTab, setActiveTab] = useState('files');

  useEffect(() => {
    if (visible && session.id) {
      loadFiles();
      loadStats();
    }
  }, [visible, session.id]);

  const loadFiles = async () => {
    try {
      setLoading(true);
      const params = new URLSearchParams();
      if (filterType !== 'all') {
        params.append('file_type', filterType);
      }
      if (filterAgent !== 'all') {
        params.append('agent_name', filterAgent);
      }

      const response = await fetch(`/api/files/sessions/${session.id}?${params}`);
      if (response.ok) {
        const data = await response.json();
        setFiles(data.files || []);
      } else {
        message.error('加载文件列表失败');
      }
    } catch (error) {
      console.error('Error loading files:', error);
      message.error('加载文件列表失败');
    } finally {
      setLoading(false);
    }
  };

  const loadStats = async () => {
    try {
      const response = await fetch(`/api/files/sessions/${session.id}/stats`);
      if (response.ok) {
        const data = await response.json();
        setStats(data);
      }
    } catch (error) {
      console.error('Error loading stats:', error);
    }
  };

  const analyzeDeliverables = async () => {
    try {
      setAnalyzing(true);
      const response = await fetch(`/api/files/sessions/${session.id}/analyze-deliverables`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          task_description: taskDescription,
          conversation_messages: [] // 可以传入对话消息
        })
      });

      if (response.ok) {
        const data = await response.json();
        setAnalysis(data);
        setActiveTab('analysis');
        message.success('交付物分析完成');
      } else {
        message.error('分析失败');
      }
    } catch (error) {
      console.error('Error analyzing deliverables:', error);
      message.error('分析失败');
    } finally {
      setAnalyzing(false);
    }
  };

  const downloadFile = async (file: ConversationFile) => {
    try {
      const response = await fetch(file.download_url);
      if (response.ok) {
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = file.filename;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
        message.success(`下载 ${file.filename} 成功`);
      } else {
        message.error('下载失败');
      }
    } catch (error) {
      console.error('Error downloading file:', error);
      message.error('下载失败');
    }
  };

  const downloadDeliverablePackage = async () => {
    try {
      setLoading(true);
      const params = new URLSearchParams({
        task_description: taskDescription,
        priority_threshold: '3'
      });

      const response = await fetch(`/api/files/sessions/${session.id}/deliverable-package?${params}`);
      if (response.ok) {
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `session_${session.id}_deliverables.zip`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
        message.success('交付物打包下载成功');
      } else {
        message.error('下载失败');
      }
    } catch (error) {
      console.error('Error downloading package:', error);
      message.error('下载失败');
    } finally {
      setLoading(false);
    }
  };

  const markAsDeliverable = async (fileId: string) => {
    try {
      const response = await fetch(`/api/files/sessions/${session.id}/mark-deliverable`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          file_id: fileId,
          description: '用户标记为交付物'
        })
      });

      if (response.ok) {
        message.success('标记为交付物成功');
        loadFiles();
        loadStats();
      } else {
        message.error('标记失败');
      }
    } catch (error) {
      console.error('Error marking as deliverable:', error);
      message.error('标记失败');
    }
  };

  const getFileTypeIcon = (fileType: string) => {
    const icons = {
      'image': '🖼️',
      'document': '📄',
      'code': '💻',
      'data': '📊',
      'media': '🎵',
      'other': '📎'
    };
    return icons[fileType] || '📎';
  };

  const getFileTypeColor = (fileType: string) => {
    const colors = {
      'image': 'blue',
      'document': 'green',
      'code': 'purple',
      'data': 'orange',
      'media': 'red',
      'other': 'default'
    };
    return colors[fileType] || 'default';
  };

  const getPriorityColor = (priority: number) => {
    if (priority <= 1) return 'red';
    if (priority <= 2) return 'orange';
    if (priority <= 3) return 'blue';
    return 'default';
  };

  const getPriorityText = (priority: number) => {
    if (priority <= 1) return '必须交付';
    if (priority <= 2) return '强烈建议';
    if (priority <= 3) return '建议交付';
    if (priority <= 4) return '可选';
    return '不建议';
  };

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const uniqueAgents = Array.from(new Set(files.map(f => f.created_by)));
  const uniqueTypes = Array.from(new Set(files.map(f => f.file_type)));

  const filteredFiles = files.filter(file => {
    if (filterType !== 'all' && file.file_type !== filterType) return false;
    if (filterAgent !== 'all' && file.created_by !== filterAgent) return false;
    return true;
  });

  const fileColumns = [
    {
      title: '文件名',
      dataIndex: 'filename',
      key: 'filename',
      render: (text: string, record: ConversationFile) => (
        <Space>
          <span>{getFileTypeIcon(record.file_type)}</span>
          <Text strong>{text}</Text>
          {record.is_deliverable && <StarFilled style={{ color: '#faad14' }} />}
        </Space>
      ),
    },
    {
      title: '类型',
      dataIndex: 'file_type',
      key: 'file_type',
      render: (type: string) => (
        <Tag color={getFileTypeColor(type)}>{type}</Tag>
      ),
    },
    {
      title: '大小',
      dataIndex: 'size',
      key: 'size',
      render: (size: number) => formatFileSize(size),
    },
    {
      title: '创建者',
      dataIndex: 'created_by',
      key: 'created_by',
      render: (agent: string) => <Tag>{agent}</Tag>,
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
      render: (time: string) => new Date(time).toLocaleString(),
    },
    {
      title: '状态',
      key: 'status',
      render: (record: ConversationFile) => (
        <Space>
          {record.is_deliverable ? (
            <Tag color="gold">交付物</Tag>
          ) : (
            <Tag>中间产物</Tag>
          )}
        </Space>
      ),
    },
    {
      title: '操作',
      key: 'actions',
      render: (record: ConversationFile) => (
        <Space>
          <Tooltip title="下载">
            <Button 
              icon={<DownloadOutlined />} 
              size="small"
              onClick={() => downloadFile(record)}
            />
          </Tooltip>
          {!record.is_deliverable && (
            <Tooltip title="标记为交付物">
              <Button 
                icon={<StarOutlined />} 
                size="small"
                onClick={() => markAsDeliverable(record.id)}
              />
            </Tooltip>
          )}
        </Space>
      ),
    },
  ];

  const analysisColumns = [
    {
      title: '推荐文件',
      dataIndex: 'filename',
      key: 'filename',
      render: (text: string, record: DeliverableRecommendation) => (
        <Space>
          <span>{getFileTypeIcon(record.file_type)}</span>
          <div>
            <Text strong>{record.suggested_filename || text}</Text>
            <br />
            <Text type="secondary" style={{ fontSize: '12px' }}>
              原文件: {text}
            </Text>
          </div>
        </Space>
      ),
    },
    {
      title: '优先级',
      dataIndex: 'delivery_priority',
      key: 'priority',
      render: (priority: number) => (
        <Tag color={getPriorityColor(priority)}>
          {getPriorityText(priority)}
        </Tag>
      ),
      sorter: (a: DeliverableRecommendation, b: DeliverableRecommendation) => 
        a.delivery_priority - b.delivery_priority,
    },
    {
      title: '相关性评分',
      dataIndex: 'relevance_score',
      key: 'relevance_score',
      render: (score: number) => (
        <Progress 
          percent={score * 100} 
          size="small" 
          format={percent => `${percent?.toFixed(0)}%`}
        />
      ),
      sorter: (a: DeliverableRecommendation, b: DeliverableRecommendation) => 
        b.relevance_score - a.relevance_score,
    },
    {
      title: '推荐理由',
      dataIndex: 'recommendation_reason',
      key: 'reason',
      ellipsis: true,
    },
    {
      title: '客户描述',
      dataIndex: 'customer_description',
      key: 'description',
      ellipsis: true,
    },
    {
      title: '操作',
      key: 'actions',
      render: (record: DeliverableRecommendation) => (
        <Space>
          <Tooltip title="下载">
            <Button 
              icon={<DownloadOutlined />} 
              size="small"
              onClick={() => {
                const file = files.find(f => f.id === record.file_id);
                if (file) downloadFile(file);
              }}
            />
          </Tooltip>
        </Space>
      ),
    },
  ];

  return (
    <Modal
      title={
        <Space>
          <FolderOutlined />
          文件管理 - {session.name}
        </Space>
      }
      visible={visible}
      onCancel={onClose}
      width={1200}
      footer={null}
      destroyOnClose
    >
      <Tabs activeKey={activeTab} onChange={setActiveTab}>
        <TabPane 
          tab={
            <Space>
              <FileOutlined />
              文件列表 ({files.length})
            </Space>
          } 
          key="files"
        >
          <Card size="small" style={{ marginBottom: 16 }}>
            <Row gutter={16}>
              <Col span={6}>
                <Statistic 
                  title="总文件数" 
                  value={stats?.total_files || 0} 
                  prefix={<FileOutlined />}
                />
              </Col>
              <Col span={6}>
                <Statistic 
                  title="交付物" 
                  value={stats?.deliverable_files || 0} 
                  prefix={<StarFilled style={{ color: '#faad14' }} />}
                />
              </Col>
              <Col span={6}>
                <Statistic 
                  title="中间产物" 
                  value={stats?.intermediate_files || 0} 
                />
              </Col>
              <Col span={6}>
                <Space>
                  <Button 
                    type="primary" 
                    icon={<AnalysisOutlined />}
                    onClick={analyzeDeliverables}
                    loading={analyzing}
                  >
                    智能分析
                  </Button>
                  <Button 
                    icon={<ReloadOutlined />}
                    onClick={loadFiles}
                    loading={loading}
                  >
                    刷新
                  </Button>
                </Space>
              </Col>
            </Row>
          </Card>

          <Space style={{ marginBottom: 16 }}>
            <Select
              value={filterType}
              onChange={setFilterType}
              style={{ width: 120 }}
              placeholder="文件类型"
            >
              <Select.Option value="all">所有类型</Select.Option>
              {uniqueTypes.map(type => (
                <Select.Option key={type} value={type}>
                  {getFileTypeIcon(type)} {type}
                </Select.Option>
              ))}
            </Select>
            
            <Select
              value={filterAgent}
              onChange={setFilterAgent}
              style={{ width: 150 }}
              placeholder="创建者"
            >
              <Select.Option value="all">所有创建者</Select.Option>
              {uniqueAgents.map(agent => (
                <Select.Option key={agent} value={agent}>
                  {agent}
                </Select.Option>
              ))}
            </Select>
          </Space>

          <Table
            columns={fileColumns}
            dataSource={filteredFiles}
            rowKey="id"
            loading={loading}
            size="small"
            pagination={{ pageSize: 10 }}
            expandable={{
              expandedRowRender: (record: ConversationFile) => (
                <div style={{ padding: '8px 0' }}>
                  <Text strong>描述: </Text>
                  <Text>{record.description || '无描述'}</Text>
                  <br />
                  <Text strong>路径: </Text>
                  <Text code>{record.relative_path}</Text>
                  <br />
                  <Text strong>标签: </Text>
                  {record.tags.map(tag => (
                    <Tag key={tag} size="small">{tag}</Tag>
                  ))}
                </div>
              ),
            }}
          />
        </TabPane>

        <TabPane 
          tab={
            <Space>
              <AnalysisOutlined />
              智能分析
              {analysis && <Tag color="green">已分析</Tag>}
            </Space>
          } 
          key="analysis"
        >
          {analysis ? (
            <div>
              <Card size="small" style={{ marginBottom: 16 }}>
                <Title level={5}>📋 分析摘要</Title>
                <Text><strong>任务目标:</strong> {analysis.task_goal}</Text>
                <br />
                <Text><strong>分析时间:</strong> {new Date(analysis.analysis_timestamp).toLocaleString()}</Text>
                <br />
                <Text><strong>分析文件数:</strong> {analysis.total_files_analyzed}</Text>
                <Divider />
                <Text>{analysis.delivery_summary}</Text>
                <br />
                <div style={{ marginTop: 16 }}>
                  <Button 
                    type="primary" 
                    icon={<PackageOutlined />}
                    onClick={downloadDeliverablePackage}
                    loading={loading}
                  >
                    下载交付物打包
                  </Button>
                </div>
              </Card>

              <Table
                columns={analysisColumns}
                dataSource={analysis.recommended_files}
                rowKey="file_id"
                size="small"
                pagination={{ pageSize: 10 }}
              />
            </div>
          ) : (
            <div style={{ textAlign: 'center', padding: '40px 0' }}>
              <Title level={4}>🤖 智能交付物分析</Title>
              <Text type="secondary">
                点击"智能分析"按钮，AI将分析对话中的文件，推荐最适合交付给客户的文件组合
              </Text>
              <br />
              <Button 
                type="primary" 
                icon={<AnalysisOutlined />}
                onClick={analyzeDeliverables}
                loading={analyzing}
                style={{ marginTop: 16 }}
              >
                开始智能分析
              </Button>
            </div>
          )}
        </TabPane>
      </Tabs>
    </Modal>
  );
};

export default FileManager;