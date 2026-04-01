/**
 * Quantum Visualization Engine
 * Renders particle effects, probability waves, and entanglement networks
 * for the Quantum Visualization module
 */

class QuantumVisualization {
    constructor(canvasId = 'quantum-canvas') {
        this.canvas = document.getElementById(canvasId);
        if (!this.canvas) {
            console.warn('Quantum canvas not found:', canvasId);
            return;
        }

        this.ctx = this.canvas.getContext('2d');
        this.width = this.canvas.width;
        this.height = this.canvas.height;

        // Visualization state
        this.particles = [];
        this.waves = [];
        this.connections = [];
        this.mode = 'particles'; // particles, waves, entanglement

        // Animation
        this.animating = false;
        this.frameId = null;

        this.init();
    }

    init() {
        // Initialize particles
        for (let i = 0; i < 50; i++) {
            this.particles.push(this.createParticle());
        }

        // Initialize wave points
        for (let i = 0; i < 100; i++) {
            this.waves.push({
                x: (this.width / 100) * i,
                y: this.height / 2,
                phase: Math.random() * Math.PI * 2,
                amplitude: 30 + Math.random() * 40,
                frequency: 0.02 + Math.random() * 0.03
            });
        }

        // Setup button listeners
        this.setupControls();

        // Start animation
        this.start();
    }

    createParticle() {
        return {
            x: Math.random() * this.width,
            y: Math.random() * this.height,
            vx: (Math.random() - 0.5) * 2,
            vy: (Math.random() - 0.5) * 2,
            radius: 2 + Math.random() * 4,
            hue: 180 + Math.random() * 60, // Cyan to purple range
            alpha: 0.5 + Math.random() * 0.5,
            pulsePhase: Math.random() * Math.PI * 2,
            entangled: Math.random() > 0.7 // 30% are entangled
        };
    }

    setupControls() {
        const buttons = document.querySelectorAll('.viz-btn');
        buttons.forEach(btn => {
            btn.addEventListener('click', (e) => {
                // Remove active class from all
                buttons.forEach(b => b.classList.remove('active'));
                // Add to clicked
                e.target.classList.add('active');

                const viz = e.target.dataset.viz;
                this.setMode(viz);
            });
        });

        // Set first button as active
        if (buttons.length > 0) {
            buttons[0].classList.add('active');
        }
    }

    setMode(mode) {
        this.mode = mode;
        console.log(`Quantum visualization mode: ${mode}`);
    }

    start() {
        if (this.animating) return;
        this.animating = true;
        this.animate();
    }

    stop() {
        this.animating = false;
        if (this.frameId) {
            cancelAnimationFrame(this.frameId);
        }
    }

    animate() {
        if (!this.animating) return;

        this.update();
        this.render();

        this.frameId = requestAnimationFrame(() => this.animate());
    }

    update() {
        const time = Date.now() * 0.001;

        // Update particles
        this.particles.forEach(p => {
            p.x += p.vx;
            p.y += p.vy;

            // Bounce off walls
            if (p.x < 0 || p.x > this.width) p.vx *= -1;
            if (p.y < 0 || p.y > this.height) p.vy *= -1;

            // Keep in bounds
            p.x = Math.max(0, Math.min(this.width, p.x));
            p.y = Math.max(0, Math.min(this.height, p.y));

            // Pulse
            p.pulsePhase += 0.05;
        });

        // Update waves
        this.waves.forEach((w, i) => {
            w.phase += w.frequency;
            w.y = this.height / 2 + Math.sin(w.phase + i * 0.1) * w.amplitude;
        });

        // Update entanglement connections
        this.connections = [];
        const entangledParticles = this.particles.filter(p => p.entangled);
        for (let i = 0; i < entangledParticles.length; i++) {
            for (let j = i + 1; j < entangledParticles.length; j++) {
                const p1 = entangledParticles[i];
                const p2 = entangledParticles[j];
                const dist = Math.sqrt((p1.x - p2.x) ** 2 + (p1.y - p2.y) ** 2);
                if (dist < 150) {
                    this.connections.push({
                        from: p1,
                        to: p2,
                        strength: 1 - dist / 150
                    });
                }
            }
        }
    }

    render() {
        // Clear canvas with fade effect
        this.ctx.fillStyle = 'rgba(10, 10, 30, 0.15)';
        this.ctx.fillRect(0, 0, this.width, this.height);

        switch (this.mode) {
            case 'particles':
                this.renderParticles();
                break;
            case 'waves':
                this.renderWaves();
                break;
            case 'entanglement':
                this.renderEntanglement();
                break;
        }
    }

    renderParticles() {
        this.particles.forEach(p => {
            const pulseSize = 1 + Math.sin(p.pulsePhase) * 0.3;
            const radius = p.radius * pulseSize;

            // Glow effect
            const gradient = this.ctx.createRadialGradient(
                p.x, p.y, 0,
                p.x, p.y, radius * 3
            );
            gradient.addColorStop(0, `hsla(${p.hue}, 100%, 70%, ${p.alpha})`);
            gradient.addColorStop(0.5, `hsla(${p.hue}, 100%, 50%, ${p.alpha * 0.5})`);
            gradient.addColorStop(1, `hsla(${p.hue}, 100%, 30%, 0)`);

            this.ctx.beginPath();
            this.ctx.arc(p.x, p.y, radius * 3, 0, Math.PI * 2);
            this.ctx.fillStyle = gradient;
            this.ctx.fill();

            // Core particle
            this.ctx.beginPath();
            this.ctx.arc(p.x, p.y, radius, 0, Math.PI * 2);
            this.ctx.fillStyle = `hsla(${p.hue}, 100%, 80%, ${p.alpha})`;
            this.ctx.fill();
        });
    }

