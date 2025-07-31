**This file has been put here as instructions for the agent**

#### The reminders file
The reminders file should be in JSON.

```json
{
    "upcoming":
        {
            "YYYYMMDD-HHMMSS":
                {
                    "name": "Name of the reminder",
                    "reocurring": # false or str | "33m"=33 minutes, "1y" =1 year, "54d" =54 days. use y,m,d,h ONLY
                }

        },
    "completed":
        {
        },
}
```

We want the name of the upcoming reminder to in a "Year Month Day - Hour Monute Second" format. Indexing can happen quickly.
If the reminder is reoccuring, we want to capture the interval for that in a "int"+"unit" format. Year or Month or Day or Hour formats ONLY.
Any reoccurring reminders with minutes or seconds should just be dropped.
We should have a way to understand the json coming out of the file.

##### Parsing Natural language
Example:
"Set a reminder to change my oil tomorrow" -> This reminder to be appended to the gui at midnight
"Set a reminder to clean the pool next month" -> This reminder should trigger on the first day of the next month

Basically this reminder tool is built specific to days out of the year, not specifically targing reminders intraday

