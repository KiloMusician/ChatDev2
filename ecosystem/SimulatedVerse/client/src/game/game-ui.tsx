// Real Game UI Components
import React from 'react';
import { SafeList } from '../components/SafeList';

export interface GameUIProps {
  resources?: { id: string; name: string; amount: number }[];
  onAction: (action: string) => void;
}

export const GameUI: React.FC<GameUIProps> = ({ resources = [], onAction }) => {
  return (
    <div className="game-ui p-4 bg-slate-800 text-white">
      <h2 className="text-xl font-bold mb-4">CoreLink Foundation</h2>
      
      <div className="resources mb-4">
        <h3 className="text-lg mb-2">Resources</h3>
        <SafeList
          data={resources}
          render={(resource) => (
            <div className="flex justify-between mb-1">
              <span>{resource.name}:</span>
              <span>{resource.amount}</span>
            </div>
          )}
        />
      </div>
      
      <div className="actions">
        <button 
          onClick={() => onAction('gather')}
          className="bg-blue-600 px-4 py-2 rounded mr-2"
        >
          Gather Resources
        </button>
        <button 
          onClick={() => onAction('build')}
          className="bg-green-600 px-4 py-2 rounded"
        >
          Build Structure
        </button>
      </div>
    </div>
  );
};