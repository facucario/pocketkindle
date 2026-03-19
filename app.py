import os
from datetime import datetime, timedelta
from urllib.parse import urlparse

from dotenv import load_dotenv
from flask import Flask, render_template, request, redirect, url_for, session, flash

from instapaper_client import InstapaperClient, InstapaperCredentials, InstapaperError


load_dotenv()

def create_app() -> Flask:
    app = Flask(__name__)

    # Configuration
    app.secret_key = os.environ.get("POCKETKINDLE_SECRET_KEY", "dev-secret-change-me")
    app.permanent_session_lifetime = timedelta(days=7)

    # Basic security-related config for cookies
    app.config.update(
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
    )

    def _get_client() -> InstapaperClient:
        return InstapaperClient.from_env()

    def _get_creds() -> InstapaperCredentials | None:
        token = session.get("instapaper_token")
        secret = session.get("instapaper_token_secret")
        if not token or not secret:
            return None
        return InstapaperCredentials(oauth_token=token, oauth_token_secret=secret)

    def _login_required():
        if _get_creds() is None:
            return redirect(url_for("login"))
        return None

    @app.route("/")
    def index():
        if "instapaper_token" in session:
            return redirect(url_for("articles"))
        return redirect(url_for("login"))

    @app.route("/login", methods=["GET"])
    def login():
        return render_template("login.html")

    @app.route("/login", methods=["POST"])
    def login_post():
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        if not username or not password:
            flash("Please enter both username and password.")
            return redirect(url_for("login"))

        try:
            client = InstapaperClient.from_env()
            creds: InstapaperCredentials = client.get_access_token(username, password)
        except InstapaperError as exc:
            flash(str(exc))
            return redirect(url_for("login"))

        session.permanent = True
        session["instapaper_token"] = creds.oauth_token
        session["instapaper_token_secret"] = creds.oauth_token_secret
        session["instapaper_username"] = username

        return redirect(url_for("articles"))

    @app.route("/articles", methods=["GET"])
    def articles():
        maybe_redirect = _login_required()
        if maybe_redirect is not None:
            return maybe_redirect

        try:
            page = int(request.args.get("page", "1"))
        except ValueError:
            page = 1
        if page < 1:
            page = 1
        page_size = 10
        # Fetch one extra item to know if a "More" page exists.
        limit = min((page_size * page) + 1, 500)

        creds = _get_creds()
        assert creds is not None
        client = _get_client()
        try:
            data = client.list_bookmarks(creds, folder_id="unread", limit=limit)
        except InstapaperError as exc:
            flash(str(exc))
            data = {"user": None, "bookmarks": []}
            page = 1
            limit = page_size

        bookmarks_all = data.get("bookmarks", [])
        start = (page - 1) * page_size
        end = start + page_size
        bookmarks = bookmarks_all[start:end]
        user = data.get("user")
        has_next = len(bookmarks_all) > end
        has_prev = page > 1
        return render_template(
            "articles.html",
            bookmarks=bookmarks,
            user=user,
            page=page,
            has_next=has_next,
            has_prev=has_prev,
        )

    @app.route("/read/<int:bookmark_id>", methods=["GET"])
    def read(bookmark_id: int):
        maybe_redirect = _login_required()
        if maybe_redirect is not None:
            return maybe_redirect

        creds = _get_creds()
        assert creds is not None
        client = _get_client()
        try:
            html = client.get_text(creds, bookmark_id)
        except InstapaperError as exc:
            flash(str(exc))
            return redirect(url_for("articles"))

        title = request.args.get("title") or ""
        reading_mode = session.get("reading_mode", "scroll")

        raw_source = request.args.get("source") or ""
        raw_saved = request.args.get("saved") or ""

        source_label = ""
        if raw_source:
            try:
                parsed = urlparse(raw_source)
                if parsed.netloc:
                    source_label = parsed.netloc
            except Exception:
                source_label = ""

        date_label = ""
        if raw_saved:
            try:
                ts = int(raw_saved)
                dt = datetime.fromtimestamp(ts)
                date_label = dt.strftime("%B %d, %Y")
            except Exception:
                date_label = ""

        article_meta = ""
        if source_label or date_label:
            parts: list[str] = []
            if source_label:
                parts.append(source_label)
            if date_label:
                parts.append(date_label)
            article_meta = " · ".join(parts)

        # Server-side pagination in paged mode: treat paragraphs as "lines"
        # and slice according to the chosen lines_per_page setting.
        page = 1
        total_pages = 1
        page_html = html
        if reading_mode == "paged":
            try:
                page = int(request.args.get("page", "1"))
            except ValueError:
                page = 1
            if page < 1:
                page = 1

            try:
                lines_per_page = int(session.get("lines_per_page", 10))
            except (TypeError, ValueError):
                lines_per_page = 10
            if lines_per_page < 3:
                lines_per_page = 3
            if lines_per_page > 100:
                lines_per_page = 100

            # Split on closing </p> tags, re-add them, and treat each
            # paragraph as one "line" for paging purposes.
            chunks = html.split("</p>")
            paragraphs = [c.strip() + "</p>" for c in chunks if c.strip()]
            if paragraphs:
                total_pages = max(1, (len(paragraphs) + lines_per_page - 1) // lines_per_page)
                if page > total_pages:
                    page = total_pages
                start = (page - 1) * lines_per_page
                end = start + lines_per_page
                page_html = "".join(paragraphs[start:end])
            else:
                page = 1
                total_pages = 1
                page_html = html

        return render_template(
            "reader.html",
            bookmark_id=bookmark_id,
            article_html=page_html,
            article_title=title,
            reading_mode=reading_mode,
            page=page,
            total_pages=total_pages,
            article_meta=article_meta,
            request_source=raw_source,
            request_saved=raw_saved,
        )

    @app.route("/articles/<int:bookmark_id>/archive", methods=["POST"])
    def archive(bookmark_id: int):
        maybe_redirect = _login_required()
        if maybe_redirect is not None:
            return maybe_redirect

        creds = _get_creds()
        assert creds is not None
        client = _get_client()
        try:
            client.archive(creds, bookmark_id)
        except InstapaperError as exc:
            flash(str(exc))

        return redirect(url_for("articles"))

    @app.route("/logout", methods=["GET"])
    def logout():
        session.clear()
        return redirect(url_for("login"))

    @app.route("/settings", methods=["GET", "POST"])
    def settings():
        maybe_redirect = _login_required()
        if maybe_redirect is not None:
            return maybe_redirect

        if request.method == "POST":
            font_size = request.form.get("font_size", "medium")
            if font_size not in ("small", "medium", "large"):
                font_size = "medium"
            session["font_size"] = font_size
            reading_mode = request.form.get("reading_mode", "scroll")
            if reading_mode not in ("scroll", "paged"):
                reading_mode = "scroll"
            session["reading_mode"] = reading_mode
            try:
                lines_per_page = int(request.form.get("lines_per_page", "10"))
            except (TypeError, ValueError):
                lines_per_page = 10
            if lines_per_page < 3:
                lines_per_page = 3
            if lines_per_page > 100:
                lines_per_page = 100
            session["lines_per_page"] = lines_per_page
            flash("Settings saved.")
            return redirect(url_for("settings"))

        current_font = session.get("font_size", "medium")
        reading_mode = session.get("reading_mode", "scroll")
        lines_per_page = session.get("lines_per_page", 10)
        return render_template(
            "settings.html",
            current_font=current_font,
            reading_mode=reading_mode,
            lines_per_page=lines_per_page,
        )

    # Additional routes (articles list, reader, settings, logout) will be
    # implemented as part of the remaining todos.

    return app


if __name__ == "__main__":
    flask_app = create_app()
    flask_app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))

