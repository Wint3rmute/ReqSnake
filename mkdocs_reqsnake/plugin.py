"""MkDocs plugin for ReqSnake requirements management integration."""

from pathlib import Path

from mkdocs.config import config_options
from mkdocs.config.defaults import MkDocsConfig
from mkdocs.plugins import BasePlugin, get_plugin_logger
from mkdocs.structure import StructureItem
from mkdocs.structure.files import File, Files, InclusionLevel
from mkdocs.structure.nav import Navigation, Section
from mkdocs.structure.pages import Page

from .generator import (
    generate_requirement_index_content,
    generate_requirement_page_content,
)
from .parser import parse_requirements_from_files
from .utils import load_ignore_patterns, should_ignore_file
from .validator import validate_requirements

logger = get_plugin_logger(__name__)


class ReqSnake(BasePlugin):  # type: ignore[no-untyped-call,type-arg]
    """MkDocs plugin for generating requirements pages from Markdown files."""

    config_scheme = (("enabled", config_options.Type(bool, default=True)),)

    def on_nav(
        self, nav: Navigation, /, *, config: MkDocsConfig, files: Files
    ) -> Navigation | None:
        """Generate requirements pages and inject them into navigation."""
        if not self.config.get("enabled", True):
            return nav

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
            return nav

        # Parse requirements from all files
        parsed_requirements = parse_requirements_from_files(file_data)

        # Validate all requirements
        validate_requirements(parsed_requirements)

        logger.info(
            f"Found {len(parsed_requirements)} requirements across "
            f"{len(file_data)} files"
        )

        # Generate individual requirement pages
        generated_files = []
        for parsed_req in parsed_requirements:
            req = parsed_req.requirement
            content = generate_requirement_page_content(parsed_req, parsed_requirements)

            # Extract category from requirement ID for directory structure
            req_id = req.req_id
            category = req_id.rsplit("-", 1)[0] if "-" in req_id else "OTHER"

            req_file = File.generated(
                config,
                src_uri=f"reqsnake/{category}/{req.req_id}.md",
                content=content,
                inclusion=InclusionLevel.INCLUDED,
            )
            files.append(req_file)
            generated_files.append(req_file)

        # Generate index page
        index_content = generate_requirement_index_content(parsed_requirements)
        index_file = File.generated(
            config,
            src_uri="reqsnake/index.md",
            content=index_content,
            inclusion=InclusionLevel.INCLUDED,
        )
        files.append(index_file)

        logger.info(f"Generated {len(parsed_requirements)} requirement pages and index")

        # Group requirement files by category for navigation
        categories: dict[str, list[File]] = {}
        for req_file in generated_files:
            # Extract category from path: reqsnake/REQ-CORE/REQ-CORE-1.md -> REQ-CORE
            path_parts = req_file.src_uri.split("/")
            if len(path_parts) >= 3:
                category = path_parts[1]
                if category not in categories:
                    categories[category] = []
                categories[category].append(req_file)

        # Create the main Requirements section
        requirements_children: list[StructureItem] = []

        # Add the index page first
        requirements_index = Page("Overview", index_file, config)
        requirements_children.append(requirements_index)

        # Add category subsections
        for category, cat_files in sorted(categories.items()):
            category_children: list[StructureItem] = []

            # Sort files by requirement ID for consistent ordering
            sorted_files = sorted(cat_files, key=lambda f: f.src_uri.split("/")[-1])

            for req_file in sorted_files:
                # Extract requirement ID from filename: REQ-CORE-1.md -> REQ-CORE-1
                req_id = req_file.src_uri.split("/")[-1].replace(".md", "")
                req_page = Page(req_id, req_file, config)
                category_children.append(req_page)

            # Create category section
            category_section = Section(category, category_children)
            requirements_children.append(category_section)

        # Create the main Requirements section
        requirements_section = Section("Requirements", requirements_children)

        # Add the Requirements section to navigation
        nav.items.append(requirements_section)

        logger.info(
            f"Injected ReqSnake navigation with {len(categories)} categories "
            f"and {len(generated_files)} pages"
        )

        return nav
