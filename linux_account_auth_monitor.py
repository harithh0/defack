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
xrdp_re = re.compile(r"xrdp-sesman\[\d+\]")

line = "Failed password for invalid user zencji from 10.0.0.212 port 56026 ssh2"
line2 = "Failed password for harith from 10.0.0.113 port 38188 ssh2"
line3 = "pam_unix(xrdp-sesman:auth): authentication failure; logname= uid=0 euid=0 tty=xrdp-sesman ruser= rhost=  user=tester"
failed_user_re = re.compile(
    r"Failed password for (?:invalid user )?(\w+) from ([\d.]+) port (\d+)")
accepted_user_re = re.compile(
    r"Accepted password for (\w+) from ([\d.]+) port (\d+)")
failed_xrdp_re = re.compile(
    r"pam_unix\(xrdp-sesman:auth\): authentication failure; logname=(\w*) uid=(\d*) euid=(\d*) tty=xrdp-sesman ruser=(\w*) rhost=(\w*)  user=(\w+)"
)

# match = failed_xrdp_re.search(line3)
# if match:
#     print("match")
#     print(match.group(6))
# os.remove(pid_file)

allowed_users = set("harith")
allowed_ips = set("10.0.0.113")


def extract_info(line: str, type: str) -> dict[str, str]:
    info = {}
    if type == "fail":
        match = failed_user_re.search(line)
    elif type == "accepted":
        match = accepted_user_re.search(line)
    else:
        return {}

    if match:
        info["user"] = match.group(1)
        info["ip"] = match.group(2)
        info["port"] = match.group(3)
        if type == "fail":
            info["is_invalid_user"] = "invalid user" in match.group(0)
    return info


def extract_info_xrdp(line: str, type: str) -> dict[str, str]:
    info = {}
    if type == "fail":
        match = failed_xrdp_re.search(line)
    else:
        return {}

    if match:
        info["user"] = match.group(6)
    return info


def main():
    for line in log.stdout:
        formatted_line = line.decode().strip()
        if sshd_re.search(formatted_line):
            if "Failed password for" in formatted_line:
                type = "fail"
            elif "Accepted password for" in formatted_line:
                type = "accepted"
            else:
                continue
            info = extract_info(formatted_line, type)
            print(info, type)

        elif xrdp_re.search(formatted_line):
            """
            Issuess running into:
                - auth.log not showing full data such as user's IP (leaves rhost= empty) and if username is invalid it will just leave user= empty
            xrdp.log shows full data but will have to read different log
            """
            if "authentication failure;" in formatted_line:
                type = "fail"
                info = extract_info_xrdp(formatted_line, type)
                print(info, type)


try:
    main()

# Guaranteed to always run even after excpetion occurs
finally:
    os.remove(pid_file)
