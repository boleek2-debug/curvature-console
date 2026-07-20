#!/usr/bin/env bash
set -euo pipefail

REPOSITORY_ROOT="$(
  cd "$(dirname "${BASH_SOURCE[0]}")/.."
  pwd
)"
LAUNCHER="$REPOSITORY_ROOT/scripts/launch_curvature_console.sh"
APPLICATIONS_DIRECTORY="$HOME/.local/share/applications"
DESKTOP_DIRECTORY="${XDG_DESKTOP_DIR:-$HOME/Desktop}"
APPLICATION_ENTRY="$APPLICATIONS_DIRECTORY/curvature-console.desktop"
DESKTOP_ENTRY="$DESKTOP_DIRECTORY/Curvature Console.desktop"

chmod +x "$LAUNCHER"
mkdir -p "$APPLICATIONS_DIRECTORY" "$DESKTOP_DIRECTORY"

cat > "$APPLICATION_ENTRY" <<EOF
[Desktop Entry]
Type=Application
Version=1.0
Name=Curvature Console
Comment=Project Curvature departmental coordination console
Exec=$LAUNCHER
Path=$REPOSITORY_ROOT
Icon=utilities-terminal
Terminal=false
Categories=Development;Utility;
StartupNotify=true
EOF

cp "$APPLICATION_ENTRY" "$DESKTOP_ENTRY"
chmod +x "$APPLICATION_ENTRY" "$DESKTOP_ENTRY"

if command -v update-desktop-database >/dev/null 2>&1; then
  update-desktop-database "$APPLICATIONS_DIRECTORY" || true
fi

printf 'Installed application menu entry:\n%s\n' "$APPLICATION_ENTRY"
printf 'Installed desktop shortcut:\n%s\n' "$DESKTOP_ENTRY"
