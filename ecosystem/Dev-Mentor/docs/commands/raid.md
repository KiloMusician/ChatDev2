# raid

Multi-agent coordination missions.

## Usage
`raid [plan|execute|status|abort]`

## Description
Coordinate a team of high-trust agents to infiltrate NexusCorp HQ.

## Requirements
- Trust >= 80 with at least 3 agents.

## Phases
1. `recon` (scan)
2. `breach` (exploit)
3. `extract` (cat)
4. `exfil` (exfil)
5. `evade` (clear)

## Commands
- `raid plan`: Shows briefing for the `chimera-control` target.
- `raid execute`: Begins the multi-step quest if requirements are met.
- `raid status`: Current phase and requirements.
- `raid abort`: Ends the current mission.

## Rewards
- 1000 XP (on completion)
- Achievement: `RAID_LEADER`
- Story Beat: `raid_hq_complete`
