from ami.headspace import Headspace, ami_tool, agent_observation
from ami.flask.manager import get_network_url

from .tool import Markdown as MarkdownTool

class Markdown(Headspace):
    """ Built-in markdown agent """

    HANDLE_PARSING_ERRORS: bool = True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.markdown = MarkdownTool()

    @ami_tool
    def list_md_files(self):
        """ Use this tool to list out the known markdown files """
        return agent_observation(str(self.markdown.md_files))

    @ami_tool
    def list_lists(self):
        """ Use this tool to list out the known lists in the markdown files """
        return agent_observation(str(self.markdown.lists))

    @ami_tool
    def add_to_list(self, list_name:str, item:str, index:int=-1):
        """ Use this tool to add an item to a list, do not supply an index unless it is the user's intention """
        md = self.markdown.add_to_list(list_name, item, index)
        if md:
            self.markdown.update_list(md)

        else:
            return agent_observation(f"List '{list_name}' not found! Try the `list_lists` tool, then retry the add_to_list tool.")

        return agent_observation(f"'{item}' successfully added to the '{list_name}' list!")


    @ami_tool
    def remove_from_list(self, list_name:str, item:str):
        """ Use this tool to remove an item to a list. Ensure to spell the list_name correctly. """
        md = self.markdown.remove_from_list(list_name, item)
        if md:
            self.markdown.update_list(md)

        else:
            return agent_observation(f"List '{list_name}' not found! Try the `list_lists` tool, then retry the remove_from_list tool.")

        return agent_observation(f"'{item}' successfully removed from the '{list_name}' list!")

    @ami_tool
    def edit_file(self, file: str):
        """ Use this tool to allow the human to edit a markdown file manually """

        if file not in self.markdown.md_files:
            return f"'{file}' not found!  Try the `list_md_files` tool!"

        markdown_file = self.markdown.get_markdown_file(file)

        if not markdown_file.exists():
            raise FileNotFoundError(f"HAI_TOOL@Markdown.edit_file(file='{file}'); file is not a file!")

        qr_code_url = f"http://{get_network_url()}/editor/{markdown_file.headspace_location}"
        qr_path = self.markdown.generate_qr_image(qr_code_url)

        self.dialog.visual = qr_path

        return agent_observation(f"Finished! Here is a QR code to use to edit the file. The URL is {qr_code_url}")

    @ami_tool
    def provide_list(self, list_name:str):
        """ Use this tool to provide a downloadable list to the human for their arbitrary purposes"""
        return "download tool has not implemented! do not use!"

