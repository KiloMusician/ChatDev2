// client/src/hooks/useSystemData.ts
// SWR-powered data fetching with ETag support for system status
import useSWR from 'swr';
import { useAppStore } from '@/store/AppStore';

interface FetchResult {
  data: any;
  etag: string | null;
  timestamp: number;
}

// Custom fetcher with ETag support
const fetcherWithETag = async (url: string): Promise<FetchResult> => {
  const response = await fetch(url, {
    headers: {
      'Cache-Control': 'no-cache',
      'Pragma': 'no-cache'
    }
  });
  
  if (!response.ok) {
    throw new Error(`Failed to fetch ${url}: ${response.status}`);
  }
  
  const data = await response.json();
  const etag = response.headers.get('etag');
  
  return { data, etag, timestamp: Date.now() };
};

// System status hook with automatic store updates
export function useSystemData() {
  const updateSystem = useAppStore(state => state.updateSystem);
  
  const { data, error, isLoading, mutate } = useSWR(
    '/system-status.json',
    fetcherWithETag,
    {
      refreshInterval: 5000, // Poll every 5 seconds
      revalidateOnFocus: true,
      revalidateOnReconnect: true,
      onSuccess: (result) => {
        // Automatically update the store when new data arrives
        if (result?.data) {
          updateSystem({
            health: result.data.health,
            pu_queue: result.data.pu_queue,
            consciousness: result.data.consciousness,
            errors: result.data.errors || []
          });
        }
      }
    }
  );
  
  return {
    systemData: data?.data,
    etag: data?.etag,
    lastUpdate: data?.timestamp,
    isLoading,
    error,
    refresh: mutate
  };
}

// Chug reports hook
export function useChugReports() {
  const { data, error, isLoading } = useSWR(
    '/ops-report/report.json',
    fetcherWithETag,
    {
      refreshInterval: 8000, // Poll every 8 seconds (matches OpsPane)
      revalidateOnFocus: false // Don't spam on focus for logs
    }
  );
  
  return {
    chugReport: data?.data,
    isLoading,
    error
  };
}

// Unstick status hook
export function useUnstickStatus() {
  const { data, error, isLoading } = useSWR(
    '/unstick-status.json',
    fetcherWithETag,
    {
      refreshInterval: 10000, // Poll every 10 seconds
      revalidateOnFocus: false
    }
  );
  
  return {
    unstickStatus: data?.data,
    isLoading,
    error
  };
}

// Combined ops monitoring hook
export function useOpsMonitoring() {
  const systemData = useSystemData();
  const chugReports = useChugReports();
  const unstickStatus = useUnstickStatus();
  
  return {
    system: systemData,
    chug: chugReports,
    unstick: unstickStatus,
    
    // Computed status
    overallHealth: systemData.systemData?.health?.build_success_rate || 0,
    isOperational: !systemData.error && !chugReports.error,
    lastActivity: Math.max(
      systemData.lastUpdate || 0,
      chugReports.chugReport?.timestamp || 0,
      unstickStatus.unstickStatus?.timestamp || 0
    )
  };
}