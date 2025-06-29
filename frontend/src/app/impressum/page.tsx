'use client';

import Header from '@/components/Header';
import Sidebar from '@/components/Sidebar';
import { useState } from 'react';

export default function ImpressumPage() {
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(true);

  const handleSidebarToggle = () => {
    setIsSidebarCollapsed(!isSidebarCollapsed);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-white to-slate-50">
      {/* Header */}
      <Header onSidebarToggle={handleSidebarToggle} />

      {/* Sidebar */}
      <Sidebar isCollapsed={isSidebarCollapsed} onToggle={handleSidebarToggle} />

      {/* Main Content Area - No TabBar */}
      <div className="w-full">
        {/* Page Content */}
        <main className="px-4 sm:px-6 lg:px-8 py-6 lg:py-8 space-y-6">
      <div className="max-w-4xl mx-auto">
        <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-8">
          <h1 className="text-3xl font-bold text-slate-900 mb-8">Impressum</h1>
          
          <div className="prose prose-slate max-w-none space-y-6">
            <section>
              <h2 className="text-xl font-semibold text-slate-800 mb-4">Angaben gemäß § 5 TMG</h2>
              <div className="bg-slate-50 border border-slate-200 rounded-lg p-4">
                <p className="text-slate-600">
                  <strong>Anbieter:</strong><br />
                  Technische Universität München<br />
                  Arbeitsgruppe Legal Tech<br />
                  Boltzmannstraße 3<br />
                  85748 Garching
                </p>
              </div>
            </section>

            <section>
              <h2 className="text-xl font-semibold text-slate-800 mb-4">Kontakt</h2>
              <div className="bg-slate-50 border border-slate-200 rounded-lg p-4">
                <p className="text-slate-600">
                  <strong>E-Mail:</strong> andreas.schultz@tum.de
                </p>
              </div>
            </section>

            

            <div className="border-t border-slate-200 pt-6 mt-8">
              <p className="text-sm text-slate-500">
                Stand: {new Date().toLocaleDateString('de-DE')}
              </p>
            </div>
          </div>
        </div>
          </div>
        </main>
      </div>
    </div>
  );
}