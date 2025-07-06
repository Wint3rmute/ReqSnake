"""MkDocs plugin for ReqSnake requirements management integration."""

from pathlib import Path
from typing import Optional

from mkdocs.plugins import BasePlugin
from mkdocs.config import config_options
from mkdocs.structure.files import File, Files, InclusionLevel
from mkdocs.config.defaults import MkDocsConfig
from mkdocs.plugins import get_plugin_logger

from .parser import parse_requirements_from_files
from .validator import validate_requirements
from .generator import (
    generate_requirement_page_content,
    generate_requirement_index_content,
)
from .exceptions import ReqSnakeError
from .utils import load_ignore_patterns, should_ignore_file

logger = get_plugin_logger(__name__)


class ReqSnake(BasePlugin):  # type: ignore[no-untyped-call,type-arg]
    """MkDocs plugin for generating requirements pages from Markdown files."""

    config_scheme = (("enabled", config_options.Type(bool, default=True)),)

    def on_files(self, files: Files, /, *, config: MkDocsConfig) -> Optional[Files]:
        """Generate requirements pages and index for MkDocs site from Markdown requirements."""
        if not self.config.get("enabled", True):
            return files

        # Load ignore patterns from .requirementsignore file
        try:
            config_dir = (
                Path(config.config_file_path).parent
                if config.config_file_path
                else Path.cwd()
            )
            ignore_patterns = load_ignore_patterns(config_dir)
        except (TypeError, AttributeError, OSError):
            # Handle mock objects or invalid paths in tests
            ignore_patterns = []

        # Extract file paths and content from MkDocs files
        file_data = []
        ignored_count = 0
        for file in files.documentation_pages():
            if file.src_uri is not None and file.content_string is not None:
                # Check if file should be ignored
                if should_ignore_file(file.src_uri, ignore_patterns):
                    ignored_count += 1
                    continue
                file_data.append((file.src_uri, file.content_string))

        if ignored_count > 0:
            logger.info(
                f"Ignored {ignored_count} files based on .requirementsignore patterns"
            )

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
                content = generate_requirement_page_content(
                    parsed_req, parsed_requirements
                )

                # Extract category from requirement ID for directory structure
                req_id = req.req_id
                if "-" in req_id:
                    category = req_id.rsplit("-", 1)[
                        0
                    ]  # e.g., "REQ-CORE-1" -> "REQ-CORE"
                else:
                    category = "OTHER"  # Fallback for non-standard IDs

                files.append(
                    File.generated(
                        config,
                        src_uri=f"reqsnake/{category}/{req.req_id}.md",
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

        except ReqSnakeError as e:
            logger.error(f"Error parsing requirements: {e}")
            # Don't fail the build, just log the error
            return files

        return files
