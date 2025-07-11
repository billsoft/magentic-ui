import React, { useState, useEffect } from 'react';
import { Alert, Button, Badge, Tooltip, Modal, notification } from 'antd';
import { Play, Pause, Square, RotateCcw, Info, Wifi, WifiOff } from 'lucide-react';
import { Run, RunStatus, AgentMessageConfig, TextMessageConfig } from '../types/datamodel';
import { runAPI } from './api';

interface BackgroundTaskIndicatorProps {
  runs: Run[];
  onReconnect: (runId: number) => void;
  onStop: (runId: number) => void;
  onViewDetails: (runId: number) => void;
}

interface BackgroundTaskInfo {
  runId: number;
  sessionId: number;
  sessionName: string;
  status: RunStatus;
  lastUpdate: string;
  taskDescription: string;
  progressInfo?: string;
  isReconnectable?: boolean;
  hasActiveManager?: boolean;
  hasWebSocketConnection?: boolean;
  canReconnect?: boolean;
}

// 提取任务描述的辅助函数
const extractTaskDescription = (task: any): string => {
  if (!task) return 'Unknown task';
  
  if (typeof task === 'string') {
    return task.length > 100 ? task.substring(0, 100) + '...' : task;
  }
  
  if (typeof task === 'object') {
    if (task.content) {
      const content = typeof task.content === 'string' ? task.content : JSON.stringify(task.content);
      return content.length > 100 ? content.substring(0, 100) + '...' : content;
    }
    return JSON.stringify(task).substring(0, 100) + '...';
  }
  
  return 'Task details unavailable';
};

// 检查任务内容是否包含特定关键词
const containsKeywords = (task: any, keywords: string[]): boolean => {
  const taskStr = JSON.stringify(task).toLowerCase();
  return keywords.some(keyword => taskStr.includes(keyword.toLowerCase()));
};

