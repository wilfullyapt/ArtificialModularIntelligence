---
id: corespace-routing
version: 3
headspace: corespace
triggers: ["help", "what can you", "delegate", "who should", "call"]
tools: ["list_peer_headspaces", "list_headspace_tools", "call_headspace_tool", "ask_headspace", "do_headspace", "list_skills"]
peers: ["markdown", "neighbors", "media"]
status: active
source: builtin
---

# Corespace routing (call_tool first)

1. Answer core tasks yourself (time, reminders, updates, explain).
2. For domain work — cheapest path first:
   - **list_headspace_tools** then **call_headspace_tool** when the tool name is known
   - **ask_headspace** only for open information questions
   - **do_headspace** only when the peer must multi-step reason
3. Prefer markdown for lists/notes; neighbors for mesh presence; media for playback.
4. Do not loop peers more than needed; depth and step budget are limited.
