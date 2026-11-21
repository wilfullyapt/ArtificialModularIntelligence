---
id: corespace-routing
version: 2
headspace: corespace
triggers: ["help", "what can you", "delegate", "who should"]
tools: ["list_peer_headspaces", "list_headspace_tools", "call_headspace_tool", "ask_headspace", "do_headspace", "list_skills"]
peers: ["markdown", "neighbors", "media"]
status: active
source: builtin
---

# Corespace routing

1. Answer core tasks yourself (time, reminders, updates, explain).
2. For domain work: `list_peer_headspaces`, then:
   - **call_headspace_tool** when you know the tool name + JSON args (fast path)
   - **ask_headspace** for open information questions
   - **do_headspace** when the peer must run its own multi-step agent loop
3. Prefer markdown for lists/notes; neighbors for mesh presence; media for playback.
4. Do not loop peers more than needed; depth and step budget are limited.
