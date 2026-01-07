import React from 'react';
import { useToast } from '../contexts/ToastContext';
import { useLightbox } from '../components/Lightbox';
import apiClient from '../services/apiClient';

const Home: React.FC = () => {
  const { addToast } = useToast();
  const { openLightbox } = useLightbox();

  const testApi = async () => {
    try {
      const res = await apiClient.get('/health');
      addToast('success', `API Success: ${JSON.stringify(res)}`);
    } catch (error) {
      addToast('error', 'API Failed (Check Console)');
      console.error(error);
    }
  };

  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold text-[var(--md-sys-color-primary)]">Frontend Shell Ready</h1>
      
      <div className="p-6 rounded-xl bg-[var(--md-sys-color-surface-container)] border border-[var(--glass-border)] space-y-4">
        <h2 className="text-xl font-semibold">Validation Area</h2>
        
        <div className="flex gap-4 flex-wrap">
          <button 
            className="btn-primary"
            onClick={() => addToast('success', 'This is a success toast!')}
          >
            Test Toast
          </button>

          <button 
            className="btn-primary bg-[var(--md-sys-color-tertiary)]"
            onClick={() => openLightbox('https://placehold.co/600x400', 'placeholder.png')}
          >
            Test Lightbox
          </button>

          <button 
            className="btn-primary bg-[var(--md-sys-color-secondary)]"
            onClick={testApi}
          >
            Test API (/health)
          </button>
        </div>

        <div className="mt-4 p-4 bg-white/50 rounded-lg text-sm text-gray-600">
          <p>Theme: Light (Google Material Design 3)</p>
          <p>Font: Sans-serif</p>
          <p>Layout: Responsive Bento Grid</p>
        </div>
      </div>
    </div>
  );
};

export default Home;
