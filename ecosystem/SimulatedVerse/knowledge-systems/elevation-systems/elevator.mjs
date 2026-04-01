import fs from "fs";
import path from "path";
import url from "url";
import { state } from "../engine/state.mjs";

const __dirname = path.dirname(url.fileURLToPath(import.meta.url));

function parseYAML(yamlText) {
  // Ultra-light YAML parser for our specific format
  const lines = yamlText.split("\n").map(s => s.trim());
  const floors = [];
  let currentFloor = null;
  
  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];
    if (line.startsWith("- id:")) {
      if (currentFloor) floors.push(currentFloor);
      currentFloor = { id: Number(line.split(":")[1].trim()) };
    } else if (line.startsWith("name:") && currentFloor) {
      currentFloor.name = line.split(":")[1].trim().replace(/"/g, "");
    } else if (line.startsWith("node:") && currentFloor) {
      currentFloor.node = line.split(":")[1].trim().replace(/"/g, "");
    } else if (line.startsWith("description:") && currentFloor) {
      currentFloor.description = line.split(":")[1].trim().replace(/"/g, "");
    } else if (line.startsWith("unlock:") && currentFloor) {
      currentFloor.unlock = line.split(":")[1].trim().replace(/"/g, "");
    }
  }
  if (currentFloor) floors.push(currentFloor);
  return floors;
}

export function elevator(floorId) {
  try {
    const manifestText = fs.readFileSync(path.join(__dirname, "manifest.yml"), "utf8");
    const floors = parseYAML(manifestText);
    const found = floors.find(x => x.id === Number(floorId));
    
    if (!found) return { error: "floor not found" };
    
    // Check if floor is unlocked
    const isUnlocked = checkUnlock(found.unlock);
    
    return { 
      path: path.join(__dirname, "floors", found.node), 
      meta: found,
      unlocked: isUnlocked,
      accessible: state.temple.unlockedFloors.includes(found.id)
    };
  } catch (error) {
    return { error: error.message };
  }
}

function checkUnlock(condition) {
  if (condition === "default") return true;
  
  // Simple condition parser for consciousness levels, etc.
  if (condition.includes("consciousness")) {
    const threshold = parseFloat(condition.split(">=")[1].trim());
    return state.consciousness.level >= threshold;
  }
  
  if (condition.includes("labyrinth.debugsFixed")) {
    const threshold = parseInt(condition.split(">=")[1].trim());
    return state.labyrinth.debugsFixed >= threshold;
  }
  
  if (condition.includes("colony.buildings.labs")) {
    const threshold = parseInt(condition.split(">=")[1].trim());
    return state.colony.buildings.labs >= threshold;
  }
  
  if (condition.includes("temple.knowledgePoints")) {
    const threshold = parseInt(condition.split(">=")[1].trim());
    return state.temple.knowledgePoints >= threshold;
  }
  
  return false;
}

export function getAccessibleFloors() {
  const manifestText = fs.readFileSync(path.join(__dirname, "manifest.yml"), "utf8");
  const floors = parseYAML(manifestText);
  
  return floors.filter(floor => {
    const unlocked = checkUnlock(floor.unlock);
    const accessible = state.temple.unlockedFloors.includes(floor.id);
    return unlocked && accessible;
  });
}