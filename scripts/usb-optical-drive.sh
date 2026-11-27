#!/usr/bin/env bash
# VINTROX USB optical drive helper for Debian 13 / Raspberry Pi OS.
# Safe defaults: no automatic disc ejection, playback, mounting or system changes
# other than explicit 'setup'.
set -Eeuo pipefail

PROG="${0##*/}"
COMMAND=""
DEVICE="${VINTROX_OPTICAL_DEVICE:-auto}"
MOUNT_POINT="${VINTROX_DISC_MOUNT:-/mnt/vintrox-disc}"
WITH_GUI=0

usage() {
  cat <<USAGE
Usage: $PROG [--device /dev/srN] [--mount-point PATH] [--with-gui] COMMAND

Commands:
  setup         Install missing command-line dependencies (idempotent).
                --with-gui also installs GNOME Disks / GVfs support.
  status        Show optical devices, USB topology and Pi power flags.
  logs          Show the last 120 kernel log lines (USB disconnects, resets).
  disc-info     Show CD/DVD information for the selected drive.
  tracks        Query audio-CD track table (does not rip or mount).
  play-cd       Play an audio CD using mpv (interactive; no sudo).
  play-dvd      Try to play a DVD-Video using mpv (interactive; no sudo).
  mount-data    Read-only mount of a data CD/DVD (idempotent).
  unmount-data  Unmount only this script's data disc mount (idempotent).
  eject         Eject / unload media.
  close         Request tray close (may not work on slot-loading drives).
  gui           Open GNOME Disks in a graphical session (no sudo).

Examples:
  bash scripts/usb-optical-drive.sh setup --with-gui
  bash scripts/usb-optical-drive.sh status
  bash scripts/usb-optical-drive.sh --device /dev/sr0 tracks
  bash scripts/usb-optical-drive.sh mount-data
  bash scripts/usb-optical-drive.sh unmount-data
USAGE
}

fail() { printf 'Error: %s\n' "$*" >&2; exit 1; }
note() { printf '[vintrox-optical] %s\n' "$*"; }
has() { command -v "$1" >/dev/null 2>&1; }
require_cmd() { has "$1" || fail "Missing '$1'; run: bash scripts/usb-optical-drive.sh setup"; }
as_root() {
  if (( EUID == 0 )); then "$@";
  else
    has sudo || fail "sudo is required: $*"
    sudo "$@"
  fi
}

while (( $# )); do
  case "$1" in
    --device)
      (( $# >= 2 )) || fail "--device needs /dev/srN"
      DEVICE="$2"; shift 2 ;;
    --mount-point)
      (( $# >= 2 )) || fail "--mount-point needs a directory"
      MOUNT_POINT="$2"; shift 2 ;;
    --with-gui) WITH_GUI=1; shift ;;
    -h|--help) usage; exit 0 ;;
    setup|status|logs|disc-info|tracks|play-cd|play-dvd|mount-data|unmount-data|eject|close|gui)
      [[ -z "$COMMAND" ]] || fail "Provide exactly one command"
      COMMAND="$1"; shift ;;
    *) fail "Unknown argument: $1 (see --help)" ;;
  esac
done
[[ -n "$COMMAND" ]] || { usage; exit 2; }
[[ "$COMMAND" == setup || "$WITH_GUI" -eq 0 ]] || fail "--with-gui is only valid with setup"

