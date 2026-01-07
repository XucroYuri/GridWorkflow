import React, { useState } from 'react';
import { Send, Settings2 } from 'lucide-react';
import { clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

function cn(...inputs: (string | undefined | null | false)[]) {
  return twMerge(clsx(inputs));
}

interface VideoEditorProps {
  onGenerate: (prompt: string, aspectRatio: string) => void;
  isGenerating: boolean;
}

export const VideoEditor: React.FC<VideoEditorProps> = ({ onGenerate, isGenerating }) => {
  const [prompt, setPrompt] = useState('');
  const [aspectRatio, setAspectRatio] = useState('16:9');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (prompt.trim()) {
      onGenerate(prompt, aspectRatio);
    }
  };

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4 h-full flex flex-col">
      <h2 className="text-lg font-semibold mb-4 text-gray-800 flex items-center gap-2">
        <Settings2 className="w-5 h-5" />
        配置与生成
      </h2>
      
      <form onSubmit={handleSubmit} className="flex flex-col gap-4 flex-1">
        <div className="flex-1 flex flex-col">
          <label className="block text-sm font-medium text-gray-700 mb-2">提示词 (Prompt)</label>
          <textarea
            className="w-full h-full p-3 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500 resize-none text-sm"
            placeholder="描述你想要生成的视频内容..."
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            disabled={isGenerating}
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">画面比例</label>
          <select
            value={aspectRatio}
            onChange={(e) => setAspectRatio(e.target.value)}
            className="w-full p-2 border border-gray-300 rounded-md bg-white focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-sm"
            disabled={isGenerating}
          >
            <option value="16:9">16:9 (横屏)</option>
            <option value="9:16">9:16 (竖屏)</option>
            <option value="1:1">1:1 (方形)</option>
          </select>
        </div>

        <button
          type="submit"
          disabled={isGenerating || !prompt.trim()}
          className={cn(
            "w-full py-2.5 px-4 rounded-md text-white font-medium flex items-center justify-center gap-2 transition-colors",
            isGenerating || !prompt.trim()
              ? "bg-gray-400 cursor-not-allowed"
              : "bg-blue-600 hover:bg-blue-700 shadow-sm"
          )}
        >
          {isGenerating ? (
            <>
              <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
              提交中...
            </>
          ) : (
            <>
              <Send className="w-4 h-4" />
              生成视频
            </>
          )}
        </button>
      </form>
    </div>
  );
};

