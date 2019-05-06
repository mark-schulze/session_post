
import os, threading
import datetime

from flask import Flask
from flask import redirect
from flask import render_template
from flask import request
from flask import url_for

from webapp.user import User

import webapp.config as config

from flask_login import current_user, LoginManager

from webapp.mockdbhelper import MockDBHelper as DBHelper

from webapp.forms import CreateTableForm

from bitlyshortener import Shortener

tokens_pool = ['my_access_token']  # Use your own.
print(os.getpid(), threading.get_ident())
shortener = Shortener(tokens=tokens_pool, max_cache_size=128)

app = Flask(__name__)
login_manager = LoginManager(app)
app.secret_key = "Gxf613UhGRkzAKd47R5daLrUelnlUL4L6AU4z0uu++TNBpdzhAolufHqPQiiEdn34pbE97bmXbN"


DB = DBHelper()


# load the user
@login_manager.user_loader
def load_user(user_id):
    user_password = DB.get_user(user_id)
    if user_password:
        return User(user_id)


# index route set to account page
@app.route("/")
#@login_required
def account():
    tables = DB.get_tables(current_user.get_id())
    return render_template("account.html", createtableform=CreateTableForm(), tables=tables)


# add a table with any name or number
@app.route("/account/createtable", methods=["POST"])
#@login_required
def account_createtable():
    form = CreateTableForm(request.form)
    if form.validate():
        tableid = DB.add_table(form.tablenumber.data, current_user.get_id())
        new_urls = [f'{config.base_url}newrequest/{tableid}']
        print(os.getpid(), threading.get_ident(), new_urls)
        short_url = shortener.shorten_urls(new_urls)[0]
        DB.update_table(tableid, short_url)
        return redirect(url_for('account'))
    return render_template("account.html", createtableform=form, tables=DB.get_tables(current_user.get_id()))


@app.route("/account/deletetable")
#@login_required
def account_deletetable():
    tableid = request.args.get("tableid")
    DB.delete_table(tableid)
    return redirect(url_for('account'))


#visit this to see attention request
@app.route("/dashboard")
#@login_required
def dashboard():
    now = datetime.datetime.now()
    requests = DB.get_requests(current_user.get_id())
    for req in requests:
        deltaseconds = (now - req['time']).seconds
        req['wait_minutes'] = "{}.{}".format(
            (deltaseconds / 60), str(deltaseconds % 60).zfill(2))
    return render_template("dashboard.html", requests=requests)


@app.route("/dashboard/resolve")
#@login_required
def dashboard_resolve():
    request_id = request.args.get("request_id")
    DB.delete_request(request_id)
    return redirect(url_for('dashboard'))


@app.route("/newrequest/<tid>")
def new_request(tid):
    if DB.add_request(tid, datetime.datetime.now()):
        return "Your request has been logged and a waiter will be with you shortly"
    return "There is already a request pending for this table. Please be patient, a waiter will be there ASAP"
