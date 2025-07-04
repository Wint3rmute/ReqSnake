"""MkDocs plugin for ReqSnake requirements management integration."""

from mkdocs.plugins import BasePlugin
from mkdocs.config import config_options

# TODO: useful?
# from typing import TYPE_CHECKING

from mkdocs.structure.files import File, Files, InclusionLevel
from mkdocs.config.defaults import MkDocsConfig
from mkdocs.plugins import get_plugin_logger

from mkdocs_reqsnake.reqsnake import (
    parse_requirements_from_files,
    validate_requirements,
    generate_requirement_page_content,
    generate_requirement_index_content,
)

logger = get_plugin_logger(__name__)


class ReqSnake(BasePlugin):  # type: ignore
    """MkDocs plugin for generating requirements pages from Markdown files."""

    config_scheme = (("enabled", config_options.Type(bool, default=True)),)

    def on_files(self, files: Files, /, *, config: MkDocsConfig) -> Files | None:
        """Generate requirements pages and index for MkDocs site from Markdown requirements."""
        if not self.config.get("enabled", True):
            return files
        # Extract file paths and content from MkDocs files
        file_data = []
        for file in files.documentation_pages():
            if file.src_uri is not None:
                file_data.append((file.src_uri, file.content_string))

        if not file_data:
            logger.info("No documentation files found to parse for requirements")
            return files

        try:
            # Parse requirements from all files
            parsed_requirements = parse_requirements_from_files(file_data)

            # Validate all requirements
            validate_requirements(parsed_requirements)

            logger.info(
                f"Found {len(parsed_requirements)} requirements across {len(file_data)} files"
            )

            # Generate individual requirement pages
            for parsed_req in parsed_requirements:
                req = parsed_req.requirement
                content = generate_requirement_page_content(parsed_req)

                files.append(
                    File.generated(
                        config,
                        src_uri=f"reqsnake/{req.req_id}.md",
                        content=content,
                        inclusion=InclusionLevel.INCLUDED,
                    )
                )

            # Generate index page
            index_content = generate_requirement_index_content(parsed_requirements)
            files.append(
                File.generated(
                    config,
                    src_uri="reqsnake/index.md",
                    content=index_content,
                    inclusion=InclusionLevel.INCLUDED,
                )
            )

            logger.info(
                f"Generated {len(parsed_requirements)} requirement pages and index"
            )

        except ValueError as e:
            logger.error(f"Error parsing requirements: {e}")
            # Don't fail the build, just log the error
            return files

        return files
