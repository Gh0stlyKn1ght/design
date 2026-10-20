#!/usr/bin/env python3
"""Capture package versions and selected non-secret ROS settings; never read keys."""
import datetime
import json
import os
import platform
import shutil
import subprocess

def command(args):
    if not shutil.which(args[0]): return {'available':False}
    result=subprocess.run(args,text=True,capture_output=True,timeout=30)
    return {'returncode':result.returncode,'stdout':result.stdout.strip(),'stderr':result.stderr.strip()}

distro=os.environ.get('ROS_DISTRO','unknown')
packages=[f'ros-{distro}-*']
print(json.dumps({
    'captured_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'architecture':platform.machine(),
    'kernel':platform.release(),
    'os_release':command(['cat','/etc/os-release']),
    'python':platform.python_version(),
    'ros_settings':{name:os.environ.get(name) for name in ['ROS_DISTRO','RMW_IMPLEMENTATION','ROS_DOMAIN_ID','ROS_AUTOMATIC_DISCOVERY_RANGE']},
    'packages':command(['dpkg-query','-W','-f=${Package}\t${Version}\n',*packages]),
    'openssl':command(['openssl','version']),
    'purpose':'Environment inventory; consult the separate runtime result record.',
},indent=2))
