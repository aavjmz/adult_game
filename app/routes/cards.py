from flask import Blueprint, render_template, jsonify
from flask_login import login_required, current_user
from app.models import db, Card, UserCard
from config import Config

bp = Blueprint('cards', __name__, url_prefix='/cards')

@bp.route('/')
@login_required
def index():
    """卡牌列表页面"""
    user_cards = UserCard.query.filter_by(user_id=current_user.id).all()
    return render_template('cards.html', user_cards=user_cards, rarities=Config.CARD_RARITIES)

@bp.route('/collection')
@login_required
def collection():
    """查看所有可收集的卡牌"""
    all_cards = Card.query.all()
    user_card_ids = [uc.card_id for uc in current_user.user_cards.all()]

    cards_data = []
    for card in all_cards:
        cards_data.append({
            'id': card.id,
            'name': card.name,
            'rarity': card.rarity,
            'attack': card.attack,
            'defense': card.defense,
            'hp': card.hp,
            'is_golden': card.is_golden,
            'image_url': card.image_url,
            'element': card.element,
            'faction': card.faction,
            'job_class': card.job_class,
            'owned': card.id in user_card_ids
        })

    return render_template('collection.html', cards=cards_data, rarities=Config.CARD_RARITIES)

@bp.route('/detail/<int:card_id>')
@login_required
def detail(card_id):
    """卡牌详情"""
    card = Card.query.get_or_404(card_id)
    user_card = UserCard.query.filter_by(user_id=current_user.id, card_id=card_id).first()

    return render_template('card_detail.html', card=card, user_card=user_card, rarities=Config.CARD_RARITIES)

@bp.route('/api/all')
def api_all_cards():
    """API: 获取所有卡牌"""
    cards = Card.query.all()
    return jsonify([{
        'id': c.id,
        'name': c.name,
        'rarity': c.rarity,
        'attack': c.attack,
        'defense': c.defense,
        'hp': c.hp,
        'is_golden': c.is_golden,
        'image_url': c.image_url,
        'element': c.element,
        'faction': c.faction,
        'job_class': c.job_class,
        'skill_name': c.skill_name,
        'skill_description': c.skill_description
    } for c in cards])
