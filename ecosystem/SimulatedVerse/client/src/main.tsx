import React from "react";
import ReactDOM from "react-dom/client";
import App from "./App";
import "./styles.css";
import "./ui/ascii/ascii.css";
import { ensureFreshUI } from "./boot/freshness";

// Ensure fresh UI on startup - kills service workers and checks build stamps
ensureFreshUI();

// Complete fix for React error #185 - remove hydration issues entirely
const container = document.getElementById("root")!;
const root = ReactDOM.createRoot(container);

// Always render without StrictMode to prevent hydration mismatch
root.render(<App />);
