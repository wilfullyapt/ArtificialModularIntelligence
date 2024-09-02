""" AMI Flask Server """

from pathlib import Path

from flask import Flask, render_template,  redirect, url_for, make_response, send_file, abort

from ami.config import Config

headspaces_dir = Config().headspaces_dir

AI_DIR = Config().ai_dir
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

app = get_app()
