""" AMI Core Headspace Blueprint for Markdown """

from functools import cached_property
from flask import make_response, redirect, url_for, request, render_template

from ami.headspace import Blueprint, HeaderButton, route, plugin_template

from .tool import Markdown as MarkdownTool
from .settings import MarkdownDefaultSettings

class Markdown(Blueprint):

    settings_class = MarkdownDefaultSettings

    @cached_property
    def markdown(self):
        return MarkdownTool(self.filespace, self.settings.markdown_files)

    @route('/editor/<path:filepath>', methods=['GET', 'POST'])
    def edit_file(self, filepath):
        path = self.filespace / filepath

        if not path.is_file():
            return f"Path({path}) is not a file."

        if request.method == 'POST':
            content = request.form['content']
            path.write_text(content)
            self.reload_gui()
            return redirect(url_for('Markdown.edit_file', filepath=filepath))

        content = path.read_text()

        return plugin_template('editor.html', buttons=[HeaderButton(form='editor-form', value='Save')], content=content)

    @route('/download_list/<path:list_name>', methods=['GET'])
    def download_list(self, list_name):

        mdf = self.markdown.get_list(list_name.replace("+", " "))

        if not mdf:
            return f"Cannot locate {list_name}!"

        raw_html = render_template('downloadable_list.html', list_title=list_name, list_items=mdf.list_contents)
        response = make_response(raw_html)
        response.headers["Content-Disposition"] = "attachment; filename=ami_list.html"
        return response

    @route('/files', methods=['GET'])
    def view_files(self):
        return plugin_template('files.html', markdown_files=self.settings.markdown_files)
