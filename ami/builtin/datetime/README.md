# Datetime AMI Headspace
The builtin library `datetime` has a special place in my heart. I only wish to do it honor.

## Capabilities

### Reminders
- *<`hotword`>: Please set a reminder every 3 months to change the HVAC filter.*
- *<`hotword`>: Please set a reminder to take the trash out every sunday at 7pm.*

#### Usage
Reminders are designed for reapeating event, but engineered to be use as one offs to.
The key idea is to schedule a reminder, but not schedule the next until the `Reminder` is signed off.
- *<`hotword`>: Go ahead and mark the HVAC reminder and trash reminder as done.*
The prompt for this is designed to figure out whether or not its repeating on it's own.

#### GUI
Reminders should act as notification do as the pull down menu on phone, just no bloat.
I **hope** to have some GUI hook up to the notification or app interface on the GUI.
This GUI `Reminder` notifications are going to describe the interface into the GUI as this module defines the plugin interface.

### Timers
- *<`hotword`>: Please set a timer for an hour and a half.*
- *<`hotword`>: Please set a stove timer for 8 minutes.*

#### Usage
Same as other voice assistiants, set a timer for something.

## Notes
- `Datetime` is my starter for the new triple process and PyQt6 AMI. See the `__init__.py` file to see the current interface.
- To reach any of the Plugin elements, GUI or Headspace or Blueprint, you need to import the entire plug, its a must.
- Fun! Fun! Fun!
