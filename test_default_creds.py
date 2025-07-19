import ftplib
import os
import smtplib
import socket
import telnetlib
import time

import paramiko
import pexpect


class TestHost:

    def __init__(self, host):
        self.host = host

    def SSHLogin(self, username, password, port=22):
        try:
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(self.host,
                        port=port,
                        username=username,
                        password=password)
            ssh_session = ssh.get_transport().open_session()
            if ssh_session.active:
                print(
                    f"SSH login successful on {self.host}:{port} with ({username}, {password})"
                )
            ssh.close()
        except OSError:
            print(f"Target port {port} is closed")
        except:
            print(f"SSH login failed ({username}, {password})")

    def TelnetLogin(self, username, password, port=23):
        try:
            tn = telnetlib.Telnet(self.host, port, timeout=10)
        except OSError:
            print(f"Target port {port} is closed")
            return
        tn.read_until(b"login:")
        tn.write((username + "\n").encode("utf-8"))
        tn.read_until(b"Password:")
        tn.write((password + "\n").encode("utf-8"))

        failed_login_status = tn.read_until(b"Login incorrect", timeout=5)

        # INFO: 'failed_login_status' can either return empty string with ' \r\n' (usually when its passed the timeout time) or 'Login incorrect' somewhere in the line
        if (b"Login incorrect" in failed_login_status
                or failed_login_status == " \r\n".encode("ascii")):
            print(f"Telnet login failed ({username}, {password})")
        else:
            print(f"Telnet successful ({username}, {password})")
            tn.write(b"exit")

        # gracefully 'FIN' close the connection
        tn.close()

    def smtpLogin(self, username, password, port=2525):
        smtp = smtplib.SMTP(self.host, port, timeout=10)
        smtp.ehlo()  # Step 1: Say hello
        login_status = smtp.login(username, password)  # Step 4: Login
        print(login_status)

    def ftpLogin(self, username, password, port=21):
        try:
            ftp = ftplib.FTP(self.host, timeout=10)
            loggin_status = ftp.login(username, password)
            print(loggin_status)
            if loggin_status == "230 Login successful.":
                print(f"FTP successful ({username}, {password})")
            else:
                print(f"FTP login failed ({username}, {password})")

        # NOTE: 'TimeoutError' is sublcass of 'OSError' so put it above parent class if doing multiple try/except or do isinstance(e, TimeoutError) ...
        except TimeoutError:
            print("timeout error something went wrong")
        except OSError:
            print(f"Target port {port} is closed")
            return


host = "10.0.0.212"
sshport = 22
telnetport = 23
target_host = TestHost(host)

# target_host.ftpLogin("kali", "kali")
target_host.smtpLogin("kali", "kali")

time.sleep(100)
with open(os.path.join(os.path.dirname(__file__), "defaults.txt"), "r") as f:
    for line in f:
        vals = line.split()
        username = vals[0].strip()
        password = vals[1].strip()
        target_host.SSHLogin(username, password)
        target_host.TelnetLogin(username, password)
