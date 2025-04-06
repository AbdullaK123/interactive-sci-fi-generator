// src/components/StoryInput.tsx
import React, { useState, useEffect } from 'react';

interface StoryInputProps {
  onSubmit: (input: string) => void;
  isLoading: boolean;
  suggestions: string[];
  loadingSuggestions: boolean;
}

export default function StoryInput({ 
  onSubmit, 
  isLoading, 
  suggestions, 
  loadingSuggestions 
}: StoryInputProps) {
  const [userInput, setUserInput] = useState('');
  const [showSuggestions, setShowSuggestions] = useState(true);
  
  // Reset suggestions display when new suggestions arrive
  useEffect(() => {
    if (suggestions && suggestions.length > 0) {
      setShowSuggestions(true);
    }
  }, [suggestions]);
  
  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!userInput.trim() || isLoading) return;
    
    onSubmit(userInput);
    setUserInput('');
    setShowSuggestions(false);
  };
  
  const handleSuggestionClick = (suggestion: string) => {
    onSubmit(suggestion);
    setUserInput('');
    setShowSuggestions(false);
  };
  
  return (
    <div className="bg-white p-6 rounded-lg shadow-md">
      <h2 className="text-xl font-semibold mb-4">Continue the story</h2>
      
      {showSuggestions && suggestions && suggestions.length > 0 && (
        <div className="mb-4">
          <p className="text-sm text-gray-600 mb-2">Suggested actions:</p>
          <div className="flex flex-wrap gap-2">
            {suggestions.map((suggestion, index) => (
              <button
                key={index}
                onClick={() => handleSuggestionClick(suggestion)}
                disabled={isLoading}
                className="px-4 py-2 bg-indigo-100 text-indigo-800 rounded-full 
                         hover:bg-indigo-200 transition disabled:opacity-50"
              >
                {suggestion}
              </button>
            ))}
          </div>
        </div>
      )}
      
      <form onSubmit={handleSubmit} className="space-y-4">
        <textarea 
          className="w-full p-3 border rounded h-32 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          value={userInput}
          onChange={(e) => setUserInput(e.target.value)}
          placeholder="Type what happens next..."
          disabled={isLoading}
        />
        
        <button 
          type="submit" 
          className="w-full py-2 px-4 bg-blue-600 text-white rounded hover:bg-blue-700 
                   transition disabled:bg-blue-300 disabled:cursor-not-allowed"
          disabled={isLoading || !userInput.trim()}
        >
          {isLoading ? 'Generating story...' : 'Continue Story'}
        </button>
      </form>
    </div>
  );
}