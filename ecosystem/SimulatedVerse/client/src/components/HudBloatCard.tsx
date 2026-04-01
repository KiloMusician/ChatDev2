import { ErrorBoundary } from '@/components/ui/ErrorBoundary';
import { useQuery } from '@tanstack/react-query';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { FileText, AlertTriangle, Archive, TrendingDown } from 'lucide-react';
import { POLLING_INTERVALS } from '@/config/polling';

interface CuratorStatus {
  status: string;
  config_loaded: boolean;
  ledger_active: boolean;
  last_scan: string | null;
  safety_rails: string[];
  endpoints: string[];
}

function HudBloatCardWrapped() {
  const { data: status, isLoading } = useQuery<CuratorStatus>({
    queryKey: ['/api/curator/status'],
    refetchInterval: POLLING_INTERVALS.standard,
  });

  if (isLoading) {
    return (
      <Card className="w-full">
        <CardHeader className="pb-2">
          <CardTitle className="text-sm flex items-center gap-2">
            <Archive className="h-4 w-4" />
            Curator Status
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-xs text-muted-foreground">Loading...</div>
        </CardContent>
      </Card>
    );
  }

  if (!status) {
    return (
      <Card className="w-full">
        <CardHeader className="pb-2">
          <CardTitle className="text-sm flex items-center gap-2">
            <AlertTriangle className="h-4 w-4 text-red-500" />
            Curator Offline
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-xs text-red-500">Admin access required</div>
        </CardContent>
      </Card>
    );
  }

  const isHealthy = status.status === "operational" && status.config_loaded;
  const lastScanTime = status.last_scan ? new Date(status.last_scan).toLocaleTimeString() : "Never";

  return (
    <Card className="w-full">
      <CardHeader className="pb-2">
        <CardTitle className="text-sm flex items-center gap-2">
          <Archive className={`h-4 w-4 ${isHealthy ? 'text-green-500' : 'text-yellow-500'}`} />
          Curator
          <span className="text-xs font-normal text-muted-foreground ml-auto">
            Warden of Weight
          </span>
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-2">
        <div className="flex items-center justify-between text-xs">
          <span className="text-muted-foreground">Status:</span>
          <span className={isHealthy ? 'text-green-600' : 'text-yellow-600'}>
            {status.status}
          </span>
        </div>
        
        <div className="flex items-center justify-between text-xs">
          <span className="text-muted-foreground">Last Scan:</span>
          <span>{lastScanTime}</span>
        </div>
        
        <div className="flex items-center justify-between text-xs">
          <span className="text-muted-foreground">Safety Rails:</span>
          <span className="text-green-600">{status.safety_rails.length} active</span>
        </div>
        
        {status.ledger_active && (
          <div className="flex items-center gap-1 text-xs text-green-600">
            <TrendingDown className="h-3 w-3" />
            <span>Ledger tracking</span>
          </div>
        )}
        
        <div className="text-xs text-muted-foreground mt-2 border-t pt-1">
          Bloat control: {status.endpoints.length} endpoints ready
        </div>
      </CardContent>
    </Card>
  );
}

export default function HudBloatCard(props: any) {
  return (
    <ErrorBoundary>
      <HudBloatCardWrapped {...props} />
    </ErrorBoundary>
  );
}
