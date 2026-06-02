'use client';

import React from 'react';
import { AmendmentEntry } from '@/types';
import { diffWords, Change } from 'diff';

interface AmendmentSplitViewProps {
  amendments: AmendmentEntry[];
}

interface DiffTextProps {
  text: string;
  changes: Change[];
  showAdditions: boolean;
}

function DiffText({ text, changes, showAdditions }: DiffTextProps) {
  if (!changes || changes.length === 0) {
    return <pre className="whitespace-pre-wrap font-sans">{text}</pre>;
  }

  return (
    <pre className="whitespace-pre-wrap font-sans">
      {changes.map((change, index) => {
        if (change.removed && showAdditions) return null;
        if (change.added && !showAdditions) return null;
        
        let className = '';
        if (change.removed && !showAdditions) {
          className = 'bg-red-200 text-red-900 px-1 rounded';
        } else if (change.added && showAdditions) {
          className = 'bg-green-200 text-green-900 px-1 rounded';
        }
        
        return (
          <span key={index} className={className}>
            {change.value}
          </span>
        );
      })}
    </pre>
  );
}

export function AmendmentSplitView({ amendments }: AmendmentSplitViewProps) {
  return (
    <div className="space-y-6">
      {amendments.map((amendment, index) => {
        const originalText = amendment.originalNorm.wording || '';
        const amendedText = amendment.amendedNorm.wording || '';
        
        // Generate diff changes
        const changes = originalText && amendedText ? diffWords(originalText, amendedText) : [];

        return (
          <div key={index} className="border border-gray-300 rounded-lg overflow-hidden">
            {/* Header with norm identification */}
            <div className="bg-gray-100 px-4 py-2 border-b border-gray-300">
              <h4 className="font-semibold text-gray-800">
                {amendment.originalNorm.enbez} {amendment.originalNorm.jurabk}
                {amendment.originalNorm.P && ` Abs. ${amendment.originalNorm.P}`}
              </h4>
            </div>

            {/* Split view content */}
            <div className="grid grid-cols-1 lg:grid-cols-2 divide-y lg:divide-y-0 lg:divide-x divide-gray-300">
              {/* Original Version */}
              <div className="p-4">
                <div className="flex items-center mb-3">
                  <div className="w-3 h-3 bg-red-500 rounded-full mr-2"></div>
                  <h5 className="font-medium text-gray-700">Ursprüngliche Fassung</h5>
                </div>
                <div className="text-sm text-gray-800 leading-relaxed">
                  {originalText && amendedText ? (
                    <DiffText 
                      text={originalText} 
                      changes={changes} 
                      showAdditions={false}
                    />
                  ) : (
                    <pre className="whitespace-pre-wrap font-sans">
                      {originalText || 'Keine ursprüngliche Fassung verfügbar'}
                    </pre>
                  )}
                </div>
              </div>

              {/* Amended Version */}
              <div className="p-4 bg-green-50">
                <div className="flex items-center mb-3">
                  <div className="w-3 h-3 bg-green-500 rounded-full mr-2"></div>
                  <h5 className="font-medium text-gray-700">Geänderte Fassung</h5>
                </div>
                <div className="text-sm text-gray-800 leading-relaxed">
                  {originalText && amendedText ? (
                    <DiffText 
                      text={amendedText} 
                      changes={changes} 
                      showAdditions={true}
                    />
                  ) : (
                    <pre className="whitespace-pre-wrap font-sans">
                      {amendedText || 'Keine geänderte Fassung verfügbar'}
                    </pre>
                  )}
                </div>
              </div>
            </div>

          </div>
        );
      })}
    </div>
  );
}

export default AmendmentSplitView;