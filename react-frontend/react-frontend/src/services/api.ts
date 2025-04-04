import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";


export interface StorySettings {
    genre: 'scifi' | 'cyberpunk' | 'space_opera' | 'dystopian';
    theme: string;
    setting: string;
  }
  
export interface StorySection {
    id: string;
    text: string;
    order: number;
    created_at: string;
  }
  
export interface Story {
    id: string;
    genre: string;
    theme: string;
    setting: string;
    created_at: string;
    updated_at: string;
    sections: StorySection[];
  }
  
// Add this new interface for the list view
export interface StoryListItem {
    id: string;
    genre: string;
    theme: string;
    setting: string;
    created_at: string;
    updated_at: string;
    sections?: StorySection[];
  }
  
const API_URL = 'http://localhost:8000';

// API functions
async function createStory(settings: StorySettings): Promise<Story> {
    const response = await fetch(`${API_URL}/stories`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(settings),
    });
    
    if (!response.ok) {
      throw new Error('Failed to create story');
    }
    
    return response.json();
  }
  
async function getStory(storyId: string): Promise<Story> {
    const response = await fetch(`${API_URL}/stories/${storyId}`);
    
    if (!response.ok) {
      throw new Error('Failed to fetch story');
    }
    
    return response.json();
  }
  
async function addStorySection(storyId: string, text: string): Promise<StorySection> {
    const response = await fetch(`${API_URL}/stories/${storyId}/sections`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ text }),
    });
    
    if (!response.ok) {
      throw new Error('Failed to add section');
    }
    
    return response.json();
  }

export async function getStorySuggestions(storyId: string): Promise<string[]> {
    const response = await fetch(`${API_URL}/stories/${storyId}/suggestions`);
    
    if (!response.ok) {
      throw new Error('Failed to fetch suggestions');
    }
    
    return response.json();
  }
  
  
async function getAllStories(): Promise<StoryListItem[]>  {
    const response = await fetch(`${API_URL}/stories`);
    
    if (!response.ok) {
      throw new Error('Failed to fetch stories');
    }
    
    return response.json();
  }

  export function useCreateStory() {
    const queryClient = useQueryClient();
    
    return useMutation({
      mutationFn: createStory,
      onSuccess: () => {
        // Invalidate the stories list query so it refreshes
        queryClient.invalidateQueries({ queryKey: ['stories'] });
      },
    });
  }
  
export function useGetStory(storyId: string) {
    return useQuery({
      queryKey: ['story', storyId],
      queryFn: () => getStory(storyId),
      enabled: !!storyId,
    });
  }
  
export function useGetStorySuggestions(storyId: string) {
    return useQuery({
      queryKey: ['suggestions', storyId],
      queryFn: () => getStorySuggestions(storyId),
      enabled: !!storyId,
    });
  }
  
export function useAddStorySection() {
    const queryClient = useQueryClient();
    
    return useMutation({
      mutationFn: ({ storyId, text }: { storyId: string; text: string }) => 
        addStorySection(storyId, text),
      onSuccess: (_, variables) => {
        // Invalidate the specific story query to refresh it
        queryClient.invalidateQueries({ queryKey: ['story', variables.storyId] });
      },
    });
  }
  
export function useGetAllStories() {
    return useQuery<StoryListItem[]>({
      queryKey: ['stories'],
      queryFn: getAllStories,
    });
  }