resolve_drive() {
  local candidate
  local -a drives=()
  if [[ "$DEVICE" == auto ]]; then
    for candidate in /dev/sr[0-9]*; do
      [[ -b "$candidate" ]] && drives+=("$candidate")
    done
    (( ${#drives[@]} )) || fail "No /dev/srN device found; check power and USB cable (use 'status')."
    (( ${#drives[@]} == 1 )) || fail "Multiple optical drives found: ${drives[*]}; pass --device /dev/srN."
    DEVICE="${drives[0]}"
  fi
  [[ "$DEVICE" =~ ^/dev/sr[0-9]+$ ]] || fail "Only /dev/srN optical devices are supported."
  [[ -b "$DEVICE" ]] || fail "Optical drive $DEVICE does not exist."
  note "Drive: $DEVICE"
}

setup() {
  has apt-get && has dpkg-query || fail "This setup targets Debian-based systems with apt/dpkg."
  local -a packages=(eject libcdio-utils cd-paranoia mpv usbutils)
  if (( WITH_GUI )); then
    packages+=(gnome-disk-utility gvfs gvfs-backends udisks2)
  fi
  local -a missing=()
  local pkg status
  for pkg in "${packages[@]}"; do
    status="$(dpkg-query -W -f='${Status}' "$pkg" 2>/dev/null || true)"
    [[ "$status" == 'install ok installed' ]] || missing+=("$pkg")
  done
  if (( ${#missing[@]} == 0 )); then
    note "All selected packages are installed; no changes made."
    return
  fi
  note "Installing missing packages: ${missing[*]}"
  as_root apt-get update
  as_root env DEBIAN_FRONTEND=noninteractive apt-get install -y "${missing[@]}"
}

status() {
  note 'USB devices:'
  if has lsusb; then lsusb; else note 'lsusb not installed; run setup.'; fi
  note 'Block devices:'
  if has lsblk; then lsblk -o NAME,TYPE,SIZE,MODEL,FSTYPE,MOUNTPOINTS; fi
  note 'Optical device nodes:'
  local found=0 dev
  for dev in /dev/sr[0-9]*; do
    if [[ -b "$dev" ]]; then ls -l "$dev"; found=1; fi
  done
  (( found )) || note 'No /dev/srN optical device currently detected.'
  if has vcgencmd; then
    note 'Pi power/throttling flags (0x0 does NOT rule out USB-device power shortage):'
    vcgencmd get_throttled || true
  fi
  note 'If devices repeatedly disappear, inspect logs and test stable auxiliary 5V power.'
}

check_mount_point() {
  [[ "$MOUNT_POINT" == /* && "$MOUNT_POINT" != / ]] || fail 'Mount point must be an absolute non-root path.'
  # Never allow arbitrary mounts or removals in system pseudo-filesystems.
  case "$MOUNT_POINT" in
    /dev|/dev/*|/proc|/proc/*|/sys|/sys/*|/run|/run/*) fail "Unsafe mount point: $MOUNT_POINT" ;;
  esac
}

mount_data() {
  resolve_drive
  require_cmd findmnt
  check_mount_point
  local existing source
  existing="$(findmnt -rn --source "$DEVICE" -o TARGET 2>/dev/null | head -n 1 || true)"
  if [[ -n "$existing" ]]; then
    note "Drive already mounted at $existing; no action needed."
    return
  fi
  source="$(findmnt -rn --mountpoint "$MOUNT_POINT" -o SOURCE 2>/dev/null || true)"
  [[ -z "$source" ]] || fail "$MOUNT_POINT is mounted from $source; refusing to replace it."
  as_root mkdir -p -- "$MOUNT_POINT"
  note "Mounting $DEVICE read-only at $MOUNT_POINT"
  as_root mount -o ro -- "$DEVICE" "$MOUNT_POINT" || fail 'Mount failed. For audio CDs use tracks/play-cd instead of mounting.'
}

unmount_data() {
  require_cmd findmnt
  check_mount_point
  local source
  source="$(findmnt -rn --mountpoint "$MOUNT_POINT" -o SOURCE 2>/dev/null || true)"
  if [[ -z "$source" ]]; then
    note "$MOUNT_POINT is not mounted; no action needed."
    return
  fi
  [[ "$source" =~ ^/dev/sr[0-9]+$ ]] || fail "$MOUNT_POINT uses $source (not an optical /dev/srN); refusing to unmount."
  note "Unmounting $MOUNT_POINT ($source)"
  as_root umount -- "$MOUNT_POINT"
}

case "$COMMAND" in
  setup) setup ;;
  status) status ;;
  logs) require_cmd journalctl; as_root journalctl -k -n 120 --no-pager ;;
  disc-info) resolve_drive; require_cmd cd-info; cd-info --cdrom-device="$DEVICE" ;;
  tracks) resolve_drive; require_cmd cd-paranoia; cd-paranoia -d "$DEVICE" -Q ;;
  play-cd) resolve_drive; require_cmd mpv; mpv --no-video --cdda-device="$DEVICE" cdda:// ;;
  play-dvd) resolve_drive; require_cmd mpv; mpv dvd:// --dvd-device="$DEVICE" ;;
  mount-data) mount_data ;;
  unmount-data) unmount_data ;;
  eject) resolve_drive; require_cmd eject; eject "$DEVICE" ;;
  close) resolve_drive; require_cmd eject; eject -t "$DEVICE" ;;
  gui)
    require_cmd gnome-disks
    [[ -n "${DISPLAY:-}${WAYLAND_DISPLAY:-}" ]] || fail 'No graphical session detected. Open a terminal within the desktop.'
    gnome-disks ;;
esac
