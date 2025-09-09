# Documentation

This directory contains comprehensive documentation for the Rooms integration.

## Files

- **`index.md`** - Documentation overview and quick start guide
- **`rationale.md`** - Design rationale and goals of the integration
- **`api.md`** - Complete API reference for entities, states, and attributes
- **`examples.md`** - Configuration examples and use cases
- **`developer.md`** - Architecture overview and development guide
- **`../CHANGELOG.md`** - Version history and release notes

## Building Documentation

To build a documentation website using MkDocs:

1. Install MkDocs and Material theme:
   ```bash
   pip install mkdocs mkdocs-material
   ```

2. Serve documentation locally:
   ```bash
   mkdocs serve
   ```

3. Build static site:
   ```bash
   mkdocs build
   ```

## Documentation Standards

- Use Markdown format
- Include code examples where relevant
- Provide both user and developer perspectives
- Keep examples practical and realistic
- Document API changes in changelog

## Contributing to Documentation

When adding new features:
1. Update relevant documentation files
2. Add examples for new functionality
3. Update API reference if entities/attributes change
4. Document breaking changes in changelog

## Style Guidelines

- Use clear, concise language
- Include headings and subheadings for navigation
- Use code blocks for commands and configuration
- Provide cross-references between documents
- Include table of contents for longer documents
