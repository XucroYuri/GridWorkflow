import React, { type ReactNode } from 'react';
import { useUIConfigContext } from '../../contexts/UIConfigContext';

interface MainLayoutProps {
  header: ReactNode;
  sidebarLeft: ReactNode;
  sidebarRight: ReactNode;
  mobileNav: ReactNode;
  footer: ReactNode;
  children: ReactNode;
  isSidebarLeftOpen: boolean;
  isSidebarRightOpen: boolean;
  onOverlayClick: () => void;
  bottomPanel?: ReactNode; // NEW prop
}

export const MainLayout: React.FC<MainLayoutProps> = ({
  header,
  sidebarLeft,
  sidebarRight,
  mobileNav,
  footer,
  children,
  isSidebarLeftOpen,
  isSidebarRightOpen,
  onOverlayClick,
  bottomPanel
}) => {
  // Use context if needed, currently placeholder
  useUIConfigContext();

  return (
    <div className="h-[100dvh] flex flex-col bg-[var(--md-sys-color-background)] text-[var(--md-sys-color-on-surface)] font-sans overflow-hidden selection:bg-[var(--md-sys-color-primary)]/30">
      {/* Header - Always visible, fixed positioning */}
      <div className="shrink-0 z-50 lg:mt-0 mt-0">
        {header}
      </div>
      
      {/* Main Bento Grid - Responsive gaps and padding */}
      <main className="flex-1 flex flex-row min-h-0 px-2 sm:px-4 pb-3 gap-3 relative isolate">
        
        {/* Mobile/Tablet Overlay */}
        {(isSidebarLeftOpen || isSidebarRightOpen) && (
          <div 
            className="fixed inset-0 top-0 bottom-0 bg-black/40 backdrop-blur-sm z-30 xl:hidden animate-in fade-in duration-200"
            onClick={onOverlayClick}
          />
        )}

        {/* Left Sidebar (Console/Script/Explorer) */}
        {sidebarLeft && (
          <aside className={`
              m3-surface
              transform transition-all duration-300 cubic-bezier(0.2, 0, 0, 1)
              fixed left-3 top-16 bottom-3 z-40 w-[85vw] max-w-[420px] shadow-2xl
              ${isSidebarLeftOpen ? 'translate-x-0 opacity-100' : '-translate-x-[120%] opacity-0'}
              lg:static lg:translate-x-0 lg:opacity-100 lg:flex lg:flex-col 
              lg:w-[340px] xl:w-[440px] 2xl:w-[500px] 
              lg:shadow-none lg:h-full lg:z-auto
              border border-[var(--glass-border)] bg-[var(--md-sys-color-surface)]
          `}>
            {sidebarLeft}
          </aside>
        )}

        {/* Center Workspace - Main Viewport */}
        <section className="flex-1 flex flex-col min-w-0 m3-surface relative w-full overflow-hidden border border-[var(--glass-border)] bg-[var(--md-sys-color-surface-container-lowest)] pb-24 lg:pb-0 transition-all duration-300 aspect-square lg:aspect-auto xl:aspect-[1/1] 2xl:aspect-[1/1] max-h-full mx-auto shadow-sm rounded-none lg:rounded-2xl">
          {children}
        </section>

        {/* Right Sidebar (Tree/Shot List/Inspector) */}
        {sidebarRight && (
          <aside className={`
              m3-surface
              transform transition-all duration-300 cubic-bezier(0.2, 0, 0, 1)
              fixed right-3 top-16 bottom-3 z-40 w-[85vw] max-w-[420px] shadow-2xl
              ${isSidebarRightOpen ? 'translate-x-0 opacity-100' : '-translate-x-[120%] opacity-0'}
              xl:static xl:translate-x-0 xl:opacity-100 xl:flex xl:flex-col 
              lg:w-[340px] xl:w-[440px] 2xl:w-[500px] 
              xl:shadow-none xl:h-full xl:z-auto
              border border-[var(--glass-border)] bg-[var(--md-sys-color-surface)]
          `}>
            {sidebarRight}
          </aside>
        )}
      </main>
      
      {bottomPanel}

      {mobileNav}
      
      {/* Footer is hidden or minimal in Pro layout */}
      <div className="hidden">
        {footer} 
      </div>
    </div>
  );
};

