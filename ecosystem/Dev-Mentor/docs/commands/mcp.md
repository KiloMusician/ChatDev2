# MCP(1) — Terminal Depths Man Page

## NAME
  mcp — Model Context Protocol server interface

## SYNOPSIS
  mcp [status|tools|call <tool> [args]]

## DESCRIPTION
Interface to the Model Context Protocol JSON-RPC 2.0 server. MCP provides
28 tools for file system, memory, game commands, LLM generation, game state,
and system status. Used by AI agents and LLMs to interact with Terminal Depths.

## SUBCOMMANDS
  status        MCP server health and active connections
  tools         List all 28 available MCP tools
  call <tool>   Call a specific MCP tool

## EXAMPLES
  mcp status
  mcp tools
  mcp call game.command '{"command":"status"}'

## SEE ALSO
  swarm, serena, agents, api

---
*Generated 2026-03-23*