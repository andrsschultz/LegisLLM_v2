'use client';

import React from 'react';
import { useApp } from '@/contexts/AppContext';
import Layout from '@/components/Layout';
import TaskDescriptionTab from '@/components/tabs/TaskDescriptionTab';
import ContextIdentificationTab from '@/components/tabs/ContextIdentificationTab';
import ProposalDevelopmentTab from '@/components/tabs/ProposalDevelopmentTab';
import EvaluationTab from '@/components/tabs/EvaluationTab';
import FinalizationTab from '@/components/tabs/FinalizationTab';

export default function HomePage() {
  const { state } = useApp();

  const renderCurrentTab = () => {
    switch (state.currentTab) {
      case 0:
        return <TaskDescriptionTab />;
      case 1:
        return <ContextIdentificationTab />;
      case 2:
        return <ProposalDevelopmentTab />;
      case 3:
        return <EvaluationTab />;
      case 4:
        return <FinalizationTab />;
      default:
        return <TaskDescriptionTab />;
    }
  };

  return (
    <Layout>
      <div className="space-y-8">
        {/* Main Tab Content */}
        <div className="min-h-[600px]">
          {renderCurrentTab()}
        </div>
      </div>
    </Layout>
  );
}
