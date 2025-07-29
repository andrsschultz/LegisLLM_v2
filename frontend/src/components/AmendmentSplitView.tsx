'use client';

import React from 'react';
import { AmendmentEntry } from '@/types';

interface AmendmentSplitViewProps {
  amendments: AmendmentEntry[];
}



export function AmendmentSplitView({ amendments }: AmendmentSplitViewProps) {
  return (
    <div className="space-y-6">
      {amendments.map((amendment, index) => (
        <div key={index} className="border border-gray-300 rounded-lg overflow-hidden">
          {/* Header with norm identification */}
          <div className="bg-gray-100 px-4 py-2 border-b border-gray-300">
            <h4 className="font-semibold text-gray-800">
              {amendment.originalNorm.jurabk} {amendment.originalNorm.enbez}
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
                <pre className="whitespace-pre-wrap font-sans">
                  {amendment.originalNorm.wording || 'Keine ursprüngliche Fassung verfügbar'}
                </pre>
              </div>
            </div>

            {/* Amended Version */}
            <div className="p-4 bg-green-50">
              <div className="flex items-center mb-3">
                <div className="w-3 h-3 bg-green-500 rounded-full mr-2"></div>
                <h5 className="font-medium text-gray-700">Geänderte Fassung</h5>
              </div>
              <div className="text-sm text-gray-800 leading-relaxed">
                <pre className="whitespace-pre-wrap font-sans">
                  {amendment.amendedNorm.wording || 'Keine geänderte Fassung verfügbar'}
                </pre>
              </div>
            </div>
          </div>

        </div>
      ))}
    </div>
  );
}

export default AmendmentSplitView;