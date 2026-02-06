"""
游戏房间管理器
负责创建、管理和销毁游戏房间
"""
import uuid
from datetime import datetime
from typing import Dict, Optional, List


class GameRoom:
    """游戏房间类"""

    def __init__(self, room_id: str, mode: str = 'pvp'):
        self.room_id = room_id
        self.mode = mode  # 'pvp' or 'pve'
        self.players = []  # 玩家列表
        self.player_sids = {}  # {player_id: socket_id}
        self.state = 'waiting'  # waiting, playing, finished
        self.current_turn = None
        self.turn_number = 0
        self.game_state = {}
        self.created_at = datetime.now()
        self.max_players = 2

    def add_player(self, player_id: str, socket_id: str, player_data: dict):
        """添加玩家到房间"""
        if len(self.players) >= self.max_players:
            return False

        player_info = {
            'player_id': player_id,
            'socket_id': socket_id,
            'username': player_data.get('username', f'Player{player_id[:6]}'),
            'deck': player_data.get('deck', []),
            'ready': False
        }

        self.players.append(player_info)
        self.player_sids[player_id] = socket_id

        # 如果房间满了，准备开始游戏
        if len(self.players) == self.max_players:
            self.state = 'ready'

        return True

    def remove_player(self, player_id: str):
        """移除玩家"""
        self.players = [p for p in self.players if p['player_id'] != player_id]
        if player_id in self.player_sids:
            del self.player_sids[player_id]

        # 如果游戏进行中有人离开，结束游戏
        if self.state == 'playing' and len(self.players) < self.max_players:
            self.state = 'finished'

    def is_full(self):
        """房间是否已满"""
        return len(self.players) >= self.max_players

    def get_opponent(self, player_id: str):
        """获取对手信息"""
        for player in self.players:
            if player['player_id'] != player_id:
                return player
        return None

    def to_dict(self):
        """转换为字典格式"""
        return {
            'room_id': self.room_id,
            'mode': self.mode,
            'state': self.state,
            'players': self.players,
            'current_turn': self.current_turn,
            'turn_number': self.turn_number
        }


class RoomManager:
    """房间管理器单例"""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.rooms: Dict[str, GameRoom] = {}
            cls._instance.player_rooms: Dict[str, str] = {}  # {player_id: room_id}
        return cls._instance

    def create_room(self, mode: str = 'pvp') -> GameRoom:
        """创建新房间"""
        room_id = str(uuid.uuid4())
        room = GameRoom(room_id, mode)
        self.rooms[room_id] = room
        return room

    def get_room(self, room_id: str) -> Optional[GameRoom]:
        """获取房间"""
        return self.rooms.get(room_id)

    def get_player_room(self, player_id: str) -> Optional[GameRoom]:
        """获取玩家所在的房间"""
        room_id = self.player_rooms.get(player_id)
        if room_id:
            return self.rooms.get(room_id)
        return None

    def join_room(self, room_id: str, player_id: str, socket_id: str, player_data: dict) -> bool:
        """加入房间"""
        room = self.get_room(room_id)
        if not room:
            return False

        if room.add_player(player_id, socket_id, player_data):
            self.player_rooms[player_id] = room_id
            return True
        return False

    def leave_room(self, player_id: str):
        """离开房间"""
        room = self.get_player_room(player_id)
        if room:
            room.remove_player(player_id)
            if player_id in self.player_rooms:
                del self.player_rooms[player_id]

            # 如果房间空了，删除房间
            if len(room.players) == 0:
                if room.room_id in self.rooms:
                    del self.rooms[room.room_id]

    def find_available_room(self, mode: str = 'pvp') -> Optional[GameRoom]:
        """查找可用的房间"""
        for room in self.rooms.values():
            if room.mode == mode and room.state == 'waiting' and not room.is_full():
                return room
        return None

    def get_all_rooms(self) -> List[GameRoom]:
        """获取所有房间"""
        return list(self.rooms.values())

    def get_room_count(self) -> int:
        """获取房间总数"""
        return len(self.rooms)
