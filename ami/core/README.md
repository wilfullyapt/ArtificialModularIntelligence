# AMI Core Components


## Config


## Logger



## Conversation

- The `Conversation` object should follow a convention for it to be saved in JSON format.


### Example JSON Conversation
```json
[
    {
        "role": "Human",
        "message": "Please set a reminder every sunday at 7pm to set out the trash",
        "agent": {
            [
                "Thought: I should use the 'set_reminder' action to set up this reminder."
                "action:
                    {
                        "action": "set_reminder",
                        "args":
                            {
                                arg1:
                                arg2:
                            }
                    }",
                "observation: The reminder has been setup",
                "thought: I know what I need to do next.",
                "observation: TASK FINISHED"
            ]
        }
    },
    {
        "role": "assistant",
        "message": "The reminder has been set up."
    }
]
```
