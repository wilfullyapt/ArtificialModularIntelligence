# Datetime AMI Headspace
The builtin library `datetime` has a special place in my heart. I only wish to do it honor.

## Capabilities

### Reminders
- *<`hotword`>: Please set a reminder every 3 months to change the HVAC filter.*
- *<`hotword`>: Please set a reminder to take the trash out every sunday at 7pm.*
- *<`hotword`>: Perform an update.*

#### Usage
Reminders are designed for reapeating event, but engineered to be use as one offs to.
The key idea is to schedule a reminder, but not schedule the next until the `Reminder` is signed off.
- *<`hotword`>: Go ahead and mark the HVAC reminder and trash reminder as done.*
The prompt for this is designed to figure out whether or not its repeating on it's own and schedule accordingly.

#### GUI
Reminders and Notification should appear here. There is a vertical access that shows reminders and notification.
There is a color coded difference for Reminder vs Notification

### Timers
- *<`hotword`>: Please set a timer for an hour and a half.*
- *<`hotword`>: Please set a stove timer for 8 minutes.*

#### Usage
Same as other voice assistiants. Set a reminder or a time.
This Headpsace also exposes core functionality, including a *Self Updating* function.
