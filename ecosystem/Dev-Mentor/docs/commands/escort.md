# escort

Protect a vulnerable agent through hostile territory.

## Usage
`escort [start <agent>|status|move <node>|end]`

## Description
Guide a vulnerable agent safely to a resistance-cell node.
While moving, agents are at risk of interception, requiring quick defensive actions.

## Requirements
- Agent threat_level > 70 or `boss_nova_defeated`.

## Process
- `escort start <agent>`: Select `ada` or `raven` (lowest trust prioritized).
- `escort move <node>`: Move through the network.
- `escort status`: Show current location and move count.
- `escort end`: Abort the escort mission.

## Rewards
- 300 XP (on success)
- Story Beat: `escort_complete`
