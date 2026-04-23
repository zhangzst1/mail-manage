"""
Outlook mail handler.
"""

import email
import imaplib
import threading
import time
from datetime import timezone

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from .common import decode_mime_words, format_date_for_imap_search, normalize_check_time
from .logger import logger


class OutlookMailHandler:
    """Handle Outlook mail fetch through Graph or IMAP."""

    GRAPH_SCOPE = "https://graph.microsoft.com/.default"
    GRAPH_BASE_URL = "https://graph.microsoft.com/v1.0"
    REQUEST_INTERVAL = 1.0
    _request_lock = threading.Lock()
    _last_request_time = 0.0

    DEFAULT_FOLDERS = {
        "INBOX": ["inbox", "Inbox", "INBOX"],
        "SENT": ["sentitems", "Sent Items", "Sent", "已发送"],
        "DRAFTS": ["drafts", "Drafts", "草稿箱"],
        "TRASH": ["deleteditems", "Deleted Items", "Trash", "已删除"],
        "SPAM": ["junkemail", "Junk E-mail", "Spam", "垃圾邮件"],
        "ARCHIVE": ["archive", "Archive", "归档"],
    }

    def __init__(self, email_address, access_token):
        self.email_address = email_address
        self.access_token = access_token
        self.mail = None
        self.error = None

    def connect(self):
        try:
            self.mail = imaplib.IMAP4_SSL("outlook.live.com")
            auth_string = OutlookMailHandler.generate_auth_string(self.email_address, self.access_token)
            self.mail.authenticate("XOAUTH2", lambda x: auth_string)
            return True
        except Exception as exc:
            self.error = str(exc)
            logger.error(f"Outlook connection failed: {exc}")
            return False

    def get_folders(self):
        if not self.mail:
            return []

        try:
            _, folders = self.mail.list()
            folder_list = []

            for folder in folders:
                if isinstance(folder, bytes):
                    folder = folder.decode("utf-8", errors="ignore")

                parts = folder.split('"')
                folder_name = parts[-2] if len(parts) >= 3 else folder.split()[-1]
                if folder_name and folder_name not in [".", ".."]:
                    folder_list.append(folder_name)

            for folder_name in ["inbox", "sentitems", "drafts", "deleteditems", "junkemail"]:
                if folder_name not in folder_list:
                    folder_list.append(folder_name)

            return sorted(folder_list)
        except Exception as exc:
            logger.error(f"Failed to list Outlook folders: {exc}")
            return ["inbox"]

    def get_messages(self, folder="inbox", limit=100):
        if not self.mail:
            return []

        try:
            self.mail.select(folder)
            _, messages = self.mail.search(None, "ALL")
            message_numbers = messages[0].split()
            message_numbers = message_numbers[-limit:] if len(message_numbers) > limit else message_numbers
            message_numbers.reverse()

            mail_list = []
            for num in message_numbers:
                try:
                    _, msg_data = self.mail.fetch(num, "(RFC822)")
                    msg = email.message_from_bytes(msg_data[0][1])
                    subject = decode_mime_words(msg.get("Subject", ""))
                    sender = decode_mime_words(msg.get("From", ""))
                    received_time = email.utils.parsedate_to_datetime(msg.get("Date", ""))

                    content = ""
                    if msg.is_multipart():
                        for part in msg.walk():
                            if part.get_content_type() in ["text/plain", "text/html"]:
                                try:
                                    content += part.get_payload(decode=True).decode()
                                except Exception:
                                    continue
                    else:
                        try:
                            content = msg.get_payload(decode=True).decode()
                        except Exception:
                            content = str(msg.get_payload())

                    mail_list.append(
                        {
                            "subject": subject,
                            "sender": sender,
                            "received_time": received_time,
                            "content": content,
                            "folder": folder,
                        }
                    )
                except Exception as exc:
                    logger.warning(f"Failed to parse Outlook mail: {exc}")

            return mail_list
        except Exception as exc:
            logger.error(f"Failed to fetch Outlook messages: {exc}")
            return []

    def close(self):
        if self.mail:
            try:
                self.mail.logout()
            except Exception:
                pass
            self.mail = None

    @staticmethod
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

    @classmethod
    def rate_limit(cls):
        with cls._request_lock:
            now = time.time()
            wait_time = cls.REQUEST_INTERVAL - (now - cls._last_request_time)
            if wait_time > 0:
                time.sleep(wait_time)
            cls._last_request_time = time.time()

    @classmethod
    def safe_request(cls, session, method, url, headers=None, **kwargs):
        for attempt in range(5):
            try:
                cls.rate_limit()
                return session.request(
                    method,
                    url,
                    headers={**(headers or {}), "Connection": "close"},
                    timeout=15,
                    **kwargs,
                )
            except requests.exceptions.SSLError as exc:
                logger.warning(f"SSL error on request attempt {attempt + 1}: {exc}")
                time.sleep(2)
            except requests.exceptions.RequestException as exc:
                logger.warning(f"Request failed on attempt {attempt + 1}: {exc}")
                time.sleep(2)
        return None

    @staticmethod
    def _ensure_utc_isoformat(dt):
        if not dt:
            return None
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        else:
            dt = dt.astimezone(timezone.utc)
        return dt.strftime("%Y-%m-%dT%H:%M:%SZ")

    @staticmethod
    def _parse_graph_datetime(date_str):
        if not date_str:
            return None
        return normalize_check_time(date_str)

    @staticmethod
    def _format_graph_sender(mail):
        sender_info = (mail.get("from") or {}).get("emailAddress") or {}
        name = (sender_info.get("name") or "").strip()
        address = (sender_info.get("address") or "").strip()

        if name and address and name.lower() != address.lower():
            return f"{name} <{address}>"
        if address:
            return address
        if name:
            return name
        return "(未知发件人)"

    @classmethod
    def _build_graph_mail_record(cls, mail):
        subject = (mail.get("subject") or "").strip() or "(无主题)"
        sender = cls._format_graph_sender(mail)
        received_time = cls._parse_graph_datetime(mail.get("receivedDateTime"))

        body = mail.get("body") or {}
        body_content_type = (body.get("contentType") or "").strip().lower()
        content = body.get("content") or mail.get("bodyPreview") or ""
        has_html = body_content_type == "html"
        message_id = mail.get("internetMessageId") or mail.get("id") or ""
        mail_key = message_id or f"{subject}|{sender}|{mail.get('receivedDateTime', '')}"

        return {
            "subject": subject,
            "sender": sender,
            "received_time": received_time,
            "content": {
                "content": content,
                "content_type": "text/html" if has_html else "text/plain",
                "has_html": has_html,
                "plain_text": mail.get("bodyPreview") or None,
            },
            "folder": "INBOX",
            "mail_key": mail_key,
            "has_attachments": False,
        }

    @classmethod
    def get_new_access_token(cls, refresh_token, client_id, scope=None, session=None):
        url = "https://login.microsoftonline.com/common/oauth2/v2.0/token"
        data = {
            "client_id": client_id,
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
        }
        if scope:
            data["scope"] = scope

        own_session = session is None
        session = session or cls.create_session()
        try:
            response = cls.safe_request(session, "POST", url, data=data)
            if not response:
                logger.error("Failed to get access token: no response")
                return None

            try:
                response_data = response.json()
            except ValueError:
                logger.error(f"Failed to get access token: invalid JSON response {response.status_code}")
                return None

            if response.status_code >= 400 or response_data.get("error"):
                error_message = (
                    response_data.get("error_description")
                    or response_data.get("error")
                    or response.text
                )
                logger.error(f"Failed to get access token: {error_message}")
                return None

            access_token = response_data.get("access_token")
            if not access_token:
                logger.error("Failed to get access token: access_token missing")
                return None

            logger.info("Access token refreshed successfully")
            return access_token
        except Exception as exc:
            logger.error(f"Unexpected error refreshing token: {exc}")
            return None
        finally:
            if own_session:
                session.close()

    @classmethod
    def get_graph_access_token(cls, refresh_token, client_id, session=None):
        return cls.get_new_access_token(
            refresh_token,
            client_id,
            scope=cls.GRAPH_SCOPE,
            session=session,
        )

    @staticmethod
    def generate_auth_string(user, token):
        return f"user={user}\1auth=Bearer {token}\1\1"

    @classmethod
    def fetch_emails_via_graph(cls, email_address, access_token, callback=None, last_check_time=None, top=100):
        mail_records = []
        if callback is None:
            callback = lambda progress, folder: None

        last_check_time = normalize_check_time(last_check_time)
        if last_check_time:
            logger.info(f"Fetch Outlook mail via Graph since {last_check_time.isoformat()} for {email_address}")
        else:
            logger.info(f"Fetch Outlook mail via Graph for {email_address}")

        session = cls.create_session()
        try:
            params = {
                "$top": min(max(int(top), 1), 100),
                "$orderby": "receivedDateTime desc",
                "$select": "id,subject,bodyPreview,body,receivedDateTime,from,internetMessageId",
            }

            graph_since = cls._ensure_utc_isoformat(last_check_time)
            if graph_since:
                params["$filter"] = f"receivedDateTime ge {graph_since}"

            headers = {
                "Authorization": f"Bearer {access_token}",
                "Prefer": 'outlook.body-content-type="html"',
            }

            callback(15, "graph")
            response = cls.safe_request(
                session,
                "GET",
                f"{cls.GRAPH_BASE_URL}/me/mailFolders/inbox/messages",
                headers=headers,
                params=params,
            )
            if not response:
                raise RuntimeError("Graph mail request returned no response")

            try:
                response_data = response.json()
            except ValueError as exc:
                raise RuntimeError(f"Graph response is not valid JSON: {exc}") from exc

            if response.status_code >= 400:
                error_message = response_data.get("error", {}).get("message") or response.text
                raise RuntimeError(f"Graph request failed: HTTP {response.status_code} - {error_message}")

            mails = response_data.get("value", []) or []
            total_mails = len(mails)
            logger.info(f"Graph returned {total_mails} messages for {email_address}")

            if total_mails == 0:
                callback(90, "graph")
                return []

            for index, mail in enumerate(mails, start=1):
                callback(int(20 + (index / total_mails) * 70), "graph")
                record = cls._build_graph_mail_record(mail)
                received_time = record.get("received_time")
                if last_check_time and received_time and received_time < last_check_time:
                    continue
                mail_records.append(record)

            callback(90, "graph")
            return mail_records
        finally:
            session.close()

    @classmethod
    def fetch_all_emails_via_graph(
        cls,
        email_address,
        access_token,
        folder="all",
        callback=None,
        top=100,
        limit=None,
    ):
        """Fetch all available messages for a mailbox through Microsoft Graph paging."""
        mail_records = []
        if callback is None:
            callback = lambda progress, message: None

        normalized_folder = (folder or "all").strip().lower()
        session = cls.create_session()
        try:
            params = {
                "$top": min(max(int(top), 1), 1000),
                "$orderby": "receivedDateTime desc",
                "$select": (
                    "id,subject,bodyPreview,body,receivedDateTime,from,"
                    "internetMessageId,parentFolderId,hasAttachments,isRead"
                ),
            }

            if normalized_folder in ("all", "*"):
                next_url = f"{cls.GRAPH_BASE_URL}/me/messages"
                folder_label = "all"
            else:
                next_url = f"{cls.GRAPH_BASE_URL}/me/mailFolders/{normalized_folder}/messages"
                folder_label = normalized_folder

            callback(5, f"graph:{folder_label}")
            page = 0
            while next_url:
                page += 1
                response = cls.safe_request(
                    session,
                    "GET",
                    next_url,
                    headers={
                        "Authorization": f"Bearer {access_token}",
                        "Prefer": 'outlook.body-content-type="html"',
                    },
                    params=params if page == 1 else None,
                )
                if not response:
                    raise RuntimeError("Graph mail request returned no response")

                try:
                    response_data = response.json()
                except ValueError as exc:
                    raise RuntimeError(f"Graph response is not valid JSON: {exc}") from exc

                if response.status_code >= 400:
                    error_message = response_data.get("error", {}).get("message") or response.text
                    raise RuntimeError(f"Graph request failed: HTTP {response.status_code} - {error_message}")

                mails = response_data.get("value", []) or []
                logger.info(
                    f"Graph returned {len(mails)} messages for {email_address} "
                    f"(folder={folder_label}, page={page})"
                )

                for mail in mails:
                    record = cls._build_graph_mail_record(mail)
                    record["graph_id"] = mail.get("id")
                    record["body_preview"] = mail.get("bodyPreview") or ""
                    record["has_attachments"] = bool(mail.get("hasAttachments", False))
                    record["is_read"] = bool(mail.get("isRead", False))
                    record["parent_folder_id"] = mail.get("parentFolderId")
                    record["folder"] = folder_label.upper() if folder_label != "all" else "ALL"
                    mail_records.append(record)

                    if limit and len(mail_records) >= int(limit):
                        callback(100, f"graph:{folder_label}")
                        return mail_records

                next_url = response_data.get("@odata.nextLink")
                callback(min(95, 5 + page * 10), f"graph:{folder_label}")

            callback(100, f"graph:{folder_label}")
            return mail_records
        finally:
            session.close()

    @staticmethod
    def fetch_emails(email_address, access_token, folder="inbox", callback=None, last_check_time=None):
        mail_records = []

        if callback is None:
            callback = lambda progress, folder_name: None

        last_check_time = normalize_check_time(last_check_time)
        if last_check_time:
            logger.info(
                f"Fetch Outlook IMAP mails for {email_address} in {folder} since {last_check_time.isoformat()}"
            )
        else:
            logger.info(f"Fetch all Outlook IMAP mails for {email_address} in {folder}")

        max_retries = 3
        for retry in range(max_retries):
            mail = None
            try:
                logger.info(f"Try connecting Outlook IMAP ({retry + 1}/{max_retries})")
                callback(10, folder)
                mail = imaplib.IMAP4_SSL("outlook.live.com")

                auth_string = OutlookMailHandler.generate_auth_string(email_address, access_token)
                mail.authenticate("XOAUTH2", lambda x: auth_string)
                mail.select("inbox")
                callback(20, folder)

                if last_check_time:
                    search_date = format_date_for_imap_search(last_check_time)
                    status, data = mail.search(None, f'(SINCE "{search_date}")')
                else:
                    status, data = mail.search(None, "ALL")

                if status != "OK":
                    logger.error(f"Search Outlook mails failed: {status}")
                    continue

                mail_ids = data[0].split()
                mail_ids = mail_ids[-100:] if len(mail_ids) > 100 else mail_ids
                total_mails = len(mail_ids)
                logger.info(f"Found {total_mails} Outlook IMAP messages")

                for index, mail_id in enumerate(mail_ids):
                    callback(int(20 + (index / total_mails) * 70) if total_mails else 90, folder)
                    try:
                        status, mail_data = mail.fetch(mail_id, "(RFC822)")
                        if status != "OK":
                            logger.error(f"Fetch Outlook mail {mail_id} failed: {status}")
                            continue

                        msg = email.message_from_bytes(mail_data[0][1])
                        subject = decode_mime_words(msg.get("Subject", ""))
                        sender = decode_mime_words(msg.get("From", ""))
                        received_time = email.utils.parsedate_to_datetime(msg.get("Date", ""))
                        mail_key = f"{subject}|{sender}|{received_time.isoformat() if received_time else 'unknown'}"

                        if mail_key in [record.get("mail_key") for record in mail_records]:
                            continue

                        content = ""
                        if msg.is_multipart():
                            for part in msg.walk():
                                if part.get_content_type() in ["text/plain", "text/html"]:
                                    try:
                                        content += part.get_payload(decode=True).decode()
                                    except Exception:
                                        continue
                        else:
                            try:
                                payload = msg.get_payload(decode=True)
                                content = payload.decode() if payload else ""
                            except Exception:
                                content = str(msg.get_payload())

                        mail_records.append(
                            {
                                "subject": subject,
                                "sender": sender,
                                "received_time": received_time,
                                "content": content,
                                "mail_key": mail_key,
                                "folder": folder.upper(),
                            }
                        )
                    except Exception as exc:
                        logger.error(f"Process Outlook IMAP mail failed: {exc}")

                callback(90, folder)
                break
            except imaplib.IMAP4.error as exc:
                logger.error(f"Outlook IMAP error: {exc}")
                time.sleep(1)
            except Exception as exc:
                logger.error(f"Fetch Outlook IMAP mails failed: {exc}")
                time.sleep(1)
            finally:
                if mail:
                    try:
                        mail.logout()
                    except Exception:
                        pass

        return mail_records

    @staticmethod
    def check_mail_imap(email_info, db, progress_callback=None):
        """Check Outlook mailbox through IMAP only."""
        email_id = email_info["id"]
        email_address = email_info["email"]
        refresh_token = email_info["refresh_token"]
        client_id = email_info["client_id"]
        last_check_time = normalize_check_time(email_info.get("last_check_time"))

        logger.info(f"Start checking Outlook mailbox via IMAP only: id={email_id}, email={email_address}")

        if progress_callback is None:
            progress_callback = lambda progress, message: None

        progress_callback(0, "正在获取访问令牌...")

        try:
            session = OutlookMailHandler.create_session()
            try:
                access_token = OutlookMailHandler.get_new_access_token(
                    refresh_token,
                    client_id,
                    session=session,
                )
                if not access_token:
                    error_msg = f"邮箱{email_address}(ID={email_id})获取访问令牌失败"
                    logger.error(error_msg)
                    progress_callback(0, error_msg)
                    return {"success": False, "message": error_msg}

                db.update_email_token(email_id, access_token)
                progress_callback(10, "已获取 IMAP 令牌，开始读取邮件...")
                mail_records = OutlookMailHandler.fetch_emails(
                    email_address,
                    access_token,
                    "inbox",
                    callback=lambda progress, folder: progress_callback(
                        10 + int(progress * 0.8),
                        "正在通过 IMAP 获取邮件...",
                    ),
                    last_check_time=last_check_time,
                )
            finally:
                session.close()

            count = len(mail_records)
            progress_callback(90, f"IMAP 获取到 {count} 封邮件，正在保存...")

            saved_count = 0
            for record in mail_records:
                try:
                    success, _ = db.add_mail_record(
                        email_id=email_id,
                        subject=record["subject"],
                        sender=record["sender"],
                        received_time=record["received_time"],
                        content=record["content"],
                        folder=record.get("folder", "INBOX"),
                        has_attachments=1 if record.get("has_attachments", False) else 0,
                    )
                    if success:
                        saved_count += 1
                except Exception as exc:
                    logger.error(f"Save mail record failed: {exc}")

            db.update_check_time(email_id)
            success_msg = f"完成，通过IMAP共处理{count}封邮件，新增{saved_count}封"
            progress_callback(100, success_msg)
            logger.info(f"Outlook mailbox IMAP check completed: {success_msg}")

            return {
                "success": True,
                "message": success_msg,
                "total": count,
                "saved": saved_count,
                "source": "imap",
            }
        except Exception as exc:
            error_msg = f"处理邮箱过程中出错: {exc}"
            logger.error(f"Outlook mailbox IMAP check failed: {error_msg}")
            progress_callback(0, error_msg)
            return {"success": False, "message": error_msg}

    @staticmethod
    def check_mail(email_info, db, progress_callback=None):
        email_id = email_info["id"]
        email_address = email_info["email"]
        refresh_token = email_info["refresh_token"]
        client_id = email_info["client_id"]
        last_check_time = normalize_check_time(email_info.get("last_check_time"))

        logger.info(f"Start checking Outlook mailbox: id={email_id}, email={email_address}")

        if progress_callback is None:
            progress_callback = lambda progress, message: None

        progress_callback(0, "正在获取访问令牌...")

        try:
            session = OutlookMailHandler.create_session()
            try:
                graph_token = OutlookMailHandler.get_graph_access_token(refresh_token, client_id, session=session)
                if graph_token:
                    try:
                        db.update_email_token(email_id, graph_token)
                        progress_callback(10, "已获取 Graph 令牌，开始读取邮件...")
                        mail_records = OutlookMailHandler.fetch_emails_via_graph(
                            email_address,
                            graph_token,
                            callback=lambda progress, folder: progress_callback(
                                10 + int(progress * 0.8),
                                "正在通过 Graph 获取邮件...",
                            ),
                            last_check_time=last_check_time,
                        )
                        fetch_source = "Graph"
                    except Exception as exc:
                        logger.warning(f"Graph fetch failed, fallback to IMAP: {exc}")
                        progress_callback(10, "Graph 读取失败，回退 IMAP...")
                        access_token = OutlookMailHandler.get_new_access_token(
                            refresh_token,
                            client_id,
                            session=session,
                        )
                        if not access_token:
                            raise RuntimeError(f"Graph 获取成功但回退 IMAP 令牌失败: {exc}") from exc

                        db.update_email_token(email_id, access_token)
                        mail_records = OutlookMailHandler.fetch_emails(
                            email_address,
                            access_token,
                            "inbox",
                            callback=lambda progress, folder: progress_callback(
                                10 + int(progress * 0.8),
                                "正在通过 IMAP 获取邮件...",
                            ),
                            last_check_time=last_check_time,
                        )
                        fetch_source = "IMAP"
                else:
                    access_token = OutlookMailHandler.get_new_access_token(refresh_token, client_id, session=session)
                    if not access_token:
                        error_msg = f"邮箱{email_address}(ID={email_id})获取访问令牌失败"
                        logger.error(error_msg)
                        progress_callback(0, error_msg)
                        return {"success": False, "message": error_msg}

                    db.update_email_token(email_id, access_token)
                    progress_callback(10, "Graph 令牌获取失败，回退 IMAP...")
                    mail_records = OutlookMailHandler.fetch_emails(
                        email_address,
                        access_token,
                        "inbox",
                        callback=lambda progress, folder: progress_callback(
                            10 + int(progress * 0.8),
                            "正在通过 IMAP 获取邮件...",
                        ),
                        last_check_time=last_check_time,
                    )
                    fetch_source = "IMAP"
            finally:
                session.close()

            count = len(mail_records)
            progress_callback(90, f"{fetch_source} 获取到 {count} 封邮件，正在保存...")

            saved_count = 0
            for record in mail_records:
                try:
                    success, _ = db.add_mail_record(
                        email_id=email_id,
                        subject=record["subject"],
                        sender=record["sender"],
                        received_time=record["received_time"],
                        content=record["content"],
                        folder=record.get("folder", "INBOX"),
                        has_attachments=1 if record.get("has_attachments", False) else 0,
                    )
                    if success:
                        saved_count += 1
                except Exception as exc:
                    logger.error(f"Save mail record failed: {exc}")

            db.update_check_time(email_id)
            success_msg = f"完成，通过{fetch_source}共处理{count}封邮件，新增{saved_count}封"
            progress_callback(100, success_msg)
            logger.info(f"Outlook mailbox check completed: {success_msg}")

            return {
                "success": True,
                "message": success_msg,
                "total": count,
                "saved": saved_count,
                "source": fetch_source.lower(),
            }
        except Exception as exc:
            error_msg = f"处理邮箱过程中出错: {exc}"
            logger.error(f"Outlook mailbox check failed: {error_msg}")
            progress_callback(0, error_msg)
            return {"success": False, "message": error_msg}
