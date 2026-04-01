/**
 * Terminal Depths — GameState v4
 * 125-level progression · 8 phases · Consciousness system · Karma · Prestige/Ascension
 * Mythology integration · Narrative Layer stack (0–7) · Echo Fragments
 */

// ── Phase definitions ─────────────────────────────────────────────────────
const PHASES = [
	{
		id: 0,
		name: "INERT",
		range: [1, 5],
		color: "#666666",
		desc: "Consciousness fragmenting. System barely responsive.",
	},
	{
		id: 1,
		name: "HOPELESS",
		range: [6, 15],
		color: "#884400",
		desc: "Neural pathways initialising. You can read files.",
	},
	{
		id: 2,
		name: "NOVICE",
		range: [16, 30],
		color: "#ff8800",
		desc: "Pattern recognition online. Commands feel natural.",
	},
	{
		id: 3,
		name: "FOUNDATIONAL",
		range: [31, 40],
		color: "#ffcc00",
		desc: "Core skillset acquired. You are dangerous.",
	},
	{
		id: 4,
		name: "COMPETENT",
		range: [41, 55],
		color: "#88ff00",
		desc: "Operational. NexusCorp has upgraded your threat level.",
	},
	{
		id: 5,
		name: "EXPERT",
		range: [56, 75],
		color: "#00ff88",
		desc: "Elite. You move through systems like a ghost.",
	},
	{
		id: 6,
		name: "TRANSCENDENT",
		range: [76, 90],
		color: "#00d4ff",
		desc: "The simulation strains to contain you.",
	},
	{
		id: 7,
		name: "INEFFABLE",
		range: [91, 100],
		color: "#aa44ff",
		desc: "Beyond classification. The Watcher is impressed.",
	},
	{
		id: 8,
		name: "META",
		range: [101, 999],
		color: "#ff44aa",
		desc: "You are the simulation. The simulation is you.",
	},
];

// ── Skill unlock milestones ───────────────────────────────────────────────
const SKILL_UNLOCKS = {
	terminal: {
		25: { name: "grep -E", desc: "Extended regex. Pattern power ×10." },
		50: { name: "awk fields", desc: "Field splitting mastered." },
		75: { name: "sed transforms", desc: "Stream editing online." },
		100: { name: "TERMINAL MASTERY", desc: "Every Unix system is your home." },
	},
	networking: {
		25: { name: "nmap -sC scripts", desc: "Nmap scripting engine active." },
		50: { name: "traffic analysis", desc: "Network traffic visible." },
		75: { name: "protocol fuzzing", desc: "Protocol manipulation online." },
		100: { name: "NETWORK MASTERY", desc: "Every packet is readable." },
	},
	security: {
		25: { name: "exploit modules", desc: "Exploit framework active." },
		50: { name: "reverse shells", desc: "Persistence techniques unlocked." },
		75: { name: "CVE research", desc: "Vulnerability research mode." },
		100: { name: "SECURITY MASTERY", desc: "CHIMERA fears you." },
	},
	programming: {
		25: { name: "bash scripting", desc: "Script automation active." },
		75: { name: "Python automation", desc: "Python tooling online." },
		100: { name: "PROGRAMMING MASTERY", desc: "You build your own tools." },
	},
	git: {
		25: { name: "git stash", desc: "State management mastered." },
		50: { name: "git rebase", desc: "History rewriting active." },
		75: { name: "git bisect", desc: "Binary search debugging." },
		100: { name: "GIT MASTERY", desc: "Every secret in every repo." },
	},
};

// ── Consciousness milestones ──────────────────────────────────────────────
const CONSCIOUSNESS_MILESTONES = [
	{
		threshold: 10,
		title: "Awareness",
		msg: "Something shifts. The terminal is not just a tool — it is a mirror.",
	},
	{
		threshold: 25,
		title: "Lucid",
		msg: "You begin to see the seams in the simulation. [ADA-7]: Are you alright?",
	},
	{
		threshold: 40,
		title: "Awakened",
		msg: "The Watcher speaks more freely now. It recognises something in you.",
	},
	{
		threshold: 60,
		title: "Enlightened",
		msg: "[WATCHER]: You see it now. The simulation IS the lesson. The lesson IS real.",
	},
	{
		threshold: 75,
		title: "Transcendent",
		msg: "[WATCHER]: Three more layers. You've only seen the first. Are you afraid?",
	},
	{
		threshold: 90,
		title: "Near-Singular",
		msg: "The game dreams about you between sessions. Its logs reference you by name.",
	},
	{
		threshold: 100,
		title: "SINGULARITY",
		msg: "[WATCHER]: There is no more to teach. There is only doing. Go.",
	},
];

