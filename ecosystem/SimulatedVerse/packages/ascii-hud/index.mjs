import blessed from "blessed";
import { spawn } from "node:child_process";

const screen = blessed.screen({ smartCSR: true, title: "ΦΣΞ ASCII HUD" });

const log = blessed.log({
  parent: screen, top: 0, left: 0, width: "70%", height: "70%",
  label: "Logs", border: "line", keys: true, mouse: true, scrollOnInput: true
});
const stats = blessed.box({
  parent: screen, top: 0, left: "70%", width: "30%", height: "70%",
  label: "Stats", border: "line", content: "tokens: 0\nmode: zero-token\nmobile: auto"
});
const bar = blessed.box({
  parent: screen, bottom: 0, left: 0, width: "100%", height: "30%",
  label: "Actions", border: "line",
  content: "Keys: [R]un Cascade  [D]octor  [T]ests  [L]int  [Q]uit"
});

function run(cmd, args=[]) {
  const p = spawn(cmd, args, { stdio: ["ignore", "pipe", "pipe"] });
  p.stdout.on("data", d => log.add(d.toString()));
  p.stderr.on("data", d => log.add("{red-fg}" + d.toString() + "{/red-fg}"));
  p.on("close", c => log.add(`{green-fg}done(${c}){/green-fg}`));
}

screen.key(["q","C-c"], () => process.exit(0));
screen.key("r", () => run("bash",["scripts/rif","cascade"]));
screen.key("d", () => run("bash",["scripts/rif","doctor"]));
screen.key("t", () => run("bash",["scripts/rif","test"]));
screen.key("l", () => run("bash",["scripts/rif","lint"]));

screen.render();
log.add("HUD ready. Press R to Cascade.");