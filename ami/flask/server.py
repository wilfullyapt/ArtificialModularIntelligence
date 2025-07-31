""" AMI Flask Server """

from functools import cached_property
from pathlib import Path
from typing import Any, List
from pprint import pprint as pp

from flask import Flask, flash, render_template,  redirect, request, url_for, make_response, send_file, abort

from ..core import Config, ConfigUpdater
from ..ipc.manager import IPCManager

headspaces_dir = Config().plugins_dir

AI_DIR = Config().data_dir
TEMPLATE_FOLDER = str(Path(__file__).parent / "templates")
STATIC_FOLDER = str(Path(__file__).parent / "static")

def logs_dir():
    """ Get the logs directory """
    log_dir = AI_DIR / "logs"
    if not log_dir.exists():
        log_dir.mkdir(parents=True)
    return log_dir

def parse_log_line(line):
    """ Parse a log line and extract components """
    import re
    # Match the log format: {time} | {level} | {name}:{function}:{line} - {message}
    pattern = r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) \| (\w+)\s* \| ([^-]+) - (.+)'
    match = re.match(pattern, line.strip())
    if match:
        return {
            'timestamp': match.group(1),
            'level': match.group(2).strip(),
            'source': match.group(3).strip(),
            'message': match.group(4).strip(),
            'raw': line.strip()
        }
    return {
        'timestamp': '',
        'level': 'UNKNOWN',
        'source': '',
        'message': line.strip(),
        'raw': line.strip()
    }

def get_all_log_files():
    """ Get all log files in the logs directory """
    log_files = []
    logs_path = logs_dir()
    for file_path in logs_path.rglob('*.log'):
        if file_path.is_file():
            relative_path = file_path.relative_to(logs_path)
            log_files.append({
                'name': str(relative_path),
                'path': file_path,
                'size': file_path.stat().st_size,
                'modified': file_path.stat().st_mtime
            })
    return sorted(log_files, key=lambda x: x['modified'], reverse=True)

