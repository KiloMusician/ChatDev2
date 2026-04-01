// Bus shim (so you can run it server-side or headless)
// If your ops loop isn't inside the web app bundle, add a tiny shim that re-exports the same bus API you use in the HUD

export { councilBus } from "../packages/council/events/eventBus.js";