    renderWaves() {
        // Draw probability wave
        this.ctx.beginPath();
        this.ctx.moveTo(0, this.height / 2);

        this.waves.forEach((w, i) => {
            if (i === 0) {
                this.ctx.moveTo(w.x, w.y);
            } else {
                const prev = this.waves[i - 1];
                const cpx = (prev.x + w.x) / 2;
                const cpy = (prev.y + w.y) / 2;
                this.ctx.quadraticCurveTo(prev.x, prev.y, cpx, cpy);
            }
        });

        // Gradient stroke
        const gradient = this.ctx.createLinearGradient(0, 0, this.width, 0);
        gradient.addColorStop(0, 'rgba(0, 245, 255, 0.8)');
        gradient.addColorStop(0.5, 'rgba(138, 43, 226, 0.8)');
        gradient.addColorStop(1, 'rgba(0, 245, 255, 0.8)');

        this.ctx.strokeStyle = gradient;
        this.ctx.lineWidth = 3;
        this.ctx.stroke();

        // Draw wave fill
        this.ctx.lineTo(this.width, this.height);
        this.ctx.lineTo(0, this.height);
        this.ctx.closePath();

        const fillGradient = this.ctx.createLinearGradient(0, 0, 0, this.height);
        fillGradient.addColorStop(0, 'rgba(0, 245, 255, 0.1)');
        fillGradient.addColorStop(1, 'rgba(138, 43, 226, 0.05)');

        this.ctx.fillStyle = fillGradient;
        this.ctx.fill();

        // Draw secondary wave (out of phase)
        this.ctx.beginPath();
        this.waves.forEach((w, i) => {
            const y2 = this.height / 2 + Math.sin(w.phase + Math.PI) * w.amplitude * 0.6;
            if (i === 0) {
                this.ctx.moveTo(w.x, y2);
            } else {
                this.ctx.lineTo(w.x, y2);
            }
        });

        this.ctx.strokeStyle = 'rgba(255, 100, 200, 0.4)';
        this.ctx.lineWidth = 2;
        this.ctx.stroke();
    }

    renderEntanglement() {
        // Draw connections first (behind particles)
        this.connections.forEach(conn => {
            this.ctx.beginPath();
            this.ctx.moveTo(conn.from.x, conn.from.y);
            this.ctx.lineTo(conn.to.x, conn.to.y);

            this.ctx.strokeStyle = `rgba(0, 245, 255, ${conn.strength * 0.5})`;
            this.ctx.lineWidth = conn.strength * 3;
            this.ctx.stroke();

            // Draw connection glow
            this.ctx.strokeStyle = `rgba(138, 43, 226, ${conn.strength * 0.3})`;
            this.ctx.lineWidth = conn.strength * 8;
            this.ctx.stroke();
        });

        // Draw particles (entangled ones glow more)
        this.particles.forEach(p => {
            const isEntangled = p.entangled;
            const pulseSize = 1 + Math.sin(p.pulsePhase) * (isEntangled ? 0.5 : 0.2);
            const radius = p.radius * pulseSize;

            // Entangled particles glow more
            const glowRadius = isEntangled ? radius * 5 : radius * 2;
            const alpha = isEntangled ? p.alpha : p.alpha * 0.5;

            // Outer glow
            const gradient = this.ctx.createRadialGradient(
                p.x, p.y, 0,
                p.x, p.y, glowRadius
            );

            if (isEntangled) {
                gradient.addColorStop(0, `rgba(0, 245, 255, ${alpha})`);
                gradient.addColorStop(0.4, `rgba(138, 43, 226, ${alpha * 0.5})`);
                gradient.addColorStop(1, 'rgba(0, 0, 0, 0)');
            } else {
                gradient.addColorStop(0, `rgba(100, 100, 120, ${alpha * 0.5})`);
                gradient.addColorStop(1, 'rgba(0, 0, 0, 0)');
            }

            this.ctx.beginPath();
            this.ctx.arc(p.x, p.y, glowRadius, 0, Math.PI * 2);
            this.ctx.fillStyle = gradient;
            this.ctx.fill();

            // Core
            this.ctx.beginPath();
            this.ctx.arc(p.x, p.y, radius, 0, Math.PI * 2);
            this.ctx.fillStyle = isEntangled
                ? `rgba(0, 245, 255, ${alpha})`
                : `rgba(150, 150, 180, ${alpha})`;
            this.ctx.fill();
        });

        // Draw connection count
        this.ctx.fillStyle = 'rgba(255, 255, 255, 0.7)';
        this.ctx.font = '12px monospace';
        this.ctx.fillText(`Entangled Pairs: ${this.connections.length}`, 10, 20);
        this.ctx.fillText(`Total Particles: ${this.particles.length}`, 10, 35);
    }

    // Resize handler
    resize(width, height) {
        this.width = width;
        this.height = height;
        this.canvas.width = width;
        this.canvas.height = height;
    }

    // Destroy and cleanup
    destroy() {
        this.stop();
        this.particles = [];
        this.waves = [];
        this.connections = [];
    }
}

// Auto-initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    // Only initialize if canvas exists
    const canvas = document.getElementById('quantum-canvas');
    if (canvas) {
        window.quantumViz = new QuantumVisualization('quantum-canvas');
        console.log('Quantum Visualization initialized');
    }
});

// Export for module usage
if (typeof module !== 'undefined' && module.exports) {
    module.exports = QuantumVisualization;
}
