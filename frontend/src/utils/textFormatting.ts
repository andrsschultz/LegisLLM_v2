import React from 'react';

/**
 * Formats text with SUP tags to render superscript sentence indicators
 * This utility can be used across all components that display legal norm text
 */
export const formatTextWithSuperscript = (text: string) => {
  if (!text) return null;
  
  // Split text by <SUP> markers and create React elements
  const parts = text.split(/(<SUP>\d+<\/SUP>)/);
  
  return parts.map((part, index) => {
    // Check if this part is a SUP marker
    const supMatch = part.match(/^<SUP>(\d+)<\/SUP>$/);
    if (supMatch) {
      const number = supMatch[1];
      return React.createElement('sup', {
        key: index,
        className: 'text-xs font-medium text-blue-600'
      }, number);
    }
    // Regular text part
    return part;
  });
};

/**
 * Formats complete norm content with title highlighting and superscript
 * Used for consistent styling across all norm displays
 */
export const formatNormContent = (text: string) => {
  if (!text) return null;

  // Split by the first line break to separate title from content
  const lines = text.split('\n');
  const firstLine = lines[0];
  const restOfContent = lines.slice(1).join('\n');

  // Check if first line is a title (contains § and text)
  const titleMatch = firstLine.match(/^(§\s*\d+[a-z]?)\s*(.*)$/);
  
  if (titleMatch) {
    const sectionNumber = titleMatch[1];
    const title = titleMatch[2];
    
    return React.createElement('div', { className: 'space-y-6' }, [
      // Section Title
      React.createElement('div', { 
        key: 'title',
        className: 'border-b-2 border-blue-200 pb-4' 
      }, [
        React.createElement('div', {
          key: 'title-content',
          className: 'flex flex-col sm:flex-row sm:items-center space-y-2 sm:space-y-0 sm:space-x-3'
        }, [
          React.createElement('span', {
            key: 'section-badge',
            className: 'inline-flex items-center justify-center text-xl font-bold text-white bg-gradient-to-r from-blue-600 to-blue-700 px-4 py-2 rounded-lg shadow-sm'
          }, sectionNumber),
          React.createElement('h3', {
            key: 'title-text',
            className: 'text-lg font-bold text-gray-900 leading-tight'
          }, title)
        ])
      ]),
      
      // Content
      React.createElement('div', {
        key: 'content',
        className: 'prose prose-sm max-w-none'
      }, [
        React.createElement('div', {
          key: 'content-text',
          className: 'text-gray-800 leading-7 font-serif whitespace-pre-wrap'
        }, formatContentParagraphs(restOfContent))
      ])
    ]);
  }

  // Fallback: no title detected, format as regular content
  return React.createElement('div', {
    className: 'prose prose-sm max-w-none'
  }, [
    React.createElement('div', {
      key: 'content',
      className: 'text-gray-800 leading-7 font-serif whitespace-pre-wrap'
    }, formatContentParagraphs(text))
  ]);
};

/**
 * Helper function to format paragraphs with proper spacing and numbering
 */
const formatContentParagraphs = (text: string) => {
  // Split content into paragraphs and format each
  const paragraphs = text.split(/\n\s*\n/);
  
  return paragraphs.map((paragraph, index) => {
    if (!paragraph.trim()) return null;
    
    // Check if paragraph starts with a number in parentheses like (1), (2), etc.
    const paragraphMatch = paragraph.match(/^(\(\d+\))\s*(.*)/s);
    
    if (paragraphMatch) {
      const paragraphNum = paragraphMatch[1];
      const paragraphContent = paragraphMatch[2];
      
      return React.createElement('div', {
        key: index,
        className: 'mb-6 text-gray-800'
      }, [
        paragraphNum + ' ',
        ...formatTextWithSuperscript(paragraphContent)
      ]);
    }
    
    // Regular paragraph without number
    return React.createElement('div', {
      key: index,
      className: 'mb-4 text-gray-800'
    }, formatTextWithSuperscript(paragraph));
  }).filter(Boolean);
};