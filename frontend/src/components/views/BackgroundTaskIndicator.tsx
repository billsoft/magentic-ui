import React, { useState, useEffect } from 'react';
import { Alert, Button, Badge, Tooltip, Modal } from 'antd';
import { Play, Pause, Square, RotateCcw, Info } from 'lucide-react';
import { Run, RunStatus, AgentMessageConfig, TextMessageConfig } from '../types/datamodel';

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
}

// 提取任务描述的辅助函数
const extractTaskDescription = (task: AgentMessageConfig | null | undefined): string => {
  if (!task) return 'No description';
  
  // 处理不同类型的消息配置
  if ('content' in task) {
    if (typeof task.content === 'string') {
      return task.content;
    } else if (Array.isArray(task.content)) {
      // 对于数组内容，提取字符串部分
      const textParts = task.content
        .filter((item): item is string => typeof item === 'string')
        .join(' ');
      return textParts || 'Mixed content message';
    }
  }
  
  return 'Unknown task type';
};

// 检查任务内容是否包含特定关键词
const containsKeywords = (task: AgentMessageConfig | null | undefined, keywords: string[]): boolean => {
  const description = extractTaskDescription(task).toLowerCase();
  return keywords.some(keyword => description.includes(keyword));
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

  // 检测后台任务
  useEffect(() => {
    const detectBackgroundTasks = () => {
      const activeTasks = runs.filter(run => 
        run.status === 'active' || 
        run.status === 'awaiting_input' || 
        run.status === 'paused'
      );

      const taskInfos: BackgroundTaskInfo[] = activeTasks.map(run => ({
        runId: parseInt(run.id),
        sessionId: run.session_id,
        sessionName: `Session ${run.session_id}`, // 实际应该从session数据获取
        status: run.status,
        lastUpdate: run.updated_at || new Date().toISOString(),
        taskDescription: extractTaskDescription(run.task),
        progressInfo: getProgressInfo(run),
      }));

      setBackgroundTasks(taskInfos);
    };

    detectBackgroundTasks();
    
    // 每30秒检查一次
    const interval = setInterval(detectBackgroundTasks, 30000);
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

  const getStatusIcon = (status: RunStatus) => {
    switch (status) {
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

  const getStatusText = (status: RunStatus) => {
    switch (status) {
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

  const truncateText = (text: string, maxLength: number = 100): string => {
    if (text.length <= maxLength) return text;
    return text.substring(0, maxLength);
  };

  if (backgroundTasks.length === 0) {
    return null;
  }

  return (
    <>
      {/* 浮动指示器 */}
      <div className="fixed bottom-4 right-4 z-50">
        <Badge count={backgroundTasks.length} offset={[-5, 5]}>
          <Button
            type="primary"
            shape="circle"
            icon={<Play size={20} />}
            size="large"
            onClick={() => setShowDetails(true)}
            className="bg-blue-500 hover:bg-blue-600 border-none shadow-lg animate-pulse"
          />
        </Badge>
      </div>

      {/* 详细信息弹窗 */}
      <Modal
        title={`后台任务 (${backgroundTasks.length})`}
        open={showDetails}
        onCancel={() => setShowDetails(false)}
        footer={null}
        width={800}
        className="background-task-modal"
      >
        <div className="space-y-4">
          {backgroundTasks.map((task) => (
            <div
              key={task.runId}
              className="border rounded-lg p-4 hover:bg-gray-50 transition-colors"
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-3">
                  {getStatusIcon(task.status)}
                  <div>
                    <div className="font-medium text-gray-900">
                      {task.sessionName}
                    </div>
                    <div className="text-sm text-gray-500">
                      运行 ID: {task.runId} • {getStatusText(task.status)}
                    </div>
                  </div>
                </div>
                
                <div className="flex items-center space-x-2">
                  <Tooltip title="重新连接">
                    <Button
                      type="text"
                      icon={<RotateCcw size={16} />}
                      onClick={() => {
                        onReconnect(task.runId);
                        setShowDetails(false);
                      }}
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

              {/* 任务详情 */}
              <div className="mt-3">
                <div className="text-sm text-gray-600 mb-2">
                  <strong>进度:</strong> {task.progressInfo}
                </div>
                
                <div 
                  className="text-sm text-gray-600 cursor-pointer"
                  onClick={() => setExpandedTask(
                    expandedTask === task.runId ? null : task.runId
                  )}
                >
                  <strong>任务描述:</strong> 
                  <span className="ml-1">
                    {expandedTask === task.runId 
                      ? task.taskDescription 
                      : task.taskDescription.length > 100
                        ? `${truncateText(task.taskDescription, 100)}...`
                        : task.taskDescription
                    }
                  </span>
                  {task.taskDescription.length > 100 && (
                    <span className="text-blue-500 ml-1">
                      {expandedTask === task.runId ? '收起' : '展开'}
                    </span>
                  )}
                </div>
                
                <div className="text-xs text-gray-400 mt-2">
                  最后更新: {new Date(task.lastUpdate).toLocaleString()}
                </div>
              </div>

              {/* 状态特定的提示 */}
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
            </div>
          ))}
        </div>
      </Modal>
    </>
  );
};

export default BackgroundTaskIndicator; 