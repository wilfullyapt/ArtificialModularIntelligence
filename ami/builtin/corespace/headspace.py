from datetime import datetime, timedelta
import re
from typing import Optional, Dict, Any

from ami.headspace import Headspace
from ami.headspace import ami_tool
from .tool import ReminderManager, UpdateManager, BinaryRunnerForAMI
from .settings import CorespaceSettings

class CorespaceHeadspace(Headspace):
    """Core AMI functionality including reminders, timers, and system updates"""

    settings_class = CorespaceSettings

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.reminder_manager = ReminderManager(self.filespace, self.settings.reminder_files)
        self.update_manager = UpdateManager()

    def _parse_time_specification(self, time_spec: str) -> Optional[datetime]:
        """Parse natural language time specifications"""
        time_spec = time_spec.lower().strip()
        now = datetime.now()

        # Handle "in X minutes/hours/days"
        in_pattern = r'in (\d+) (minute|minutes|hour|hours|day|days|week|weeks)'
        match = re.search(in_pattern, time_spec)
        if match:
            amount, unit = match.groups()
            amount = int(amount)
            if 'minute' in unit:
                return now + timedelta(minutes=amount)
            elif 'hour' in unit:
                return now + timedelta(hours=amount)
            elif 'day' in unit:
                return now + timedelta(days=amount)
            elif 'week' in unit:
                return now + timedelta(weeks=amount)

        # Handle "tomorrow"
        if 'tomorrow' in time_spec:
            base_date = now + timedelta(days=1)
            # Try to extract time
            time_match = re.search(r'(\d{1,2})(?::(\d{2}))?\s*(am|pm)', time_spec)
            if time_match:
                hour, minute, ampm = time_match.groups()
                hour = int(hour)
                minute = int(minute) if minute else 0
                if ampm == 'pm' and hour != 12:
                    hour += 12
                elif ampm == 'am' and hour == 12:
                    hour = 0
                return base_date.replace(hour=hour, minute=minute, second=0, microsecond=0)
            else:
                return base_date.replace(hour=9, minute=0, second=0, microsecond=0)  # Default 9 AM

        # Handle "next friday", "next monday", etc.
        weekdays = {
            'monday': 0, 'tuesday': 1, 'wednesday': 2, 'thursday': 3,
            'friday': 4, 'saturday': 5, 'sunday': 6
        }
        for day_name, day_num in weekdays.items():
            if f'next {day_name}' in time_spec or f'{day_name}' in time_spec:
                days_ahead = day_num - now.weekday()
                if days_ahead <= 0:  # Target day already happened this week
                    days_ahead += 7
                target_date = now + timedelta(days=days_ahead)
                return target_date.replace(hour=9, minute=0, second=0, microsecond=0)

        # Handle specific date formats
        date_patterns = [
            r'(\d{1,2})/(\d{1,2})/(\d{4})',  # MM/DD/YYYY
            r'(\d{4})-(\d{1,2})-(\d{1,2})',  # YYYY-MM-DD
        ]

        for pattern in date_patterns:
            match = re.search(pattern, time_spec)
            if match:
                try:
                    if '/' in pattern:
                        month, day, year = map(int, match.groups())
                    else:
                        year, month, day = map(int, match.groups())

                    # Try to extract time
                    time_match = re.search(r'(\d{1,2})(?::(\d{2}))?\s*(am|pm)', time_spec)
                    if time_match:
                        hour, minute, ampm = time_match.groups()
                        hour = int(hour)
                        minute = int(minute) if minute else 0
                        if ampm == 'pm' and hour != 12:
                            hour += 12
                        elif ampm == 'am' and hour == 12:
                            hour = 0
                    else:
                        hour, minute = 9, 0  # Default 9 AM

                    return datetime(year, month, day, hour, minute)
                except ValueError:
                    continue

        return None

    @ami_tool
    def set_reminder(self, message: str, time_spec: str, recurring: Optional[str] = None):
        """Set a reminder for a specific time.
        time_spec can be like 'in 2 hours', 'tomorrow at 3pm', 'next friday', etc.
        recurring can be 'daily', 'weekly', 'monthly', or 'every X days/weeks/months'
        """
        try:
            due_date = self._parse_time_specification(time_spec)
            if not due_date:
                return f"Could not parse time specification: {time_spec}"

            success = self.reminder_manager.add_reminder(message, due_date, recurring)
            if success:
                recurring_text = f" (recurring {recurring})" if recurring else ""
                return f"Reminder set: '{message}' for {due_date.strftime('%Y-%m-%d %H:%M')}{recurring_text}"
            else:
                return "Failed to set reminder"
        except Exception as e:
            return f"Error setting reminder: {e}"

    @ami_tool
    def list_reminders(self):
        """List all active reminders"""
        try:
            upcoming = self.reminder_manager.get_upcoming_reminders(threshold_hours=72)  # Next 3 days
            if not upcoming:
                return "No active reminders"

            reminder_list = []
            for reminder in upcoming:
                time_left = reminder['time_left']
                if time_left.total_seconds() > 0:
                    hours_left = int(time_left.total_seconds() // 3600)
                    minutes_left = int((time_left.total_seconds() % 3600) // 60)
                    time_text = f"{hours_left}h {minutes_left}m"
                else:
                    time_text = "OVERDUE"

                reminder_list.append(
                    f"- {reminder['message']} (Due: {reminder['due_date'].strftime('%Y-%m-%d %H:%M')}, {time_text})"
                )

            return "Active reminders:\n" + "\n".join(reminder_list)
        except Exception as e:
            return f"Error listing reminders: {e}"

    @ami_tool
    def check_system_updates(self):
        """Check if system updates are available"""
        try:
            result = self.update_manager.check_for_updates()
            return f"Update status: {result['message']}"
        except Exception as e:
            return f"Error checking updates: {e}"

    @ami_tool
    def perform_system_update(self):
        """Perform a system update"""
        try:
            result = self.update_manager.perform_update()
            if result['success']:
                return "System updated successfully. Please restart AMI to apply changes."
            else:
                return f"Update failed: {result['message']}"
        except Exception as e:
            return f"Error performing update: {e}"

    @ami_tool
    def explain_topic(self, topic: str):
        """Explain a topic or concept to the user"""
        return f"I'd be happy to explain '{topic}'. However, I need more context about what specific aspect you'd like me to explain. Could you be more specific about what you'd like to know?"

    @ami_tool
    def tell_me_about(self, subject: str):
        """Tell the user about a specific subject"""
        return f"I'd love to tell you about '{subject}'. To provide the most helpful information, could you let me know what specific aspects interest you most?"

    @ami_tool
    def get_current_date_time(self):
        """Get the current date and time"""
        now = datetime.now()
        return f"Current date and time: {now.strftime('%A, %B %d, %Y at %I:%M %p')}"



    @ami_tool
    def run_ami_app(self, real_time: bool = False):
        runner = BinaryRunnerForAMI(self.ipc_manager)  # Pass manager if needed
        return runner.run_ami_app(real_time)
    @ami_tool
    def update_ami_source(self, real_time: bool = False):
        runner = BinaryRunnerForAMI(self.ipc_manager)
        return runner.update_ami_source(real_time)



    @ami_tool
    def update_ami_source(real_time: bool = False) -> Dict[str, Any]:
        BinaryRunnerForAMI.update()

    def safe_update_ami(real_time: bool = False) -> Dict[str, Any]:
        return _run_ami_command(['safe-update'], real_time)

    def rollback_ami(real_time: bool = False) -> Dict[str, Any]:
        return _run_ami_command(['rollback'], real_time)

    def install_headspace_plugins(user_repo: str, real_time: bool = False) -> Dict[str, Any]:
        return _run_ami_command(['gethead', user_repo], real_time)

    def list_plugins(real_time: bool = False) -> Dict[str, Any]:
        return _run_ami_command(['plugin', 'list'], real_time)

    def enable_plugin(name: str, real_time: bool = False) -> Dict[str, Any]:
        return _run_ami_command(['plugin', 'enable', name], real_time)

    def disable_plugin(name: str, real_time: bool = False) -> Dict[str, Any]:
        return _run_ami_command(['plugin', 'disable', name], real_time)

    @ami_tool
    def install_plugin(self, url_or_repo: str, real_time: bool = False) -> Dict[str, Any]:
        return BinaryRunnerForAMI(True).install_plugin(url_or_repo, real_time)

    def remove_plugin(name: str, real_time: bool = False) -> Dict[str, Any]:
        return _run_ami_command(['plugin', 'remove', name], real_time)

    def update_plugin(name: str, real_time: bool = False) -> Dict[str, Any]:
        return _run_ami_command(['plugin', 'update', name], real_time)
