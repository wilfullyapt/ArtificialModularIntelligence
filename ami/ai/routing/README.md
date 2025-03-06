
```python
scripted = {
    "what can you do": wcyd,
    "lesson mode": lesson_ai
}

if __name__ == 'main':
    user_prompt = get_user_input()
    if user_prompt in scripted.keys():
        scripted[user_prompt](context)


routes = {
    "tool"
    "conversation"
}
```

```graph
INPUT PROMPT
  |
  v
Scripted command? -----> [Yes] --> Scripted Response --> END
        # "What can you do?"
  |                  |
  |                 [No]
  |                  |
  v                  v
Intent: Config or Setter? --> [Yes] --> Handle settings operations --> END
  |                  |
  |                 [No]
  |                  |
  v                  v
Is this tool use or conversation? --> [tool] --> Use tool and timout convo --> END
  |                  |
  |            [conversation]
  |                  |
  v                  v
tools = [deepresearch, think, picture]
thoughtful response, continue conversation
  |                  |
  |         [personality filter?]
  |                  |
  v                  v
Decide how the convo goes into memory ---------> END

```
