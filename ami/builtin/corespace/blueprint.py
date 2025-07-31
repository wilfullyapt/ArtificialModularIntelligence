from flask import request, redirect, url_for, render_template_string

from ami.headspace import Blueprint, route

from .tool import ReminderManager, UpdateManager
from .settings import CorespaceSettings

class CorespaceBlueprint(Blueprint):
    """Web interface for corespace functionality"""
    
    settings_class = CorespaceSettings
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.reminder_manager = ReminderManager(self.filespace, self.settings.reminder_files)
        self.update_manager = UpdateManager()
    
    @route('/', methods=['GET'])
    def dashboard(self):
        """Main dashboard view"""
        upcoming = self.reminder_manager.get_upcoming_reminders(72)  # Next 3 days
        
        template = """
        <div style="background: #1a1a1a; color: white; padding: 20px; font-family: Arial, sans-serif;">
            <h2>AMI Core System Dashboard</h2>
            
            <div style="margin: 20px 0;">
                <h3>Upcoming Reminders ({{ reminders|length }})</h3>
                {% if reminders %}
                    {% for reminder in reminders %}
                    <div style="background: {% if reminder.is_urgent %}#ff8c00{% else %}#333{% endif %}; 
                                padding: 10px; margin: 5px 0; border-radius: 5px; 
                                color: {% if reminder.is_urgent %}black{% else %}white{% endif %};">
                        <strong>{{ reminder.message }}</strong><br>
                        Due: {{ reminder.due_date.strftime('%Y-%m-%d %H:%M') }}<br>
                        {% if reminder.time_left.total_seconds() > 0 %}
                            Time left: {{ (reminder.time_left.total_seconds() // 3600)|int }}h 
                            {{ ((reminder.time_left.total_seconds() % 3600) // 60)|int }}m
                        {% else %}
                            <span style="color: red; font-weight: bold;">OVERDUE</span>
                        {% endif %}
                        <form method="post" action="{{ url_for('CorespaceBlueprint.complete_reminder') }}" style="display: inline;">
                            <input type="hidden" name="reminder_text" value="{{ reminder.original_text }}">
                            <button type="submit" style="background: #4CAF50; color: white; border: none; 
                                                       padding: 5px 10px; border-radius: 3px; margin-left: 10px;">
                                Complete
                            </button>
                        </form>
                    </div>
                    {% endfor %}
                {% else %}
                    <p>No upcoming reminders</p>
                {% endif %}
            </div>
            
            <div style="margin: 20px 0;">
                <h3>System Updates</h3>
                <form method="post" action="{{ url_for('CorespaceBlueprint.check_updates') }}">
                    <button type="submit" style="background: #333; color: white; border: 1px solid #555; 
                                               padding: 10px 20px; border-radius: 5px;">
                        Check for Updates
                    </button>
                </form>
            </div>
        </div>
        """
        
        return render_template_string(template, reminders=upcoming)
    
    @route('/complete_reminder', methods=['POST'])
    def complete_reminder(self):
        """Complete a reminder"""
        reminder_text = request.form.get('reminder_text')
        if reminder_text:
            self.reminder_manager.complete_reminder(reminder_text)
        return redirect(url_for('CorespaceBlueprint.dashboard'))
    
    @route('/check_updates', methods=['POST'])
    def check_updates(self):
        """Check for system updates"""
        result = self.update_manager.check_for_updates()
        # For now, just redirect back to dashboard
        # In a real implementation, you might want to show the result
        return redirect(url_for('CorespaceBlueprint.dashboard'))
