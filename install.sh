#!/usr/bin/env bash
set -e

INSTALL_DIR="${HOME}/.local/bin"
mkdir -p "${INSTALL_DIR}"

SCRIPT_TARGET="${INSTALL_DIR}/claude-migrate"

# Check if running locally or piped from curl
if [ -f "$(dirname "${BASH_SOURCE[0]}")/claude-migrate.py" ]; then
    SRC="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/claude-migrate.py"
    chmod +x "${SRC}"
    ln -sf "${SRC}" "${SCRIPT_TARGET}"
    echo "✓ Linked local claude-migrate to ${SCRIPT_TARGET}"
else
    echo "⬇️ Downloading claude-migrate from devaxl/claude-desktop-migrator..."
    curl -fsSL "https://raw.githubusercontent.com/devaxl/claude-desktop-migrator/main/claude-migrate.py" -o "${SCRIPT_TARGET}"
    chmod +x "${SCRIPT_TARGET}"
    echo "✓ Installed claude-migrate to ${SCRIPT_TARGET}"
fi

# Ensure ~/.local/bin is in PATH
if [[ ":$PATH:" != *":${HOME}/.local/bin:"* ]]; then
    SHELL_PROFILE="${HOME}/.zshrc"
    if [ ! -f "${SHELL_PROFILE}" ]; then
        SHELL_PROFILE="${HOME}/.bashrc"
    fi
    echo 'export PATH="${HOME}/.local/bin:$PATH"' >> "${SHELL_PROFILE}"
    echo "ℹ️ Added ~/.local/bin to PATH in ${SHELL_PROFILE}"
fi

echo ""
echo "🎉 Installation complete! Run:"
echo "   claude-migrate --list"
echo "   claude-migrate"
