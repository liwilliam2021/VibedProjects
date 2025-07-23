# Project Rules

## Build & Test Commands
- No specific build system detected - follow standard practices for each project type
- For individual projects: navigate to `basic_projects/<project_name>` before running commands
- Use language-specific test runners (e.g., `pytest` for Python, `npm test` for Node.js)
- Run single tests using framework-specific syntax (e.g., `pytest test_file.py::test_name`)

## Code Style & Formatting
- Follow language-specific style guides (PEP 8 for Python, ESLint for JavaScript, etc.)
- Use consistent indentation (2 spaces for JS/JSON, 4 spaces for Python)
- Keep line length under 100 characters
- Use meaningful variable and function names in camelCase or snake_case per language convention
- Add type hints where supported (TypeScript, Python 3.6+)

## Project Structure
- Each basic project should be self-contained in `basic_projects/<project_name>/`
- Include a README.md for each project explaining setup and usage
- Keep dependencies minimal and well-documented
- Use relative imports within projects, absolute imports for external libraries

## Error Handling & Best Practices
- Always handle errors gracefully with try-catch or equivalent
- Log errors with context information
- Validate inputs at function boundaries
- Write unit tests for core functionality
- Use version control best practices with clear commit messages
- Document any setup requirements or dependencies in project READMEs

## Multi-Project Repository
- Maintain independence between projects in `basic_projects/`
- Share common utilities only when absolutely necessary
- Test each project individually before committing changes