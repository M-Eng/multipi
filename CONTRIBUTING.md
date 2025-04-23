# Contributing to MultiPi

First off, thank you for considering contributing to MultiPi! It's people like you that make open source such a great community.

We welcome many types of contributions, including bug reports, feature requests, documentation improvements, and code contributions.

## Ways to Contribute

### Reporting Bugs

If you encounter a bug, please open an issue on our GitHub repository. Before submitting, please check if a similar issue already exists.

When reporting a bug, please include:
*   Your operating system name and version.
*   Version of MultiPi you are using.
*   Steps to reproduce the bug.
*   Expected behavior.
*   Actual behavior, including any error messages and stack traces.

### Suggesting Enhancements

If you have an idea for a new feature or an improvement to an existing one, please open an issue on GitHub first to discuss it.

*   Provide a clear description of the enhancement.
*   Explain why this enhancement would be useful.
*   Include examples or mockups if possible.

### Improving Documentation

Improvements to the documentation (READMEs, guides in `docs/`, code comments, docstrings) are always welcome. You can submit a pull request with your changes.

### Submitting Pull Requests

Code contributions are highly appreciated. Here's how to submit a pull request:

1.  **Fork the Repository:** Create your own fork of the `M-Eng/multipi` repository on GitHub.
2.  **Clone Your Fork:** Clone your fork to your local machine.
    ```bash
    git clone https://github.com/YOUR_USERNAME/multipi.git
    cd multipi
    ```
3.  **Create a Branch:** Create a new branch for your changes.
    ```bash
    git checkout -b feature/your-feature-name # For features
    # or
    git checkout -b fix/issue-number-description # For bug fixes
    ```
4.  **Set Up Development Environment:** Follow the installation instructions in the main `README.md`. Consider installing development dependencies if a `requirements-dev.txt` exists.
5.  **Make Changes:** Implement your feature or fix the bug.
6.  **Code Style:** Please ensure your code adheres to standard Python style guidelines (PEP 8). We recommend using a formatter like Black and a linter like Flake8.
7.  **Add Tests:** If you add new functionality, please include tests. Ensure existing tests pass.
8.  **Commit Changes:** Commit your changes with a clear and concise message.
    ```bash
    git commit -m "feat: Add feature X"
    # or
    git commit -m "fix: Resolve issue #123 by doing Y"
    ```
9.  **Push to Your Fork:** Push your branch to your fork on GitHub.
    ```bash
    git push origin feature/your-feature-name
    ```
10. **Open a Pull Request:** Go to the original `M-Eng/multipi` repository on GitHub and open a pull request from your branch to the `main` branch (or the appropriate target branch).
    *   Provide a clear title and description for your pull request.
    *   Reference any relevant issues (e.g., "Closes #123").

## Questions?

If you have questions about contributing, feel free to open an issue. 