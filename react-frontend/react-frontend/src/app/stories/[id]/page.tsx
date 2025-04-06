// src/app/stories/[id]/page.tsx
'use client';
import { useState, useEffect } from 'react';
import { useParams } from 'next/navigation';
import Link from 'next/link';
import { useQueryClient } from '@tanstack/react-query';
import { 
  useGetStory, 
  useAddStorySection,
  useGetStorySuggestions,
  useGetStoryCharacters // New hook to fetch characters
} from '@/services/api';
import StoryDisplay from '@/components/StoryDisplay';
import StoryInput from '@/components/StoryInput';
import CharacterPanel from '@/components/CharacterPanel';

export default function StoryPage() {
  const params = useParams();
  const storyId = params.id as string;
  const queryClient = useQueryClient();
  
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
  
  // Fetch characters - new query
  const {
    data: characters,
    isPending: isLoadingCharacters
  } = useGetStoryCharacters(storyId);
  
  // Add section mutation
  const addSectionMutation = useAddStorySection();
  
  const handleSubmit = async (text: string) => {
    if (!text.trim()) return;
    
    addSectionMutation.mutate(
      { storyId, text },
      {
        onSuccess: () => {
          // Invalidate queries to refresh data
          queryClient.invalidateQueries({ queryKey: ['story', storyId] });
          queryClient.invalidateQueries({ queryKey: ['suggestions', storyId] });
          queryClient.invalidateQueries({ queryKey: ['characters', storyId] });
        },
      }
    );
  };
  
  if (isLoadingStory) {
    return (
      <div className="min-h-screen p-8 max-w-6xl mx-auto">
        <div className="animate-pulse">
          <div className="h-8 bg-gray-200 rounded w-1/3 mb-4"></div>
          <div className="h-4 bg-gray-200 rounded w-2/3 mb-8"></div>
          <div className="h-64 bg-gray-100 rounded mb-8"></div>
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
    <main className="min-h-screen p-8 max-w-6xl mx-auto">
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-8">
        {/* Main story column */}
        <div className="lg:col-span-3">
          <h1 className="text-3xl font-bold mb-2">{story.theme} in a {story.genre} world</h1>
          <p className="text-gray-600 mb-8">{story.setting}</p>
          
          <StoryDisplay 
            story={story} 
            isLoading={isLoadingStory} 
          />
          
          {addSectionMutation.isPending && (
            <div className="animate-pulse text-gray-500 italic mt-4 mb-8 p-4 border border-gray-200 rounded">
              Generating the next part of your story...
            </div>
          )}
          
          <StoryInput 
            onSubmit={handleSubmit}
            isLoading={addSectionMutation.isPending}
            suggestions={suggestions || []}
            loadingSuggestions={isLoadingSuggestions}
          />
          
          {addSectionMutation.isError && (
            <p className="text-red-600 text-center mt-2">
              {(addSectionMutation.error as Error).message || 'Failed to add your contribution. Please try again.'}
            </p>
          )}
        </div>
        
        {/* Sidebar */}
        <div>
          <CharacterPanel 
            characters={characters || []} 
            isLoading={isLoadingCharacters} 
          />
          
          <div className="bg-white p-4 rounded-lg shadow-md">
            <h2 className="text-lg font-semibold mb-2">Story Information</h2>
            <div className="text-sm">
              <p><span className="font-medium">Genre:</span> {story.genre}</p>
              <p><span className="font-medium">Theme:</span> {story.theme}</p>
              <p><span className="font-medium">Started:</span> {new Date(story.created_at).toLocaleDateString()}</p>
              <p><span className="font-medium">Sections:</span> {story.sections.length}</p>
            </div>
            
            <div className="mt-4 space-y-2">
              <Link href="/stories" className="text-blue-600 hover:underline block">
                View All Stories
              </Link>
              <Link href="/" className="text-blue-600 hover:underline block">
                Create Another Story
              </Link>
            </div>
          </div>
        </div>
      </div>
    </main>
  );
}