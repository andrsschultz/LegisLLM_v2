'use client';

import React, { useState } from 'react';
import Header from './Header';
import Sidebar from './Sidebar';
import TabBar from './TabBar';

interface LayoutProps {
  children: React.ReactNode;
}

export default function Layout({ children }: LayoutProps) {
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(true); // Start collapsed on mobile

  const handleSidebarToggle = () => {
    setIsSidebarCollapsed(!isSidebarCollapsed);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-white to-slate-50">
      {/* Header */}
      <Header onSidebarToggle={handleSidebarToggle} />

      {/* Sidebar */}
      <Sidebar isCollapsed={isSidebarCollapsed} onToggle={handleSidebarToggle} />

      {/* Main Content Area - No margins, sidebar always overlays */}
      <div className="w-full">
        {/* Tab Bar */}
        <TabBar />

        {/* Page Content */}
        <main className="px-4 sm:px-6 lg:px-8 py-6 lg:py-8 space-y-6">
          <div className="max-w-7xl mx-auto">
            {children}
          </div>
        </main>
      </div>
    </div>
  );
}