#!/usr/bin/env tsx
/**
 * Fetch (or read) a Godot docs export you've dropped into /docs/godot/
 * and build a tiny JSONL index for retrieval-augmented generation.
 * Agents can load this into your existing retrieval tool (llamaindex/langchain).
 */
import fs from "node:fs";
import path from "node:path";

const SRC = "docs/godot";
const OUT = "docs/godot.index.jsonl";

function walk(dir: string, acc: string[]=[]): string[] {
  for (const f of fs.readdirSync(dir)) {
    const p = path.join(dir, f);
    const st = fs.statSync(p);
    if (st.isDirectory()) walk(p, acc);
    else if (p.endsWith(".md") || p.endsWith(".rst") || p.endsWith(".txt")) acc.push(p);
  }
  return acc;
}

fs.mkdirSync("docs", { recursive: true });

// Create sample docs if none exist
if (!fs.existsSync(SRC)) {
  fs.mkdirSync(SRC, { recursive: true });
  
  // Create basic Godot reference docs
  const sampleDocs = [
    {
      file: "getting-started.md",
      content: `# Godot Getting Started
      
Godot is a feature-packed, cross-platform game engine to create 2D and 3D games from a unified interface.

## Basic Concepts
- Scene: Collection of nodes that form the basic building block
- Node: Basic element in the scene tree
- Script: Code that defines behavior attached to nodes

## Common Nodes
- Node2D: Base for all 2D nodes
- Control: Base for all UI nodes
- RigidBody2D: Physics-enabled body
- KinematicBody2D: Character movement body
- Area2D: Detection area
`
    },
    {
      file: "scripting.md", 
      content: `# GDScript Scripting

GDScript is Godot's built-in scripting language.

## Basic Syntax
\`\`\`gdscript
extends Node

func _ready():
    print("Hello World")

func _process(delta):
    # Called every frame
    pass
\`\`\`

## Variables
\`\`\`gdscript
var health = 100
var player_name = "Player"
var is_alive = true
\`\`\`

## Functions
\`\`\`gdscript
func take_damage(amount):
    health -= amount
    if health <= 0:
        die()

func die():
    queue_free()
\`\`\`
`
    },
    {
      file: "signals.md",
      content: `# Signals

Signals are Godot's observer pattern implementation.

## Defining Signals
\`\`\`gdscript
signal health_changed(new_health)
signal player_died
\`\`\`

## Emitting Signals
\`\`\`gdscript
func take_damage(amount):
    health -= amount
    emit_signal("health_changed", health)
    if health <= 0:
        emit_signal("player_died")
\`\`\`

## Connecting Signals
\`\`\`gdscript
func _ready():
    player.connect("health_changed", self, "_on_health_changed")
    player.connect("player_died", self, "_on_player_died")
\`\`\`
`
    }
  ];
  
  sampleDocs.forEach(doc => {
    fs.writeFileSync(path.join(SRC, doc.file), doc.content);
  });
  
  console.log(`[godot-docs-index] Created ${sampleDocs.length} sample docs in ${SRC}`);
}

const files = fs.existsSync(SRC) ? walk(SRC) : [];
const w = fs.createWriteStream(OUT);
for (const f of files) {
  const txt = fs.readFileSync(f, "utf-8");
  w.write(JSON.stringify({ 
    id: f, 
    text: txt.slice(0, 120000),
    filename: path.basename(f),
    category: path.dirname(f).split(path.sep).pop()
  }) + "\n");
}
w.end();
console.log(`[godot-docs-index] Wrote ${files.length} docs to ${OUT}`);