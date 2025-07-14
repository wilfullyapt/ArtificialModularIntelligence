""" AMI Flask Server """

from functools import cached_property
from pathlib import Path
from typing import Any, List

from flask import Flask, render_template,  redirect, url_for, make_response, send_file, abort

from ami.ipc.manager import IPCManager

from ..core import Config

headspaces_dir = Config().headspaces_dir

AI_DIR = Config().data_dir
TEMPLATE_FOLDER = str(Path(__file__).parent / "templates")
STATIC_FOLDER = str(Path(__file__).parent / "static")

def logs_dir():
    """ Get the logs directory """
    log_dir = AI_DIR / "logs"
    if not log_dir.exists():
        log_dir.mkdir(parents=True)
    return log_dir

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

    @app.route('/tree')
    def tree():
        tree_dict = get_directory_tree(headspaces_dir)
        return render_template('tree.html', tree=tree_dict)

    @app.route('/logs')
    def logs():
        tree_dict = get_directory_tree(logs_dir())
        return render_template('tree.html', tree=tree_dict)

    @app.route('/logs/<path:logfile>', methods=['GET'])
    def render_logfile(logfile):
        logfile_path = logs_dir() / logfile

        if not logfile_path.is_file():
            return f"File '{logfile}' not found in {logfile_path}", 404

        with logfile_path.open('r') as f:
            content = f.readlines()

        return render_template('logs.html', logfile=logfile, log_content=content)

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
