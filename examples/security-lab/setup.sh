#!/usr/bin/env bash
# Provision only a NEW local teaching keystore; never run against a robot.
set -euo pipefail
if [[ "${1:-}" == "--help" ]]; then
  echo 'Usage: bash examples/security-lab/setup.sh /absolute/new-lab-directory'
  exit 0
fi
if [[ $# -ne 1 || "$1" != /* ]]; then
  echo 'Supply one absolute path for a new lab directory.' >&2
  exit 2
fi
lab_directory="$1"
lab_source_directory="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
if [[ -e "$lab_directory" || -L "$lab_directory" ]]; then
  echo 'Refusing to overwrite an existing lab path.' >&2
  exit 2
fi
command -v ros2 >/dev/null || { echo 'Source an installed ROS 2 Jazzy environment first.' >&2; exit 2; }
if [[ "${ROS_DISTRO:-}" != jazzy ]]; then
  echo 'This exercise targets Jazzy; use a separately validated recipe for other distributions.' >&2
  exit 2
fi
export RMW_IMPLEMENTATION=rmw_fastrtps_cpp
export ROS_DOMAIN_ID=42
export ROS_AUTOMATIC_DISCOVERY_RANGE=LOCALHOST
unset ROS_SECURITY_ENCLAVE_OVERRIDE
for package in sros2 demo_nodes_cpp rmw_fastrtps_cpp; do
  ros2 pkg prefix "$package" >/dev/null
done
python3 "$lab_source_directory/check_policy.py" --output "$(mktemp -d /tmp/ros2-policy-check.XXXXXX)"
umask 077
# Atomic directory creation also rejects a path that appeared after the preflight check.
mkdir -- "$lab_directory"
ros2 security create_keystore "$lab_directory/keystore"
for role in talker listener; do
  ros2 security create_enclave "$lab_directory/keystore" "/security_lab/$role"
  ros2 security create_permission "$lab_directory/keystore" "/security_lab/$role" "$lab_source_directory/policy.xml"
done
python3 "$lab_source_directory/capture_versions.py" > "$lab_directory/versions.json"
printf 'Created teaching keystore in %s/keystore\n' "$lab_directory"
printf '%s\n' 'Keep this provisioning directory private. Run the documented checks before deployment.'
