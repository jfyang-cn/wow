#! -*- coding:utf-8 -*-

characters = [
    'Moderator', # 0
    'Werewolf', # 1
    'Seer',      # 2
    'Witch',     # 3
    'Hunter',    # 4
    'Savior',    # 5
    'Villager',  # 6
]

# characters = [
#     '法官',     # 0
#     '狼人',     # 1
#     '预言家',   # 2
#     '女巫',     # 3
#     '猎人',     # 4
#     '守卫',     # 5
#     '村民',     # 6
# ]

info = {
    'is_werewolf': '%d号玩家的身份是狼人',
    'not_werewolf': '%d号玩家的身份不是狼人',
    'poisoned': '%d号玩家被毒',
    'rescued': '%d号玩家被救',
    'guarded': '%d号玩家被守护',
    'attacked': '%d号玩家被攻击',
    'round': '当前是%s的操作时间',
    'player_out': '%d号玩家出局',
    'has_gun': '你的开枪状态是%s',
    'player_die': '%d号玩家死亡',
}

def info_arg1(key, arg1):
    return info[key] % (arg1)

class Room:
    
    def __init__(self):
        self.clear()

    # 清除座位信息
    def clear(self):
        self._seats=['']*10
        
        # debugging
        for i in range(len(self._seats)):
            self._seats[i] = str(i)
    
    # 选择座位
    def sit(self, seat_no, code):
        if self._seats[seat_no] == '':
            for seat in self._seats:
                # 禁止code相同
                if seat == code:
                    return False

            self._seats[seat_no] = code
            return True
        return False
    
    # 获取玩家号
    def seat(self, code):
        if code != '':
            for i in range(10):
                if self._seats[i] == code:
                    return i
        return -1
    
    # 获取所有玩家的标识
    def players(self):
        return self._seats
    
    # 获取玩家的标识
    def whois(self, i):
        return self._seats[i]
    
    # 当前玩家是否为法官
    def isModerator(self, code):
        return self._seats[0] == code

class Player:
    
    def __init__(self, seat, role, code):
        
        self.seat = seat
        self.role = role
        self.alive = True
        self.code = code
        
    def to_dict(self):
        ndict = {}
        ndict['seat'] = self.seat
        ndict['role'] = self.role
        ndict['alive'] = self.alive
        ndict['code'] = self.code
        return ndict
        
class Game:
    
    def __init__(self, board, players):
        self.board = board
        
        self._players = []
        
        # 每局游戏只能毒，救，开枪一次
        self._poisoned = -1
        self._rescued = -1
        self._gun = True
        self._guarded = -1   # 上一晚守护的玩家
                
        self._status = 0   # 0 not started, 1 playing, 2 end
        
        for i in range(10):
            self._players.append(Player(i, board[i], players[i]))

    # 开始游戏
    def start(self):
        self._status = 1
        return self._status
    
    # 当前游戏状态， 0：未开始，1：进行中，2：结束
    def status(self):
        return self._status

    # 获取猎人的玩家号
    def hunter(self):
        for player in self._players:
            if player.role == 4:
                return player.seat
        return -1   

    # 获取所有玩家信息
    def players(self):
        return self._players    
    
    # 请一位玩家出局
    def out(self, player_no):
        if player_no > 0:
            self._players[player_no].alive = False
    
    # 复活一位玩家
    def revive(self, player_no):
        if player_no > 0: 
            self._players[player_no].alive = True
    
    # 撒毒一位玩家
    def poison(self, player_no):
        if self._poisoned == -1 and player_no > 0:
            self._poisoned = player_no
            self.out(player_no)
            
            # 如果玩家是猎人则吞枪
            if self._players[player_no].role == 4:
                self._gun = False
        return
    
    # 救一位玩家
    def rescue(self, player_no):
        if self._rescued == -1 and player_no > 0:
            self._rescued = player_no
            self.revive(player_no)
        return

    # 守护一位玩家
    def guard(self, player_no):
        self._guarded = player_no
    
    # 开枪状态
    def hasGun(self):
        return self._gun
    
    # 猎人吞枪
    def noGun(self):
        self._gun = False
    
    # 是否有毒药
    def hasPoison(self):
        return self._poisoned == -1
    
    # 是否有解药
    def hasCure(self):
        return self._rescued == -1
    
    # 上一晚守护的玩家
    def lastGuarded(self):
        return self._guarded


