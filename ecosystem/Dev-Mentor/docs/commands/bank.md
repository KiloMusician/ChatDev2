# BANK(1) — Terminal Depths Man Page

## NAME
  bank — Colony Bank — manage credits and view financial ledger

## SYNOPSIS
  bank [balance|leaderboard|history|transfer <agent> <amount>|deposit <amount>|agents]

## DESCRIPTION
The Colony Bank tracks all credit flows in the simulation. Credits fund
augments, darknet purchases, and crafting. Agents accumulate credits through
missions, challenges, and trade.

## SUBCOMMANDS
  balance               Show your current credit balance
  leaderboard           Top agents ranked by net worth
  history               Recent transaction ledger
  transfer <agent> <n>  Move credits to another agent
  deposit <n>           Deposit credits from your wallet
  agents                List all agents and their balances

## EXAMPLES
  bank balance
  bank history
  bank transfer ada 500
  bank leaderboard

## SEE ALSO
  darknet, bazaar, credits, craft

---
*Generated 2026-03-23*