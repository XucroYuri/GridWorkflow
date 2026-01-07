import React from 'react';
import { Clock, CheckCircle2, AlertCircle, Loader2, PlayCircle } from 'lucide-react';
import { clsx } from 'clsx';
import type { VideoTask } from '../../services/videoService';

interface TaskListProps {
  tasks: VideoTask[];
  currentTaskId: string | null;
  onSelectTask: (task: VideoTask) => void;
}

export const TaskList: React.FC<TaskListProps> = ({ tasks, currentTaskId, onSelectTask }) => {
  const getStatusIcon = (status: VideoTask['status']) => {
    switch (status) {
      case 'queued':
        return <Clock className="w-4 h-4 text-gray-500" />;
      case 'running':
        return <Loader2 className="w-4 h-4 text-blue-500 animate-spin" />;
      case 'succeeded':
        return <CheckCircle2 className="w-4 h-4 text-green-500" />;
      case 'failed':
        return <AlertCircle className="w-4 h-4 text-red-500" />;
    }
  };

  const getStatusText = (status: VideoTask['status'], progress: number) => {
    switch (status) {
      case 'queued': return '排队中';
      case 'running': return `生成中 ${progress}%`;
      case 'succeeded': return '完成';
      case 'failed': return '失败';
    }
  };

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 flex flex-col h-full overflow-hidden">
      <div className="p-3 border-b border-gray-200 bg-gray-50">
        <h3 className="text-sm font-semibold text-gray-700">任务列表</h3>
      </div>
      <div className="flex-1 overflow-y-auto">
        {tasks.length === 0 ? (
          <div className="p-4 text-center text-sm text-gray-500">
            暂无任务
          </div>
        ) : (
          <ul className="divide-y divide-gray-100">
            {tasks.map((task) => (
              <li 
                key={task.task_id}
                onClick={() => onSelectTask(task)}
                className={clsx(
                  "p-3 cursor-pointer hover:bg-gray-50 transition-colors",
                  currentTaskId === task.task_id ? "bg-blue-50 hover:bg-blue-50" : ""
                )}
              >
                <div className="flex justify-between items-start mb-1">
                  <span className="text-xs text-gray-500">
                    {new Date(task.created_at * 1000).toLocaleString()}
                  </span>
                  <div className="flex items-center gap-1.5 text-xs font-medium">
                    {getStatusIcon(task.status)}
                    <span className={clsx(
                      task.status === 'succeeded' ? 'text-green-600' :
                      task.status === 'failed' ? 'text-red-600' :
                      task.status === 'running' ? 'text-blue-600' : 'text-gray-600'
                    )}>
                      {getStatusText(task.status, task.progress)}
                    </span>
                  </div>
                </div>
                <p className="text-sm text-gray-800 line-clamp-2 mb-1">{task.prompt}</p>
                {task.status === 'succeeded' && (
                  <div className="flex items-center gap-1 text-xs text-blue-600 font-medium">
                    <PlayCircle className="w-3 h-3" />
                    点击播放
                  </div>
                )}
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
};

