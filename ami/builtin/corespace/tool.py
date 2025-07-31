from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
import json
import re
from threading import Lock

from ami.core import LogBase
from ami.builtin.markdown.tool import Markdown as MarkdownTool

class ReminderManager(LogBase):
    """Manages reminders and timers for corespace"""
    
    def __init__(self, filespace: Path, reminder_files: List[str]):
        self.filespace = filespace
        self.reminder_files = reminder_files
        self._lock = Lock()
        self.markdown_tool = MarkdownTool(filespace, reminder_files)
        self._ensure_reminder_files()
    
    def _ensure_reminder_files(self):
        """Ensure reminder files exist with proper structure"""
        for filename in self.reminder_files:
            filepath = self.filespace / filename
            if not filepath.exists():
                content = """# Active Reminders

# Completed Reminders

# Recurring Reminders
"""
                filepath.write_text(content)
                self.logs.debug(f"Created reminder file: {filename}")
    
    def add_reminder(self, message: str, due_date: datetime, recurring: Optional[str] = None) -> bool:
        """Add a new reminder"""
        try:
            with self._lock:
                reminder_data = {
                    "message": message,
                    "due_date": due_date.isoformat(),
                    "created": datetime.now().isoformat(),
                    "recurring": recurring
                }
                
                if recurring:
                    list_name = "Recurring Reminders"
                else:
                    list_name = "Active Reminders"
                
                reminder_text = f"{message} - Due: {due_date.strftime('%Y-%m-%d %H:%M')}"
                if recurring:
                    reminder_text += f" (Recurring: {recurring})"
                
                self.markdown_tool.add_to_list(list_name, reminder_text)
                self.logs.info(f"Added reminder: {message}")
                return True
        except Exception as e:
            self.logs.error(f"Failed to add reminder: {e}")
            return False
    
    def get_upcoming_reminders(self, threshold_hours: int = 2) -> List[Dict[str, Any]]:
        """Get reminders that are due within the threshold"""
        upcoming = []
        try:
            with self._lock:
                active_reminders = self.markdown_tool.get_list("Active Reminders")
                now = datetime.now()
                threshold = now + timedelta(hours=threshold_hours)
                
                for reminder_text in active_reminders.contents:
                    reminder_data = self._parse_reminder_text(reminder_text)
                    if reminder_data and reminder_data['due_date'] <= threshold:
                        time_left = reminder_data['due_date'] - now
                        reminder_data['time_left'] = time_left
                        reminder_data['is_urgent'] = time_left.total_seconds() <= threshold_hours * 3600
                        upcoming.append(reminder_data)
                
        except Exception as e:
            self.logs.error(f"Error getting upcoming reminders: {e}")
        
        return upcoming
    
    def _parse_reminder_text(self, text: str) -> Optional[Dict[str, Any]]:
        """Parse reminder text to extract data"""
        try:
            # Pattern: "message - Due: YYYY-MM-DD HH:MM (Recurring: pattern)"
            pattern = r"^(.*?) - Due: (\d{4}-\d{2}-\d{2} \d{2}:\d{2})(?:\s*\(Recurring: (.*?)\))?$"
            match = re.match(pattern, text)
            if match:
                message, due_str, recurring = match.groups()
                due_date = datetime.strptime(due_str, '%Y-%m-%d %H:%M')
                return {
                    "message": message.strip(),
                    "due_date": due_date,
                    "recurring": recurring,
                    "original_text": text
                }
        except Exception as e:
            self.logs.error(f"Error parsing reminder text '{text}': {e}")
        return None
    
    def complete_reminder(self, reminder_text: str) -> bool:
        """Mark a reminder as completed"""
        try:
            with self._lock:
                self.markdown_tool.remove_from_list("Active Reminders", reminder_text)
                self.markdown_tool.add_to_list("Completed Reminders", 
                    f"{reminder_text} - Completed: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
                return True
        except Exception as e:
            self.logs.error(f"Error completing reminder: {e}")
            return False
    
    def process_recurring_reminders(self):
        """Process recurring reminders and create new instances"""
        try:
            with self._lock:
                recurring_reminders = self.markdown_tool.get_list("Recurring Reminders")
                now = datetime.now()
                
                for reminder_text in recurring_reminders.contents:
                    reminder_data = self._parse_reminder_text(reminder_text)
                    if reminder_data and reminder_data['due_date'] <= now:
                        # Create next occurrence
                        next_due = self._calculate_next_occurrence(
                            reminder_data['due_date'], 
                            reminder_data['recurring']
                        )
                        if next_due:
                            self.add_reminder(
                                reminder_data['message'],
                                next_due,
                                reminder_data['recurring']
                            )
        except Exception as e:
            self.logs.error(f"Error processing recurring reminders: {e}")
    
    def _calculate_next_occurrence(self, last_date: datetime, pattern: str) -> Optional[datetime]:
        """Calculate next occurrence based on recurring pattern"""
        try:
            pattern = pattern.lower().strip()
            if 'daily' in pattern or 'day' in pattern:
                return last_date + timedelta(days=1)
            elif 'weekly' in pattern or 'week' in pattern:
                return last_date + timedelta(weeks=1)
            elif 'monthly' in pattern or 'month' in pattern:
                return last_date + timedelta(days=30)  # Approximate
            elif 'yearly' in pattern or 'year' in pattern:
                return last_date + timedelta(days=365)  # Approximate
            else:
                # Try to parse "every X days/weeks/months"
                match = re.search(r'every (\d+) (day|week|month)', pattern)
                if match:
                    count, unit = match.groups()
                    count = int(count)
                    if unit == 'day':
                        return last_date + timedelta(days=count)
                    elif unit == 'week':
                        return last_date + timedelta(weeks=count)
                    elif unit == 'month':
                        return last_date + timedelta(days=count * 30)
        except Exception as e:
            self.logs.error(f"Error calculating next occurrence: {e}")
        return None

class UpdateManager(LogBase):
    """Handles self-update functionality"""
    
    def __init__(self):
        pass
    
    def check_for_updates(self) -> Dict[str, Any]:
        """Check if updates are available"""
        try:
            import subprocess
            result = subprocess.run(['git', 'fetch'], capture_output=True, text=True)
            if result.returncode == 0:
                # Check if local is behind remote
                result = subprocess.run(['git', 'status', '-uno'], capture_output=True, text=True)
                if 'behind' in result.stdout:
                    return {"update_available": True, "message": "Updates available"}
                else:
                    return {"update_available": False, "message": "Up to date"}
            else:
                return {"update_available": False, "message": "Error checking for updates"}
        except Exception as e:
            self.logs.error(f"Error checking for updates: {e}")
            return {"update_available": False, "message": f"Error: {e}"}
    
    def perform_update(self) -> Dict[str, Any]:
        """Perform the update"""
        try:
            import subprocess
            result = subprocess.run(['git', 'pull'], capture_output=True, text=True)
            if result.returncode == 0:
                return {"success": True, "message": "Update completed successfully"}
            else:
                return {"success": False, "message": f"Update failed: {result.stderr}"}
        except Exception as e:
            self.logs.error(f"Error performing update: {e}")
            return {"success": False, "message": f"Error: {e}"}
