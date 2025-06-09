# Contributing to CogniVerve-AI

Thank you for your interest in contributing to CogniVerve-AI! This document provides guidelines and information for contributors.

## 🌟 Ways to Contribute

- **🐛 Bug Reports**: Help us identify and fix issues
- **💡 Feature Requests**: Suggest new features and improvements
- **📝 Documentation**: Improve our docs and guides
- **💻 Code Contributions**: Submit bug fixes and new features
- **🎨 Design**: Improve UI/UX and visual design
- **🧪 Testing**: Help test new features and releases

## 🚀 Getting Started

### 1. Fork and Clone

```bash
# Fork the repository on GitHub
# Then clone your fork
git clone https://github.com/yourusername/cogniverve-ai.git
cd cogniverve-ai

# Add upstream remote
git remote add upstream https://github.com/original-owner/cogniverve-ai.git
```

### 2. Set Up Development Environment

```bash
# Install backend dependencies
cd backend
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Install frontend dependencies
cd ../frontend
npm install

# Set up pre-commit hooks
cd ..
pip install pre-commit
pre-commit install
```

### 3. Create a Branch

```bash
# Create a new branch for your feature/fix
git checkout -b feature/your-feature-name
# or
git checkout -b fix/issue-number
```

## 📋 Development Guidelines

### Code Style

#### Python (Backend)
- Follow [PEP 8](https://pep8.org/) style guide
- Use [Black](https://black.readthedocs.io/) for code formatting
- Use [isort](https://pycqa.github.io/isort/) for import sorting
- Use type hints where possible
- Maximum line length: 88 characters

```bash
# Format code
black .
isort .

# Check linting
flake8 .
mypy .
```

#### JavaScript/React (Frontend)
- Use [Prettier](https://prettier.io/) for code formatting
- Follow [ESLint](https://eslint.org/) rules
- Use functional components with hooks
- Use TypeScript for type safety

```bash
# Format code
npm run format

# Check linting
npm run lint
```

### Commit Messages

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
type(scope): description

feat(agents): add custom tool integration
fix(auth): resolve JWT token expiration issue
docs(api): update authentication endpoints
style(ui): improve dashboard layout
test(backend): add unit tests for task executor
```

Types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

### Testing

#### Backend Tests
```bash
cd backend
pytest tests/ -v --cov=app --cov-report=html
```

#### Frontend Tests
```bash
cd frontend
npm test
npm run test:coverage
```

### Documentation

- Update relevant documentation for any changes
- Add docstrings to new functions and classes
- Update API documentation for endpoint changes
- Include examples in documentation

## 🔄 Pull Request Process

### 1. Before Submitting

- [ ] Code follows style guidelines
- [ ] Tests pass locally
- [ ] Documentation is updated
- [ ] Commit messages follow convention
- [ ] Branch is up to date with main

```bash
# Update your branch
git fetch upstream
git rebase upstream/main
```

### 2. Submit Pull Request

1. Push your branch to your fork
2. Create a pull request on GitHub
3. Fill out the PR template completely
4. Link any related issues

### 3. PR Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] Tests pass
- [ ] New tests added
- [ ] Manual testing completed

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] No breaking changes (or documented)
```

### 4. Review Process

- Maintainers will review your PR
- Address any feedback promptly
- Keep discussions constructive
- Be patient - reviews take time

## 🐛 Bug Reports

Use the bug report template:

```markdown
**Bug Description**
Clear description of the bug

**Steps to Reproduce**
1. Go to '...'
2. Click on '...'
3. See error

**Expected Behavior**
What should happen

**Actual Behavior**
What actually happens

**Environment**
- OS: [e.g., Ubuntu 22.04]
- Browser: [e.g., Chrome 91]
- Version: [e.g., v1.0.0]

**Additional Context**
Screenshots, logs, etc.
```

## 💡 Feature Requests

Use the feature request template:

```markdown
**Feature Description**
Clear description of the feature

**Problem Statement**
What problem does this solve?

**Proposed Solution**
How should this work?

**Alternatives Considered**
Other solutions you've considered

**Additional Context**
Mockups, examples, etc.
```

## 🏗️ Architecture Guidelines

### Backend Structure
```
backend/
├── app/
│   ├── api/           # API routes
│   ├── core/          # Core functionality
│   ├── models/        # Data models
│   ├── agents/        # Agent logic
│   └── tools/         # Tool implementations
├── tests/             # Test files
└── requirements.txt   # Dependencies
```

### Frontend Structure
```
frontend/
├── src/
│   ├── components/    # React components
│   ├── services/      # API services
│   ├── contexts/      # React contexts
│   └── utils/         # Utility functions
├── public/            # Static assets
└── package.json       # Dependencies
```

### Database Guidelines

- Use Alembic for migrations
- Follow naming conventions
- Add proper indexes
- Document schema changes

### API Guidelines

- Follow RESTful principles
- Use proper HTTP status codes
- Include comprehensive error handling
- Document all endpoints
- Version APIs appropriately

## 🧪 Testing Guidelines

### Backend Testing
- Unit tests for business logic
- Integration tests for API endpoints
- Mock external dependencies
- Aim for >80% code coverage

### Frontend Testing
- Component unit tests
- Integration tests for user flows
- Mock API calls
- Test accessibility

### Test Structure
```python
# Backend test example
def test_create_agent():
    """Test agent creation with valid data."""
    # Arrange
    agent_data = {...}
    
    # Act
    response = client.post("/api/v1/agents", json=agent_data)
    
    # Assert
    assert response.status_code == 201
    assert response.json()["name"] == agent_data["name"]
```

## 📚 Documentation Guidelines

### Code Documentation
- Use clear, descriptive docstrings
- Include parameter and return type information
- Provide usage examples

```python
def create_agent(name: str, description: str) -> Agent:
    """Create a new AI agent.
    
    Args:
        name: The agent's name
        description: The agent's description
        
    Returns:
        The created agent instance
        
    Raises:
        ValueError: If name is empty
        
    Example:
        >>> agent = create_agent("Assistant", "Helpful AI")
        >>> print(agent.name)
        Assistant
    """
```

### User Documentation
- Write for your audience
- Include step-by-step instructions
- Use screenshots and examples
- Keep it up to date

## 🚀 Release Process

### Versioning
We use [Semantic Versioning](https://semver.org/):
- `MAJOR.MINOR.PATCH`
- Major: Breaking changes
- Minor: New features
- Patch: Bug fixes

### Release Checklist
- [ ] All tests pass
- [ ] Documentation updated
- [ ] CHANGELOG updated
- [ ] Version bumped
- [ ] Release notes prepared

## 🤝 Community Guidelines

### Code of Conduct
- Be respectful and inclusive
- Welcome newcomers
- Provide constructive feedback
- Focus on the issue, not the person

### Communication
- Use clear, professional language
- Be patient with responses
- Ask questions if unclear
- Share knowledge freely

## 🆘 Getting Help

- **Discord**: [Join our community](https://discord.gg/cogniverve)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/cogniverve-ai/discussions)
- **Email**: dev@cogniverve.ai

## 🏆 Recognition

Contributors will be:
- Listed in our README
- Mentioned in release notes
- Invited to contributor events
- Given special Discord roles

Thank you for contributing to CogniVerve-AI! 🎉

