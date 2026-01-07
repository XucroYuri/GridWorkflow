import React, { useState } from 'react';
import { 
  ArrowRight, 
  RotateCcw, 
  CheckCircle2, 
  AlertCircle,
  Loader2,
  Image as ImageIcon,
  Film,
  Edit
} from 'lucide-react';
import { videoService, type Anchor } from '../../services/videoService';

// Types for State Machine
type WorkflowStep = 'input' | 'concept' | 'storyboard_plan' | 'storyboard_gen' | 'video_prompt' | 'video_result';

interface WorkflowState {
  step: WorkflowStep;
  isLoading: boolean;
  error: string | null;
  
  // Data
  plot: string;
  style: string;
  anchors: Record<string, Anchor>;
  aspectRatio: string;
  
  // Responses
  conceptPrompt?: string;
  conceptImageUrl?: string;
  storyboardPrompt?: string;
  gridImageUrl?: string;
  videoPrompt?: string;
  videoTaskId?: string;
}

const INITIAL_STATE: WorkflowState = {
  step: 'input',
  isLoading: false,
  error: null,
  plot: '',
  style: 'Anime style, OLM studio',
  anchors: {
    character: { text: '' },
    environment: { text: '' },
    prop: { text: '' }
  },
  aspectRatio: '16:9',
};

