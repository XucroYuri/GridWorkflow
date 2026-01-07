import React, { useState, useEffect, useCallback } from 'react';
import { GridWorkflow } from '../components/video/GridWorkflow'; // New component
import { TaskList } from '../components/video/TaskList';
import { VideoPreview } from '../components/video/VideoPreview';
import { videoService, type VideoTask } from '../services/videoService';

export const VideoStudio: React.FC = () => {
  const [tasks, setTasks] = useState<VideoTask[]>([]);
  const [selectedTask, setSelectedTask] = useState<VideoTask | null>(null);

  // Fetch tasks
  const fetchTasks = useCallback(async () => {
    try {
      const data = await videoService.listTasks();
      // Ensure data is array
      const taskList = Array.isArray(data) ? data : [];
      setTasks(taskList);
      
      // Update selected task if it exists in the list
      if (selectedTask) {
        const updated = taskList.find(t => t.task_id === selectedTask.task_id);
        if (updated) {
          setSelectedTask(updated);
        }
      }
    } catch (error) {
      console.error('Failed to fetch tasks:', error);
    }
  }, [selectedTask]);

  // Initial load and polling
  useEffect(() => {
    fetchTasks();
    const interval = setInterval(fetchTasks, 3000); // Poll every 3 seconds
    return () => clearInterval(interval);
  }, [fetchTasks]);

  return (
    <div className="h-screen bg-gray-50 flex flex-col">
      <header className="bg-white border-b border-gray-200 px-6 py-4 flex items-center justify-between shadow-sm z-10">
        <h1 className="text-xl font-bold text-gray-800 flex items-center gap-2">
          Video Studio
          <span className="text-xs font-normal text-gray-500 bg-gray-100 px-2 py-0.5 rounded-full">Beta</span>
        </h1>
      </header>
      
      <main className="flex-1 p-6 overflow-hidden">
        <div className="grid grid-cols-12 gap-6 h-full">
          {/* Left Column: Workflow & Task List */}
          <div className="col-span-5 flex flex-col gap-6 h-full overflow-hidden">
            {/* Workflow takes more space now */}
            <div className="flex-1 min-h-0 overflow-hidden flex flex-col">
              <GridWorkflow />
            </div>
            {/* Task List takes less space */}
            <div className="h-1/3 min-h-[200px]">
              <TaskList 
                tasks={tasks} 
                currentTaskId={selectedTask?.task_id || null} 
                onSelectTask={setSelectedTask} 
              />
            </div>
          </div>
          
          {/* Right Column: Preview */}
          <div className="col-span-7 h-full">
             {/* Pass selected task to preview */}
            <VideoPreview task={selectedTask} />
          </div>
        </div>
      </main>
    </div>
  );
};
