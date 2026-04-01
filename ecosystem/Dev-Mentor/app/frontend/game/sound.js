/**
 * Terminal Depths — Sound System
 * Web Audio API: ambient cyberpunk music + terminal SFX
 * Settings stored in localStorage
 */

(() => {
	// ── Settings ───────────────────────────────────────────────────────────────
	const PREFS_KEY = "td_sound_prefs";

	function loadPrefs() {
		try {
			return JSON.parse(localStorage.getItem(PREFS_KEY) || "{}");
		} catch {
			return {};
		}
	}

	function savePrefs(prefs) {
		try {
			localStorage.setItem(PREFS_KEY, JSON.stringify(prefs));
		} catch {}
	}

	const prefs = loadPrefs();
	let sfxEnabled = prefs.sfx !== false;
	let ambientEnabled = prefs.ambient !== false;

	// ── AudioContext (lazy) ────────────────────────────────────────────────────
	let _ctx = null;

	function ctx() {
		if (!_ctx) {
			try {
				_ctx = new (window.AudioContext || window.webkitAudioContext)();
			} catch (e) {
				return null;
			}
		}
		if (_ctx.state === "suspended") _ctx.resume().catch(() => {});
		return _ctx;
	}

	// ── SFX helpers ────────────────────────────────────────────────────────────

	/**
	 * Generate a short beep.
	 */
	function _beep(freq, duration, type = "sine", gain = 0.08) {
		const c = ctx();
		if (!c) return;
		try {
			const osc = c.createOscillator();
			const env = c.createGain();
			osc.connect(env);
			env.connect(c.destination);
			osc.type = type;
			osc.frequency.setValueAtTime(freq, c.currentTime);
			env.gain.setValueAtTime(gain, c.currentTime);
			env.gain.exponentialRampToValueAtTime(0.0001, c.currentTime + duration);
			osc.start(c.currentTime);
			osc.stop(c.currentTime + duration);
		} catch {}
	}

	/**
	 * White-noise burst for glitch / error sounds.
	 */
	function _noise(duration, gain = 0.05) {
		const c = ctx();
		if (!c) return;
		try {
			const sr = c.sampleRate;
			const frames = Math.ceil(sr * duration);
			const buf = c.createBuffer(1, frames, sr);
			const data = buf.getChannelData(0);
			for (let i = 0; i < frames; i++) data[i] = Math.random() * 2 - 1;
			const src = c.createBufferSource();
			src.buffer = buf;
			const env = c.createGain();
			src.connect(env);
			env.connect(c.destination);
			env.gain.setValueAtTime(gain, c.currentTime);
			env.gain.exponentialRampToValueAtTime(0.0001, c.currentTime + duration);
			src.start(c.currentTime);
		} catch {}
	}

	// ── Public SFX API ─────────────────────────────────────────────────────────

	function sfxKeyClick() {
		if (!sfxEnabled) return;
		// Randomise pitch slightly for organic feel
		const freq = 280 + Math.random() * 80;
		_beep(freq, 0.04, "square", 0.04);
	}

	function sfxEnter() {
		if (!sfxEnabled) return;
		_beep(660, 0.06, "sine", 0.06);
		setTimeout(() => _beep(880, 0.04, "sine", 0.04), 50);
	}

	function sfxError() {
		if (!sfxEnabled) return;
		_noise(0.12, 0.07);
		setTimeout(() => _beep(180, 0.2, "sawtooth", 0.05), 30);
	}

	function sfxXp() {
		if (!sfxEnabled) return;
		[440, 550, 660].forEach((f, i) =>
			setTimeout(() => _beep(f, 0.08, "sine", 0.07), i * 60),
		);
	}

	function sfxLevelUp() {
		if (!sfxEnabled) return;
		[440, 550, 660, 880, 1100].forEach((f, i) =>
			setTimeout(() => _beep(f, 0.1, "sine", 0.09), i * 80),
		);
	}

	function sfxHackStart() {
		if (!sfxEnabled) return;
		_noise(0.08, 0.06);
		[220, 330, 440].forEach((f, i) =>
			setTimeout(() => _beep(f, 0.15, "sawtooth", 0.06), i * 40),
		);
	}

	function sfxHackSuccess() {
		if (!sfxEnabled) return;
		[660, 880, 1100, 1320].forEach((f, i) =>
			setTimeout(() => _beep(f, 0.12, "sine", 0.08), i * 70),
		);
	}

	function sfxUnlock() {
		if (!sfxEnabled) return;
		[440, 660, 880].forEach((f, i) =>
			setTimeout(() => _beep(f, 0.1, "triangle", 0.07), i * 50),
		);
	}

	// ── Ambient Music ──────────────────────────────────────────────────────────

	let _ambientNodes = null;
	let _hackingMode = false;

	function _buildAmbient() {
		const c = ctx();
		if (!c) return null;

		const master = c.createGain();
		master.gain.setValueAtTime(0.0001, c.currentTime);
		master.connect(c.destination);

		// Deep drone — a chord of three detuned oscillators
		const droneFreqs = [55, 82.5, 110];
		const drones = droneFreqs.map((f) => {
			const osc = c.createOscillator();
			const g = c.createGain();
			osc.type = "sawtooth";
			osc.frequency.setValueAtTime(
				f + (Math.random() - 0.5) * 0.5,
				c.currentTime,
			);
			g.gain.setValueAtTime(0.07, c.currentTime);
			osc.connect(g);
			g.connect(master);
			osc.start();
			return { osc, g };
		});

		// High-pitch shimmer
		const shimmer = c.createOscillator();
		const shimmerGain = c.createGain();
		shimmer.type = "sine";
		shimmer.frequency.setValueAtTime(880, c.currentTime);
		shimmerGain.gain.setValueAtTime(0.015, c.currentTime);
		shimmer.connect(shimmerGain);
		shimmerGain.connect(master);
		shimmer.start();

		// LFO modulating shimmer
		const lfo = c.createOscillator();
		const lfoGain = c.createGain();
		lfo.frequency.setValueAtTime(0.15, c.currentTime);
		lfoGain.gain.setValueAtTime(20, c.currentTime);
		lfo.connect(lfoGain);
		lfoGain.connect(shimmer.frequency);
		lfo.start();

		// Pulse rhythm — low kick-like thump
		let _pulseTimer = null;
		function _pulse() {
			if (!_ambientNodes) return;
			const c2 = ctx();
			if (!c2) return;
			const kickOsc = c2.createOscillator();
			const kickEnv = c2.createGain();
			kickOsc.type = "sine";
			kickOsc.frequency.setValueAtTime(120, c2.currentTime);
			kickOsc.frequency.exponentialRampToValueAtTime(30, c2.currentTime + 0.2);
			kickEnv.gain.setValueAtTime(0.12, c2.currentTime);
			kickEnv.gain.exponentialRampToValueAtTime(0.0001, c2.currentTime + 0.4);
			kickOsc.connect(kickEnv);
			kickEnv.connect(master);
			kickOsc.start(c2.currentTime);
			kickOsc.stop(c2.currentTime + 0.4);
			const interval = _hackingMode ? 400 : 800;
			_pulseTimer = setTimeout(_pulse, interval);
		}
		_pulse();

		return {
			master,
			drones,
			shimmer,
			shimmerGain,
			lfo,
			lfoGain,
			_stop() {
				clearTimeout(_pulseTimer);
			},
		};
	}

	function startAmbient() {
		if (!ambientEnabled || _ambientNodes) return;
		const c = ctx();
		if (!c) return;
		_ambientNodes = _buildAmbient();
		if (!_ambientNodes) return;
		const m = _ambientNodes.master;
		m.gain.cancelScheduledValues(c.currentTime);
		m.gain.setValueAtTime(0.0001, c.currentTime);
		m.gain.linearRampToValueAtTime(0.4, c.currentTime + 3);
	}

	function stopAmbient() {
		if (!_ambientNodes) return;
		const c = ctx();
		if (c) {
			try {
				_ambientNodes.master.gain.cancelScheduledValues(c.currentTime);
				_ambientNodes.master.gain.setValueAtTime(
					_ambientNodes.master.gain.value,
					c.currentTime,
				);
				_ambientNodes.master.gain.linearRampToValueAtTime(
					0.0001,
					c.currentTime + 2,
				);
			} catch {}
		}
		const nodes = _ambientNodes;
		_ambientNodes = null;
		setTimeout(() => {
			try {
				nodes._stop();
				nodes.drones.forEach((d) => {
					d.osc.stop();
					d.g.disconnect();
				});
				nodes.shimmer.stop();
				nodes.lfo.stop();
				nodes.master.disconnect();
			} catch {}
		}, 2500);
	}

	/**
	 * Switch to hacking intensity (faster pulse, higher volume).
	 */
	function setHackingMode(enabled) {
		_hackingMode = enabled;
		if (!_ambientNodes) return;
		const c = ctx();
		if (!c) return;
		const targetGain = enabled ? 0.7 : 0.4;
		_ambientNodes.master.gain.cancelScheduledValues(c.currentTime);
		_ambientNodes.master.gain.setValueAtTime(
			_ambientNodes.master.gain.value,
			c.currentTime,
		);
		_ambientNodes.master.gain.linearRampToValueAtTime(
			targetGain,
			c.currentTime + 1.5,
		);
		// Speed up shimmer LFO
		_ambientNodes.lfo.frequency.setValueAtTime(
			enabled ? 0.8 : 0.15,
			c.currentTime,
		);
	}

	// ── Toggle controls ────────────────────────────────────────────────────────

	function toggleSfx() {
		sfxEnabled = !sfxEnabled;
		prefs.sfx = sfxEnabled;
		savePrefs(prefs);
		return sfxEnabled;
	}

	function toggleAmbient() {
		ambientEnabled = !ambientEnabled;
		prefs.ambient = ambientEnabled;
		savePrefs(prefs);
		if (ambientEnabled) {
			startAmbient();
		} else {
			stopAmbient();
		}
		return ambientEnabled;
	}

	// ── Export ─────────────────────────────────────────────────────────────────

	window.SoundSystem = {
		sfxKeyClick,
		sfxEnter,
		sfxError,
		sfxXp,
		sfxLevelUp,
		sfxHackStart,
		sfxHackSuccess,
		sfxUnlock,
		startAmbient,
		stopAmbient,
		setHackingMode,
		toggleSfx,
		toggleAmbient,
		get sfxEnabled() {
			return sfxEnabled;
		},
		get ambientEnabled() {
			return ambientEnabled;
		},
	};
})();
