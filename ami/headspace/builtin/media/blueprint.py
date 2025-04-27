""" AMI Core Headspace Blueprint for Markdown """

from flask import redirect, url_for, request

from ami.headspace.blueprint import Blueprint, HeaderButton, route, render_template

class Markdown(Blueprint):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.update_tempsets(css='markdown_styles.css')

    @route('/editor/<path:filepath>', methods=['GET', 'POST'])
    def edit_file(self, filepath):
        path = self.filesystem / filepath

        if not path.is_file():
            return f"Path({path}) is not a file."

        if request.method == 'POST':
            content = request.form['content']
            path.write_text(content)
            self.reload_gui()
            return redirect(url_for('Markdown.edit_file', filepath=filepath))

        content = path.read_text()
        tempate_settings = self.tempsets.augment(
                heading=filepath,
                buttons=[HeaderButton(form='editor-form', value='Save')]
        )
        return render_template('editor.html', tempsets=tempate_settings, content=content)