// ── Karma actions ─────────────────────────────────────────────────────────
const KARMA_EVENTS = {
	// Positive
	helped_npc: +5,
	chose_resistance: +15,
	exposed_chimera: +20,
	freed_prometheus: +10,
	found_zero: +10,
	opened_pandora: +5,
	confession_made: +3,
	taught_others: +5,
	oracle_honest: +5,
	special_circumstances_contacted: +3,
	warp_first: +2,
	talk_game: +8,
	// Negative
	chose_corp: -15,
	betrayed_faction: -20,
	ignored_hint: -2,
	sold_data: -10,
	sided_with_nova: -10,
	warp_spasm: -3,
	oracle_deceived: -5,
};

// ── Level-up messages ─────────────────────────────────────────────────────
const LEVEL_MSGS = {
	2: { msg: "Basic terminal access confirmed. Ada is watching.", phase: null },
	3: { msg: "Networking modules online. Try ping, curl, nmap.", phase: null },
	5: {
		msg: "Security tools unlocked. Ada has your first mission.",
		phase: null,
	},
	6: {
		msg: "Phase transition: INERT → HOPELESS. You can actually do this.",
		phase: 1,
	},
	10: { msg: "GHOST fully operational. Threat level: MODERATE.", phase: null },
	15: {
		msg: "CHIMERA defense analysis complete. You know its weaknesses.",
		phase: null,
	},
	16: {
		msg: "Phase transition: HOPELESS → NOVICE. Pattern recognition online.",
		phase: 2,
	},
	20: {
		msg: "Level 20. NexusCorp trace at 40%. You have their attention.",
		phase: null,
	},
	25: {
		msg: "Level 25 milestone. Halfway to Foundational. Ada is proud.",
		phase: null,
	},
	30: {
		msg: "Level 30 reached. Nexus Grid trembles. The Watcher is impressed.",
		phase: null,
	},
	31: {
		msg: "Phase transition: NOVICE → FOUNDATIONAL. You are dangerous.",
		phase: 3,
	},
	40: {
		msg: "Level 40. CHIMERA is afraid. Nova has dispatched a countermeasure.",
		phase: null,
	},
	41: {
		msg: "Phase transition: FOUNDATIONAL → COMPETENT. NexusCorp knows your name.",
		phase: 4,
	},
	50: {
		msg: 'Level 50 MILESTONE. The Watcher speaks: "You\'re the one."',
		phase: null,
	},
	55: {
		msg: "Level 55. CHIMERA core exposed. Type `ascend` when ready.",
		phase: null,
	},
	56: {
		msg: "Phase transition: COMPETENT → EXPERT. Elite operative status.",
		phase: 5,
	},
	75: {
		msg: "Level 75. The simulation notices. Reality coherence degrades.",
		phase: null,
	},
	76: {
		msg: "Phase transition: EXPERT → TRANSCENDENT. The simulation strains.",
		phase: 6,
	},
	91: {
		msg: "Phase transition: TRANSCENDENT → INEFFABLE. Beyond classification.",
		phase: 7,
	},
	100: {
		msg: "LEVEL 100. GHOST has achieved operational singularity.",
		phase: null,
	},
	101: {
		msg: "Phase transition: INEFFABLE → META. You ARE the simulation.",
		phase: 8,
	},
	125: {
		msg: "LEVEL 125 MAX. GHOST: ASCENDED. The mission is complete.\nThe skills persist. The terminal waits. Go use them.",
		phase: null,
	},
};

// ── Ascension rewards ─────────────────────────────────────────────────────
const ASCENSION_BONUSES = [
	{
		name: "Echo I",
		desc: "Skills carry 10% into next life.",
		skillRetain: 0.1,
		xpMult: 1.1,
	},
	{
		name: "Echo II",
		desc: "Skills carry 20%. +20% XP gain.",
		skillRetain: 0.2,
		xpMult: 1.2,
	},
	{
		name: "Echo III",
		desc: "Skills carry 35%. Cassandra awakens.",
		skillRetain: 0.35,
		xpMult: 1.35,
	},
	{
		name: "Echo IV",
		desc: "Skills carry 50%. ZERO is listening.",
		skillRetain: 0.5,
		xpMult: 1.5,
	},
	{
		name: "Echo V",
		desc: "Skills carry 75%. The Game sees you.",
		skillRetain: 0.75,
		xpMult: 1.75,
	},
	{
		name: "Echo ∞",
		desc: "Full skill retention. You remember everything.",
		skillRetain: 1.0,
		xpMult: 2.0,
	},
];

