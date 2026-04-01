/**
 * House of Leaves - Debugging Labyrinth Game Engine
 * ASCII maze navigation with error tracking (Minotaur)
 */

class HouseOfLeavesEngine {
    constructor(containerId) {
        this.containerId = containerId;
        this.maze = [];
        this.playerPos = { x: 1, y: 1 };
        this.minotaurPos = { x: 15, y: 15 };
        this.errors = [];
        this.rooms = [];
        this.currentFloor = 1;
        this.maxFloors = 7;
        this.keysCollected = 0;
        this.doorsUnlocked = 0;

        this.generateMaze(20, 20);
    }

    generateMaze(width, height) {
        // Generate procedural maze
        this.maze = Array(height).fill(null).map(() => Array(width).fill('#'));

        // Carve paths using recursive backtracker
        const stack = [];
        const start = { x: 1, y: 1 };
        this.maze[start.y][start.x] = '.';
        stack.push(start);

        const directions = [
            { dx: 0, dy: -2, label: 'N' },
            { dx: 2, dy: 0, label: 'E' },
            { dx: 0, dy: 2, label: 'S' },
            { dx: -2, dy: 0, label: 'W' }
        ];

        while (stack.length > 0) {
            const current = stack[stack.length - 1];
            const validDirs = directions.filter(dir => {
                const nx = current.x + dir.dx;
                const ny = current.y + dir.dy;
                return nx > 0 && nx < width - 1 && ny > 0 && ny < height - 1 && this.maze[ny][nx] === '#';
            });

            if (validDirs.length > 0) {
                const dir = validDirs[Math.floor(Math.random() * validDirs.length)];
                const nx = current.x + dir.dx;
                const ny = current.y + dir.dy;
                const mx = current.x + dir.dx / 2;
                const my = current.y + dir.dy / 2;

                this.maze[ny][nx] = '.';
                this.maze[my][mx] = '.';
                stack.push({ x: nx, y: ny });
            } else {
                stack.pop();
            }
        }

        // Place special tiles
        this.placeKeys();
        this.placeDoors();
        this.placeErrors();
        this.placeExit();
    }

    placeKeys() {
        for (let i = 0; i < 3; i++) {
            const pos = this.getRandomOpenPosition();
            this.maze[pos.y][pos.x] = 'K'; // Key
        }
    }

    placeDoors() {
        for (let i = 0; i < 2; i++) {
            const pos = this.getRandomOpenPosition();
            this.maze[pos.y][pos.x] = 'D'; // Door
        }
    }

    placeErrors() {
        // Errors are the Minotaur - place error markers
        for (let i = 0; i < 5; i++) {
            const pos = this.getRandomOpenPosition();
            this.maze[pos.y][pos.x] = 'E'; // Error
            this.errors.push({ x: pos.x, y: pos.y, type: 'syntax', severity: 'high' });
        }
    }

    placeExit() {
        const pos = this.getRandomOpenPosition();
        this.maze[pos.y][pos.x] = 'X'; // Exit
    }

    getRandomOpenPosition() {
        let x, y;
        do {
            x = Math.floor(Math.random() * (this.maze[0].length - 2)) + 1;
            y = Math.floor(Math.random() * (this.maze.length - 2)) + 1;
        } while (this.maze[y][x] !== '.');
        return { x, y };
    }

    render() {
        const container = document.getElementById(this.containerId);
        if (!container) return;

        // Place player
        this.maze[this.playerPos.y][this.playerPos.x] = '@';

        let html = '<div style="font-family: monospace; line-height: 1.2; color: #0f0; background: #000; padding: 20px;">';

        // HUD
        html += `<div style="margin-bottom: 10px; color: #0ff;">`;
        html += `Floor ${this.currentFloor}/${this.maxFloors} | Keys: ${this.keysCollected} | Doors: ${this.doorsUnlocked} | Errors: ${this.errors.length}<br>`;
        html += `Commands: WASD/Arrows = Move | H = Help | R = Reset<br>`;
        html += `</div>`;

        // Maze
        html += '<pre style="margin: 0;">';
        this.maze.forEach((row, y) => {
            row.forEach((cell, x) => {
                if (x === this.playerPos.x && y === this.playerPos.y) {
                    html += '<span style="color: #0ff; font-weight: bold;">@</span>';
                } else if (x === this.minotaurPos.x && y === this.minotaurPos.y) {
                    html += '<span style="color: #f00; font-weight: bold;">M</span>';
                } else {
                    let color = '#0f0';
                    switch (cell) {
                        case '#': color = '#555'; break;
                        case 'K': color = '#ff0'; break;
                        case 'D': color = '#f80'; break;
                        case 'E': color = '#f00'; break;
                        case 'X': color = '#0ff'; break;
                    }
                    html += `<span style="color: ${color}">${cell}</span>`;
                }
            });
            html += '\n';
        });
        html += '</pre>';

        // Legend
        html += '<div style="margin-top: 10px; font-size: 12px; color: #888;">';
        html += '@ = You | M = Minotaur (Errors) | K = Key | D = Door | E = Error | X = Exit | # = Wall';
        html += '</div>';

        html += '</div>';

        container.innerHTML = html;

        // Reset player position marker
        this.maze[this.playerPos.y][this.playerPos.x] = '.';
    }

