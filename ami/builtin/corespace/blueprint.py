from functools import cached_property
from flask import request, redirect, url_for, render_template_string, flash, jsonify

from ami.headspace import Blueprint, route, plugin_template

from .tool import ReminderManager, UpdateManager, BinaryRunnerForAMI
from .settings import CorespaceSettings

class CorespaceBlueprint(Blueprint):
    """Web interface for corespace functionality"""
    
    settings_class = CorespaceSettings
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Use the instance settings, not class settings
        settings_instance = self.settings if hasattr(self, 'settings') else CorespaceSettings()
        reminder_files = getattr(settings_instance, 'reminder_files', ['reminders.md'])
        self.reminder_manager = ReminderManager(self.filespace, reminder_files)
        self.update_manager = UpdateManager()
    
    @cached_property
    def binary_runner(self):
        return BinaryRunnerForAMI(ipc_manager=self.ipc_manager)

    @route('/', methods=['GET'])
    def index(self):
        """Redirect root to dashboard"""
        return redirect(url_for('CorespaceBlueprint.dashboard'))

    @route('/dashboard', methods=['GET'])
    def dashboard(self):
        """Enhanced main dashboard view"""
        upcoming = self.reminder_manager.get_upcoming_reminders(72)  # Next 3 days
        
        # Get system status info
        try:
            plugins_result = self.binary_runner.list_plugins()
            plugin_count = len(plugins_result.get('data', {}).get('plugins', []))
        except Exception:
            plugin_count = 0
            
        template = """
        <div style="background: #1a1a1a; color: white; padding: 20px; font-family: Arial, sans-serif;">
            <h2><i class="fas fa-tachometer-alt"></i> AMI Core System Dashboard</h2>
            
            <div style="display: flex; gap: 20px; margin: 20px 0;">
                <div style="background: #333; padding: 15px; border-radius: 5px; flex: 1;">
                    <h4><i class="fas fa-clock"></i> Reminders</h4>
                    <p>{{ reminders|length }} upcoming</p>
                    <a href="{{ url_for('CorespaceBlueprint.reminders') }}" style="color: #decbb3;">Manage →</a>
                </div>
                <div style="background: #333; padding: 15px; border-radius: 5px; flex: 1;">
                    <h4><i class="fas fa-puzzle-piece"></i> Plugins</h4>
                    <p>{{ plugin_count }} installed</p>
                    <a href="{{ url_for('CorespaceBlueprint.plugins') }}" style="color: #decbb3;">Manage →</a>
                </div>
                <div style="background: #333; padding: 15px; border-radius: 5px; flex: 1;">
                    <h4><i class="fas fa-cogs"></i> System</h4>
                    <p>Status: Active</p>
                    <a href="{{ url_for('CorespaceBlueprint.system') }}" style="color: #decbb3;">Manage →</a>
                </div>
            </div>
            
            <div style="margin: 20px 0;">
                <h3>Recent Reminders</h3>
                {% if reminders %}
                    {% for reminder in reminders[:3] %}
                    <div style="background: {% if reminder.is_urgent %}#ff8c00{% else %}#333{% endif %}; 
                                padding: 10px; margin: 5px 0; border-radius: 5px; 
                                color: {% if reminder.is_urgent %}black{% else %}white{% endif %};">
                        <strong>{{ reminder.message }}</strong><br>
                        Due: {{ reminder.due_date.strftime('%Y-%m-%d %H:%M') }}
                    </div>
                    {% endfor %}
                {% else %}
                    <p>No upcoming reminders</p>
                {% endif %}
            </div>
        </div>
        """
        
        return plugin_template('corespace_dashboard.html', 
                             reminders=upcoming, 
                             plugin_count=plugin_count,
                             fallback_template=template)
    
    # SYSTEM MANAGEMENT ROUTES
    @route('/system', methods=['GET'])
    def system(self):
        """System management dashboard"""
        template = """
        <div style="background: #1a1a1a; color: white; padding: 20px; font-family: Arial, sans-serif;">
            <h2><i class="fas fa-cogs"></i> System Management</h2>
            
            <div style="display: flex; gap: 20px; margin: 20px 0;">
                <div style="background: #333; padding: 20px; border-radius: 5px; flex: 1;">
                    <h3>Updates</h3>
                    <p>Keep your AMI system up to date</p>
                    <form method="post" action="{{ url_for('CorespaceBlueprint.system_update') }}">
                        <button type="submit" style="background: #4CAF50; color: white; border: none; 
                                                   padding: 10px 20px; border-radius: 5px; margin: 5px;">
                            <i class="fas fa-download"></i> Update System
                        </button>
                    </form>
                    <form method="post" action="{{ url_for('CorespaceBlueprint.system_safe_update') }}">
                        <button type="submit" style="background: #ff9500; color: white; border: none; 
                                                   padding: 10px 20px; border-radius: 5px; margin: 5px;">
                            <i class="fas fa-shield-alt"></i> Safe Update
                        </button>
                    </form>
                </div>
                
                <div style="background: #333; padding: 20px; border-radius: 5px; flex: 1;">
                    <h3>Recovery</h3>
                    <p>Rollback to a previous version if needed</p>
                    <form method="post" action="{{ url_for('CorespaceBlueprint.system_rollback') }}" 
                          onsubmit="return confirm('Are you sure you want to rollback? This will revert recent changes.')">
                        <button type="submit" style="background: #f44336; color: white; border: none; 
                                                   padding: 10px 20px; border-radius: 5px; margin: 5px;">
                            <i class="fas fa-undo"></i> Rollback System
                        </button>
                    </form>
                </div>
            </div>
            
            <div style="margin: 20px 0;">
                <h3>System Status</h3>
                <div style="background: #333; padding: 15px; border-radius: 5px;">
                    <p><strong>Status:</strong> Running</p>
                    <p><strong>Last Update Check:</strong> {{ status.get('last_check', 'Never') }}</p>
                    <p><strong>Version:</strong> {{ status.get('version', 'Unknown') }}</p>
                </div>
            </div>
        </div>
        """
        
        status = {'last_check': 'Never', 'version': 'AMI 0.1.0'}
        return plugin_template('system_management.html', status=status, fallback_template=template)
    
    @route('/system/update', methods=['POST'])
    def system_update(self):
        """Perform system update"""
        try:
            result = self.binary_runner.update_ami_source()
            if result.get('status') == 'completed':
                flash('System update completed successfully', 'success')
            else:
                flash(f"Update failed: {result.get('message', 'Unknown error')}", 'error')
        except Exception as e:
            flash(f'Update failed: {str(e)}', 'error')
        return redirect(url_for('CorespaceBlueprint.system'))
    
    @route('/system/safe-update', methods=['POST'])
    def system_safe_update(self):
        """Perform safe system update"""
        try:
            result = self.binary_runner.safe_update_ami()
            if result.get('status') == 'completed':
                flash('Safe system update completed successfully', 'success')
            else:
                flash(f"Safe update failed: {result.get('message', 'Unknown error')}", 'error')
        except Exception as e:
            flash(f'Safe update failed: {str(e)}', 'error')
        return redirect(url_for('CorespaceBlueprint.system'))
    
    @route('/system/rollback', methods=['POST'])
    def system_rollback(self):
        """Perform system rollback"""
        try:
            result = self.binary_runner.rollback_ami()
            if result.get('status') == 'completed':
                flash('System rollback completed successfully', 'success')
            else:
                flash(f"Rollback failed: {result.get('message', 'Unknown error')}", 'error')
        except Exception as e:
            flash(f'Rollback failed: {str(e)}', 'error')
        return redirect(url_for('CorespaceBlueprint.system'))
    
    # PLUGIN MANAGEMENT ROUTES
    @route('/plugins', methods=['GET'])
    def plugins(self):
        """Plugin management interface"""
        try:
            result = self.binary_runner.list_plugins()
            plugins_data = result.get('data', {}).get('plugins', [])
        except Exception as e:
            plugins_data = []
            flash(f'Error loading plugins: {str(e)}', 'error')
        
        template = """
        <div style="background: #1a1a1a; color: white; padding: 20px; font-family: Arial, sans-serif;">
            <h2><i class="fas fa-puzzle-piece"></i> Plugin Management</h2>
            
            <div style="margin: 20px 0;">
                <h3>Install New Plugin</h3>
                <form method="post" action="{{ url_for('CorespaceBlueprint.plugin_install') }}" style="background: #333; padding: 15px; border-radius: 5px;">
                    <input type="text" name="plugin_url" placeholder="Plugin URL or repository" 
                           style="padding: 10px; margin: 5px; width: 300px; background: #555; color: white; border: 1px solid #777;">
                    <button type="submit" style="background: #4CAF50; color: white; border: none; 
                                               padding: 10px 20px; border-radius: 5px; margin: 5px;">
                        <i class="fas fa-plus"></i> Install Plugin
                    </button>
                </form>
            </div>
            
            <div style="margin: 20px 0;">
                <h3>Installed Plugins ({{ plugins|length }})</h3>
                {% if plugins %}
                    {% for plugin in plugins %}
                    <div style="background: #333; padding: 15px; margin: 10px 0; border-radius: 5px; display: flex; justify-content: space-between; align-items: center;">
                        <div>
                            <h4>{{ plugin.name }}</h4>
                            <p style="color: #ccc;">Version: {{ plugin.get('version', 'Unknown') }}</p>
                            <p style="color: #ccc;">Status: 
                                <span style="color: {% if plugin.get('enabled') %}#4CAF50{% else %}#f44336{% endif %};">
                                    {{ 'Enabled' if plugin.get('enabled') else 'Disabled' }}
                                </span>
                            </p>
                        </div>
                        <div>
                            <form method="post" action="{{ url_for('CorespaceBlueprint.plugin_toggle', name=plugin.name) }}" style="display: inline;">
                                <button type="submit" style="background: {% if plugin.get('enabled') %}#f44336{% else %}#4CAF50{% endif %}; color: white; border: none; 
                                                           padding: 8px 15px; border-radius: 3px; margin: 2px;">
                                    {% if plugin.get('enabled') %}Disable{% else %}Enable{% endif %}
                                </button>
                            </form>
                            <form method="post" action="{{ url_for('CorespaceBlueprint.plugin_update', name=plugin.name) }}" style="display: inline;">
                                <button type="submit" style="background: #ff9500; color: white; border: none; 
                                                           padding: 8px 15px; border-radius: 3px; margin: 2px;">
                                    Update
                                </button>
                            </form>
                            <form method="post" action="{{ url_for('CorespaceBlueprint.plugin_remove', name=plugin.name) }}" 
                                  style="display: inline;" onsubmit="return confirm('Remove plugin {{ plugin.name }}?')">
                                <button type="submit" style="background: #f44336; color: white; border: none; 
                                                           padding: 8px 15px; border-radius: 3px; margin: 2px;">
                                    Remove
                                </button>
                            </form>
                        </div>
                    </div>
                    {% endfor %}
                {% else %}
                    <p>No plugins installed</p>
                {% endif %}
            </div>
        </div>
        """
        
        return plugin_template('plugin_management.html', plugins=plugins_data, fallback_template=template)
    
    @route('/plugins/install', methods=['POST'])
    def plugin_install(self):
        """Install a new plugin"""
        plugin_url = request.form.get('plugin_url', '').strip()
        if not plugin_url:
            flash('Please provide a plugin URL', 'error')
            return redirect(url_for('CorespaceBlueprint.plugins'))
        
        try:
            result = self.binary_runner.install_plugin(plugin_url)
            if result.get('status') == 'completed':
                flash(f'Plugin installed successfully from {plugin_url}', 'success')
            else:
                flash(f"Plugin installation failed: {result.get('message', 'Unknown error')}", 'error')
        except Exception as e:
            flash(f'Plugin installation failed: {str(e)}', 'error')
        
        return redirect(url_for('CorespaceBlueprint.plugins'))
    
    @route('/plugins/<name>/remove', methods=['POST'])
    def plugin_remove(self, name):
        """Remove a plugin"""
        try:
            result = self.binary_runner.remove_plugin(name)
            if result.get('status') == 'completed':
                flash(f'Plugin {name} removed successfully', 'success')
            else:
                flash(f"Failed to remove plugin {name}: {result.get('message', 'Unknown error')}", 'error')
        except Exception as e:
            flash(f'Failed to remove plugin {name}: {str(e)}', 'error')
        
        return redirect(url_for('CorespaceBlueprint.plugins'))
    
    @route('/plugins/<name>/update', methods=['POST'])
    def plugin_update(self, name):
        """Update a plugin"""
        try:
            result = self.binary_runner.update_plugin(name)
            if result.get('status') == 'completed':
                flash(f'Plugin {name} updated successfully', 'success')
            else:
                flash(f"Failed to update plugin {name}: {result.get('message', 'Unknown error')}", 'error')
        except Exception as e:
            flash(f'Failed to update plugin {name}: {str(e)}', 'error')
        
        return redirect(url_for('CorespaceBlueprint.plugins'))
    
    @route('/plugins/<name>/toggle', methods=['POST'])
    def plugin_toggle(self, name):
        """Toggle plugin enabled/disabled state"""
        try:
            # First get current state
            list_result = self.binary_runner.list_plugins()
            plugins_data = list_result.get('data', {}).get('plugins', [])
            plugin = next((p for p in plugins_data if p.get('name') == name), None)
            
            if not plugin:
                flash(f'Plugin {name} not found', 'error')
                return redirect(url_for('CorespaceBlueprint.plugins'))
            
            if plugin.get('enabled'):
                result = self.binary_runner.disable_plugin(name)
                action = 'disabled'
            else:
                result = self.binary_runner.enable_plugin(name)
                action = 'enabled'
            
            if result.get('status') == 'completed':
                flash(f'Plugin {name} {action} successfully', 'success')
            else:
                flash(f"Failed to toggle plugin {name}: {result.get('message', 'Unknown error')}", 'error')
        except Exception as e:
            flash(f'Failed to toggle plugin {name}: {str(e)}', 'error')
        
        return redirect(url_for('CorespaceBlueprint.plugins'))
    
    # ENHANCED REMINDER MANAGEMENT ROUTES
    @route('/reminders', methods=['GET'])
    def reminders(self):
        """Enhanced reminder management interface"""
        upcoming = self.reminder_manager.get_upcoming_reminders(24*7)  # Next week
        
        template = """
        <div style="background: #1a1a1a; color: white; padding: 20px; font-family: Arial, sans-serif;">
            <h2><i class="fas fa-clock"></i> Reminder Management</h2>
            
            <div style="margin: 20px 0;">
                <h3>Add New Reminder</h3>
                <form method="post" action="{{ url_for('CorespaceBlueprint.reminder_add') }}" style="background: #333; padding: 15px; border-radius: 5px;">
                    <input type="text" name="message" placeholder="Reminder message" required
                           style="padding: 10px; margin: 5px; width: 300px; background: #555; color: white; border: 1px solid #777;">
                    <input type="text" name="time_spec" placeholder="When? (e.g., 'tomorrow 3pm', 'in 2 hours')" required
                           style="padding: 10px; margin: 5px; width: 200px; background: #555; color: white; border: 1px solid #777;">
                    <input type="text" name="recurring" placeholder="Recurring? (e.g., 'daily', 'weekly')" 
                           style="padding: 10px; margin: 5px; width: 150px; background: #555; color: white; border: 1px solid #777;">
                    <button type="submit" style="background: #4CAF50; color: white; border: none; 
                                               padding: 10px 20px; border-radius: 5px; margin: 5px;">
                        <i class="fas fa-plus"></i> Add Reminder
                    </button>
                </form>
            </div>
            
            <div style="margin: 20px 0;">
                <h3>Active Reminders ({{ reminders|length }})</h3>
                {% if reminders %}
                    {% for reminder in reminders %}
                    <div style="background: {% if reminder.is_urgent %}#ff8c00{% else %}#333{% endif %}; 
                                padding: 15px; margin: 10px 0; border-radius: 5px; 
                                color: {% if reminder.is_urgent %}black{% else %}white{% endif %};">
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <div>
                                <h4>{{ reminder.message }}</h4>
                                <p>Due: {{ reminder.due_date.strftime('%Y-%m-%d %H:%M') }}</p>
                                {% if reminder.time_left.total_seconds() > 0 %}
                                    <p>Time left: {{ (reminder.time_left.total_seconds() // 3600)|int }}h 
                                       {{ ((reminder.time_left.total_seconds() % 3600) // 60)|int }}m</p>
                                {% else %}
                                    <p style="color: red; font-weight: bold;">OVERDUE</p>
                                {% endif %}
                            </div>
                            <div>
                                <form method="post" action="{{ url_for('CorespaceBlueprint.complete_reminder') }}" style="display: inline;">
                                    <input type="hidden" name="reminder_text" value="{{ reminder.original_text }}">
                                    <button type="submit" style="background: #4CAF50; color: white; border: none; 
                                                               padding: 8px 15px; border-radius: 3px; margin: 2px;">
                                        <i class="fas fa-check"></i> Complete
                                    </button>
                                </form>
                            </div>
                        </div>
                    </div>
                    {% endfor %}
                {% else %}
                    <p>No active reminders</p>
                {% endif %}
            </div>
        </div>
        """
        
        return plugin_template('reminder_management.html', reminders=upcoming, fallback_template=template)
    
    @route('/reminders/add', methods=['POST'])
    def reminder_add(self):
        """Add a new reminder with natural language parsing"""
        message = request.form.get('message', '').strip()
        time_spec = request.form.get('time_spec', '').strip()
        recurring = request.form.get('recurring', '').strip()
        
        if not message or not time_spec:
            flash('Please provide both message and time specification', 'error')
            return redirect(url_for('CorespaceBlueprint.reminders'))
        
        # Parse time specification using simple natural language patterns
        due_date = self._parse_time_specification(time_spec)
        
        if not due_date:
            flash(f'Could not parse time specification: {time_spec}', 'error')
            return redirect(url_for('CorespaceBlueprint.reminders'))
        
        try:
            success = self.reminder_manager.add_reminder(
                message, 
                due_date, 
                recurring if recurring else None
            )
            if success:
                flash(f'Reminder added: {message} at {due_date.strftime("%Y-%m-%d %H:%M")}', 'success')
            else:
                flash('Failed to add reminder', 'error')
        except Exception as e:
            flash(f'Error adding reminder: {str(e)}', 'error')
        
        return redirect(url_for('CorespaceBlueprint.reminders'))

    @route('/complete_reminder', methods=['POST'])
    def complete_reminder(self):
        """Complete a reminder"""
        reminder_text = request.form.get('reminder_text')
        if reminder_text:
            try:
                success = self.reminder_manager.complete_reminder(reminder_text)
                if success:
                    flash('Reminder completed successfully', 'success')
                else:
                    flash('Failed to complete reminder', 'error')
            except Exception as e:
                flash(f'Error completing reminder: {str(e)}', 'error')
        return redirect(url_for('CorespaceBlueprint.reminders'))
    
    def _parse_time_specification(self, time_spec: str):
        """Parse natural language time specifications"""
        from datetime import datetime, timedelta
        import re
        
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

        # Handle "today" with time
        if 'today' in time_spec:
            time_match = re.search(r'(\d{1,2})(?::(\d{2}))?\s*(am|pm)', time_spec)
            if time_match:
                hour, minute, ampm = time_match.groups()
                hour = int(hour)
                minute = int(minute) if minute else 0
                if ampm == 'pm' and hour != 12:
                    hour += 12
                elif ampm == 'am' and hour == 12:
                    hour = 0
                return now.replace(hour=hour, minute=minute, second=0, microsecond=0)

        # Handle "next [weekday]"
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
                    return target_date.replace(hour=hour, minute=minute, second=0, microsecond=0)
                else:
                    return target_date.replace(hour=9, minute=0, second=0, microsecond=0)
        
        # Try to parse direct date format YYYY-MM-DD HH:MM or YYYY-MM-DD
        try:
            if len(time_spec) == 16 and time_spec[10] == ' ':  # YYYY-MM-DD HH:MM
                return datetime.strptime(time_spec, '%Y-%m-%d %H:%M')
            elif len(time_spec) == 10 and time_spec[4] == '-':  # YYYY-MM-DD
                return datetime.strptime(time_spec, '%Y-%m-%d').replace(hour=9, minute=0)
        except ValueError:
            pass
        
        return None

    # LEGACY ROUTES (for backward compatibility)
    @route('/check_updates', methods=['POST'])
    def check_updates(self):
        """Legacy check updates route - redirect to system page"""
        return redirect(url_for('CorespaceBlueprint.system'))