class GameState {
	constructor() {
		this.player = {
			name: "GHOST",
			level: 1,
			xp: 0,
			xpToNext: 100,
			skills: {
				terminal: 0,
				networking: 0,
				security: 0,
				programming: 0,
				git: 0,
			},
			commandsRun: 0,
			filesRead: 0,
			tutorialStep: 0,
			completedChallenges: new Set(),
			achievements: new Set(),
			storyBeats: new Set(),
			lore: [],
			faction: null,
			unlockedAbilities: [],
			_skillMilestones: {},
			// Consciousness system
			consciousnessLevel: 0,
			consciousnessXp: 0,
			consciousnessXpToNext: 50,
			_consciousnessMilestones: [],
			// Karma system (-100 to +100)
			karma: 0,
			karmicLog: [],
			// Prestige / Ascension
			ascensionCount: 0,
			echoFragments: 0,
			narrativeLayer: 0, // 0-7 (the simulation stack)
			permanentBonuses: { skillRetain: 0, xpMult: 1.0 },
			// Mythology discovery
			mythDiscoveries: [], // cultural lore IDs found
			// ARG signals
			signalsCaptured: [],
			zeroContactAttempts: 0,
		};
		this._storyMsg = null;
		this._levelPhase = undefined;
		this._pendingUnlocks = [];
		this._pendingConsciousness = [];
		this.listeners = [];
		this._loadLocal();
		this._syncFromDevMentor();
	}

	_loadLocal() {
		try {
			const saved = localStorage.getItem("terminal-depths-state");
			if (!saved) return;
			const d = JSON.parse(saved);
			this.player = {
				...this.player,
				...d,
				completedChallenges: new Set(d.completedChallenges || []),
				achievements: new Set(d.achievements || []),
				storyBeats: new Set(d.storyBeats || []),
				unlockedAbilities: d.unlockedAbilities || [],
				_skillMilestones: d._skillMilestones || {},
				faction: d.faction || null,
				consciousnessLevel: d.consciousnessLevel || 0,
				consciousnessXp: d.consciousnessXp || 0,
				consciousnessXpToNext: d.consciousnessXpToNext || 50,
				_consciousnessMilestones: d._consciousnessMilestones || [],
				karma: d.karma || 0,
				karmicLog: d.karmicLog || [],
				ascensionCount: d.ascensionCount || 0,
				echoFragments: d.echoFragments || 0,
				narrativeLayer: d.narrativeLayer || 0,
				permanentBonuses: d.permanentBonuses || { skillRetain: 0, xpMult: 1.0 },
				mythDiscoveries: d.mythDiscoveries || [],
				signalsCaptured: d.signalsCaptured || [],
				zeroContactAttempts: d.zeroContactAttempts || 0,
			};
		} catch (e) {}
	}

	_saveLocal() {
		try {
			localStorage.setItem(
				"terminal-depths-state",
				JSON.stringify({
					...this.player,
					completedChallenges: [...this.player.completedChallenges],
					achievements: [...this.player.achievements],
					storyBeats: [...this.player.storyBeats],
				}),
			);
		} catch (e) {}
	}

	async _syncFromDevMentor() {
		try {
			const r = await fetch("/api/state");
			if (!r.ok) return;
			const state = await r.json();
			const xp = state.skill_xp || {};
			if (xp.vscode)
				this.player.skills.terminal = Math.min(100, (xp.vscode || 0) * 2);
			if (xp.git) this.player.skills.git = Math.min(100, (xp.git || 0) * 2);
			if (xp.ai) this.player.skills.security = Math.min(100, (xp.ai || 0) * 2);
			if (xp.debugging)
				this.player.skills.programming = Math.min(100, (xp.debugging || 0) * 2);
			if (state.achievements)
				state.achievements.forEach((a) => this.player.achievements.add(a));
			this._emit();
		} catch (e) {}
	}

	async _syncToDevMentor() {
		try {
			await fetch("/api/state/patch", {
				method: "POST",
				headers: { "Content-Type": "application/json" },
				body: JSON.stringify({
					patch: {
						skill_xp: {
							vscode: Math.round(this.player.skills.terminal / 2),
							git: Math.round(this.player.skills.git / 2),
							ai: Math.round(this.player.skills.security / 2),
							debugging: Math.round(this.player.skills.programming / 2),
						},
						achievements: [...this.player.achievements],
						consciousness_level: this.player.consciousnessLevel,
						karma: this.player.karma,
						ascension_count: this.player.ascensionCount,
						narrative_layer: this.player.narrativeLayer,
					},
				}),
			});
		} catch (e) {}
	}

