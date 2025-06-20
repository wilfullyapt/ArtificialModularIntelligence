""" AMI Core Headspace Blueprint for Markdown """

from flask import make_response, redirect, url_for, request, render_template as jinja_template

from ami.headspace.blueprint import Blueprint, HeaderButton, route, render_template
from .tool import Markdown as MarkdownTool

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

    @route('/download_list/<path:list_name>', methods=['GET'])
    def download_list(self, list_name):

        mdf = MarkdownTool().get_list(list_name.replace("+", " "))

        if not mdf:
            return f"Cannot locate {list_name}!"

        raw_html = jinja_template('downloadable_list.html', list_title=list_name, list_items=mdf.list_contents)
        response = make_response(raw_html)
        response.headers["Content-Disposition"] = "attachment; filename=ami_list.html"
        return response
