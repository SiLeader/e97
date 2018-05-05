"""
  Copyright 2018 SiLeader.

   Licensed under the Apache License, Version 2.0 (the "License");
   you may not use this file except in compliance with the License.
   You may obtain a copy of the License at

       http://www.apache.org/licenses/LICENSE-2.0

   Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   See the License for the specific language governing permissions and
   limitations under the License.
"""


import pathlib
from datetime import datetime, timezone

from flask import Flask, render_template, redirect, request, url_for, abort, make_response  # , send_file
from flask_wtf import CSRFProtect

from urllib import parse

from core import auth, util
from models import users, pages
import settings

app = Flask(__name__)
app.config['SECRET_KEY'] = util.random_string()
app.jinja_env.filters["datetime"] = auth.to_local_datetime
app.jinja_env.filters["user"] = users.to_name
csrf = CSRFProtect(app)


@app.before_request
def before_request():
    if request.path.startswith("/static"):
        return
    if request.path in [url_for("web_top"), url_for("login")]:
        return
    if auth.check():
        return
    return redirect(url_for("web_top"))


def render(template: str, title: str, **kwargs):
    return render_template(template, title=title, latests=pages.get_latest(), **kwargs)


@app.route('/')
def web_top():
    if auth.check():
        with open(settings.TOP_PAGE_REST) as fp:
            data = fp.read()
        content = {
            "title": "Top Page",
            "update": {
                "by": "System",
                "date": datetime.fromtimestamp(pathlib.Path(settings.TOP_PAGE_REST).lstat().st_mtime)
            },
            "content": util.rest_to_html(data),
            "noedit": True
        }
        return render("in/content.html", title="Top", content=content)
    return render_template("out/login.html", title="Sign in")


@app.route('/login', methods=["POST"])
def login():
    if users.check(request.form["email"], request.form["password"]):
        auth.login(request.form["email"], request.form["tz"])
    return redirect(url_for("web_top"))


@app.route('/logout', methods=["GET"])
def logout():
    auth.logout()
    return redirect(url_for("web_top"))


@app.route('/contents/<pid>')
def contents_show(pid):
    page = pages.get(pid)
    if page is None:
        abort(404)
    page["content"] = util.rest_to_html(page[pages.CONTENT])
    return render("in/content.html", title=page[pages.TITLE], content=page)


@app.route('/contents/<pid>/edit', methods=["GET", "POST"])
def contents_edit(pid):
    if request.method == "GET":
        page = pages.get(pid)
        if page is None:
            abort(404)
        return render("in/edit.html",
                      title="edit {}".format(page[pages.TITLE]),
                      content=page,
                      post_to=url_for("contents_edit", pid=pid))

    # POST
    title = request.form["title"]
    content = request.form["content"]
    user = auth.get_id()

    new_pid = pages.update(pid, user, title, content)
    if new_pid is not None:
        # Success
        page = pages.get(new_pid)
        if page is None:
            abort(404)
        return redirect(url_for("contents_show", pid=new_pid))

    page = pages.get(pid)
    if page is None:
        abort(404)
    return render("in/edit.html",
                  title="edit {}".format(page[pages.TITLE]),
                  content={"title": title, "content": content},
                  post_to=url_for("contents_edit", pid=pid))


@app.route('/contents/<pid>/pdf')
def contents_pdf(pid):
    page = pages.get(pid)
    if page is None:
        abort(404)

    res = make_response(util.create_pdf(page[pages.CONTENT]))
    disposition = "attachment; filename*=UTF-8''"
    disposition += parse.quote(page[pages.TITLE] + '.pdf')
    res.headers["Content-Disposition"] = disposition
    res.mimetype = 'application/pdf'
    return res


@app.route('/index')
def index():
    page_index = pages.get_all_as_index()
    return render("in/index.html", title="Index", pages=page_index)


@app.route('/users/new', methods=["GET", "POST"])
def add_user():
    if request.method == "GET":
        return render("in/edit_user.html", title="New user", new_user=True, post_to=url_for("add_user"))
    email = request.form["email"]
    name = request.form["name"]
    password = request.form["password"]
    if len(name) <= 0 and len(password) <= 0:
        return redirect(url_for("web_top"))

    if password != request.form["password-confirm"]:
        return render("in/edit_user.html",
                      title="New user",
                      new_user=True,
                      post_to=url_for("add_user"),
                      message="Password is difference from Password(Confirm).")
    users.add(email, name, password, users.LEVEL_WRITER)
    return redirect(url_for("web_top"))


@app.route('/users/edit', methods=["GET", "POST"])
def edit_user():
    if request.method == "GET":
        return render("in/edit_user.html", title="Edit user", new_user=False, post_to=url_for("edit_user"))
    password = request.form["password"]
    if password != request.form["password-confirm"]:
        return render("in/edit_user.html",
                      title="Edit user",
                      new_user=False,
                      post_to=url_for("edit_user"),
                      message="Password is difference from Password(Confirm).")
    users.update(auth.get_id(), password, users.LEVEL_WRITER)
    return redirect(url_for("web_top"))


@app.route('/pages/new', methods=["GET", "POST"])
def add_page():
    if request.method == "GET":
        return render("in/edit.html", title="new page", post_to=url_for("add_page"))

    title = request.form["title"]
    content = request.form["content"]
    user = auth.get_id()

    pid = pages.add(title, content, user)
    if pid is not None:
        page = pages.get(pid)
        if page is None:
            abort(404)
        return redirect(url_for("contents_show", pid=pid))

    return render("in/edit.html",
                  title="new page",
                  content={"title": title, "content": content},
                  post_to=url_for("add_page"), message="Already exist")


@app.route('/search')
def search_pages():
    start_time = datetime.now(timezone.utc)
    query = request.args["q"].replace("　", " ")
    and_q = []
    or_q = []
    not_q = []
    for q in query.split(" "):
        if q.startswith("-"):
            not_q.append(q)
        else:
            and_q.append(q)
    result = pages.search(and_q, or_q, not_q)
    finish_time = datetime.now(timezone.utc)
    time = finish_time - start_time
    return render("in/search_result.html",
                  title="Search",
                  results=result,
                  count=len(result),
                  time=time.total_seconds(),
                  search_query=request.args["q"])


@app.errorhandler(404)
def error_handle(error):
    error_page_rest = settings.ERROR_PAGE_DIRECTORY + "/{}.rst".format(error.code)
    with open(error_page_rest) as fp:
        data = fp.read()
    content = {
        "title": "Error",
        "update": {
            "by": "System",
            "date": datetime.fromtimestamp(pathlib.Path(error_page_rest).lstat().st_mtime)
        },
        "content": util.rest_to_html(data),
        "noedit": True
    }
    return render("in/content.html", title="Error {}".format(error.code), content=content), error.code


if __name__ == '__main__':
    app.run()
