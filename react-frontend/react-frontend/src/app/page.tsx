// src/app/page.tsx
'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { useCreateStory, StorySettings } from '@/services/api';

export default function Home() {
  const router = useRouter();
  const [settings, setSettings] = useState<StorySettings>({
    genre: 'scifi',
    theme: 'exploration',
    setting: 'A distant galaxy in the far future',
  });
  
  const createStoryMutation = useCreateStory();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    createStoryMutation.mutate(settings, {
      onSuccess: (story) => {
        router.push(`/stories/${story.id}`);
      },
    });
  };

  return (
    <main className="min-h-screen p-8 max-w-3xl mx-auto">
      <h1 className="text-4xl font-bold mb-2 text-center">
        Interactive Sci-Fi Story Generator
      </h1>
      <p className="text-center text-gray-600 mb-8">
        Create AI-powered interactive stories that respond to your choices
      </p>
      
      <div className="bg-white p-6 rounded-lg shadow-md">
        <h2 className="text-2xl font-semibold mb-4">Create a New Story</h2>
        
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block mb-1 font-medium">Genre</label>
            <select 
              className="w-full p-2 border rounded" 
              value={settings.genre}
              onChange={(e) => setSettings({
                ...settings,
                genre: e.target.value as StorySettings['genre'],
              })}
            >
              <option value="scifi">Science Fiction</option>
              <option value="cyberpunk">Cyberpunk</option>
              <option value="space_opera">Space Opera</option>
              <option value="dystopian">Dystopian</option>
            </select>
          </div>
          
          <div>
            <label className="block mb-1 font-medium">Theme</label>
            <input 
              type="text" 
              className="w-full p-2 border rounded"
              value={settings.theme}
              onChange={(e) => setSettings({
                ...settings,
                theme: e.target.value,
              })}
              placeholder="e.g., exploration, rebellion, survival"
            />
          </div>
          
          <div>
            <label className="block mb-1 font-medium">Setting</label>
            <textarea 
              className="w-full p-2 border rounded h-24"
              value={settings.setting}
              onChange={(e) => setSettings({
                ...settings,
                setting: e.target.value,
              })}
              placeholder="Describe the world where your story takes place..."
            />
          </div>
          
          <button 
            type="submit" 
            className="w-full py-2 px-4 bg-blue-600 text-white rounded hover:bg-blue-700 transition"
            disabled={createStoryMutation.isPending}
          >
            {createStoryMutation.isPending ? 'Creating AI Story...' : 'Begin Your Adventure'}
          </button>
          
          {createStoryMutation.isError && (
            <p className="text-red-600 text-center mt-2">
              {(createStoryMutation.error as Error).message || 'Failed to create story. Please try again.'}
            </p>
          )}
        </form>
      </div>
      
      <div className="mt-8 text-center">
        <Link href="/stories" className="text-blue-600 hover:underline">
          View Existing Stories
        </Link>
      </div>
      
      <div className="mt-12 p-6 bg-gray-100 rounded-lg">
        <h2 className="text-xl font-semibold mb-4">How It Works</h2>
        <ol className="list-decimal pl-5 space-y-2">
          <li>Create a new story by choosing a genre, theme, and setting</li>
          <li>Our AI will generate an engaging introduction based on your inputs</li>
          <li>Read the story and decide what happens next</li>
          <li>Use AI suggestions or write your own continuation</li>
          <li>The AI will respond to your choices, creating a unique narrative</li>
        </ol>
      </div>
    </main>
  );
}