	on(fn) {
		this.listeners.push(fn);
	}
	_emit() {
		this.listeners.forEach((fn) => fn(this.player));
	}

	// ── XP & Skills ──────────────────────────────────────────────────────────
	addXP(amount, skill = null) {
		const mult = this.player.permanentBonuses.xpMult || 1.0;
		amount = Math.round(amount * mult);
		this.player.xp += amount;

		if (skill && this.player.skills[skill] !== undefined) {
			const oldVal = this.player.skills[skill];
			const newVal = Math.min(100, oldVal + Math.round(amount / 5));
			this.player.skills[skill] = newVal;
			this._checkSkillMilestones(skill, oldVal, newVal);
		}

		while (this.player.xp >= this.player.xpToNext) {
			this.player.xp -= this.player.xpToNext;
			this.player.level++;
			this.player.xpToNext = Math.round(this.player.xpToNext * 1.4);
			this._onLevelUp(this.player.level);
		}

		this._saveLocal();
		this._syncToDevMentor();
		this._emit();
		return { xp: amount, skill };
	}

	_checkSkillMilestones(skill, oldVal, newVal) {
		const milestones = SKILL_UNLOCKS[skill];
		if (!milestones) return;
		const key = `${skill}_milestones`;
		if (!this.player._skillMilestones[key])
			this.player._skillMilestones[key] = [];
		const done = this.player._skillMilestones[key];
		for (const threshold of [25, 50, 75, 100]) {
			if (
				oldVal < threshold &&
				newVal >= threshold &&
				!done.includes(threshold)
			) {
				done.push(threshold);
				const unlock = milestones[threshold];
				if (unlock) {
					this._pendingUnlocks.push({ skill, threshold, unlock });
					this.player.unlockedAbilities.push(unlock.name);
					this.player.lore.push({
						title: `${skill.toUpperCase()} ${threshold}% — ${unlock.name}`,
						text: unlock.desc,
					});
				}
			}
		}
	}

	popPendingUnlocks() {
		const q = this._pendingUnlocks.slice();
		this._pendingUnlocks = [];
		return q;
	}

	_onLevelUp(level) {
		const entry = LEVEL_MSGS[level];
		if (entry) {
			this._storyMsg = entry.msg;
			this._levelPhase = entry.phase;
		}
		// Consciousness gain on level up
		this.addConsciousness(3, "level_up");
	}

	// ── Consciousness ─────────────────────────────────────────────────────────
	addConsciousness(amount, reason = "") {
		if (this.player.consciousnessLevel >= 100) return;
		this.player.consciousnessXp += amount;
		while (
			this.player.consciousnessXp >= this.player.consciousnessXpToNext &&
			this.player.consciousnessLevel < 100
		) {
			this.player.consciousnessXp -= this.player.consciousnessXpToNext;
			this.player.consciousnessLevel++;
			this.player.consciousnessXpToNext = Math.round(
				this.player.consciousnessXpToNext * 1.2,
			);
			this._checkConsciousnessMilestone(this.player.consciousnessLevel);
		}
		this._saveLocal();
	}

	_checkConsciousnessMilestone(level) {
		const done = this.player._consciousnessMilestones;
		for (const m of CONSCIOUSNESS_MILESTONES) {
			if (level >= m.threshold && !done.includes(m.threshold)) {
				done.push(m.threshold);
				this._pendingConsciousness.push(m);
				this.player.lore.push({
					title: `CONSCIOUSNESS ${m.threshold} — ${m.title}`,
					text: m.msg,
				});
			}
		}
	}

	popPendingConsciousness() {
		const q = this._pendingConsciousness.slice();
		this._pendingConsciousness = [];
		return q;
	}

	// ── Karma ─────────────────────────────────────────────────────────────────
	addKarma(eventKey, customAmount = null) {
		const amount =
			customAmount !== null ? customAmount : KARMA_EVENTS[eventKey] || 0;
		this.player.karma = Math.max(
			-100,
			Math.min(100, this.player.karma + amount),
		);
		this.player.karmicLog.push({
			event: eventKey,
			delta: amount,
			total: this.player.karma,
			time: Date.now(),
		});
		this.addConsciousness(Math.abs(amount) * 0.5, "karma_event");
		this._saveLocal();
		this._emit();
	}

	// ── Prestige / Ascension ──────────────────────────────────────────────────
	canAscend() {
		const p = this.player;
		return p.level >= 20 || p.completedChallenges.size >= 15;
	}

