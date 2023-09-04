from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for
)
from werkzeug.exceptions import abort

from resurgence.auth import login_required
from resurgence.db import get_db
import get_video_info

bp = Blueprint('user', __name__, url_prefix="/user")

def get_post(id, check_author=True):
    info = (
        get_db().execute(
            "SELECT i.playlist_id, playlist_title, created, owner_id, username"
            " FROM playlist i JOIN user u ON i.owner_id = u.id"
            " WHERE i.playlist_id = ?",
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
        "SELECT i.playlist_id, playlist_title, created, owner_id, username"
        " FROM playlist i JOIN user u ON i.owner_id = u.id"
        " ORDER BY created DESC"
    ).fetchall()
    return render_template('user/history.html', info=info_entries)

@bp.route('/<int:id>/entry.html')
@login_required
def view_entry(id):

    get_video_info.top_k_frequent_tags(id, 5)

    playlist = get_post(id)
    db = get_db()
    videos = db.execute(
        "SELECT * FROM video WHERE playlist_id = ?", (id,)
    ).fetchall()
    
    video_list = []
    for v in videos:
        video_list.append({k: v[k] for k in v.keys()})
        tag_list = db.execute(
            "SELECT tag_text FROM tag WHERE video_id = ?", (v['video_id'],)
        ).fetchall()
        tag_list = [tag[0] for tag in tag_list]
        tags_string = ", "
        tags_string = tags_string.join(tag_list)
        video_list[-1]['tags'] = tags_string

    return render_template('user/entry.html', playlist=playlist, videos=video_list)

@bp.route('/<int:id>/delete', methods=('POST',))
@login_required
def delete(id):
    get_post(id)
    db = get_db()
    db.execute('DELETE FROM playlist WHERE playlist_id = ?', (id,))
    db.commit()
    return redirect(url_for('home.index'))