class GameRound():

    def __init__(self, game):            
        self.game = game
        self.clear()
        
    def clear(self):
        self.steps = [0,2,1,3,4]  # Seer, Werewolf, Witch, Hunter
        self._current = 0
        
        # 每轮游戏可守，可查，可刀
        self._guarded = -1
        self._attacked = -1
        self._inspected = -1
        
        # 记录每轮的操作
        self._poisoned = -1
        self._rescued = -1
        
        self._last_audit = []
    
    # 游戏继续
    def go(self):
        if self._current == 0:
            self.clear()
        
        self._current = self._current + 1
        if self._current == len(self.steps):
            self._current = 0
            self.audit()

        return self.now()
    
    # 检查当前玩家操作轮次
    def verify(self, seat):
        if self.game.players()[seat].role == 0:
            return True
        
        return self.now() == self.game.players()[seat].role

    # 当前角色的轮次
    def now(self):
        return self.steps[self._current]
    
    # 获取角色的视角
    def roleView(self, role):
        
        if role == 0:
            ret = ''
            if len(self._last_audit) > 0:
                for i in self._last_audit:
                    ret += info_arg1('player_die', i)
                    ret += ' '
            else:
                ret = '昨夜没有玩家死亡'
            return ret
        elif role == 2:            # Seer
            if self._inspected > 0:
                if (self.game.players()[self._inspected].role == 1):
                    return info_arg1('is_werewolf', self._inspected)
                else:
                    return info_arg1('not_werewolf', self._inspected)
        elif role == 3:       # Witch
            if self._rescued == -1 and self._attacked > 0:
                return info_arg1('attacked', self._attacked)
            else:
                return ''
        elif role == 4:       # Hunter
            if self.game.hasGun():
                return info_arg1('has_gun', 'YES')
            else:
                return info_arg1('has_gun', 'NO')
        else:
            return ''
        
        return ''

    # 验人
    def inspect(self, player_no):
        if self._inspected <= 0:
            self._inspected = player_no
            return True
        return False

    # 守人
    def guard(self, player_no):
        if self._guarded <= 0:
            if player_no > 0:
                self._guarded = player_no
                return True
        return False

    # 刀人
    def attack(self, player_no):
        if self._attacked <= 0:
            self._attacked = player_no
            return True
        return False
        
    # 毒人
    def poison(self, player_no):
        # 有药
        if self.game.hasPoison():
            # 本轮没有使用过任何药
            if self._poisoned == -1 and self._rescued == -1 and player_no > 0:
                self._poisoned = player_no
                # 猎人吞枪
                if player_no == self.game.hunter():
                    self.game.noGun()
                return True
        return False
    
    # 救人
    def rescue(self):
        # 有药
        if self.game.hasCure():
            # 本轮没有使用过任何药
            if self._rescued == -1 and self._poisoned == -1:
                self._rescued = self._attacked
                return True
        return False
    
    # 天亮
    def audit(self):
        
        self._last_audit.clear()
        
        # 检查守卫是否连续两晚守了同一个人
        if self._guarded > 0 and self._guarded == self.game.lastGuarded():
            # 更新守护信息
            self.game.guard(self._guarded)
            # 使当前守护信息无效
            self._guarded = 0
        else:
            # 更新守护信息
            self.game.guard(self._guarded)
        
        # 毒
        if self._poisoned > 0:
            self.game.poison(self._poisoned)
            self._last_audit.append(self._poisoned)
        
        # 刀
        self.game.out(self._attacked)
        
        # 同守同救
        if self._rescued > 0 and self._guarded == self._rescued:
            self._last_audit.append(self._attacked)
        else:
            alive = False # 是否被救
            # 女巫救人
            if self._rescued > 0:
                self.game.rescue(self._rescued)
                alive = True
        
            # 守卫守对了人
            if self._guarded > 0 and self._guarded == self._attacked:
                self.game.revive(self._guarded)
                alive = True

            if alive is not True and self._attacked > 0:
                self._last_audit.append(self._attacked)
            

    # 获取前一晚的信息
    def lastAudit(self):
        return self._last_audit