// src/components/CharacterPanel.tsx
import React from 'react';

interface Character {
  id: string;
  name: string;
  description: string;
  traits: Record<string, any>;
  importance: number;
}

interface CharacterPanelProps {
  characters: Character[];
  isLoading: boolean;
}

export default function CharacterPanel({ characters, isLoading }: CharacterPanelProps) {
  if (isLoading) {
    return (
      <div className="bg-white p-4 rounded-lg shadow-md animate-pulse">
        <div className="h-4 bg-gray-200 rounded w-1/2 mb-4"></div>
        {[1, 2].map(i => (
          <div key={i} className="mb-4">
            <div className="h-3 bg-gray-200 rounded w-1/3 mb-2"></div>
            <div className="h-3 bg-gray-200 rounded w-2/3 mb-2"></div>
          </div>
        ))}
      </div>
    );
  }
  
  if (!characters || characters.length === 0) {
    return null;
  }
  
  return (
    <div className="bg-white p-4 rounded-lg shadow-md mb-4">
      <h2 className="text-lg font-semibold mb-2">Characters</h2>
      <div className="space-y-3">
        {characters.map(character => (
          <div key={character.id} className="p-2 hover:bg-gray-50 rounded">
            <h3 className="font-medium">{character.name}</h3>
            <p className="text-sm text-gray-600">{character.description.substring(0, 100)}...</p>
            
            {character.traits && Object.keys(character.traits).length > 0 && (
              <div className="mt-1">
                <h4 className="text-xs text-gray-500">Traits:</h4>
                <div className="flex flex-wrap gap-1 mt-1">
                  {Object.entries(character.traits)
                    .filter(([key]) => typeof key === 'string' && !key.startsWith('_'))
                    .map(([key, value]) => (
                      <span 
                        key={key}
                        className="text-xs px-2 py-1 bg-gray-100 rounded-full"
                        title={`${value}`}
                      >
                        {key}
                      </span>
                    ))
                  }
                </div>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}