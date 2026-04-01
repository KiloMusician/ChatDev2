// Declarative "wiring" of signals -> actions with boolean/temporal logic.
{
  rules: [
    { when: {metric: "imports.broken", op: ">", value: 0}, do: {task:"import.fix", priority:1}},
    { when: {metric: "cpu.softlock",   op: "==", value: true}, do: {task:"softlock.recover", priority:0}},
    { when: {metric: "tokens.left",    op: "<", value: 5}, do: {task:"cascade.plan", data:{mode:"offline-heavy"}, priority:1}},
    { when: {event:"user.vague_prompt"}, do: {task:"intermediary.disambiguate", priority:3}},
  ],
}