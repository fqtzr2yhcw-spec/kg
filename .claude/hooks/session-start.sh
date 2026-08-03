#!/bin/bash
# SessionStart hook: provision the TypeScript language server for the
# `typescript-lsp@claude-plugins-official` plugin.
#
# The plugin wraps the `typescript-language-server` binary; without it on
# PATH the plugin loads but provides no diagnostics/navigation. Cloud (web)
# sessions start from a fresh container, so we install the binary here.
set -euo pipefail

# Only run in Claude Code on the web / remote sessions. Local machines are
# expected to manage their own toolchain.
if [ "${CLAUDE_CODE_REMOTE:-}" != "true" ]; then
  exit 0
fi

# Idempotent: only install when the binary is missing. `typescript` is
# installed alongside so the language server always has a compiler to load.
if ! command -v typescript-language-server >/dev/null 2>&1; then
  echo "session-start: installing typescript-language-server..." >&2
  if npm install -g typescript-language-server typescript >/dev/null 2>&1; then
    echo "session-start: typescript-language-server installed." >&2
  else
    # Non-fatal: don't block the session if the registry is unreachable.
    echo "session-start: warning: could not install typescript-language-server (network policy?)." >&2
  fi
fi

exit 0
