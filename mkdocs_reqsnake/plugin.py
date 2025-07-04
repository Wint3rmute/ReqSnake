from typing import override
from mkdocs.plugins import BasePlugin
from mkdocs.config import config_options

# TODO: useful?
# from typing import TYPE_CHECKING

from mkdocs.structure.files import File, Files, InclusionLevel
from mkdocs.config.defaults import MkDocsConfig
from mkdocs.plugins import get_plugin_logger

from mkdocs_reqsnake.reqsnake import Requirement, _parse_requirements_from_markdown

logger = get_plugin_logger(__name__)

class ReqSnake(BasePlugin):
    config_scheme = (
        ('enabled', config_options.Type(bool, default=True)),
    )

    @override
    def on_files(self, files: Files, /, *, config: MkDocsConfig) -> Files | None:
        requirements: list[Requirement] = []

        for file in files.documentation_pages():
            if file.src_dir is not None:
                requirements.extend(_parse_requirements_from_markdown(file.content_string))

        content = """# All Requirements
"""
        for requirement in requirements:
            files.append(File.generated(config, src_uri=f"./reqsnake/{requirement.req_id}.md", content=f"# {requirement.req_id} \n\n {requirement.description}", inclusion=InclusionLevel.INCLUDED))
            content+= f"""
# {requirement.req_id}
{requirement.description}
"""
        files.append(File.generated(config, src_uri="./reqsnake/index.md", content=content, inclusion=InclusionLevel.INCLUDED))