    move(direction) {
        const moves = {
            'w': { dx: 0, dy: -1 },
            'a': { dx: -1, dy: 0 },
            's': { dx: 0, dy: 1 },
            'd': { dx: 1, dy: 0 },
            'ArrowUp': { dx: 0, dy: -1 },
            'ArrowLeft': { dx: -1, dy: 0 },
            'ArrowDown': { dx: 0, dy: 1 },
            'ArrowRight': { dx: 1, dy: 0 }
        };

        const move = moves[direction];
        if (!move) return false;

        const newX = this.playerPos.x + move.dx;
        const newY = this.playerPos.y + move.dy;

        // Check bounds
        if (newY < 0 || newY >= this.maze.length || newX < 0 || newX >= this.maze[0].length) {
            return false;
        }

        const tile = this.maze[newY][newX];

        // Check wall
        if (tile === '#') {
            return false;
        }

        // Check door
        if (tile === 'D') {
            if (this.keysCollected > 0) {
                this.keysCollected--;
                this.doorsUnlocked++;
                this.maze[newY][newX] = '.';
                alert('🚪 Door unlocked!');
            } else {
                alert('🔒 You need a key to open this door');
                return false;
            }
        }

        // Check key
        if (tile === 'K') {
            this.keysCollected++;
            this.maze[newY][newX] = '.';
            alert('🔑 Key collected!');
        }

        // Check error
        if (tile === 'E') {
            this.maze[newY][newX] = '.';
            this.errors = this.errors.filter(e => !(e.x === newX && e.y === newY));
            alert('🐛 Error resolved! The Minotaur weakens...');
        }

        // Check exit
        if (tile === 'X') {
            if (this.errors.length === 0) {
                this.advanceFloor();
                return true;
            } else {
                alert('❌ You cannot exit while errors remain! Resolve all errors first.');
                return false;
            }
        }

        // Move player
        this.playerPos.x = newX;
        this.playerPos.y = newY;

        // Move Minotaur (if there are errors)
        if (this.errors.length > 0) {
            this.moveMinotaur();
        }

        return true;
    }

    moveMinotaur() {
        // Minotaur chases player
        const dx = this.playerPos.x - this.minotaurPos.x;
        const dy = this.playerPos.y - this.minotaurPos.y;

        if (Math.abs(dx) > Math.abs(dy)) {
            const newX = this.minotaurPos.x + Math.sign(dx);
            if (this.maze[this.minotaurPos.y][newX] !== '#') {
                this.minotaurPos.x = newX;
            }
        } else {
            const newY = this.minotaurPos.y + Math.sign(dy);
            if (this.maze[newY] && this.maze[newY][this.minotaurPos.x] !== '#') {
                this.minotaurPos.y = newY;
            }
        }

        // Check if Minotaur caught player
        if (this.minotaurPos.x === this.playerPos.x && this.minotaurPos.y === this.playerPos.y) {
            alert('💀 The Minotaur (accumulated errors) caught you! Resetting floor...');
            this.reset();
        }
    }

    advanceFloor() {
        if (this.currentFloor < this.maxFloors) {
            this.currentFloor++;
            alert(`✨ Floor ${this.currentFloor} reached! Generating new maze...`);
            this.generateMaze(20 + this.currentFloor * 2, 20 + this.currentFloor * 2);
            this.playerPos = { x: 1, y: 1 };
            this.render();
        } else {
            alert('🎉 Congratulations! You have escaped the House of Leaves!');
        }
    }

    reset() {
        this.playerPos = { x: 1, y: 1 };
        this.minotaurPos = { x: 15, y: 15 };
        this.keysCollected = 0;
        this.doorsUnlocked = 0;
        this.generateMaze(20, 20);
        this.render();
    }

    setupControls() {
        document.addEventListener('keydown', (e) => {
            if (['w', 'a', 's', 'd', 'ArrowUp', 'ArrowLeft', 'ArrowDown', 'ArrowRight'].includes(e.key)) {
                e.preventDefault();
                if (this.move(e.key)) {
                    this.render();
                }
            } else if (e.key.toLowerCase() === 'h') {
                alert('HOUSE OF LEAVES - Help\n\n' +
                      'Goal: Navigate the maze, collect keys, unlock doors, resolve all errors, and reach the exit.\n\n' +
                      'Controls:\n' +
                      'WASD or Arrow Keys - Move\n' +
                      'H - Help\n' +
                      'R - Reset\n\n' +
                      'Legend:\n' +
                      '@ = You\n' +
                      'M = Minotaur (Accumulated Errors)\n' +
                      'K = Key\n' +
                      'D = Door (needs key)\n' +
                      'E = Error (resolve to weaken Minotaur)\n' +
                      'X = Exit (only accessible when all errors resolved)\n' +
                      '# = Wall\n\n' +
                      'Beware: The Minotaur chases you!');
            } else if (e.key.toLowerCase() === 'r') {
                this.reset();
            }
        });
    }
}

// Global export
window.HouseOfLeavesEngine = HouseOfLeavesEngine;

console.log('✅ House of Leaves Engine loaded');
