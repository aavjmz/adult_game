"""
匹配队列系统
负责玩家匹配逻辑
"""
import time
from typing import Dict, Optional, List
from collections import deque


class MatchRequest:
    """匹配请求"""

    def __init__(self, player_id: str, socket_id: str, mode: str, rank: int = 0):
        self.player_id = player_id
        self.socket_id = socket_id
        self.mode = mode  # 'pvp' or 'pve'
        self.rank = rank
        self.timestamp = time.time()

    def __repr__(self):
        return f"MatchRequest({self.player_id}, {self.mode}, rank={self.rank})"


class MatchQueue:
    """匹配队列管理器"""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.pvp_queue = deque()
            cls._instance.pve_queue = deque()
            cls._instance.player_requests: Dict[str, MatchRequest] = {}
        return cls._instance

    def add_to_queue(self, player_id: str, socket_id: str, mode: str = 'pvp', rank: int = 0):
        """添加玩家到匹配队列"""
        # 如果玩家已经在队列中，先移除
        self.remove_from_queue(player_id)

        request = MatchRequest(player_id, socket_id, mode, rank)
        self.player_requests[player_id] = request

        if mode == 'pvp':
            self.pvp_queue.append(request)
        else:
            self.pve_queue.append(request)

        return True

    def remove_from_queue(self, player_id: str):
        """从队列中移除玩家"""
        if player_id not in self.player_requests:
            return False

        request = self.player_requests[player_id]

        if request.mode == 'pvp':
            self.pvp_queue = deque([r for r in self.pvp_queue if r.player_id != player_id])
        else:
            self.pve_queue = deque([r for r in self.pve_queue if r.player_id != player_id])

        del self.player_requests[player_id]
        return True

    def find_match(self, player_id: str) -> Optional[MatchRequest]:
        """为玩家寻找匹配对手"""
        if player_id not in self.player_requests:
            return None

        request = self.player_requests[player_id]

        if request.mode == 'pve':
            # PVE模式立即匹配（对抗AI）
            return request

        # PVP模式：查找合适的对手
        for opponent_request in self.pvp_queue:
            if opponent_request.player_id != player_id:
                # 检查段位是否接近（简单匹配逻辑）
                rank_diff = abs(request.rank - opponent_request.rank)
                if rank_diff <= 200:  # 段位差距不超过200
                    # 找到匹配，从队列中移除双方
                    self.remove_from_queue(player_id)
                    self.remove_from_queue(opponent_request.player_id)
                    return opponent_request

        return None

    def get_queue_position(self, player_id: str) -> int:
        """获取玩家在队列中的位置"""
        if player_id not in self.player_requests:
            return -1

        request = self.player_requests[player_id]
        queue = self.pvp_queue if request.mode == 'pvp' else self.pve_queue

        for i, req in enumerate(queue):
            if req.player_id == player_id:
                return i

        return -1

    def get_queue_length(self, mode: str = 'pvp') -> int:
        """获取队列长度"""
        if mode == 'pvp':
            return len(self.pvp_queue)
        else:
            return len(self.pve_queue)

    def is_in_queue(self, player_id: str) -> bool:
        """检查玩家是否在队列中"""
        return player_id in self.player_requests

    def clear_old_requests(self, max_age: int = 300):
        """清除超时的匹配请求（默认5分钟）"""
        current_time = time.time()
        expired_players = []

        for player_id, request in self.player_requests.items():
            if current_time - request.timestamp > max_age:
                expired_players.append(player_id)

        for player_id in expired_players:
            self.remove_from_queue(player_id)

        return len(expired_players)
