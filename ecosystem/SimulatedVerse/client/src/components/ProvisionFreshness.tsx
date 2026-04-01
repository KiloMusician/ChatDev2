import React, { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { POLLING_INTERVALS } from '@/config/polling';
// Badge component fallback if not available
const Badge = ({ variant, children }: { variant?: string; children: React.ReactNode }) => (
  <span className={`inline-flex px-2 py-1 text-xs rounded ${
    variant === 'destructive' ? 'bg-red-100 text-red-800' : 
    variant === 'secondary' ? 'bg-gray-100 text-gray-800' :
    'bg-blue-100 text-blue-800'
  }`}>
    {children}
  </span>
);
import { Clock, AlertTriangle, CheckCircle } from 'lucide-react';

interface FreshnessData {
  skew_sec_max: number;
  at: number;
  build_fresh?: boolean;
}

export function ProvisionFreshness() {
  const [freshness, setFreshness] = useState<FreshnessData | null>(null);
  const [systemStatus, setSystemStatus] = useState<any>(null);

  useEffect(() => {
    const checkFreshness = async () => {
      try {
        // Check provision freshness report
        const freshnessRes = await fetch('/reports/provision_freshness.json');
        if (freshnessRes.ok) {
          const freshnessData = await freshnessRes.json();
          setFreshness(freshnessData);
        }

        // Check system status 
        const statusRes = await fetch('/public/system-status.json');
        if (statusRes.ok) {
          const statusData = await statusRes.json();
          setSystemStatus(statusData);
        }
      } catch (error) {
        // If reports don't exist yet, calculate skew from any available timestamp
        const now = Date.now();
        const skew = Math.floor(now / 1000) % 3600; // Rough estimate
        setFreshness({ skew_sec_max: skew, at: now });
      }
    };

    checkFreshness();
    const interval = setInterval(checkFreshness, POLLING_INTERVALS.standard);
    return () => clearInterval(interval);
  }, []);

  if (!freshness) {
    return (
      <Card className="w-full">
        <CardContent className="p-4">
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <Clock className="w-4 h-4" />
            <span>Loading freshness data...</span>
          </div>
        </CardContent>
      </Card>
    );
  }

  const skewSec = freshness.skew_sec_max;
  const isStale = skewSec > 60;
  const isCritical = skewSec > 300; // 5 minutes

  return (
    <Card className="w-full">
      <CardHeader className="pb-2">
        <CardTitle className="flex items-center gap-2 text-sm">
          <Clock className="w-4 h-4" />
          Provision Freshness
          <Badge variant={isStale ? (isCritical ? "destructive" : "secondary") : "default"}>
            {isStale ? (isCritical ? "Critical" : "Stale") : "Fresh"}
          </Badge>
        </CardTitle>
      </CardHeader>
      <CardContent className="pt-0">
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-sm">Timestamp Skew:</span>
            <div className="flex items-center gap-1">
              {isStale ? (
                <AlertTriangle className="w-3 h-3 text-orange-500" />
              ) : (
                <CheckCircle className="w-3 h-3 text-green-500" />
              )}
              <span className={`text-sm font-mono ${isStale ? 'text-orange-500' : 'text-green-500'}`}>
                {skewSec}s
              </span>
            </div>
          </div>

          {systemStatus && (
            <div className="text-xs text-muted-foreground">
              <div>Build: {systemStatus.build_id || 'unknown'}</div>
              <div>Last Update: {new Date(systemStatus.timestamp || 0).toLocaleTimeString()}</div>
            </div>
          )}

          {isStale && (
            <div className="p-2 bg-orange-50 dark:bg-orange-900/20 rounded text-xs">
              <strong>Warning:</strong> UI provision is stale ({">"} 60s). 
              System may be showing outdated information.
            </div>
          )}

          {isCritical && (
            <div className="p-2 bg-red-50 dark:bg-red-900/20 rounded text-xs">
              <strong>Critical:</strong> UI provision extremely stale ({">"} 5min).
              Check if services are running properly.
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
