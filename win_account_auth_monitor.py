import win32evtlog

# local access to event logs
server = "localhost"

# we are looking for the security log file
logtype = "Security"

# defines how we want to read the log data
flags = win32evtlog.EVENTLOG_FORWARDS_READ | win32evtlog.EVENTLOG_SEQUENTIAL_READ


def QueryEventLog(eventID):
    """
    Returns logs that match a specific eventID
    """

    logs = []

    h = win32evtlog.OpenEventLog(server, logtype)

    # read each record until there is no more entries to read
    while True:
        events = win32evtlog.ReadEventLog(h, flags, 0)
        if events:
            for event in events:
                if event.EventID == eventID:
                    logs.append(event)
        else:
            break
    return logs


def DetectBruteForce():
    """
    Uses event ID 4625 to detect failed login attempts
    """

    # TODO: should smartly indicate a likely brute force attack
    # Same IPs, Time frame, Frequency, low num -> less likely a brute force attack

    failures = {}

    # get all event logs that indicate a failed login attempt
    events = QueryEventLog(4625)
    for event in events:
        # 'event.StringInserts' access the 'EventData' inside the windows event log and we can query which variable to get with an index starting from 0
        account = event.StringInserts[5]
        if account in failures:
            failures[account] += 1
        else:
            failures[account] = 1
    for account in failures:
        print("%s: %s failed logins" % (account, failures[account]))


def CheckDefaultAccounts():
    """
    Searches unauthorized logins that are not in allowed IP and that match a common brute force username.
    """

    with open("defaults.txt", "r") as f:
        defaults = [[x for x in line.split(" ")][0] for line in f]
    with open("allowlist.txt", "r") as f:
        allowed = f.read().splitlines()

    # get all event logs that indicate a successful login attempt
    events = QueryEventLog(4624)
    for event in events:
        if event.StringInserts[8] == ["10", "3"]:  # remote login attempt
            # common brute force username
            if event.StringInserts[5] in defaults:
                # if IP address not in allowed IPs
                if event.StringInserts[18] not in allowed:
                    print("Unauthorized login to %s from %s" %
                          (event.StringInserts[5], event.StringInserts[18]))


DetectBruteForce()
CheckDefaultAccounts()
