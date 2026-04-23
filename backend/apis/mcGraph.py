import re
import threading
import time
from datetime import datetime
from pathlib import Path
from queue import Queue

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


MAX_WORKERS = 3
REQUEST_INTERVAL = 1

lock = threading.Lock()
last_request_time = 0.0


def create_session():
    session = requests.Session()

    retries = Retry(
        total=5,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET", "POST", "PATCH"],
    )

    adapter = HTTPAdapter(max_retries=retries, pool_connections=10, pool_maxsize=10)
    session.mount("https://", adapter)
    return session


def rate_limit():
    global last_request_time
    with lock:
        now = time.time()
        wait_time = REQUEST_INTERVAL - (now - last_request_time)
        if wait_time > 0:
            time.sleep(wait_time)
        last_request_time = time.time()


def safe_request(session, method, url, headers=None, **kwargs):
    for _ in range(5):
        try:
            rate_limit()
            return session.request(
                method,
                url,
                headers={**(headers or {}), "Connection": "close"},
                timeout=10,
                **kwargs,
            )
        except requests.exceptions.SSLError as exc:
            print("SSL error, retrying:", exc)
            time.sleep(2)
        except requests.exceptions.RequestException as exc:
            print("Request failed:", exc)
            time.sleep(2)

    return None


def get_access_token(session, client_id, refresh_token):
    url = "https://login.microsoftonline.com/common/oauth2/v2.0/token"
    data = {
        "client_id": client_id,
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
        "scope": "https://graph.microsoft.com/.default",
    }

    resp = safe_request(session, "POST", url, data=data)
    if not resp:
        return None

    result = resp.json()
    return result.get("access_token")


def get_unread_mails(session, access_token, top=10):
    url = (
        "https://graph.microsoft.com/v1.0/me/messages"
        f"?$filter=isRead eq false&$top={top}"
        "&$select=id,subject,bodyPreview,receivedDateTime"
    )
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Prefer": 'outlook.body-content-type="text"',
    }

    resp = safe_request(session, "GET", url, headers=headers)
    if not resp:
        return []

    data = resp.json()
    return data.get("value", [])


def mark_as_read(session, access_token, message_id):
    url = f"https://graph.microsoft.com/v1.0/me/messages/{message_id}"
    headers = {"Authorization": f"Bearer {access_token}"}
    safe_request(session, "PATCH", url, headers=headers, json={"isRead": True})


def extract_code(text):
    match = re.search(r"\b\d{4,8}\b", text)
    return match.group(0) if match else None


def parse_account_line(line):
    raw_line = line.strip()
    if not raw_line:
        return None

    parts = raw_line.split("----")
    if len(parts) != 4:
        raise ValueError(
            "Invalid account line format, expected: email----password----client_id----refresh_token"
        )

    email, password, client_id, refresh_token = (part.strip() for part in parts)
    return {
        "email": email,
        "password": password,
        "client_id": client_id,
        "refresh_token": refresh_token,
    }


def load_accounts(file_path):
    accounts = {}
    path = Path(file_path)

    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            try:
                account = parse_account_line(line)
            except ValueError as exc:
                raise ValueError(f"{path}:{line_number}: {exc}") from exc

            if not account:
                continue

            accounts[account["email"].lower()] = account

    return accounts


def parse_received_timestamp(mail):
    received_time = mail.get("receivedDateTime")
    if not received_time:
        return None

    try:
        return datetime.fromisoformat(received_time.replace("Z", "+00:00")).timestamp()
    except ValueError:
        return None


def wait_for_verification_code(
    session,
    client_id,
    refresh_token,
    start_time=None,
    timeout=40,
    poll_interval=2,
    mark_read=True,
):
    deadline = time.time() + timeout
    start_timestamp = start_time.timestamp() if start_time else None

    while time.time() < deadline:
        access_token = get_access_token(session, client_id, refresh_token)
        if access_token:
            mails = get_unread_mails(session, access_token)
            mails.sort(key=lambda mail: parse_received_timestamp(mail) or 0, reverse=True)

            for mail in mails:
                received_timestamp = parse_received_timestamp(mail)
                if (
                    start_timestamp is not None
                    and received_timestamp is not None
                    and received_timestamp < start_timestamp
                ):
                    continue

                mail_text = " ".join(
                    value for value in (mail.get("subject", ""), mail.get("bodyPreview", "")) if value
                )
                code = extract_code(mail_text)
                if not code:
                    continue

                if mark_read:
                    mark_as_read(session, access_token, mail["id"])

                return code

        remaining = deadline - time.time()
        if remaining <= 0:
            break
        time.sleep(min(poll_interval, remaining))

    return None


def worker(queue):
    session = create_session()

    while True:
        account = queue.get()
        if account is None:
            break

        try:
            code = wait_for_verification_code(
                session=session,
                client_id=account["client_id"],
                refresh_token=account["refresh_token"],
            )
            if code:
                print(f"[SUCCESS] {account['email']} code: {code}")
            else:
                print(account["email"], "no unread verification mail")
        except Exception as exc:
            print("Processing error:", exc)
        finally:
            queue.task_done()


def read_accounts_from_console():
    lines = []
    print("Please input account data, one per line:")
    print("email----password----client_id----refresh_token")
    print("Press Enter on an empty line to finish.")

    while True:
        line = input().strip()
        if not line:
            break
        lines.append(line)

    return lines


def main():
    q = Queue()

    for line in read_accounts_from_console():
        q.put(parse_account_line(line))

    threads = []
    for _ in range(MAX_WORKERS):
        thread = threading.Thread(target=worker, args=(q,))
        thread.start()
        threads.append(thread)

    q.join()

    for _ in threads:
        q.put(None)

    for thread in threads:
        thread.join()


if __name__ == "__main__":
    main()
