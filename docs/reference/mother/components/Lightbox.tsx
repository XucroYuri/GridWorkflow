
import React, { createContext, useContext, useState, ReactNode, useEffect } from 'react';

interface LightboxContextType {
  openLightbox: (url: string, downloadName?: string) => void;
  closeLightbox: () => void;
}

const LightboxContext = createContext<LightboxContextType | undefined>(undefined);

export const useLightbox = () => {
  const context = useContext(LightboxContext);
  if (!context) throw new Error("useLightbox must be used within LightboxProvider");
  return context;
};

export const LightboxProvider: React.FC<{children: ReactNode}> = ({ children }) => {
  const [isOpen, setIsOpen] = useState(false);
  const [url, setUrl] = useState<string | null>(null);
  const [filename, setFilename] = useState<string>('image.png');

  const openLightbox = (image: string, name: string = 'image.png') => {
    setUrl(image);
    setFilename(name);
    setIsOpen(true);
  };

  const closeLightbox = () => {
    setIsOpen(false);
    setUrl(null);
  };

  // Handle ESC key
  useEffect(() => {
    const handleEsc = (e: KeyboardEvent) => {
        if (e.key === 'Escape') closeLightbox();
    };
    if (isOpen) window.addEventListener('keydown', handleEsc);
    return () => window.removeEventListener('keydown', handleEsc);
  }, [isOpen]);

  const handleDownload = () => {
    if (!url) return;
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  return (
    <LightboxContext.Provider value={{ openLightbox, closeLightbox }}>
      {children}
      {isOpen && url && (
        <div 
          className="fixed inset-0 z-[200] flex items-center justify-center bg-black/95 backdrop-blur-xl animate-in fade-in duration-200"
          onClick={closeLightbox}
        >
          {/* Close Button */}
          <button 
            className="absolute top-6 right-6 p-2 text-slate-400 hover:text-white transition-colors hover:bg-white/10 rounded-full z-50"
            onClick={(e) => { e.stopPropagation(); closeLightbox(); }}
          >
             <svg className="w-8 h-8" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" /></svg>
          </button>

          {/* Large Image */}
          <div className="relative w-full h-full p-4 md:p-10 flex items-center justify-center">
             <img 
               src={url} 
               onClick={(e) => e.stopPropagation()}
               className="max-w-full max-h-full object-contain shadow-2xl rounded-sm select-none" 
               alt="Full Preview"
             />
             
             {/* Floating Action Bar */}
             <div 
               className="absolute bottom-10 left-1/2 -translate-x-1/2 flex items-center gap-4 bg-slate-900/80 backdrop-blur-md px-6 py-3 rounded-2xl border border-white/10 shadow-2xl"
               onClick={(e) => e.stopPropagation()}
             >
                 <button 
                   onClick={handleDownload}
                   className="flex items-center gap-2 text-xs font-bold uppercase tracking-widest text-white hover:text-indigo-400 transition-colors"
                 >
                   <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" /></svg>
                   Download Original
                 </button>
             </div>
          </div>
        </div>
      )}
    </LightboxContext.Provider>
  )
}
