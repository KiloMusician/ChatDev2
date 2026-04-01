// client/src/boot/freshness.ts
// UI freshness checker + service worker killer (fixes stale UI)
export async function ensureFreshUI() {
  try {
    console.log("[freshness] 🔄 Checking UI freshness and killing stuck service workers...");
    
    // 1) Kill any stuck service workers that might be serving old content
    const unstickInfo = await fetch("/unstick.json", { cache: "no-store" })
      .then(r => r.json())
      .catch(() => ({ kill_sw: true })); // Default to killing SWs if unstick.json missing
    
    if (unstickInfo?.kill_sw && "serviceWorker" in navigator) {
      try {
        const registrations = await navigator.serviceWorker.getRegistrations();
        if (registrations.length > 0) {
          console.log(`[freshness] 🗑️ Unregistering ${registrations.length} service workers...`);
          await Promise.all(registrations.map(reg => reg.unregister()));
        }
        
        // Also clear any caches that might be serving stale content
        if (window.caches) {
          const cacheNames = await caches.keys();
          if (cacheNames.length > 0) {
            console.log(`[freshness] 🧹 Clearing ${cacheNames.length} caches...`);
            await Promise.all(cacheNames.map(name => caches.delete(name)));
          }
        }
      } catch (e) {
        console.warn("[freshness] Failed to clear service workers/caches:", e);
      }
    }
    
    // 2) Fetch and expose build stamp for debugging
    const buildStamp = await fetch("/build-stamp.json", { cache: "no-store" })
      .then(r => r.json())
      .catch(() => null);
    
    if (buildStamp) {
      // Expose to global scope for debugging
      (window as any).__BUILD_ID = buildStamp;
      (window as any).__BUILD_TIMESTAMP = buildStamp.timestamp;
      
      console.log(`[freshness] ✅ Build ID: ${buildStamp.build_id} (${new Date(buildStamp.timestamp).toLocaleString()})`);
      
      // Update build indicator in UI if present
      updateBuildIndicator(buildStamp);
    } else {
      console.warn("[freshness] ⚠️ No build stamp found - UI might be stale");
    }
    
    // 3) Force a hard reload if we detect we're on a very stale build
    // Temporarily disable forced reload during development to prevent infinite loops
    const buildAge = buildStamp ? Date.now() - buildStamp.timestamp : Infinity;
    if (buildAge > 24 * 60 * 60 * 1000) { // Older than 24 hours (disabled for dev)
      console.log("[freshness] 🔄 Build is very stale but reload disabled in development mode");
      // window.location.reload(); // Disabled to prevent infinite reload loops
      return;
    }
    
  } catch (e) {
    console.warn("[freshness] Error ensuring fresh UI:", e);
  }
}

function updateBuildIndicator(buildStamp: any) {
  // Update any build indicator elements
  const indicators = [
    document.getElementById("build-id"),
    document.querySelector("[data-build-id]"),
    document.querySelector(".build-indicator")
  ].filter(Boolean);
  
  const buildText = `${buildStamp.build_id} • ${new Date(buildStamp.timestamp).toLocaleTimeString()}`;
  
  indicators.forEach(element => {
    if (element) {
      element.textContent = buildText;
      element.setAttribute('title', `Build: ${buildStamp.build_id}\nTime: ${new Date(buildStamp.timestamp).toLocaleString()}\nMode: ${buildStamp.env?.UI_MODE || 'unknown'}`);
    }
  });
}

// Auto-check freshness when the page becomes visible
document.addEventListener('visibilitychange', () => {
  if (!document.hidden) {
    ensureFreshUI();
  }
});

// Also check on focus (when user switches back to tab)
window.addEventListener('focus', () => {
  ensureFreshUI();
});