---
id: P-0091-ops-queue-viz
title: Ops Queue Visualizer
priority: medium
phase: expansion
class: Euclid
tags: ops, visualization, monitoring, queue
---

# Ops Queue Visualizer (P-0091-ops-queue-viz)

**Classification:** Euclid  
**Priority:** Medium  
**Phase:** Expansion  
**Subsystems:** client, ops, docs  

## Special Containment Procedures
UI component with real-time data. Ensure minimal performance impact on queue processing. Implement proper error boundaries and graceful degradation. Limit update frequency to prevent excessive re-renders.

## Description
Visual dashboard for the PU (Proposal Unit) queue system showing:
- Queue depth and processing status
- Task types and priorities
- Success/failure rates
- Processing time metrics
- Budget utilization tracking

This provides operators with real-time visibility into system automation and helps identify bottlenecks or issues in the autonomous development pipeline.

## Experiments
- EXP-1: Render queue with 50+ items without performance impact
- EXP-2: Real-time updates via WebSocket/SSE integration
- EXP-3: Historical metrics display and trending

## Risks & Mitigations
- **Risk:** Performance impact on queue processing
  - **Mitigation:** Debounced updates, efficient React rendering
- **Risk:** Information overload in UI
  - **Mitigation:** Collapsible sections, filtering options
- **Risk:** Security exposure of sensitive queue data
  - **Mitigation:** Admin-only access, sanitized data display

## Addenda
- A1: Integration with existing HUD system
- A2: Mobile-responsive design considerations

## RSEV
```rsev
RSEV::ADD_FILE path="client/src/components/QueueViz.tsx" <<EOF
import { useQuery } from '@tanstack/react-query';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import { Clock, CheckCircle, XCircle, Loader } from 'lucide-react';

interface QueueStats {
  depth: number;
  processing: number;
  completed: number;
  failed: number;
  types: Record<string, number>;
}

export default function QueueViz() {
  const { data: stats, isLoading } = useQuery<QueueStats>({
    queryKey: ['/api/ops/queue/stats'],
    refetchInterval: 5000, // Update every 5 seconds
  });

  if (isLoading) return <div>Loading queue stats...</div>;
  if (!stats) return <div>Queue stats unavailable</div>;

  const total = stats.depth + stats.completed + stats.failed;
  const successRate = total > 0 ? (stats.completed / total) * 100 : 0;

  return (
    <Card className="w-full">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Loader className="h-4 w-4" />
          PU Queue Status
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="grid grid-cols-4 gap-2 text-sm">
          <div className="text-center">
            <div className="text-blue-600 font-bold">{stats.depth}</div>
            <div className="text-muted-foreground">Queued</div>
          </div>
          <div className="text-center">
            <div className="text-yellow-600 font-bold">{stats.processing}</div>
            <div className="text-muted-foreground">Processing</div>
          </div>
          <div className="text-center">
            <div className="text-green-600 font-bold">{stats.completed}</div>
            <div className="text-muted-foreground">Completed</div>
          </div>
          <div className="text-center">
            <div className="text-red-600 font-bold">{stats.failed}</div>
            <div className="text-muted-foreground">Failed</div>
          </div>
        </div>
        
        <div>
          <div className="flex justify-between text-sm mb-1">
            <span>Success Rate</span>
            <span>{successRate.toFixed(1)}%</span>
          </div>
          <Progress value={successRate} className="h-2" />
        </div>
        
        <div className="text-xs text-muted-foreground">
          Types: {Object.entries(stats.types).map(([type, count]) => 
            `${type}(${count})`
          ).join(', ')}
        </div>
      </CardContent>
    </Card>
  );
}
EOF
RSEV::ADD_FILE path="tests/components/QueueViz.spec.tsx" <<EOF
import { render, screen } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import QueueViz from '../../client/src/components/QueueViz';

const mockStats = {
  depth: 5,
  processing: 2,
  completed: 45,
  failed: 3,
  types: { RefactorPU: 10, TestPU: 5, GamePU: 2 }
};

test('displays queue statistics', () => {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } }
  });
  
  render(
    <QueryClientProvider client={queryClient}>
      <QueueViz />
    </QueryClientProvider>
  );
  
  expect(screen.getByText('PU Queue Status')).toBeInTheDocument();
});
EOF
RSEV::TEST name="queue-viz" run="npm test -- QueueViz.spec.tsx"
RSEV::OPEN_PR branch="agent/P-0091-ops-queue-viz" labels="automerge,agent,ui"
```