def get_aggregated_logs(selected_files=None, level_filter=None, limit=1000):
    """ Get aggregated logs from selected files with optional level filtering """
    all_logs = []
    log_files = get_all_log_files()
    
    # Filter files if specific ones are selected
    if selected_files:
        log_files = [f for f in log_files if f['name'] in selected_files]
    
    for log_file in log_files:
        try:
            with log_file['path'].open('r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    if line.strip():
                        parsed = parse_log_line(line)
                        parsed['file'] = log_file['name']
                        parsed['line_number'] = line_num
                        
                        # Apply level filter if specified
                        if level_filter and parsed['level'] != level_filter:
                            continue
                            
                        all_logs.append(parsed)
        except Exception as e:
            print(f"Error reading log file {log_file['name']}: {e}")
    
    # Sort by timestamp (most recent first)
    all_logs.sort(key=lambda x: x['timestamp'], reverse=True)
    
    # Limit results
    return all_logs[:limit]

def get_app():
    """ Create and return the app """

    app = Flask("AMI", template_folder=TEMPLATE_FOLDER, static_folder=STATIC_FOLDER)

# ------------------------------------------------------------------------------
#                       ERROR HANDLING

    @app.errorhandler(404)
    def page_not_found(e):
        # Note that we set the 404 status explicitly
        return render_template('404.html'), 404

    @app.errorhandler(500)
    def internal_server_error(e):
        # Note that we set the 500 status explicitly
        return render_template('500.html'), 500

# ------------------------------------------------------------------------------
#                       ERROR HANDLING

    @app.context_processor
    def inject_menu_options():
        menu_items = []
        for bp_name, bp in app.blueprints.items():
            if 'menu_items' in dir(bp.settings):
                for menu_item in bp.settings.menu_items:
                    menu_items.append({'name': f"{bp_name}:{menu_item[0]}", 'url': f'/{bp_name.lower()}/{menu_item[1]}'})
        return {'menu_items': menu_items}

# ------------------------------------------------------------------------------
#                       MENU

    @app.route('/')
    def welcome():
        return render_template('welcome.html')

    def get_directory_tree(path):
        if path.is_dir():
            return  { entry.name: get_directory_tree(entry) for entry in path.iterdir() }
        return None


    @app.route('/settings', methods=['GET', 'POST'])
    def settings():

        conf_updtr = ConfigUpdater()
        if request.method == 'POST':
            try:

                if 'ami_config_submit' in request.form:
                    if conf_updtr.save_ami_config(request.form):
                        flash('AMI configuration saved successfully!', 'success')

                if 'env_submit' in request.form:
                    if conf_updtr.save_env_file(request.form):
                        flash('Environment variables saved successfully!', 'success')
                
                conf_updtr.update_headspace_setting(request.form)

            except Exception as e:
                flash(f'Error saving settings: {str(e)}', 'error')

            return redirect(url_for('settings'))

        ami_config = conf_updtr.load_ami_config()
        env_vars = conf_updtr.load_env_file()

        headspace_settings = {}
        settings_files = conf_updtr.get_headspace_settings_files()
        print(f"settings file: {settings_files}")
        for name, file_path in settings_files.items():
            print(f"settings_file[{name}] = {file_path}")
            headspace_settings[name] = conf_updtr.load_headspace_settings(file_path)

#       template_settings = self.tempsets.augment(header="System Settings", buttons=[])
#       return render_template('settings_manager.html', ami_config=ami_config, env_vars=env_vars, headspace_settings=headspace_settings, tempsets=template_settings)

        print("setting.html file rendered")

        print("ami_config")
        pp(ami_config)

        print("env_vars")
        pp(env_vars)

        print("headspace_settings")
        pp(headspace_settings)

        return render_template('settings.html', ami_config=ami_config, env_vars=env_vars, headspace_settings=headspace_settings)
#       return render_template('settings.html')

    @app.route('/tree')
    def tree():
        tree_dict = get_directory_tree(headspaces_dir)
        return render_template('tree.html', tree=tree_dict)

    @app.route('/logs')
    def logs():
        # Get query parameters
        selected_files = request.args.getlist('files')
        level_filter = request.args.get('level')
        view_mode = request.args.get('view', 'aggregated')  # 'aggregated' or 'tree'
        
        if view_mode == 'tree':
            tree_dict = get_directory_tree(logs_dir())
            return render_template('tree.html', tree=tree_dict)
        
        # Get available log files and levels
        available_files = get_all_log_files()
        available_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        
        # Get aggregated logs
        logs_data = get_aggregated_logs(selected_files, level_filter, limit=1000)
        
        return render_template('logs_aggregated.html', 
                             logs=logs_data,
                             available_files=available_files,
                             selected_files=selected_files,
                             available_levels=available_levels,
                             selected_level=level_filter,
                             total_logs=len(logs_data))

    @app.route('/logs/<path:logfile>', methods=['GET'])
    def render_logfile(logfile):
        logfile_path = logs_dir() / logfile

        if not logfile_path.is_file():
            return f"File '{logfile}' not found in {logfile_path}", 404

        # Get query parameters for filtering
        level_filter = request.args.get('level')
        raw_view = request.args.get('raw', 'false').lower() == 'true'

        parsed_logs = []
        raw_content = []
        
        with logfile_path.open('r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                raw_content.append(line.rstrip())
                if line.strip():
                    parsed = parse_log_line(line)
                    parsed['line_number'] = line_num
                    
                    # Apply level filter if specified
                    if not level_filter or parsed['level'] == level_filter:
                        parsed_logs.append(parsed)

        if raw_view:
            return render_template('logs.html', logfile=logfile, log_content=raw_content)
        else:
            available_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
            return render_template('logs_single.html', 
                                 logfile=logfile, 
                                 logs=parsed_logs,
                                 available_levels=available_levels,
                                 selected_level=level_filter,
                                 total_logs=len(parsed_logs))

# ------------------------------------------------------------------------------
#                       TREE ROUTING
#                          + /upload
#                          + /download
#                          + /editor

    @app.route('/upload')
    def uploader():
        return redirect(url_for('tree'))

    @app.route('/upload/<path:destination_directory>', methods=['GET'])
    def upload_to_dir(destination_directory):
        path = headspaces_dir / destination_directory
        if (path).is_dir():
            dir_selection = [ dir.name for dir in (path).glob('*/') if dir.is_dir() ]
            return render_template("upload.html",
                                   directories=dir_selection,
                                   local_path=destination_directory.split('/')[-1])

        abort(404)

    @app.route('/download/<path:filename>', methods=['GET'])
    def download_file(filename):
        path = headspaces_dir / filename
        if path.is_file():
            response = make_response(send_file(str(path), as_attachment=True))
            response.headers['Content-Disposition'] = f'attachment; filename="{filename}"'
            return response
        else:
            return render_template('404.html'), 404

    return app

def assemble_flask_server(blueprints: List[Any], ipc_manager: IPCManager):
    app = get_app()
    for bp in blueprints:
        app.register_blueprint(bp(ipc_manager))

    return app
