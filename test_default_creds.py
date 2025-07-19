import argparse
import ftplib
import ipaddress
import os
import smtplib
import sys
import telnetlib
import time
from typing import List, TextIO

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


def get_creds_from_file(file_object: TextIO) -> List[str]:
    # TODO: Validate file in right format
    creds = file_object.read()
    if creds.strip() == "":
        return []
    creds_list = creds.split("\n")
    # returns list without last index as is empty string
    return creds_list[:len(creds_list) - 1]


def main():
    parser = argparse.ArgumentParser(description="Default credential tester")
    parser.add_argument("-a",
                        "--all",
                        action="store_true",
                        help="Include all services")
    parser.add_argument("-f",
                        "--ftp",
                        action="store_true",
                        help="Enable FTP service")
    parser.add_argument("-s",
                        "--ssh",
                        action="store_true",
                        help="Enable SSH service")
    parser.add_argument("-m",
                        "--smtp",
                        action="store_true",
                        help="Enable SMTP service")
    parser.add_argument("-t",
                        "--tel",
                        action="store_true",
                        help="Enable Telnet service")
    parser.add_argument("-i",
                        "--ignore-fails",
                        action="store_true",
                        help="Ignore failed loggin creds")
    parser.add_argument("-x",
                        "--text-file",
                        help="Optional path of text file of credentials")
    parser.add_argument("target", help="Target host to test credentials")
    args = parser.parse_args()
    print(args)

    # Check correct usage
    list_of_args = [args.ftp, args.ssh, args.smtp, args.tel]

    if not args.all and not any(list_of_args):
        print("Incorrect usage, please specify which service")
        return
    if args.all and any(list_of_args):
        print("Incorrect usage, using all with specific args")
        return

    # Check correct IP
    try:
        ip_addr = ipaddress.ip_address(args.target)
        print(ip_addr.version)
    except ValueError:
        print("enter correct ip address")

    creds = []

    # Check correct file
    if args.text_file:
        if os.path.exists(args.text_file):
            if os.path.splitext(args.text_file)[1] == ".txt":
                with open(args.text_file, "r") as f:
                    creds = get_creds_from_file(f)
            else:
                print("Must be .txt file")
                return
        else:
            print("Text file does not exist")
            return
    else:
        with open(os.path.join(os.path.dirname(__file__), "defaults.txt"),
                  "r") as f:
            creds = get_creds_from_file(f)

    target_host = TestHost(args.target)

    # Make sure creds list is not empty
    print(creds)
    if creds:
        for cred in creds:
            print(f"Testing creds: {cred}")
            username = cred.split()[0].strip()
            password = cred.split()[1].strip()
            if args.all:
                target_host.sshLogin(username, password)
                target_host.telnetLogin(username, password)
                target_host.ftpLogin(username, password)
                target_host.smtpLogin(username, password)
            else:
                if args.ftp:
                    target_host.ftpLogin(username, password)
                if args.ssh:
                    target_host.sshLogin(username, password)
                if args.smtp:
                    target_host.smtpLogin(username, password)
                if args.tel:
                    target_host.telnetLogin(username, password)
    else:
        print("Empty file provided")
        return


main()
