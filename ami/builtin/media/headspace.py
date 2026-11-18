from ami.headspace import Headspace, ami_tool

from .tool import Media as MediaTool


class Media(Headspace):
    """Built-in media headspace (thin / WIP)."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        try:
            self.media = MediaTool()
        except Exception:
            self.media = None

    @ami_tool
    def list_videos_from_youtube_creator(self, creator: str):
        """List known videos for a YouTube creator (stub until media backend lands)."""
        if self.media is None:
            return f"Media backend not configured. Asked for creator '{creator}'."
        result = self.media.get_youtube_videos(creator)
        return str(result) if result is not None else f"No videos found for '{creator}' (stub)."
