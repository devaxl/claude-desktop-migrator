# 🚀 Claude Desktop Session & Worktree Migrator

> **Zero-dependency tool to run multiple Claude Desktop accounts side-by-side on macOS and safely transfer Claude Code projects & chat histories between them.**

---

## 💡 The Problem
On macOS, Claude Desktop binds all your projects, worktrees, and chat histories to a single user account profile. If you have:
* A **personal account** (e.g. `personal@gmail.com`)
* A **work / team account** (e.g. `work@company.io`)
* Or switch to a new email

...you normally lose access to your past Claude Code desktop chats, or have to sign out and lose your session context. Furthermore, macOS normally prevents running two instances of Claude Desktop simultaneously.

---

## ✨ What This Tool Does
1. **Multi-Instance Support**: Lets you run 2, 3, or more separate Claude Desktop apps side-by-side on the same Mac without session collision or logouts.
2. **Safe Session Transfer**: Seamlessly links previous project chats (e.g. *ANinja*, *Backend*, *Stripe integrations*) to a new or secondary account.
3. **Zero Code Duplication**: Connects directly to your existing repositories. **Your physical code directories are never moved, modified, or duplicated.**
4. **Interactive Safety Checks**: Lists all detected profiles, previews every session to be copied, and **always asks for confirmation** before touching anything.

---

## 📦 Quick Installation

### Option 1: Quick Install (1 command)
Run this in your macOS Terminal:
```bash
curl -fsSL https://raw.githubusercontent.com/devaxl/claude-desktop-migrator/main/install.sh | bash
```
*(Or if sharing locally in your team repository:)*
```bash
chmod +x claude-migrate.py && ln -sf "$(pwd)/claude-migrate.py" /usr/local/bin/claude-migrate
```

Now you can run `claude-migrate` from any terminal!

---

## 🛠️ Usage

### 1. View all Claude profiles & saved sessions
```bash
claude-migrate --list
```
Displays all detected Claude Desktop profiles (`Claude`, `Claude-2`, `Claude-Work`), their active account IDs, and all saved chats categorized by project.

### 2. Interactive Migration (Recommended)
```bash
claude-migrate
```
The CLI will guide you interactively:
1. Choose the **Source** profile.
2. Choose the **Destination** profile.
3. Select which projects to move (e.g., `aninja`, `backend`, or `all`).
4. Enter any projects to exclude (e.g. `frontend`).
5. Review the migration summary.
6. Confirm with `y` to apply.

### 3. Automated Flag Mode
```bash
claude-migrate --src-profile Claude --dst-profile Claude-Work --include aninja,backend --exclude frontend --yes
```

---

## 🖥️ How to Run Multiple Claude Instances on macOS

To create a secondary Claude Desktop instance for another account:

1. Create a launcher script or alias:
   ```bash
   open -n -a "/Applications/Claude.app" --args --user-data-dir="$HOME/Library/Application Support/Claude-Work"
   ```
2. Or create a native macOS `.app` bundle:
   * Duplicate `/Applications/Claude.app` or use an AppleScript / Swift wrapper pointing `--user-data-dir` to your secondary profile folder.
   * Sign in with your work email.
   * Both instances will now run simultaneously with zero interference!

---

## 🤖 Using with AI Assistants (Antigravity / Cursor / Claude Code)

Paste this prompt to have your coding assistant manage your session migrations automatically:

```markdown
Please help me transfer my Claude Code desktop sessions between accounts using `claude-migrate`.
First, run `claude-migrate --list` and ask me which source and destination accounts to use, and which projects to include or exclude. Always verify and ask for my confirmation before copying any files.
```

---

## 🔒 Safety & Privacy
* **100% Local**: No network requests, telemetry, or external API calls. Everything runs locally on your Mac.
* **Standard Library Only**: Written entirely in pure Python 3 (`pathlib`, `json`, `shutil`). Requires zero pip packages.
