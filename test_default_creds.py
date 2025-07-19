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
from paramiko.ssh_exception import AuthenticationException, SSHException
from rich.console import Console

console = Console()


class TestHost:

    def __init__(self, host):
        self.host = host

    def sshLogin(self, username, password, ignore_failed, port=22):
        try:
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(self.host,
                        port=port,
                        username=username,
                        password=password)
            ssh_session = ssh.get_transport().open_session()
            if ssh_session.active:
                console.print(
                    f"[+] SSH login successful ({username}, {password})",
                    style="bold green",
                )
            ssh.close()
        except OSError:
            console.print(f"[!] ERROR: SSH port {port} is closed",
                          style="bold red")
        except AuthenticationException:
            if not ignore_failed:
                console.print("[-] SSH login failed", style="bold yellow")
        except SSHException:
            console.print(f"[!] ERROR: SSH network error", style="bold red")

    def telnetLogin(self, username, password, ignore_failed, port=23):
        try:
            tn = telnetlib.Telnet(self.host, port)
        except OSError:
            console.print(f"[!] ERROR: TELNET port {port} is closed",
                          style="bold red")
            return
        tn.read_until(b"login:")
        tn.write((username + "\n").encode("utf-8"))
        tn.read_until(b"Password:")
        tn.write((password + "\n").encode("utf-8"))

        # keep timeout since if after timeout sill can't read, then its correct
        failed_login_status = tn.read_until(b"Login incorrect", timeout=10)

        # INFO: 'failed_login_status' can either return empty string with ' \r\n' (usually when its passed the timeout time) or 'Login incorrect' somewhere in the line
        if (b"Login incorrect" in failed_login_status
                or failed_login_status == " \r\n".encode("ascii")):
            if not ignore_failed:
                console.print("[-] Telnet login failed", style="bold yellow")
        else:
            console.print(f"[+] Telnet successful ({username}, {password})",
                          style="bold green")
            tn.write(b"exit")

        # gracefully 'FIN' close the connection
        tn.close()

    def smtpLogin(self, username, password, ignore_failed, port=2525):
        # WARN: this was only tested against 'smtp4dev' (no tls) via docker on port 2525
        try:
            smtp = smtplib.SMTP(self.host, port, timeout=10)
        except TimeoutError:
            console.print("[!] ERROR: SMTP timeout error something went wrong",
                          style="bold red")
            return
        smtp.ehlo()
        login_status = smtp.login(username, password)
        if login_status == 235:
            console.print(f"[+] SMTP successful ({username}, {password})",
                          style="bold green")
        else:
            if not ignore_failed:
                console.print("[-] SMTP login failed", style="bold yellow")

    def ftpLogin(self, username, password, ignore_failed, port=21):
        try:
            ftp = ftplib.FTP(self.host, timeout=10)
            try:
                login_status = ftp.login(username, password)
                if login_status == "230 Login successful.":
                    console.print(
                        f"[+] FTP successful ({username}, {password})",
                        style="bold green",
                    )
                else:
                    if not ignore_failed:
                        console.print("[-] FTP login failed",
                                      style="bold yellow")
            except ftplib.error_perm:
                if not ignore_failed:
                    console.print("[-] FTP login failed", style="bold yellow")

        # NOTE: 'TimeoutError' is sublcass of 'OSError' so put it above parent class if doing multiple try/except or do isinstance(e, TimeoutError) ...
        except TimeoutError:
            console.print("[!] ERROR: timeout error something went wrong",
                          style="bold red")
        except OSError:
            console.print(f"[!] ERROR FTP port {port} is closed",
                          style="bold red")
            return


def get_creds_from_file(file_object: TextIO) -> List[str]:
    # TODO: Validate file in right format
    creds = file_object.read()
    if creds.strip() == "":
        return []
    creds_list = creds.split("\n")
    # returns list without last index as is empty string
    return creds_list[:len(creds_list) - 1]


def try_cred(target_host, username, password, args):
    # help functions
    def try_ssh(username, password, args):
        with console.status(
                f"[cyan] SSH Trying {username}, {password}...[/cyan]",
                spinner="dots",
        ):
            target_host.sshLogin(username, password, args.ignore_failed)

    def try_telnet(username, password, args):
        with console.status(
                f"[cyan] TELNET Trying {username}, {password}...[/cyan]",
                spinner="dots",
        ):
            target_host.telnetLogin(username, password, args.ignore_failed)

    def try_ftp(username, password, args):
        with console.status(
                f"[cyan] FTP Trying {username}, {password}...[/cyan]",
                spinner="dots",
        ):
            target_host.ftpLogin(username, password, args.ignore_failed)

    def try_smtp(username, password, args):
        with console.status(
                f"[cyan] SMTP Trying {username}, {password}...[/cyan]",
                spinner="dots",
        ):
            target_host.smtpLogin(username, password, args.ignore_failed)

    if args.all:
        try_ssh(username, password, args)
        try_telnet(username, password, args)
        try_ftp(username, password, args)
        try_smtp(username, password, args)
    else:
        if args.ftp:
            try_ftp(username, password, args)
        if args.ssh:
            try_ssh(username, password, args)
        if args.smtp:
            try_smtp(username, password, args)
        if args.tel:
            try_telnet(username, password, args)


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
                        "--ignore-failed",
                        action="store_true",
                        help="Ignore failed loggin creds")
    parser.add_argument("-x",
                        "--text-file",
                        help="Optional path of text file of credentials")
    parser.add_argument("target", help="Target host to test credentials")
    args = parser.parse_args()

    # Check correct usage
    list_of_args = [args.ftp, args.ssh, args.smtp, args.tel]

    if not args.all and not any(list_of_args):
        console.print(
            "[!] ERROR: Incorrect usage, please specify which service",
            style="bold red")
        return
    if args.all and any(list_of_args):
        console.print(
            "[!] ERROR: Incorrect usage, using all with specific args",
            style="bold red")
        return

    # Check correct IP
    try:
        ip_addr = ipaddress.ip_address(args.target)
    except ValueError:
        console.print("[!] ERROR: Enter correct IP address", style="bold red")

    target_host = TestHost(args.target)

    # Check correct file
    if args.text_file:
        if os.path.exists(args.text_file):
            if os.path.splitext(args.text_file)[1] == ".txt":
                with open(args.text_file, "r") as f:
                    # TODO: Test if file is valid format / not empty

                    for line in f:
                        username, password = line.split()
                        console.print(f"Trying {username}, {password}",
                                      style="cyan")
                        try_cred(target_host, username, password, args)
            else:
                print("Must be .txt file")
                return
        else:
            print("Text file does not exist")
            return
    else:
        with open(os.path.join(os.path.dirname(__file__), "defaults.txt"),
                  "r") as f:
            for line in f:
                username, password = line.split()
                try_cred(target_host, username, password, args)


main()