export const BackgroundTaskIndicator: React.FC<BackgroundTaskIndicatorProps> = ({
  runs,
  onReconnect,
  onStop,
  onViewDetails,
}) => {
  const [backgroundTasks, setBackgroundTasks] = useState<BackgroundTaskInfo[]>([]);
  const [showDetails, setShowDetails] = useState(false);
  const [expandedTask, setExpandedTask] = useState<number | null>(null);
  const [reconnectingTasks, setReconnectingTasks] = useState<Set<number>>(new Set());

  // 检测后台任务并增强状态信息
  useEffect(() => {
    const detectBackgroundTasks = async () => {
      const activeTasks = runs.filter(run => 
        run.status === 'active' || 
        run.status === 'awaiting_input' || 
        run.status === 'paused'
      );

      const enhancedTasks: BackgroundTaskInfo[] = [];

      for (const run of activeTasks) {
        try {
          // 🔧 修复：减少健康检查API调用，只在必要时调用
          const healthData = await runAPI.getRunHealth(parseInt(run.id));

          enhancedTasks.push({
            runId: parseInt(run.id),
            sessionId: run.session_id,
            sessionName: `Session ${run.session_id}`,
            status: run.status,
            lastUpdate: run.updated_at || new Date().toISOString(),
            taskDescription: extractTaskDescription(run.task),
            progressInfo: getProgressInfo(run),
            isReconnectable: healthData?.is_reconnectable || false,
            hasActiveManager: healthData?.has_active_manager || false,
            hasWebSocketConnection: healthData?.has_websocket_connection || false,
            canReconnect: healthData?.can_reconnect || false,
          });
        } catch (error) {
          // 🔧 修复：减少健康检查错误的噪音，但保留基本功能
          console.debug(`Health check failed for run ${run.id}:`, error);
          // 添加基本信息，即使没有健康数据
          enhancedTasks.push({
            runId: parseInt(run.id),
            sessionId: run.session_id,
            sessionName: `Session ${run.session_id}`,
            status: run.status,
            lastUpdate: run.updated_at || new Date().toISOString(),
            taskDescription: extractTaskDescription(run.task),
            progressInfo: getProgressInfo(run),
            // 🔧 修复：当健康检查失败时，不假设任务可重连
            isReconnectable: false,
            hasActiveManager: false,
            hasWebSocketConnection: false,
            canReconnect: false,
          });
        }
      }

      setBackgroundTasks(enhancedTasks);
    };

    detectBackgroundTasks();
    
    // 🔧 修复：减少检查频率，避免过度的API调用
    const interval = setInterval(detectBackgroundTasks, 30000); // 每30秒检查一次，而不是15秒
    return () => clearInterval(interval);
  }, [runs]);

  const getProgressInfo = (run: Run): string => {
    if (run.status === 'awaiting_input') {
      return '等待用户输入';
    }
    if (run.status === 'paused') {
      return '任务已暂停';
    }
    if (run.status === 'active') {
      // 根据任务内容判断可能的进度
      if (containsKeywords(run.task, ['绘图', '图表', 'plot', 'chart', 'graph'])) {
        return '正在生成图表...';
      }
      if (containsKeywords(run.task, ['分析', '处理', 'analyze', 'process'])) {
        return '正在分析数据...';
      }
      if (containsKeywords(run.task, ['搜索', 'search', 'browse', '浏览'])) {
        return '正在搜索信息...';
      }
      return '正在执行中...';
    }
    return '未知状态';
  };

  const getStatusIcon = (task: BackgroundTaskInfo) => {
    // 如果正在重连，显示特殊图标
    if (reconnectingTasks.has(task.runId)) {
      return <RotateCcw className="text-blue-500 animate-spin" size={16} />;
    }

    // 根据连接状态显示不同图标
    if (task.canReconnect) {
      return <WifiOff className="text-orange-500" size={16} />;
    }
    
    if (task.hasWebSocketConnection) {
      return <Wifi className="text-green-500" size={16} />;
    }

    switch (task.status) {
      case 'active':
        return <Play className="text-green-500 animate-pulse" size={16} />;
      case 'paused':
        return <Pause className="text-yellow-500" size={16} />;
      case 'awaiting_input':
        return <Info className="text-blue-500 animate-bounce" size={16} />;
      default:
        return <Play className="text-gray-500" size={16} />;
    }
  };

  const getStatusText = (task: BackgroundTaskInfo) => {
    if (reconnectingTasks.has(task.runId)) {
      return '重连中';
    }
    
    if (task.canReconnect) {
      return '可重连';
    }
    
    if (task.hasWebSocketConnection) {
      return '已连接';
    }

    switch (task.status) {
      case 'active':
        return '运行中';
      case 'paused':
        return '已暂停';
      case 'awaiting_input':
        return '等待输入';
      default:
        return '未知';
    }
  };

  const handleManualReconnect = async (taskId: number) => {
    setReconnectingTasks(prev => new Set([...prev, taskId]));
    
    try {
      // 显示通知
      notification.info({
        message: '正在重连',
        description: `正在尝试重新连接到任务 ${taskId}...`,
        duration: 2,
      });

      // 调用重连函数
      onReconnect(taskId);
      
      // 等待一段时间再移除重连状态
      setTimeout(() => {
        setReconnectingTasks(prev => {
          const newSet = new Set(prev);
          newSet.delete(taskId);
          return newSet;
        });
      }, 3000);
      
    } catch (error) {
      console.error('Manual reconnect failed:', error);
      notification.error({
        message: '重连失败',
        description: `无法重新连接到任务 ${taskId}`,
        duration: 4,
      });
      
      setReconnectingTasks(prev => {
        const newSet = new Set(prev);
        newSet.delete(taskId);
        return newSet;
      });
    }
  };

  const truncateText = (text: string, maxLength: number = 100): string => {
    if (text.length <= maxLength) return text;
    return text.substring(0, maxLength) + '...';
  };

  if (backgroundTasks.length === 0) {
    return null;
  }

  return (
    <>
      {/* 悬浮指示器 */}
      <div className="fixed bottom-6 right-6 z-50">
        <Badge count={backgroundTasks.length} offset={[-8, 8]}>
          <Button
            type="primary"
            shape="round"
            size="large"
            icon={<Play size={20} />}
            onClick={() => setShowDetails(true)}
            className="bg-blue-500 hover:bg-blue-600 border-none shadow-lg"
          >
            后台任务
          </Button>
        </Badge>
      </div>

      {/* 详情模态框 */}
      <Modal
        title={
          <div className="flex items-center space-x-2">
            <Play size={20} className="text-blue-500" />
            <span>后台任务管理 ({backgroundTasks.length})</span>
          </div>
        }
        open={showDetails}
        onCancel={() => setShowDetails(false)}
        footer={null}
        width={700}
        className="background-task-modal"
      >
        <div className="space-y-4 max-h-96 overflow-y-auto">
          {backgroundTasks.map((task) => (
            <div
              key={task.runId}
              className="border rounded-lg p-4 hover:bg-gray-50 transition-colors"
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-3">
                  {getStatusIcon(task)}
                  <div>
                    <div className="font-medium text-gray-900">
                      {task.sessionName}
                    </div>
                    <div className="text-sm text-gray-500">
                      运行 ID: {task.runId} • {getStatusText(task)}
                    </div>
                    {task.canReconnect && (
                      <div className="text-xs text-orange-600 mt-1">
                        🔌 WebSocket断开，可以重新连接
                      </div>
                    )}
                  </div>
                </div>
                
                <div className="flex items-center space-x-2">
                  {task.canReconnect && (
                    <Tooltip title="手动重连">
                      <Button
                        type="text"
                        icon={<RotateCcw size={16} />}
                        onClick={() => handleManualReconnect(task.runId)}
                        loading={reconnectingTasks.has(task.runId)}
                        className="text-orange-500 hover:bg-orange-50"
                      />
                    </Tooltip>
                  )}
                  
                  <Tooltip title="重新连接">
                    <Button
                      type="text"
                      icon={<RotateCcw size={16} />}
                      onClick={() => {
                        onReconnect(task.runId);
                        setShowDetails(false);
                      }}
                      loading={reconnectingTasks.has(task.runId)}
                      className="text-blue-500 hover:bg-blue-50"
                    />
                  </Tooltip>
                  
                  <Tooltip title="查看详情">
                    <Button
                      type="text"
                      icon={<Info size={16} />}
                      onClick={() => {
                        onViewDetails(task.runId);
                        setShowDetails(false);
                      }}
                      className="text-gray-500 hover:bg-gray-50"
                    />
                  </Tooltip>
                  
                  <Tooltip title="停止任务">
                    <Button
                      type="text"
                      icon={<Square size={16} />}
                      onClick={() => onStop(task.runId)}
                      className="text-red-500 hover:bg-red-50"
                    />
                  </Tooltip>
                </div>
              </div>
              
              <div className="mt-3">
                <div className="text-sm text-gray-700">
                  <strong>任务：</strong>
                  <span
                    className={`${
                      expandedTask === task.runId ? '' : 'line-clamp-2'
                    }`}
                  >
                    {expandedTask === task.runId 
                      ? task.taskDescription 
                      : truncateText(task.taskDescription)
                    }
                  </span>
                  {task.taskDescription.length > 100 && (
                    <button
                      onClick={() => 
                        setExpandedTask(
                          expandedTask === task.runId ? null : task.runId
                        )
                      }
                      className="text-blue-500 hover:text-blue-700 ml-2"
                    >
                      {expandedTask === task.runId ? '收起' : '展开'}
                    </button>
                  )}
                </div>
                
                <div className="text-xs text-gray-500 mt-1">
                  进度：{task.progressInfo} • 最后更新：
                  {new Date(task.lastUpdate).toLocaleString()}
                </div>
              </div>

              {task.status === 'awaiting_input' && (
                <Alert
                  message="任务正在等待您的输入"
                  description="点击重新连接继续与任务交互"
                  type="info"
                  showIcon
                  className="mt-3"
                />
              )}
              
              {task.status === 'paused' && (
                <Alert
                  message="任务已暂停"
                  description="重新连接后可以恢复任务执行"
                  type="warning"
                  showIcon
                  className="mt-3"
                />
              )}

              {task.canReconnect && (
                <Alert
                  message="连接已断开"
                  description="任务仍在后台运行，点击重连按钮恢复连接"
                  type="warning"
                  showIcon
                  className="mt-3"
                  action={
                    <Button
                      size="small"
                      type="primary"
                      icon={<RotateCcw size={14} />}
                      onClick={() => handleManualReconnect(task.runId)}
                      loading={reconnectingTasks.has(task.runId)}
                    >
                      立即重连
                    </Button>
                  }
                />
              )}
            </div>
          ))}
        </div>
      </Modal>
    </>
  );
};

export default BackgroundTaskIndicator; 