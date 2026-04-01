import blessed from 'blessed';
import contrib from 'blessed-contrib';

const screen = blessed.screen({ 
    smartCSR: true, 
    fullUnicode: true, 
    mouse: true, 
    dockBorders: true 
});
screen.title = 'CoreLink Foundation ASCII HUD';

const grid = new contrib.grid({rows: 12, cols: 12, screen});

// Create widgets using your exact layout
const log  = grid.set(0, 0, 4, 8, contrib.log, {
    label:'CoreLink Feed',
    style: { border: { fg: '#32c8ff' } }
});

const map  = grid.set(0, 8, 8, 4, contrib.map, {
    label:'Minimap',
    style: { border: { fg: '#ff7850' } }
});

const spark = grid.set(4, 0, 4, 8, contrib.sparkline, {
    label:'Energy Systems',
    style: { border: { fg: '#78dc78' } }
});

const box = grid.set(8, 0, 4, 12, blessed.box, {
    label:'TouchDesigner Status',
    tags: true,
    border: 'line',
    style: { border: { fg: '#ffd25a' } }
});

// Animation state
let t = 0;

// Populate with TouchDesigner-style data
function updateDisplay() {
    t += 1;
    
    // Add CoreLink-style log entries
    const logEntries = [
        `tick ${t} {#32c8ff-fg}ripple effect{/} active`,
        `energy field {#78dc78-fg}stabilized{/} at ${(890 + Math.sin(t/10)*50)|0}W`,
        `colonist ${Math.floor(Math.random()*3)+1} {#ffd25a-fg}discovered{/} rare mineral`,
        `defense grid {#ff7850-fg}scanning{/} sector ${((t/7)|0)%8+1}`,
        `ai core {#32c8ff-fg}processing{/} optimization task`,
        `braille renderer {#78dc78-fg}fps{/}: ${(18+Math.random()*4)|0}`,
    ];
    
    if (t % 3 === 0) {
        log.log(logEntries[Math.floor(Math.random() * logEntries.length)]);
    }
    
    // Energy sparkline with realistic patterns
    const energyData = Array.from({length: 60}, (_, i) => {
        const base = Math.sin((i + t) / 7) * 5 + 5;
        const noise = Math.random() * 2 - 1;
        return Math.max(0, (base + noise) | 0);
    });
    
    spark.setData(['Energy'], [energyData]);
    
    // Status box with TouchDesigner aesthetic
    const statusContent = `{#32c8ff-fg}⌘ CORELINK FOUNDATION{/}
═══════════════════════════════════════════

{#78dc78-fg}SYSTEMS STATUS{/}:
  Viewport: {#32c8ff-fg}20 FPS{/} braille micro-pixels
  Effects:  {#ffd25a-fg}sine_ripple{/} | {#ff7850-fg}noise_flow{/} | {#78dc78-fg}radar_sweep{/}
  
{#ff7850-fg}RESOURCES{/}:
  Energy:     ${(890 + Math.sin(t/10)*50)|0} W
  Materials:  ${(2400 + Math.sin(t/15)*200)|0} kg
  Colonists:  ${3 + ((t/100)|0)%2}
  
{#ffd25a-fg}ACTIVE MODULES{/}:
  [1] Ripple     [2] Noise      [3] Radar
  [4] Matrix     [5] Stars      [6] Cellular
  
{#32c8ff-fg}TouchDesigner-style ASCII interface ready{/}
Press 'q' to exit, 'r' to restart, 'm' for modes`;

    box.setContent(statusContent);
    
    screen.render();
}

// Key bindings matching your TUI
screen.key(['escape', 'q', 'C-c'], () => {
    process.exit(0);
});

screen.key(['r'], () => {
    log.log('{#78dc78-fg}System restarted{/}');
});

screen.key(['m'], () => {
    log.log('{#ffd25a-fg}Mode cycling{/} through effects');
});

screen.key(['1', '2', '3', '4', '5'], (ch, key) => {
    const modes = ['ripple', 'noise', 'radar', 'matrix', 'stars'];
    const mode = modes[parseInt(key.name) - 1];
    log.log(`{#32c8ff-fg}Effect mode{/}: ${mode}`);
});

// Start the animation loop at 20 FPS
setInterval(updateDisplay, 50);

// Initial render
updateDisplay();

console.log('CoreLink Foundation Node.js ASCII HUD started');
console.log('Press q to quit, r to restart, m for modes, 1-5 for effects');