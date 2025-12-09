# How to Contribute to MetaKB

We welcome contributions! Please review the following guidelines before submitting a pull request or opening an issue.

---

## 🐛 Found a Bug?

- **Do not open a GitHub issue if the bug is a security vulnerability.**
- **Check if the bug has already been reported** by searching [existing issues](https://github.com/cancervariants/metakb/issues).
- If you're unable to find an open issue addressing the problem, [open a new one](https://github.com/cancervariants/metakb/issues/new?template=bug-report.yaml). Be sure to include a **title and clear description**, as much relevant information as possible, and a **code sample** or an **executable test case** demonstrating the expected behavior that is not occurring.
- If possible, use the relevant bug report template when submitting.

---

## 🔧 Fixing a Bug?

- Open a new GitHub pull request with your patch.
- Ensure your PR clearly describes the problem and the solution.
- Link to the relevant issue number, if applicable.
- Review the codebase to understand coding conventions and performance considerations.

---

## ✨ Proposing New Features

- Discuss your idea in the [mailing list](todo) before submitting code.
- Wait to create a GitHub issue until you've gathered positive feedback.
- GitHub issues are primarily for bugs and confirmed feature plans.

---

## 💬 Questions?

- Ask any questions about MetaKB in the [mailing list](todo).

---

## 📝 Contributing to Documentation?

- We'd love your help! Questions and suggestions can be shared in the [mailing list](todo).

---

## 🧹 Formatting & Linting

MetaKB uses automated tooling to maintain consistent code quality across the project.

### Frontend (`client/`)

- Uses **ESLint** and **Prettier** for TypeScript/React.
- Available scripts:

  ```bash
  pnpm --filter client lint         # Lint the project
  pnpm --filter client format       # Check formatting
  pnpm --filter client format:fix   # Auto-fix formatting issues
  ```

### Backend (`server/`)

- Uses **Ruff** for linting and formatting Python code.
- To manually check or fix:

  ```bash
  ruff check --fix server
  ruff format server
  ```

### Git Hooks (pre-commit)

- We use **Husky** and **lint-staged** to automatically lint and format staged files on commit
- Hooks run automatically after `pnpm install` via a `prepare` script
- To manually test:

  ```bash
  pnpm lint-staged
  ```

Thanks! ❤️

The MetaKB team
