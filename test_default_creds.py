import os
import socket
import telnetlib

import paramiko
import pexpect


def SSHLogin(host, port, username, password):
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(host, port=port, username=username, password=password)
        ssh_session = ssh.get_transport().open_session()
        if ssh_session.active:
            print(
                "SSH login successful on %s:%s with username %s and password %s"
                % (host, port, username, password))
        ssh.close()
    except:
        print("SSH login failed %s %s" % (username, password))


def TelnetLogin(host, port, username, password):
    tn = telnetlib.Telnet(host, port, timeout=10)

    tn.read_until(b"login:")
    tn.write((username + "\n").encode("utf-8"))
    tn.read_until(b"Password:")
    tn.write((password + "\n").encode("utf-8"))

    failed_login_status = tn.read_until(b"Login incorrect", timeout=5)

    # INFO: 'failed_login_status' can either return empty string with ' \r\n' (usually when its passed the timeout time) or 'Login incorrect' somewhere in the line
    if (b"Login incorrect" in failed_login_status
            or failed_login_status == " \r\n".encode("ascii")):
        print(f"Telnet login failed {username}:{password}")
    else:
        print(f"Telnet successful {username}:{password}")
        tn.write(b"exit")

    # gracefully 'FIN' close the connection
    tn.close()


host = "10.0.0.212"
sshport = 22
telnetport = 23
with open(os.path.join(os.path.dirname(__file__), "defaults.txt"), "r") as f:
    for line in f:
        vals = line.split()
        username = vals[0].strip()
        password = vals[1].strip()
        # SSHLogin(host, sshport, username, password)
        TelnetLogin(host, telnetport, username, password)
