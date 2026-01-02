# Contributing to Cloud HVAC Operations Lab

We welcome contributions to the Cloud HVAC Operations Lab! To ensure a smooth and collaborative development process, please follow these guidelines.

## Getting Started

Refer to the [README.md](README.md) for project setup instructions.

## Branching Strategy

We use a **Trunk-Based Development** model. This means:
*   All development happens on short-lived feature branches.
*   Feature branches are merged into `main` as quickly as possible (ideally within a day).
*   The `main` branch is always deployable.

### Branch Naming Convention

Use the following prefixes for your branch names:
*   `feature/ISSUE-ID-short-description` for new features.
*   `bugfix/ISSUE-ID-short-description` for bug fixes.
*   `hotfix/ISSUE-ID-short-description` for urgent production fixes.
*   `chore/task-description` for routine tasks, maintenance, or build process changes.
*   `docs/doc-update` for documentation updates.

Example: `feature/US-1-temp-sensor-data-gen`

## Commit Message Convention

We follow the [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/) specification. This helps in generating changelogs and understanding the purpose of each commit.

**Format:**

```
<type>(<scope>): <description>

[optional body]

[optional footer(s)]
```

**Types:**
*   `feat`: A new feature
*   `fix`: A bug fix
*   `docs`: Documentation only changes
*   `style`: Changes that do not affect the meaning of the code (white-space, formatting, missing semicolons, etc.)
*   `refactor`: A code change that neither fixes a bug nor adds a feature
*   `perf`: A code change that improves performance
*   `test`: Adding missing tests or correcting existing tests
*   `build`: Changes that affect the build system or external dependencies (example scopes: gulp, broccoli, npm)
*   `ci`: Changes to our CI configuration files and scripts (example scopes: Travis, Circle, BrowserStack, SauceLabs)
*   `chore`: Other changes that don't modify src or test files

**Scope:**
Refers to the part of the codebase affected (e.g., `sensor-service`, `monitoring-service`, `ci`, `docs`, `shared`).

**Examples:**
*   `feat(sensor-service): add simulated temperature data generation`
*   `fix(monitoring-service): resolve high temp alert false positives`
*   `docs(runbook): update high-temp-alarm runbook`

## Development Workflow

1.  **Fork and Clone**: Fork the repository and clone it to your local machine.
2.  **Create a Branch**: Create a new branch from `main` using the naming convention.
3.  **Develop**: Write your code, ensuring it adheres to the project's coding standards.
4.  **Test**: Run unit, integration, and if applicable, E2E tests. Ensure all tests pass.
5.  **Commit**: Commit your changes using the Conventional Commits convention.
6.  **Push**: Push your branch to your fork.
7.  **Create Pull Request (PR)**: Open a PR against the `main` branch of the upstream repository.
    *   Provide a clear title and description for your PR.
    *   Reference any relevant issues (e.g., `Closes #123`).
8.  **Code Review**: Your PR will be reviewed by at least one team member. Address any feedback promptly.
9.  **Merge**: Once approved, your PR will be merged into `main`.

## Definition of Done (DoD)

For a User Story or Task to be considered 'Done', the following criteria must be met:
*   Code reviewed and approved by at least one peer.
*   Unit tests passed with a minimum of 80% code coverage.
*   Integration tests passed, verifying inter-service communication.
*   Feature tested manually and verified against acceptance criteria.
*   All relevant documentation (e.g., API docs, README updates, runbook snippets) updated.
*   Deployed to a staging or development environment for further validation.
*   No critical or major bugs identified in testing.
*   Acceptance criteria for the User Story are fully met.

## Code Style

*   **Python**: Follow [PEP 8](https://www.python.org/dev/peps/pep-0008/) guidelines. We use `flake8` for linting and `black` for formatting.
*   **JavaScript/TypeScript**: Follow ESLint rules (if applicable). We use `prettier` for formatting.

## Questions?

If you have any questions or need assistance, please reach out to the project team.