export const GridWorkflow: React.FC = () => {
  const [state, setState] = useState<WorkflowState>(INITIAL_STATE);
  const [editedPrompt, setEditedPrompt] = useState<string>('');

  const updateState = (updates: Partial<WorkflowState>) => {
    setState(prev => ({ ...prev, ...updates }));
  };

  const handleError = (error: any) => {
    console.error(error);
    updateState({ 
      isLoading: false, 
      error: error.message || '操作失败，请重试' 
    });
  };

  // Step 1: Generate Concept
  const handleGenerateConcept = async () => {
    if (!state.plot.trim()) {
      updateState({ error: '剧情片段不能为空' });
      return;
    }
    updateState({ isLoading: true, error: null });
    try {
      const res = await videoService.generateConcept(
        state.style,
        state.plot,
        state.anchors,
        state.aspectRatio
      );
      updateState({
        step: 'concept',
        isLoading: false,
        conceptPrompt: res.concept_prompt,
        conceptImageUrl: res.concept_image_url
      });
    } catch (err) {
      handleError(err);
    }
  };

  // Step 2: Plan Storyboard
  const handlePlanStoryboard = async () => {
    updateState({ isLoading: true, error: null });
    try {
      const res = await videoService.planStoryboard(
        state.style,
        state.plot,
        state.anchors,
        state.conceptPrompt,
        state.conceptImageUrl
      );
      setEditedPrompt(res.storyboard_prompt); // Allow editing
      updateState({
        step: 'storyboard_plan',
        isLoading: false,
        storyboardPrompt: res.storyboard_prompt
      });
    } catch (err) {
      handleError(err);
    }
  };

  // Step 3: Generate Storyboard Grid
  const handleGenerateStoryboard = async () => {
    if (!editedPrompt.trim()) {
      updateState({ error: '分镜 Prompt 不能为空' });
      return;
    }
    updateState({ isLoading: true, error: null });
    try {
      // If prompt was edited, use it
      const promptToUse = editedPrompt;
      const res = await videoService.generateStoryboard(
        promptToUse,
        state.conceptImageUrl, // Use concept image as reference
        state.aspectRatio
      );
      updateState({
        step: 'storyboard_gen',
        isLoading: false,
        storyboardPrompt: promptToUse, // Commit the edited prompt
        gridImageUrl: res.grid_image_url
      });
    } catch (err) {
      handleError(err);
    }
  };

  // Reroll (Step 3) - Only regenerates image, keeps prompt
  const handleRerollStoryboard = async () => {
    updateState({ isLoading: true, error: null });
    try {
      const res = await videoService.generateStoryboard(
        state.storyboardPrompt!, // Use existing confirmed prompt
        state.conceptImageUrl,
        state.aspectRatio
      );
      updateState({
        isLoading: false,
        gridImageUrl: res.grid_image_url
      });
    } catch (err) {
      handleError(err);
    }
  };

  // Step 4: Generate Video Prompt
  const handleGenerateVideoPrompt = async () => {
    updateState({ isLoading: true, error: null });
    try {
      const res = await videoService.generateVideoPrompt(
        state.storyboardPrompt!,
        state.plot
      );
      setEditedPrompt(res.video_prompt);
      updateState({
        step: 'video_prompt',
        isLoading: false,
        videoPrompt: res.video_prompt
      });
    } catch (err) {
      handleError(err);
    }
  };

  // Step 5: Generate Video
  const handleGenerateVideo = async () => {
    if (!editedPrompt.trim()) {
      updateState({ error: '视频 Prompt 不能为空' });
      return;
    }
    updateState({ isLoading: true, error: null });
    try {
      const promptToUse = editedPrompt;
      const res = await videoService.generateVideo(
        promptToUse,
        'sora-2',
        state.aspectRatio
      );
      updateState({
        step: 'video_result',
        isLoading: false,
        videoPrompt: promptToUse,
        videoTaskId: res.task_id
      });
    } catch (err) {
      handleError(err);
    }
  };

  const handleReset = () => {
    if (confirm('确定要重置所有内容吗？')) {
      setState(INITIAL_STATE);
      setEditedPrompt('');
    }
  };

  // UI Components
  const ProgressBar = () => {
    const steps = ['input', 'concept', 'storyboard_plan', 'storyboard_gen', 'video_prompt', 'video_result'];
    const currentIndex = steps.indexOf(state.step);
    const progress = Math.max(5, (currentIndex / (steps.length - 1)) * 100);

    return (
      <div className="w-full bg-gray-200 h-1.5 mt-4">
        <div 
          className="bg-blue-600 h-1.5 transition-all duration-500 ease-out" 
          style={{ width: `${progress}%` }} 
        />
      </div>
    );
  };

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden flex flex-col h-full">
      <div className="p-4 border-b border-gray-100 flex justify-between items-center bg-gray-50">
        <div className="flex items-center gap-2">
          <span className="font-semibold text-gray-800">Grid Workflow</span>
          <span className="text-xs px-2 py-0.5 bg-blue-100 text-blue-700 rounded-full font-medium">
             Step: {state.step.replace('_', ' ').toUpperCase()}
          </span>
        </div>
        <button onClick={handleReset} className="text-gray-500 hover:text-red-600 transition-colors" title="重置">
          <RotateCcw className="w-4 h-4" />
        </button>
      </div>
      
      <ProgressBar />

      <div className="flex-1 overflow-y-auto p-6">
        {state.error && (
          <div className="mb-6 bg-red-50 text-red-700 p-3 rounded-md flex items-start gap-2 text-sm">
            <AlertCircle className="w-4 h-4 mt-0.5 flex-shrink-0" />
            <p>{state.error}</p>
          </div>
        )}

        {/* Step 1: Input */}
        {state.step === 'input' && (
          <div className="space-y-6 max-w-2xl mx-auto">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">剧情片段 (Plot)</label>
              <textarea 
                value={state.plot}
                onChange={e => updateState({ plot: e.target.value })}
                className="w-full p-3 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 h-32"
                placeholder="例如：樱花树下的少女，微风吹拂，花瓣飘落..."
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">风格 (Style)</label>
              <input 
                value={state.style}
                onChange={e => updateState({ style: e.target.value })}
                className="w-full p-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
               <div>
                 <label className="block text-sm font-medium text-gray-700 mb-1">比例</label>
                 <select 
                   value={state.aspectRatio}
                   onChange={e => updateState({ aspectRatio: e.target.value })}
                   className="w-full p-2 border border-gray-300 rounded-md"
                 >
                   <option value="16:9">16:9</option>
                   <option value="9:16">9:16</option>
                 </select>
               </div>
            </div>

            <div className="bg-gray-50 p-4 rounded-md border border-gray-200">
              <h3 className="text-sm font-medium text-gray-700 mb-3">视觉锚点 (Anchors)</h3>
              <div className="grid gap-3">
                <input 
                  placeholder="人物 (Character)"
                  value={state.anchors.character.text}
                  onChange={e => updateState({ anchors: { ...state.anchors, character: { ...state.anchors.character, text: e.target.value } } })}
                  className="w-full p-2 border border-gray-300 rounded-md text-sm"
                />
                <input 
                  placeholder="场景 (Environment)"
                  value={state.anchors.environment.text}
                  onChange={e => updateState({ anchors: { ...state.anchors, environment: { ...state.anchors.environment, text: e.target.value } } })}
                  className="w-full p-2 border border-gray-300 rounded-md text-sm"
                />
                <input 
                  placeholder="道具 (Prop)"
                  value={state.anchors.prop.text}
                  onChange={e => updateState({ anchors: { ...state.anchors, prop: { ...state.anchors.prop, text: e.target.value } } })}
                  className="w-full p-2 border border-gray-300 rounded-md text-sm"
                />
              </div>
            </div>

            <div className="pt-4">
              <button 
                onClick={handleGenerateConcept}
                disabled={state.isLoading}
                className="w-full bg-blue-600 text-white py-3 rounded-md hover:bg-blue-700 disabled:bg-gray-400 flex justify-center items-center gap-2"
              >
                {state.isLoading ? <Loader2 className="animate-spin w-5 h-5" /> : <ArrowRight className="w-5 h-5" />}
                生成概念图
              </button>
            </div>
          </div>
        )}

        {/* Step 2: Concept Result */}
        {state.step === 'concept' && (
          <div className="space-y-6">
            <div className="bg-gray-50 p-4 rounded-lg border border-gray-200">
              <h3 className="font-medium text-gray-900 mb-2 flex items-center gap-2">
                <ImageIcon className="w-4 h-4" /> 概念图
              </h3>
              <div className="aspect-video bg-gray-200 rounded-md overflow-hidden mb-4">
                <img src={state.conceptImageUrl} alt="Concept" className="w-full h-full object-contain" />
              </div>
              <div className="bg-white p-3 rounded border border-gray-200 text-sm text-gray-600 max-h-32 overflow-y-auto">
                <span className="font-semibold text-gray-800">Concept Prompt:</span> {state.conceptPrompt}
              </div>
            </div>

            <div className="flex gap-4">
              <button 
                 onClick={() => updateState({ step: 'input' })}
                 className="px-4 py-2 border border-gray-300 rounded-md hover:bg-gray-50 text-gray-700"
              >
                返回修改
              </button>
              <button 
                onClick={handlePlanStoryboard}
                disabled={state.isLoading}
                className="flex-1 bg-blue-600 text-white py-2 rounded-md hover:bg-blue-700 disabled:bg-gray-400 flex justify-center items-center gap-2"
              >
                {state.isLoading ? <Loader2 className="animate-spin w-4 h-4" /> : '下一步：规划分镜'}
              </button>
            </div>
          </div>
        )}

        {/* Step 3: Storyboard Plan */}
        {state.step === 'storyboard_plan' && (
          <div className="space-y-6">
             <div className="bg-yellow-50 border border-yellow-200 p-4 rounded-md">
               <h3 className="font-medium text-yellow-800 mb-2 flex items-center gap-2">
                 <Edit className="w-4 h-4" /> 编辑分镜 Prompt
               </h3>
               <textarea 
                 value={editedPrompt}
                 onChange={e => setEditedPrompt(e.target.value)}
                 className="w-full h-48 p-3 border border-yellow-300 rounded-md focus:ring-2 focus:ring-yellow-500 text-sm font-mono"
               />
               <p className="text-xs text-yellow-600 mt-2">您可以修改上方生成的 Prompt 以调整九宫格内容。</p>
             </div>

             <div className="flex gap-4">
               <button 
                 onClick={() => updateState({ step: 'concept' })}
                 className="px-4 py-2 border border-gray-300 rounded-md hover:bg-gray-50 text-gray-700"
               >
                 上一步
               </button>
               <button 
                 onClick={handleGenerateStoryboard}
                 disabled={state.isLoading}
                 className="flex-1 bg-blue-600 text-white py-2 rounded-md hover:bg-blue-700 disabled:bg-gray-400 flex justify-center items-center gap-2"
               >
                 {state.isLoading ? <Loader2 className="animate-spin w-4 h-4" /> : '生成九宫格'}
               </button>
             </div>
          </div>
        )}

        {/* Step 4: Storyboard Grid */}
        {state.step === 'storyboard_gen' && (
          <div className="space-y-6">
             <div className="bg-gray-900 rounded-lg overflow-hidden border border-gray-800">
                <img src={state.gridImageUrl} alt="Storyboard Grid" className="w-full h-auto object-contain" />
             </div>

             <div className="flex gap-4">
               <button 
                 onClick={handleRerollStoryboard}
                 disabled={state.isLoading}
                 className="flex-1 px-4 py-2 border border-gray-300 rounded-md hover:bg-gray-50 text-gray-700 flex justify-center items-center gap-2"
                 title="仅重绘图像，不改变 Prompt"
               >
                 {state.isLoading ? <Loader2 className="animate-spin w-4 h-4" /> : <RotateCcw className="w-4 h-4" />}
                 Reroll (重绘)
               </button>
               <button 
                 onClick={handleGenerateVideoPrompt}
                 disabled={state.isLoading}
                 className="flex-1 bg-blue-600 text-white py-2 rounded-md hover:bg-blue-700 disabled:bg-gray-400 flex justify-center items-center gap-2"
               >
                 {state.isLoading ? <Loader2 className="animate-spin w-4 h-4" /> : '下一步：视频 Prompt'}
               </button>
             </div>
          </div>
        )}

        {/* Step 5: Video Prompt */}
        {state.step === 'video_prompt' && (
          <div className="space-y-6">
             <div className="bg-indigo-50 border border-indigo-200 p-4 rounded-md">
               <h3 className="font-medium text-indigo-800 mb-2 flex items-center gap-2">
                 <Film className="w-4 h-4" /> 确认视频 Prompt
               </h3>
               <textarea 
                 value={editedPrompt}
                 onChange={e => setEditedPrompt(e.target.value)}
                 className="w-full h-48 p-3 border border-indigo-300 rounded-md focus:ring-2 focus:ring-indigo-500 text-sm font-mono"
               />
             </div>

             <div className="flex gap-4">
               <button 
                 onClick={() => updateState({ step: 'storyboard_gen' })}
                 className="px-4 py-2 border border-gray-300 rounded-md hover:bg-gray-50 text-gray-700"
               >
                 上一步
               </button>
               <button 
                 onClick={handleGenerateVideo}
                 disabled={state.isLoading}
                 className="flex-1 bg-blue-600 text-white py-2 rounded-md hover:bg-blue-700 disabled:bg-gray-400 flex justify-center items-center gap-2 shadow-md"
               >
                 {state.isLoading ? <Loader2 className="animate-spin w-4 h-4" /> : '生成视频 (Sora 2)'}
               </button>
             </div>
          </div>
        )}

        {/* Step 6: Result */}
        {state.step === 'video_result' && (
          <div className="text-center py-10">
            <div className="w-16 h-16 bg-green-100 text-green-600 rounded-full flex items-center justify-center mx-auto mb-4">
              <CheckCircle2 className="w-8 h-8" />
            </div>
            <h3 className="text-xl font-semibold text-gray-800 mb-2">任务已提交</h3>
            <p className="text-gray-600 mb-6">视频正在生成中，请在右侧任务列表查看进度。</p>
            <p className="text-xs text-gray-400 font-mono mb-6">Task ID: {state.videoTaskId}</p>
            
            <button 
              onClick={handleReset}
              className="px-6 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
            >
              开始新任务
            </button>
          </div>
        )}
      </div>
    </div>
  );
};

