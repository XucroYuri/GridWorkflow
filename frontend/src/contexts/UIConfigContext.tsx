import React, { createContext, useContext, useState, type ReactNode } from 'react';

interface UIConfigContextType {
  isHeaderVisible: boolean;
  setHeaderVisible: (visible: boolean) => void;
  // 可以根据需要添加其他 UI 配置
}

const UIConfigContext = createContext<UIConfigContextType | undefined>(undefined);

export const useUIConfigContext = () => {
  const context = useContext(UIConfigContext);
  if (!context) {
    throw new Error('useUIConfigContext must be used within a UIConfigProvider');
  }
  return context;
};

export const UIConfigProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [isHeaderVisible, setHeaderVisible] = useState(true);

  return (
    <UIConfigContext.Provider value={{ isHeaderVisible, setHeaderVisible }}>
      {children}
    </UIConfigContext.Provider>
  );
};

