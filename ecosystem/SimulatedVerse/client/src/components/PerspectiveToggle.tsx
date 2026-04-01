import React from 'react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { perspectiveManager, PerspectiveMode, InformationSource } from '@/lib/informationSources';

interface PerspectiveToggleProps {
  onPerspectiveChange?: (mode: PerspectiveMode) => void;
}

export function PerspectiveToggle({ onPerspectiveChange }: PerspectiveToggleProps) {
  const [currentMode, setCurrentMode] = React.useState<PerspectiveMode>('traditional');
  const [analysisResults, setAnalysisResults] = React.useState<any>(null);

  const perspectiveModes: { mode: PerspectiveMode; label: string; description: string; sources: InformationSource[] }[] = [
    {
      mode: 'isolated',
      label: 'Pure Repository',
      description: 'Traditional coding view only',
      sources: ['repository']
    },
    {
      mode: 'traditional',
      label: 'Standard Analysis',
      description: 'Normal repository analysis',
      sources: ['repository']
    },
    {
      mode: 'enhanced',
      label: 'Enhanced Workspace',
      description: 'With Replit enhancements',
      sources: ['repository', 'workspace']
    },
    {
      mode: 'active',
      label: 'System Active',
      description: 'Using consciousness features',
      sources: ['repository', 'workspace', 'system']
    },
    {
      mode: 'fullsystem',
      label: 'Full System',
      description: 'All capabilities engaged',
      sources: ['repository', 'workspace', 'system', 'meta']
    },
    {
      mode: 'gamedev',
      label: 'Game Development',
      description: 'Game code development focus',
      sources: ['repository', 'game_dev']
    }
  ];

  const switchPerspective = (mode: PerspectiveMode) => {
    setCurrentMode(mode);
    perspectiveManager.setMode(mode);
    
    // Perform analysis from new perspective
    const analysis = perspectiveManager.analyzeFromPerspective({});
    setAnalysisResults(analysis);
    
    onPerspectiveChange?.(mode);
  };

  React.useEffect(() => {
    // Initial analysis
    const analysis = perspectiveManager.analyzeFromPerspective({});
    setAnalysisResults(analysis);
  }, []);

  return (
    <div className="space-y-4">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <span>Perspective Mode</span>
            <Badge variant="outline">{currentMode}</Badge>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
            {perspectiveModes.map(({ mode, label, description, sources }) => (
              <Button
                key={mode}
                variant={currentMode === mode ? "default" : "outline"}
                onClick={() => switchPerspective(mode)}
                className="h-auto p-3 flex flex-col items-start text-left"
                data-testid={`perspective-${mode}`}
              >
                <span className="font-medium text-sm">{label}</span>
                <span className="text-xs text-muted-foreground mt-1">{description}</span>
                <div className="flex flex-wrap gap-1 mt-2">
                  {sources.map(source => (
                    <Badge key={source} variant="secondary" className="text-xs">
                      {source}
                    </Badge>
                  ))}
                </div>
              </Button>
            ))}
          </div>
        </CardContent>
      </Card>

      {analysisResults && (
        <Card>
          <CardHeader>
            <CardTitle>Analysis: {analysisResults.perspective} Perspective</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {analysisResults.errors.length > 0 && (
              <div>
                <h4 className="font-medium text-red-600 mb-2">Errors Detected:</h4>
                <ul className="list-disc list-inside space-y-1 text-sm">
                  {analysisResults.errors.map((error: string, idx: number) => (
                    <li key={idx} data-testid={`error-${idx}`}>{error}</li>
                  ))}
                </ul>
              </div>
            )}

            {analysisResults.opportunities.length > 0 && (
              <div>
                <h4 className="font-medium text-blue-600 mb-2">Opportunities:</h4>
                <ul className="list-disc list-inside space-y-1 text-sm">
                  {analysisResults.opportunities.map((opp: string, idx: number) => (
                    <li key={idx} data-testid={`opportunity-${idx}`}>{opp}</li>
                  ))}
                </ul>
              </div>
            )}

            {analysisResults.concrete_actions.length > 0 && (
              <div>
                <h4 className="font-medium text-green-600 mb-2">Concrete Actions:</h4>
                <ul className="list-disc list-inside space-y-1 text-sm">
                  {analysisResults.concrete_actions.map((action: string, idx: number) => (
                    <li key={idx} data-testid={`action-${idx}`}>{action}</li>
                  ))}
                </ul>
              </div>
            )}
          </CardContent>
        </Card>
      )}
    </div>
  );
}