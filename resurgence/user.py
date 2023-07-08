from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for
)
from werkzeug.exceptions import abort

from resurgence.auth import login_required
from resurgence.db import get_db

bp = Blueprint('user', __name__, url_prefix="/user")

def get_post(id, check_author=True):
    info = (
        get_db().execute(
            "SELECT i.id, playlist_title, html_df, created, owner_id, username"
            " FROM info i JOIN user u ON i.owner_id = u.id"
            " WHERE i.id = ?",
            (id,),
        ).fetchone()
    )

    if info is None:
        abort(404, f"Post id {id} doesn't exist.")
    
    if check_author and info['owner_id'] != g.user['id']:
        abort(403)

    return info

@bp.route('/history')
@login_required
def view_history():
    db = get_db()
    info_entries = db.execute(
        "SELECT i.id, playlist_title, html_df, created, owner_id, username"
        " FROM info i JOIN user u ON i.owner_id = u.id"
        " ORDER BY created DESC"
    ).fetchall()
    return render_template('user/history.html', info=info_entries)

@bp.route('/<int:id>/entry.html')
@login_required
def view_entry(id):

    info = get_post(id)

    return render_template('user/entry.html', info=info)

@bp.route('/<int:id>/delete', methods=('POST',))
@login_required
def delete(id):
    get_post(id)
    db = get_db()
    db.execute('DELETE FROM info WHERE id = ?', (id,))
    db.commit()
    return redirect(url_for('home.index'))