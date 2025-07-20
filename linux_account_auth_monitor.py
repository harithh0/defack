import os
import re
import subprocess
import sys

pid_file = "/tmp/log_watcher.pid"

if os.path.exists(pid_file):
    print("Another instance is already running.")
    sys.exit(1)

with open(pid_file, "w") as f:
    f.write(str(os.getpid()))

log = subprocess.Popen(
    ["tail", "-n0", "-F", "/var/log/auth.log"],
    stdout=subprocess.PIPE,
)

sshd_re = re.compile(r"sshd\[\d+\]")

line = "Failed password for invalid user zencji from 10.0.0.212 port 56026 ssh2"
line2 = "Failed password for harith from 10.0.0.113 port 38188 ssh2"
failed_user_re = re.compile(
    r"Failed password for (?:invalid user )?(\w+) from ([\d.]+) port (\d+)")
match = failed_user_re.search(line2)


def extract_info(line: str, type: str) -> dict[str, str]:
    info = {}
    if type == "fail":
        match = failed_user_re.search(line)
        if match:
            info["user"] = match.group(1)
            info["ip"] = match.group(2)
            info["port"] = match.group(3)

    return info


def main():
    for line in log.stdout:
        formatted_line = line.decode().strip()
        if sshd_re.search(formatted_line):
            if "Failed password for" in formatted_line:
                info = extract_info(formatted_line, "fail")
                print(info)


try:
    main()

# Guaranteed to always run even after excpetion occurs
finally:
    os.remove(pid_file)
