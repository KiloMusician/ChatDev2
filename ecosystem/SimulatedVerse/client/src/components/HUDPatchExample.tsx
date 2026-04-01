import { ErrorBoundary } from '@/components/ui/ErrorBoundary';
// client/src/components/HUDPatchExample.tsx
import React from "react";
import { SafeList } from "./SafeList";

function HUDPatchExampleWrapped({ model }: { model: any }) {
  return (
    <div>
      <h3 className="font-semibold">Patched HUD List</h3>
      {/* BEFORE: {model.menu.map(...)}  (crashes when not an array) */}
      <ul>
        <SafeList<any>
          data={model?.menu}
          label="HUD.menu"
          render={(item) => <li>{item?.label ?? String(item)}</li>}
        />
      </ul>
      
      {/* Additional safe patterns */}
      <div className="mt-4">
        <h4>Safe Achievements List:</h4>
        <SafeList<any>
          data={model?.achievements}
          label="HUD.achievements"
          render={(achievement, i) => (
            <div className="bg-green-100 p-2 m-1 rounded">
              {achievement?.emoji} {achievement?.text}
            </div>
          )}
        />
      </div>
      
      <div className="mt-4">
        <h4>Safe Recent Gains:</h4>
        <SafeList<any>
          data={model?.effects?.recentGains}
          label="HUD.recentGains"
          render={(gain) => (
            <span className="inline-block bg-blue-100 px-2 py-1 mr-1 rounded text-sm">
              {gain?.emoji} +{gain?.amount}
            </span>
          )}
        />
      </div>
    </div>
  );
}

export default function HUDPatchExample(props: any) {
  return (
    <ErrorBoundary>
      <HUDPatchExampleWrapped {...props} />
    </ErrorBoundary>
  );
}