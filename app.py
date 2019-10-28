#! -*- coding:utf-8 -*-
import numpy as np
from flask import Flask, url_for
from flask import request
from werewolf import Room, GameRound, Game, err_reason
import json
import logging

logger = logging.getLogger('app.module')

app = Flask(__name__)
static_folder = '/home/philyang/git/wow/static'

global room_one, game_one, game_round
# 9 players
board = [1,1,1,2,3,4,6,6,6]

debug_board = [1,2,3,4,5,6,7]

boards = {
    '1':[1,1,1,2,3,4,6,6,6]
}
np.random.shuffle(board)
board.insert(0,0)

room_one = Room(8)
game_one = None
game_round = None

# 构造返回消息
def encode_response(result=0, error_code='success'):
    reason = err_reason(error_code)
    return json.dumps({'code': result, 'reason': reason}, ensure_ascii=False) 

def round_verify(code):
    if game_one is None or game_one.status() != 1:
        return -1, 'game_not_start'

    seat = room_one.seat(code)
    if game_round.verify(seat) is not True:
        return -1, 'not_your_round'
    
    return 0, ''

# 重新创建房间
@app.route('/wow/recreate', methods=['GET', 'POST'])
def recreate():
    global room_one, game_one, game_round
    
    room_one = Room(8)
    game_one = None
    game_round = None
    return encode_response()

# 选择座位
@app.route('/wow/sit', methods=['GET', 'POST'])
def sit():
    global room_one, game_one, game_round
    
    player_no = int(request.args.get("player_no"))
    code = request.args.get("code")
    
    ret, res = room_one.sit(player_no, code)
    return json.dumps({'code': ret, 'reason': res}, ensure_ascii=False)

# 重新开始游戏
@app.route('/wow/restart', methods=['GET', 'POST'])
def restart():
    global room_one, game_one, game_round
    
    player_no = int(request.args.get("player_no"))
    code = request.args.get("code")
    
    if room_one.seat(code) != 0:
        return encode_response(-1, 'moderator_only')
    else:
        # 9 players
#         board = [1,1,1,2,3,4,6,6,6]
        board = debug_board
        np.random.shuffle(board)
        board.insert(0,0)

        game_one = Game(board, room_one)
        game_round = GameRound(game_one)
    
    return encode_response()

# 开始游戏
@app.route('/wow/start', methods=['GET', 'POST'])
def start():
    global room_one, game_one, game_round
    
    player_no = int(request.args.get("player_no"))
    code = request.args.get("code")
    
    if room_one.seat(code) != 0:
        return encode_response(-1, 'moderator_only')
    else:
        if game_one is None:
            # 9 players
#             board = [1,1,1,2,3,4,6,6,6]
            board = debug_board
            np.random.shuffle(board)
            board.insert(0,0)

            game_one = Game(board, room_one)
            game_round = GameRound(game_one)
            game_one.start()
        else:
            game_one.start()

    return encode_response()

# 获取最新信息
@app.route('/wow/refresh', methods=['GET', 'POST'])
def refresh():
    
    player_no = int(request.args.get("player_no"))
    code = request.args.get("code")
    
    player_array = []
    isModerator = room_one.isModerator(code)
    started = False
    role = 6
    roleView = ''
    seat = room_one.seat(code)
    round_now = 0
    
    if game_one is not None:
        started = (game_one.status() == 1)
        players = game_one.players()
        round_now = game_round.now()
        player_array = []
        if (seat >= 0):
            role = players[seat].role
            roleView = game_round.roleView(role)
            
#         if (seat == 0):
            for player in players:
                ndict = player.to_dict()
                player_array.append(ndict)   

    return json.dumps({'code': 0, 
                       'reason': 'success', 
                       'started':started,
                       'isModerator':isModerator,
                       'seat':seat,
                       'role':role,
                       'roleView':roleView,
                       'round':round_now,
                       'seats':room_one.players(),
                       'players':player_array}, ensure_ascii=False)

# 完成当前步骤，游戏继续
@app.route('/wow/go', methods=['GET', 'POST'])
def go():
    player_no = int(request.args.get("player_no"))
    code = request.args.get("code")
    
    if game_one is None or game_one.status() != 1:
        return encode_response(-1, 'game_not_start')

    seat = room_one.seat(code)
    if game_round.verify(seat) is not True:
        return encode_response(-1, 'not_your_round')
    
    game_round.go()
    return encode_response()

# 玩家出局
@app.route('/wow/out', methods=['GET', 'POST'])
def out():
    player_no = int(request.args.get("player_no"))
    code = request.args.get("code")
    
    if game_one is None or game_one.status() != 1:
        return encode_response(-1, 'game_not_start')
    
    if room_one.seat(code) != 0:
        return encode_response(-1, 'moderator_only')
    
    game_one.out(player_no)
    return encode_response()

# 验人
@app.route('/wow/inspect', methods=['GET', 'POST'])
def inspect():
    player_no = int(request.args.get("player_no"))
    code = request.args.get("code")
    
    ret, err = round_verify(code)
    if ret < 0:
        return encode_response(ret, err)
    
    if game_round.inspect(player_no) is not True:
        return encode_response(-1, 'inspect_reject')
    
#     game_round.go()
    return encode_response()

# 守人
@app.route('/wow/guard', methods=['GET', 'POST'])
def guard():
    player_no = int(request.args.get("player_no"))
    code = request.args.get("code")
    
    ret, err = round_verify(code)
    if ret < 0:
        return encode_response(ret, err)
    
    if game_round.guard(player_no) is not True:
        return encode_response(-1, 'guard_reject')

#     game_round.go()
    return encode_response()

# 刀人
@app.route('/wow/attack', methods=['GET', 'POST'])
def attack():
    player_no = int(request.args.get("player_no"))
    code = request.args.get("code")
    
    ret, err = round_verify(code)
    if ret < 0:
        return encode_response(ret, err)
    
    if game_round.attack(player_no) is not True:
        return encode_response(-1, 'attack_reject')
    
#     game_round.go()
    return encode_response() 

# 撒毒
@app.route('/wow/poison', methods=['GET', 'POST'])
def poison():
    player_no = int(request.args.get("player_no"))
    code = request.args.get("code")
    
    ret, err = round_verify(code)
    if ret < 0:
        return encode_response(ret, err)
    
    if game_round.poison(player_no) is not True:
        return encode_response(-1, 'medicine_reject')
    
#     game_round.go()
    return encode_response() 

# 救人
@app.route('/wow/rescue', methods=['GET', 'POST'])
def rescue():
    player_no = int(request.args.get("player_no"))
    code = request.args.get("code")
    
    ret, err = round_verify(code)
    if ret < 0:
        return encode_response(ret, err)
    
    if game_round.rescue() is not True:
        return encode_response(-1, 'medicine_reject')

#     game_round.go()
    return encode_response() 

# then start the server
if __name__ == "__main__":
    print(("* Loading Keras model and Flask starting server..."
        "please wait until server has fully started"))
    app.run(host='0.0.0.0',port=8989,debug=True)
