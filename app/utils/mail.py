# -*- coding: utf-8 -*-
"""
军书：发信、列表、阅读、领取附物、弃书

信件内容见 app/mail_data.py；附物格式与发放见 app/rewards.py。
"""
import json
from datetime import datetime, timedelta

from app.models import db, Mail, Stage, UserStageProgress
from app.rewards import grant

# 列表最多显示的信件数（按时间倒序）
MAIL_LIST_LIMIT = 100


# ============ 发信 ============

def send_mail(user_id, title, body='', sender='军 府', rewards=None, tag=None, expire_days=None):
    """给一名玩家发信；只加进 session，由调用方提交。

    tag 非空时同一玩家只发一次，已发过返回 None。
    """
    if tag and Mail.query.filter_by(user_id=user_id, tag=tag).first():
        return None
    mail = Mail(
        user_id=user_id, title=title, body=body, sender=sender, tag=tag,
        attachments=json.dumps(rewards or [], ensure_ascii=False),
        expires_at=datetime.utcnow() + timedelta(days=expire_days) if expire_days else None,
    )
    db.session.add(mail)
    return mail


def send_template(user_id, tpl):
    """按 app/mail_data.py 里的模板发信（带 tag 去重）"""
    return send_mail(user_id, tpl['title'], tpl['body'], tpl['sender'], tpl['rewards'], tag=tpl['tag'])


def check_chapter_cleared(user_id, stage):
    """某主线关卡首通后调用：该章主线全部通关时发平定之赏（每章一次）"""
    from app.mail_data import chapter_mail

    if stage.stage_type != 'main':
        return None
    total = Stage.query.filter_by(stage_type='main', chapter=stage.chapter).count()
    cleared = UserStageProgress.query.join(Stage, UserStageProgress.stage_id == Stage.id).filter(
        UserStageProgress.user_id == user_id, UserStageProgress.is_cleared.is_(True),
        Stage.stage_type == 'main', Stage.chapter == stage.chapter).count()
    if total and cleared >= total:
        return send_template(user_id, chapter_mail(stage.chapter))
    return None


# ============ 查询 ============

def _visible(user_id):
    now = datetime.utcnow()
    return Mail.query.filter(
        Mail.user_id == user_id, Mail.deleted_at.is_(None),
        db.or_(Mail.expires_at.is_(None), Mail.expires_at > now))


def unread_count(user_id):
    return _visible(user_id).filter(Mail.is_read.is_(False)).count()


def _attachments(mail):
    try:
        return json.loads(mail.attachments or '[]')
    except ValueError:
        return []


def _has_loot(mail):
    return bool(_attachments(mail)) and mail.claimed_at is None


def mail_payload(mail):
    return {
        'id': mail.id,
        'title': mail.title,
        'sender': mail.sender,
        'body': mail.body,
        'attachments': _attachments(mail),
        'is_read': bool(mail.is_read),
        'claimed': mail.claimed_at is not None,
        'created_at': mail.created_at.isoformat() + 'Z' if mail.created_at else None,
        'expires_at': mail.expires_at.isoformat() + 'Z' if mail.expires_at else None,
    }


def mail_state(user_id):
    """军书弹层全部数据：信件（新的在前）与未读数"""
    mails = _visible(user_id).order_by(Mail.created_at.desc(), Mail.id.desc()).limit(MAIL_LIST_LIMIT).all()
    return {'mails': [mail_payload(m) for m in mails], 'unread': unread_count(user_id)}


def get_mail(user_id, mail_id):
    if not isinstance(mail_id, int) or isinstance(mail_id, bool):
        return None
    return _visible(user_id).filter(Mail.id == mail_id).first()


# ============ 操作 ============

def mark_read(user_id, mail_id):
    mail = get_mail(user_id, mail_id)
    if mail is None:
        return '军书不存在'
    mail.is_read = True
    db.session.commit()
    return None


def claim(user, mail_ids):
    """领取若干封信的附物（已领、无附物的跳过）。

    用条件更新占住 claimed_at，并发重复点击只有一次能领到。
    Returns:
        (领到的奖励列表, 领取的信件数)
    """
    now = datetime.utcnow()
    gained, count = [], 0
    for mail in _visible(user.id).filter(Mail.id.in_(mail_ids), Mail.claimed_at.is_(None)).all():
        rewards = _attachments(mail)
        if not rewards:
            continue
        won = Mail.query.filter(Mail.id == mail.id, Mail.claimed_at.is_(None)).update(
            {'claimed_at': now, 'is_read': True}, synchronize_session=False)
        if not won:
            continue
        grant(user, rewards)
        gained.extend(rewards)
        count += 1
    db.session.commit()
    return gained, count


def claimable_ids(user_id):
    return [m.id for m in _visible(user_id).filter(Mail.claimed_at.is_(None)).all() if _attachments(m)]


def delete(user_id, mail_ids):
    """弃书：附物未领的信不能删。Returns: (删除数, 错误信息或 None)"""
    mails = _visible(user_id).filter(Mail.id.in_(mail_ids)).all()
    if any(_has_loot(m) for m in mails):
        return 0, '附物未领，不可弃书'
    now = datetime.utcnow()
    for m in mails:
        m.deleted_at = now
    db.session.commit()
    return len(mails), None


def read_ids(user_id):
    """「清已阅」的对象：已读且无未领附物的信"""
    return [m.id for m in _visible(user_id).filter(Mail.is_read.is_(True)).all() if not _has_loot(m)]
