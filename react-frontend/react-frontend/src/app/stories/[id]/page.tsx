// src/app/stories/[id]/page.tsx
'use client';

import { useState } from 'react';
import { useParams } from 'next/navigation';
import Link from 'next/link';
import { useQueryClient } from '@tanstack/react-query';
import { 
  useGetStory, 
  useAddStorySection,
  useGetStorySuggestions 
} from '@/services/api';

export default function StoryPage() {
  const params = useParams();
  const storyId = params.id as string;
  const queryClient = useQueryClient();
  
  const [userInput, setUserInput] = useState('');
  
  // Fetch story data
  const { 
    data: story, 
    isPending: isLoadingStory, 
    isError: isStoryError, 
    error: storyError 
  } = useGetStory(storyId);
  
  // Fetch suggestions
  const {
    data: suggestions,
    isPending: isLoadingSuggestions,
    isError: isSuggestionsError
  } = useGetStorySuggestions(storyId);
  
  // Add section mutation
  const addSectionMutation = useAddStorySection();
  
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!userInput.trim()) return;
    
    addSectionMutation.mutate(
      { storyId, text: userInput },
      {
        onSuccess: () => {
          setUserInput('');
          // Invalidate both the story and suggestions queries
          queryClient.invalidateQueries({ queryKey: ['story', storyId] });
          queryClient.invalidateQueries({ queryKey: ['suggestions', storyId] });
        },
      }
    );
  };
  
  const selectSuggestion = (suggestion: string) => {
    setUserInput(suggestion);
  };
  
  if (isLoadingStory) {
    return (
      <div className="min-h-screen p-8 max-w-3xl mx-auto flex justify-center items-center">
        <div className="text-center">
          <h2 className="text-xl mb-4">Loading story...</h2>
        </div>
      </div>
    );
  }
  
  if (isStoryError) {
    return (
      <div className="min-h-screen p-8 max-w-3xl mx-auto flex justify-center items-center">
        <div className="text-center">
          <h2 className="text-xl mb-4 text-red-600">
            {(storyError as Error).message || 'Failed to load story'}
          </h2>
          <button 
            onClick={() => window.location.reload()} 
            className="py-2 px-4 bg-blue-600 text-white rounded hover:bg-blue-700 transition"
          >
            Try Again
          </button>
        </div>
      </div>
    );
  }
  
  if (!story) {
    return (
      <div className="min-h-screen p-8 max-w-3xl mx-auto flex justify-center items-center">
        <div className="text-center">
          <h2 className="text-xl mb-4">Story not found</h2>
          <Link 
            href="/" 
            className="py-2 px-4 bg-blue-600 text-white rounded hover:bg-blue-700 transition"
          >
            Back to Home
          </Link>
        </div>
      </div>
    );
  }
  
  return (
    <main className="min-h-screen p-8 max-w-3xl mx-auto">
      <h1 className="text-3xl font-bold mb-2">{story.theme} in a {story.genre} world</h1>
      <p className="text-gray-600 mb-8">{story.setting}</p>
      
      <div className="bg-white p-6 rounded-lg shadow-md mb-8">
        {story.sections.map((section) => (
          <div key={section.id} className="mb-6 last:mb-0">
            <p className="whitespace-pre-line">{section.text}</p>
          </div>
        ))}
        {addSectionMutation.isPending && (
          <div className="animate-pulse text-gray-500 italic mt-4">
            Generating the next part of your story...
          </div>
        )}
      </div>
      
      {/* AI Suggestions */}
      <div className="mb-8">
        <h2 className="text-xl font-semibold mb-4">What would you like to do next?</h2>
        {isLoadingSuggestions ? (
          <div className="flex items-center space-x-2 text-gray-500">
            <svg className="animate-spin h-5 w-5" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
            <span>Loading suggestions...</span>
          </div>
        ) : isSuggestionsError ? (
          <p className="text-red-500">Failed to load suggestions</p>
        ) : suggestions && suggestions.length > 0 ? (
          <div className="flex flex-wrap gap-2">
            {suggestions.map((suggestion, index) => (
              <button
                key={index}
                onClick={() => selectSuggestion(suggestion)}
                className="px-4 py-2 bg-indigo-100 text-indigo-800 rounded-full hover:bg-indigo-200 transition"
              >
                {suggestion}
              </button>
            ))}
          </div>
        ) : (
          <p>No suggestions available</p>
        )}
      </div>
      
      <div className="bg-white p-6 rounded-lg shadow-md">
        <h2 className="text-xl font-semibold mb-4">Continue the story</h2>
        
        <form onSubmit={handleSubmit} className="space-y-4">
          <textarea 
            className="w-full p-3 border rounded h-32"
            value={userInput}
            onChange={(e) => setUserInput(e.target.value)}
            placeholder="Type what happens next..."
            disabled={addSectionMutation.isPending}
          />
          
          <button 
            type="submit" 
            className="w-full py-2 px-4 bg-blue-600 text-white rounded hover:bg-blue-700 transition"
            disabled={addSectionMutation.isPending || !userInput.trim()}
          >
            {addSectionMutation.isPending ? 'Generating story...' : 'Continue Story'}
          </button>
          
          {addSectionMutation.isError && (
            <p className="text-red-600 text-center mt-2">
              {(addSectionMutation.error as Error).message || 'Failed to add your contribution. Please try again.'}
            </p>
          )}
        </form>
      </div>
      
      <div className="mt-8 text-center">
        <Link href="/" className="text-blue-600 hover:underline mr-4">
          Create Another Story
        </Link>
        <Link href="/stories" className="text-blue-600 hover:underline">
          View All Stories
        </Link>
      </div>
    </main>
  );
}