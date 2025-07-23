# Project Rules

## Build & Test Commands
- No package manager detected - use standard commands for your language/framework
- For single test: Use language-specific test runner with file/function targeting
- Check for Makefile, scripts/, or package.json for project-specific commands

## Code Style & Conventions
- Use consistent indentation (2 or 4 spaces, no tabs)
- Follow language-standard naming conventions (camelCase, snake_case, PascalCase as appropriate)
- Group imports: standard library first, third-party second, local modules last
- Add type hints/annotations where supported by the language
- Use descriptive variable and function names that explain intent
- Keep functions small and focused on single responsibility

## Error Handling & Quality
- Handle errors explicitly - no silent failures
- Use proper exception types and meaningful error messages
- Add docstrings/comments for public APIs and complex logic
- Validate inputs at function boundaries
- Use linting tools and fix all warnings before committing

## Project Standards
- Follow existing code patterns and file organization in the repository
- Write tests for new functionality and bug fixes
- Keep dependencies minimal and well-justified
- Use version control best practices with clear, descriptive commit messages