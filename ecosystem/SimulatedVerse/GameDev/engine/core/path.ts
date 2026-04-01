// Pathfinding - A* and Jump Point Search for navigation
// Bridges symbolic movement to literal optimal paths

import { spatialGrid, type Coord } from './spatial.js';

export interface PathNode {
  coord: Coord;
  g: number; // Distance from start
  h: number; // Heuristic distance to goal
  f: number; // Total cost (g + h)
  parent?: PathNode;
}

export interface PathResult {
  path: Coord[];
  found: boolean;
  cost: number;
  nodes_explored: number;
}

export class Pathfinder {
  private heuristic(a: Coord, b: Coord): number {
    // Manhattan distance for grid-based movement
    return Math.abs(a.x - b.x) + Math.abs(a.y - b.y);
  }

  private getNeighbors(coord: Coord): Coord[] {
    const neighbors: Coord[] = [
      { x: coord.x - 1, y: coord.y },     // Left
      { x: coord.x + 1, y: coord.y },     // Right
      { x: coord.x, y: coord.y - 1 },     // Up
      { x: coord.x, y: coord.y + 1 }      // Down
    ];

    // Filter out blocked/invalid positions
    return neighbors.filter(pos => {
      if (pos.x < 0 || pos.x >= spatialGrid.width || pos.y < 0 || pos.y >= spatialGrid.height) {
        return false;
      }
      const tile = spatialGrid.getTile(pos.x, pos.y);
      return !tile.blocked;
    });
  }

  // A* pathfinding implementation
  findPath(start: Coord, goal: Coord, maxNodes: number = 1000): PathResult {
    const openSet = new Map<string, PathNode>();
    const closedSet = new Set<string>();
    const coordKey = (c: Coord) => `${c.x},${c.y}`;
    
    let nodesExplored = 0;
    
    // Initialize start node
    const startNode: PathNode = {
      coord: start,
      g: 0,
      h: this.heuristic(start, goal),
      f: this.heuristic(start, goal)
    };
    
    openSet.set(coordKey(start), startNode);
    
    while (openSet.size > 0 && nodesExplored < maxNodes) {
      // Find node with lowest f cost
      let current = Array.from(openSet.values()).reduce((min, node) => 
        node.f < min.f ? node : min
      );
      
      const currentKey = coordKey(current.coord);
      openSet.delete(currentKey);
      closedSet.add(currentKey);
      nodesExplored++;
      
      // Check if we reached the goal
      if (current.coord.x === goal.x && current.coord.y === goal.y) {
        const path = this.reconstructPath(current);
        return {
          path,
          found: true,
          cost: current.g,
          nodes_explored: nodesExplored
        };
      }
      
      // Explore neighbors
      for (const neighborCoord of this.getNeighbors(current.coord)) {
        const neighborKey = coordKey(neighborCoord);
        
        if (closedSet.has(neighborKey)) continue;
        
        const tentativeG = current.g + 1; // Uniform cost for grid movement
        
        let neighbor = openSet.get(neighborKey);
        if (!neighbor) {
          neighbor = {
            coord: neighborCoord,
            g: Infinity,
            h: this.heuristic(neighborCoord, goal),
            f: Infinity
          };
        }
        
        if (tentativeG < neighbor.g) {
          neighbor.parent = current;
          neighbor.g = tentativeG;
          neighbor.f = neighbor.g + neighbor.h;
          openSet.set(neighborKey, neighbor);
        }
      }
    }
    
    // No path found
    return {
      path: [],
      found: false,
      cost: Infinity,
      nodes_explored: nodesExplored
    };
  }

  private reconstructPath(node: PathNode): Coord[] {
    const path: Coord[] = [];
    let current: PathNode | undefined = node;
    
    while (current) {
      path.unshift(current.coord);
      current = current.parent;
    }
    
    return path;
  }

  // Simplified pathfinding for real-time enemies
  findSimplePath(start: Coord, goal: Coord): Coord[] {
    // Direct path with basic obstacle avoidance
    const path: Coord[] = [];
    let current = { ...start };
    
    while (current.x !== goal.x || current.y !== goal.y) {
      path.push({ ...current });
      
      // Move toward goal, prefer X then Y
      if (current.x < goal.x && !spatialGrid.getTile(current.x + 1, current.y).blocked) {
        current.x++;
      } else if (current.x > goal.x && !spatialGrid.getTile(current.x - 1, current.y).blocked) {
        current.x--;
      } else if (current.y < goal.y && !spatialGrid.getTile(current.x, current.y + 1).blocked) {
        current.y++;
      } else if (current.y > goal.y && !spatialGrid.getTile(current.x, current.y - 1).blocked) {
        current.y--;
      } else {
        // Stuck, try to move around obstacle
        const neighbors = this.getNeighbors(current);
        if (neighbors.length > 0) {
          const closest = neighbors.reduce((min, coord) => 
            this.heuristic(coord, goal) < this.heuristic(min, goal) ? coord : min
          );
          current = closest;
        } else {
          break; // No valid moves
        }
      }
      
      // Prevent infinite loops
      if (path.length > 200) break;
    }
    
    path.push(goal);
    return path;
  }

  // Pre-computed paths for tower defense lanes
  createLanePaths(lanes: number = 2): Coord[][] {
    const paths: Coord[][] = [];
    const laneSpacing = Math.floor(spatialGrid.height / (lanes + 1));
    
    for (let lane = 0; lane < lanes; lane++) {
      const y = laneSpacing * (lane + 1);
      const path: Coord[] = [];
      
      for (let x = 0; x < spatialGrid.width; x += 2) {
        path.push({ x, y });
      }
      
      paths.push(path);
    }
    
    return paths;
  }
}

export const pathfinder = new Pathfinder();
