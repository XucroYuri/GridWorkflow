import React from 'react';
import { Film } from 'lucide-react';
import type { VideoTask } from '../../services/videoService';

interface VideoPreviewProps {
  task: VideoTask | null;
}

export const VideoPreview: React.FC<VideoPreviewProps> = ({ task }) => {
  if (!task) {
    return (
      <div className="bg-gray-100 rounded-lg border border-gray-200 h-full flex flex-col items-center justify-center text-gray-400">
        <Film className="w-16 h-16 mb-4 opacity-20" />
        <p>选择或创建一个视频任务以预览</p>
      </div>
    );
  }

  return (
    <div className="bg-black rounded-lg border border-gray-800 h-full flex flex-col overflow-hidden relative">
      {task.status === 'succeeded' && task.video_url ? (
        <video 
          src={task.video_url} 
          controls 
          autoPlay 
          loop 
          className="w-full h-full object-contain bg-black"
        />
      ) : (
        <div className="flex-1 flex flex-col items-center justify-center text-gray-400 p-8">
          {task.status === 'failed' ? (
            <div className="text-center text-red-400">
              <p className="font-medium mb-1">生成失败</p>
              <p className="text-sm opacity-80">请重试或修改提示词</p>
            </div>
          ) : (
            <div className="text-center">
              <div className="w-12 h-12 border-4 border-gray-700 border-t-blue-500 rounded-full animate-spin mb-4 mx-auto" />
              <p className="text-white font-medium mb-1">视频生成中...</p>
              <p className="text-sm opacity-60">
                 {task.status === 'queued' ? '正在排队...' : `进度: ${task.progress}%`}
              </p>
            </div>
          )}
        </div>
      )}
      
      {/* Overlay info */}
      <div className="absolute top-0 left-0 right-0 bg-gradient-to-b from-black/80 to-transparent p-4 pointer-events-none">
        <h3 className="text-white font-medium line-clamp-1">{task.prompt}</h3>
        <p className="text-white/60 text-xs mt-1">ID: {task.task_id}</p>
      </div>
    </div>
  );
};

