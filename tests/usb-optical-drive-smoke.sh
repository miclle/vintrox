#!/usr/bin/env bash
# No optical drive, root access or network required for these safe smoke tests.
set -Eeuo pipefail

ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
SCRIPT="$ROOT/scripts/usb-optical-drive.sh"
TEMP="$(mktemp -d)"
trap 'rm -rf -- "$TEMP"' EXIT

bash -n "$SCRIPT"
bash "$SCRIPT" --help | grep -q 'mount-data'

mkdir -p "$TEMP/bin"
cat > "$TEMP/bin/dpkg-query" <<'MOCK'
#!/usr/bin/env bash
printf 'install ok installed'
MOCK
cat > "$TEMP/bin/apt-get" <<'MOCK'
#!/usr/bin/env bash
echo 'ERROR: apt-get should not run for installed packages' >&2
exit 10
MOCK
chmod +x "$TEMP/bin/dpkg-query" "$TEMP/bin/apt-get"

# When packages are installed, setup with or without GUI makes no changes.
for i in 1 2; do
  PATH="$TEMP/bin:$PATH" bash "$SCRIPT" setup | grep -q 'no changes made'
  PATH="$TEMP/bin:$PATH" bash "$SCRIPT" setup --with-gui | grep -q 'no changes made'
  bash "$SCRIPT" --mount-point "$TEMP/not-mounted" unmount-data | grep -q 'not mounted'
done

# Invalid devices and arguments must stop before any hardware command.
if bash "$SCRIPT" --device /dev/sr999 tracks >"$TEMP/out" 2>&1; then
  echo 'Expected non-existent drive to fail' >&2; exit 1
fi
if bash "$SCRIPT" --mount-point / unmount-data >"$TEMP/out" 2>&1; then
  echo 'Expected root mount point to be rejected' >&2; exit 1
fi
if bash "$SCRIPT" --made-up-option status >"$TEMP/out" 2>&1; then
  echo 'Expected unknown option to be rejected' >&2; exit 1
fi
printf 'USB optical smoke tests passed (hardware playback not exercised).\n'
