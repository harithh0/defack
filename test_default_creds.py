import ftplib
import os
import smtplib
import telnetlib

import paramiko


class TestHost:

    def __init__(self, host):
        self.host = host

    def sshLogin(self, username, password, port=22):
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

    def telnetLogin(self, username, password, port=23):
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
        # WARN: this was only tested against 'smtp4dev' (no tls) via docker on port 2525
        try:
            smtp = smtplib.SMTP(self.host, port, timeout=10)
        except TimeoutError:
            print("SMTP timeout error something went wrong")
            return
        smtp.ehlo()
        login_status = smtp.login(username, password)
        if login_status == 235:
            print(f"SMTP successful ({username}, {password})")

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
            print(f"FTP: Target port {port} is closed")
            return


target_host = TestHost("10.0.0.212")

creds = []
with open(os.path.join(os.path.dirname(__file__), "defaults.txt"), "r") as f:
    for line in f:
        vals = line.split()
        username = vals[0].strip()
        password = vals[1].strip()
        creds.append((username, password))

for cred in creds:
    print(f"Testing creds: {cred}")
    target_host.sshLogin(cred[0], cred[1])
    target_host.telnetLogin(cred[0], cred[1])
    target_host.ftpLogin(cred[0], cred[1])
