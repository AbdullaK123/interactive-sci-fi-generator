// src/app/stories/page.tsx
'use client';

import Link from 'next/link';
import { useGetAllStories } from '@/services/api';

export default function StoriesPage() {
  const { 
    data: stories, 
    isPending: isLoading, 
    isError, 
    error 
  } = useGetAllStories();
  
  if (isLoading) {
    return (
      <div className="min-h-screen p-8 max-w-3xl mx-auto flex justify-center items-center">
        <div className="text-center">
          <h2 className="text-xl mb-4">Loading stories...</h2>
        </div>
      </div>
    );
  }
  
  if (isError) {
    return (
      <div className="min-h-screen p-8 max-w-3xl mx-auto flex justify-center items-center">
        <div className="text-center">
          <h2 className="text-xl mb-4 text-red-600">
            {(error as Error).message || 'Failed to load stories.'}
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
  
  return (
    <main className="min-h-screen p-8 max-w-3xl mx-auto">
      <h1 className="text-3xl font-bold mb-8 text-center">Your AI Stories</h1>
      
      {!stories || stories.length === 0 ? (
        <div className="bg-white p-6 rounded-lg shadow-md text-center">
          <h2 className="text-xl mb-4">No stories found</h2>
          <Link 
            href="/" 
            className="py-2 px-4 bg-blue-600 text-white rounded hover:bg-blue-700 transition"
          >
            Create Your First Story
          </Link>
        </div>
      ) : (
        <div className="grid gap-6">
          {stories.map((story) => (
            <Link 
              key={story.id} 
              href={`/stories/${story.id}`}
              className="block bg-white p-6 rounded-lg shadow-md hover:shadow-lg transition"
            >
              <h2 className="text-xl font-semibold mb-2">
                {story.theme} in a {story.genre} world
              </h2>
              <p className="text-gray-600 mb-4">{story.setting}</p>
              <div className="flex justify-between text-sm text-gray-500">
                <span>
                  {new Date(story.created_at).toLocaleDateString()}
                </span>
                <span>
                  {story.sections ? 
                    `${story.sections.length} ${story.sections.length === 1 ? 'part' : 'parts'}` : 
                    '0 parts'}
                </span>
              </div>
            </Link>
          ))}
        </div>
      )}
      
      <div className="mt-8 text-center">
        <Link href="/" className="text-blue-600 hover:underline">
          Create a New Story
        </Link>
      </div>
    </main>
  );
}