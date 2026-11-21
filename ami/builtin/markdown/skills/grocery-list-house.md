---
id: grocery-list-house
version: 1
headspace: markdown
triggers: ["grocery", "groceries", "shopping list", "shopping"]
tools: ["add_to_list", "list_lists", "remove_from_list"]
peers: []
status: active
source: builtin
---

# Grocery / shopping lists

1. Prefer list name **Groceries** (create via list tools if missing).
2. Add one item per `add_to_list` call unless the user batches clearly.
3. After mutations, GUI reload is expected.
4. If unsure of list names, call `list_lists` first.