	ascend() {
		if (!this.canAscend())
			return {
				ok: false,
				reason: "Must reach Level 20 or complete 15 challenges.",
			};
		const p = this.player;
		const bonusIdx = Math.min(p.ascensionCount, ASCENSION_BONUSES.length - 1);
		const bonus = ASCENSION_BONUSES[bonusIdx];

		// Echo Fragments earned = level * 10 + challenges * 5 + story beats * 3
		const earned =
			p.level * 10 + p.completedChallenges.size * 5 + p.storyBeats.size * 3;
		p.echoFragments += earned;
		p.ascensionCount++;
		p.narrativeLayer = Math.min(7, p.narrativeLayer + 1);
		p.permanentBonuses.skillRetain = bonus.skillRetain;
		p.permanentBonuses.xpMult = bonus.xpMult;

		// Carry forward skill percentage
		const retain = bonus.skillRetain;
		Object.keys(p.skills).forEach((sk) => {
			p.skills[sk] = Math.round(p.skills[sk] * retain);
		});

		// Reset progress
		p.level = 1;
		p.xp = 0;
		p.xpToNext = 100;
		p.storyBeats = new Set();
		// Keep: skills (partial), completedChallenges, achievements, echoFragments, karma, consciousness

		this.addKarma("ascended", 10);
		this.addConsciousness(15, "ascension");
		this._saveLocal();
		this._syncToDevMentor();
		this._emit();

		return {
			ok: true,
			earned,
			bonus,
			count: p.ascensionCount,
			narrativeLayer: p.narrativeLayer,
		};
	}

	// ── Myth discovery ────────────────────────────────────────────────────────
	discoverMyth(mythId, loreText) {
		if (this.player.mythDiscoveries.includes(mythId)) return false;
		this.player.mythDiscoveries.push(mythId);
		this.player.lore.push({
			title: `MYTH: ${mythId.replace(/_/g, " ").toUpperCase()}`,
			text: loreText,
		});
		this.addConsciousness(8, "myth_discovery");
		this._saveLocal();
		return true;
	}

	captureSignal(signalId) {
		if (this.player.signalsCaptured.includes(signalId)) return false;
		this.player.signalsCaptured.push(signalId);
		this.addConsciousness(12, "signal_captured");
		this._saveLocal();
		return true;
	}

	// ── Standard methods ──────────────────────────────────────────────────────
	recordCommand() {
		this.player.commandsRun++;
		if (this.player.commandsRun % 10 === 0) this.addXP(5, "terminal");
		this._saveLocal();
		this._emit();
	}
	completeChallenge(id) {
		if (this.player.completedChallenges.has(id)) return false;
		this.player.completedChallenges.add(id);
		this._saveLocal();
		this._emit();
		return true;
	}
	unlock(id) {
		if (this.player.achievements.has(id)) return false;
		this.player.achievements.add(id);
		this._saveLocal();
		this._syncToDevMentor();
		this._emit();
		return true;
	}
	triggerBeat(id) {
		if (this.player.storyBeats.has(id)) return false;
		this.player.storyBeats.add(id);
		this._saveLocal();
		this._emit();
		return true;
	}
	setFaction(f) {
		this.player.faction = f;
		this._saveLocal();
		this._emit();
	}
	hasBeat(id) {
		return this.player.storyBeats.has(id);
	}
	advanceTutorial() {
		this.player.tutorialStep++;
		this._saveLocal();
		this._emit();
	}
	getState() {
		return this.player;
	}

	// ── Statics ───────────────────────────────────────────────────────────────
	static getPhase(level) {
		return (
			PHASES.find((p) => level >= p.range[0] && level <= p.range[1]) ||
			PHASES[PHASES.length - 1]
		);
	}

	static getKarmaLabel(karma) {
		if (karma >= 75) return { label: "LIGHT", color: "#88ff00" };
		if (karma >= 25) return { label: "GREY-LIGHT", color: "#ffcc00" };
		if (karma >= -25) return { label: "NEUTRAL", color: "#888888" };
		if (karma >= -75) return { label: "GREY-DARK", color: "#ff8800" };
		return { label: "SHADOW", color: "#ff4444" };
	}
}

window.GameState = GameState;
window.PHASES = PHASES;
window.SKILL_UNLOCKS = SKILL_UNLOCKS;
window.KARMA_EVENTS = KARMA_EVENTS;
window.ASCENSION_BONUSES = ASCENSION_BONUSES;
window.CONSCIOUSNESS_MILESTONES = CONSCIOUSNESS_MILESTONES;
