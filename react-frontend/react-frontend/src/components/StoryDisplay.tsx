// src/components/StoryDisplay.tsx
import React, { useState } from 'react';
import { Story, StorySection } from '@/services/api';

interface StoryDisplayProps {
  story: Story;
  isLoading: boolean;
}

export default function StoryDisplay({ story, isLoading }: StoryDisplayProps) {
  const [expandedSection, setExpandedSection] = useState<string | null>(null);
  
  if (isLoading) {
    return (
      <div className="bg-white p-6 rounded-lg shadow-md animate-pulse">
        <div className="h-4 bg-gray-200 rounded w-3/4 mb-4"></div>
        <div className="h-4 bg-gray-200 rounded w-1/2 mb-2"></div>
        <div className="h-4 bg-gray-200 rounded w-5/6 mb-2"></div>
        <div className="h-4 bg-gray-200 rounded w-4/6 mb-2"></div>
      </div>
    );
  }
  
  if (!story || !story.sections || story.sections.length === 0) {
    return (
      <div className="bg-white p-6 rounded-lg shadow-md">
        <p className="text-gray-500 italic">No story content available yet.</p>
      </div>
    );
  }
  
  return (
    <div className="bg-white p-6 rounded-lg shadow-md mb-8">
      {story.sections.map((section, index) => (
        <div 
          key={section.id} 
          className={`mb-6 last:mb-0 ${
            index === story.sections.length - 1 ? 'font-normal' : 'text-gray-700'
          }`}
        >
          <p className="whitespace-pre-line">{section.text}</p>
          
          {expandedSection === section.id && section.events && section.events.length > 0 && (
            <div className="mt-2 p-2 bg-blue-50 rounded text-sm">
              <p className="font-semibold text-blue-800">Key events:</p>
              <ul className="list-disc pl-4">
                {section.events.map(event => (
                  <li key={event.id}>{event.description}</li>
                ))}
              </ul>
            </div>
          )}
          
          {section.events && section.events.length > 0 && (
            <button 
              onClick={() => setExpandedSection(
                expandedSection === section.id ? null : section.id
              )}
              className="text-xs text-blue-600 hover:underline mt-1"
            >
              {expandedSection === section.id ? 'Hide details' : 'Show details'}
            </button>
          )}
        </div>
      ))}
    </div>
  );
}