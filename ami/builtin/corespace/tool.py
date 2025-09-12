import os
import json
import re
import uuid
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import subprocess
import socket
from threading import Lock

from ami.core import LogBase
from ami.builtin.markdown.tool import Markdown as MarkdownTool

class BinaryRunnerForAMI(LogBase):
    """Handles running the AMI binary with optional real-time socket communication.

    Supports synchronous (JSON output) and real-time (socket events) modes.
    In real-time, events are forwarded to IPC (if provided) and collected for return.
    """

    def __init__(self, ipc_manager=None):
        self.ipc_manager = ipc_manager
        self._lock = Lock()

    def ami_binary_command(self, args: List[str], real_time: bool = False) -> Dict[str, Any]:
        """
        Run binary, optionally in real-time mode.
        Non-real-time: Synchronous capture with --json-output.
        Real-time: Create socket, launch Popen, block on accept/recv to forward and collect events.
        Returns consistent dict with status, message, and (if applicable) data/events.
        """
        cmd = ['ami'] + args
        with self._lock:
            if not real_time:
                cmd.insert(1, '--json-output')
                try:
                    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
                    return json.loads(result.stdout)
                except FileNotFoundError:
                    return {"status": "error", "message": "AMI binary not found in PATH"}
                except subprocess.CalledProcessError as e:
                    return {"status": "error", "message": e.stderr.strip(), "return_code": e.returncode}
                except json.JSONDecodeError:
                    return {"status": "error", "message": "Invalid JSON output"}
            else:
                # Real-time mode
                socket_dir = Path.home() / '.ami' / 'sockets'
                socket_dir.mkdir(parents=True, exist_ok=True)
                socket_path = str(socket_dir / f'ami-{os.getpid()}-{uuid.uuid4().hex[:8]}.sock')
                if os.path.exists(socket_path):
                    os.unlink(socket_path)

                conn = None
                server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
                proc = None
                try:
                    server.bind(socket_path)
                    os.chmod(socket_path, 0o600)
                    server.listen(1)
                    cmd.insert(1, f'--socket-path={socket_path}')
                    self.logs.info(f"Starting binary with socket: {socket_path}")
                    try:
                        proc = subprocess.Popen(
                            cmd,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE,
                            text=True
                        )
                    except FileNotFoundError:
                        return {"status": "error", "message": "AMI binary not found in PATH"}

                    server.settimeout(10.0)
                    conn, _ = server.accept()
                    server.settimeout(None)
                    data = b''
                    events = []

                    while True:
                        chunk = conn.recv(1024)
                        if not chunk:
                            break
                        data += chunk
                        while b'\n' in data:
                            line, data = data.split(b'\n', 1)
                            try:
                                msg = json.loads(line.decode('utf-8'))
                                events.append(msg)
                                if self.ipc_manager:
                                    self.logs.info(f"Message recieved: {msg}")
#                                   self.ipc_manager.route_event(IPCEvent(type=EventType.REAL_TIME_UPDATE, source=ProcessType.AI, target=ProcessType.AI, data=msg))
                                else:
                                    self.logs.info(f"Real-time event: {msg}")
                            except json.JSONDecodeError:
                                self.logs.error("Invalid JSON from binary")

                    if data:
                        try:
                            msg = json.loads(data.decode('utf-8'))
                            events.append(msg)
                        except json.JSONDecodeError:
                            self.logs.error("Incomplete final JSON from binary")

                    stdout, stderr = proc.communicate()
                    ret_code = proc.returncode
                    if stdout:
                        self.logs.info(f"Binary stdout: {stdout.strip()}")
                    if stderr:
                        self.logs.error(f"Binary stderr: {stderr.strip()}")

                    if ret_code != 0:
                        return {"status": "error", "message": "Binary failed", "return_code": ret_code, "events": events}

                    return {"status": "completed", "message": "Real-time operation finished", "events": events}
                except socket.timeout:
                    self.logs.error("Timeout waiting for binary connection")
                    return {"status": "error", "message": "Binary connection timeout"}
                except Exception as e:
                    self.logs.error(f"Unexpected error: {str(e)}")
                    return {"status": "error", "message": str(e)}
                finally:
                    if conn:
                        conn.close()
                    server.close()
                    if os.path.exists(socket_path):
                        os.unlink(socket_path)
                    if proc is not None and proc.poll() is None:
                        try:
                            proc.terminate()
                            proc.wait(timeout=5.0)
                        except subprocess.TimeoutExpired:
                            # Force kill if terminate doesn't work
                            proc.kill()
                            proc.wait()

    ##################################################
    ###     AMI Binary Commands
    def update_ami_source(self, real_time: bool = False) -> Dict[str, Any]:
        return self.ami_binary_command(['update'], real_time)
    def safe_update_ami(self, real_time: bool = False) -> Dict[str, Any]:
        return self.ami_binary_command(['safe-update'], real_time)
    def rollback_ami(self, real_time: bool = False) -> Dict[str, Any]:
        return self.ami_binary_command(['rollback'], real_time)
    def install_headspace_plugins(self, user_repo: str, real_time: bool = False) -> Dict[str, Any]:
        return self.ami_binary_command(['gethead', user_repo], real_time)
    def install_plugin(self, url_or_repo: str, real_time: bool = False) -> Dict[str, Any]:
        return self.ami_binary_command(['plugin', 'install', url_or_repo], real_time)
    def remove_plugin(self, name: str, real_time: bool = False) -> Dict[str, Any]:
        return self.ami_binary_command(['plugin', 'remove', name], real_time)
    def update_plugin(self, name: str, real_time: bool = False) -> Dict[str, Any]:
        return self.ami_binary_command(['plugin', 'update', name], real_time)


    ##################################################
    ###     AMI Non-Binary Commands
    def list_plugins(self, real_time: bool = False) -> Dict[str, Any]:
        # Use ami_binary_command for consistency
        return self.ami_binary_command(['plugin', 'list'], real_time)
    def enable_plugin(self, name: str, real_time: bool = False) -> Dict[str, Any]:
        return self.ami_binary_command(['plugin', 'enable', name], real_time)
    def disable_plugin(self, name: str, real_time: bool = False) -> Dict[str, Any]:
        return self.ami_binary_command(['plugin', 'disable', name], real_time)


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
