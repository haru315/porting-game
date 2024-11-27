import tkinter as tk
import tkinter.ttk as ttk
import tkinter.messagebox as messagebox
from enum import Enum
import random
import time
import os
import json

# 状態を列挙型で定義
class State(Enum):
    SELECT = 1
    GAME = 2        #始める前
    GAME_PLAY = 3   #ゲーム中
    GAME_PLAY_NEXT = 4      #次への遷移用
    GAME_PLAY_RESULT = 5    #終了画面

# モードを配列で用意
game_mode =("足し算", "引き算", "掛け算", "割り算", "クイズ")
game_mode_sign =("+", "-", "×", "÷", "NULL")

# 記録用ファイル名
config_josn_path = "config.json"

# 文章問題用（chatGPT製）
problems = [
    {
        "problem": "食べ物の中で果物の一つは何ですか？",
        "answer": ["りんご", "リンゴ", "林檎"]
    },
    {
        "problem": "人が歩くときに使う足の部分は何ですか？",
        "answer": ["あし", "足"]
    },
    {
        "problem": "朝ごはんによく食べる飲み物は何ですか？",
        "answer": ["みず", "水"]
    },
    {
        "problem": "空に浮かぶ白いものは何ですか？",
        "answer": ["くも", "雲"]
    },
    {
        "problem": "動物の中で犬の仲間は何と呼ばれますか？",
        "answer": ["いぬ", "イヌ", "犬"]
    },
    {
        "problem": "冬に寒い時に着るものは何ですか？",
        "answer": ["こたつ", "炬燵"]
    },
    {
        "problem": "家の中で寝る場所はどこですか？",
        "answer": ["へや", "部屋"]
    },
    {
        "problem": "みんなが集まる場所は何と呼ばれますか？",
        "answer": ["こうえん", "公園"]
    },
    {
        "problem": "お金を入れるものは何ですか？",
        "answer": ["さいふ", "財布"]
    },
    {
        "problem": "ひとが住むところを何と呼びますか？",
        "answer": ["いえ", "家"]
    }
]

class App(tk.Tk):

    # show_○○系は、シーンフレーム操作関数
    def show_select(self):
        """セレクト画面への遷移"""
        self.state = State.SELECT
        self.score_list_updated()
        # Aフレームを最前列に
        self.screen_a.tkraise()

    def score_list_updated(self):
        """ リストの更新 """
        self.game_mode = self.combo_a.get()
        self.game_mode_id = game_mode.index(self.game_mode)

        # ハイスコアリストの表示処理
        if self.check_var_a.get():
            results = self.game_endless_mode_results[self.game_mode_id]
        else :
            results = self.game_mode_results[self.game_mode_id]
        results = sorted(results, reverse=True, key=lambda x: x[0])  #[0]に注目して降順ソート

        if self.check_var_a.get():
            formatted_temps = [f" {temp[0]}点、レベル{temp[1]}、{temp[2]}秒" for temp in results]
        else :
            formatted_temps = [f" {temp[0]}点、{temp[1]}秒" for temp in results]
        self.list_a_cnames.set(formatted_temps)
 
    def quit(self):
        """ アプリの終了 """
        self.save_json()
        self.destroy()

    def game_update(self):
        """ゲーム画面のアップデート・リセット"""
        self.label_b["text"] = f"{self.game_mode}ゲーム"
        if self.check_var_a.get():
            self.score_b["text"] = f" {self.points}点 残りチャンス{self.chance_point}"
        else :
            self.score_b["text"] = f" {self.points}点"

    def show_game(self):
        """ゲーム画面への遷移"""
        self.state = State.GAME
        self.game_mode = self.combo_a.get()
        self.game_mode_id = game_mode.index(self.game_mode)
        self.points = 0
        self.num_questions = 0
        self.game_level = 0
        self.chance_point = self.chance_point_max
        
        # 画面の更新
        self.game_update()
        self.button_b["text"] = "スタート"

        # UI配置変更処理
        if self.game_mode_id >= 0 and self.game_mode_id <= 3:
            # 四則演算問題の場合
            self.problem_b["text"] = f"??{game_mode_sign[self.game_mode_id]}??="
            self.problem_b.pack(side = tk.LEFT)
            self.element_sub_b.pack(side = tk.LEFT)
            self.entry_b["width"]=5
        elif self.game_mode_id == 4:
            # クイズの場合
            self.problem_b["text"] = f"Q:????"
            self.problem_b.pack(side = tk.TOP)
            self.element_sub_b.pack(side = tk.TOP)
            self.entry_b["width"]=15
        self.entry_b.delete(0, tk.END)

        # Bフレームを最前列に
        self.screen_b.tkraise()

    def game_play(self):
        """ゲーム開始"""
        if self.button_b["text"] == "スタート":
            self.state = State.GAME_PLAY_NEXT
            
            self.button_b["text"] = "中断"
            # 計測スタート
            self.timer_start()
            # 問題出題へ
            self.game_next()
        elif self.button_b["text"] == "中断" :
            self.state = State.GAME
            self.button_b["text"] = "スタート"
            # セレクト画面へ
            self.show_select()
    
    def game_next(self):
        """問題出題処理"""
        if self.state == State.GAME_PLAY_NEXT:
            self.state = State.GAME_PLAY
            self.entry_b.delete(0, tk.END)
            self.answer = 0

            if self.game_mode_id >= 0 and self.game_mode_id <= 3:
                # 計算系の問題の場合
                # 問題の最大数
                max_num = 5 + self.num_questions + self.game_level

                a = random.randint(0,max_num)
                b = random.randint(0,max_num)
                self.answer = 0

                # 各モードで出題処理
                if self.game_mode_id == 0:
                    self.answer = a+b
                elif self.game_mode_id == 1:
                    self.answer = a-b
                elif self.game_mode_id == 2:
                    self.answer = a*b
                elif self.game_mode_id == 3:
                    # 必ず割り切れる問題だけにする
                    b = random.randint(1,max_num)
                    self.answer = a
                    a = a*b

                self.game_update()
                self.problem_b["text"] = f"{a}{game_mode_sign[self.game_mode_id]}{b}="
            elif self.game_mode_id == 4:
                # クイズ問題の場合
                qid = random.randint(0,len(problems)-1)

                self.answer = problems[qid]["answer"]
                self.game_update()
                self.problem_b["text"] = f"Q:{problems[qid]["problem"]}"

    def game_result(self):
        """結果・中間結果表示"""
        next = False

        self.chance_point <= 0
        if not self.check_var_a.get():
            # 通常モード
            # 計測終わり
            self.timer_stop()
            # 記録
            self.game_mode_results[self.game_mode_id].append([self.points,round(self.stopTime,1)])
            self.game_mode_results[self.game_mode_id] = sorted(self.game_mode_results[self.game_mode_id])
            if self.points >= self.point_max :
                next = messagebox.askyesno('結果発表', f"お疲れ様です。あなたの点数は、満点です。{round(self.stopTime,1)}秒\n\n続けますか?")
            else :
                next = messagebox.askyesno('結果発表', f"お疲れ様です。あなたの点数は、{self.points}点です。{round(self.stopTime,1)}秒\n\n続けますか?")
        else :
            # エンドレスモード
            if self.chance_point > 0:
                old_level = self.game_level
                self.game_level += 1
                next =  messagebox.askyesno('レベルアップ', f"レベルが上がりました。[ {old_level} ⇒ {self.game_level} ]\n\n続けますか?")
            else :
                next = False
            if not next:
                # 計測終わり
                self.timer_stop()
                # 記録
                self.game_endless_mode_results[self.game_mode_id].append([self.points,self.game_level,round(self.stopTime,1)])
                self.game_endless_mode_results[self.game_mode_id] = sorted(self.game_endless_mode_results[self.game_mode_id])
                messagebox.showinfo('結果発表', f"お疲れ様です。あなたの点数は、{self.points}点、到達レベル{self.game_level}です。{round(self.stopTime,1)}秒")

        # また再度始めるか終えるか分岐
        if next :
            if not self.check_var_a.get():
                self.show_game()
            else :
                self.num_questions = 0
                self.state = State.GAME_PLAY_NEXT
                self.after(self.time_next,self.game_next)
        else :
            self.show_select()

    def checking_answers(self):
        """答え合わせ"""
        if self.state == State.GAME_PLAY :
            try:
                correct = False
                if self.game_mode_id >= 0 and self.game_mode_id <= 3:
                    if self.answer == int(self.entry_b.get()) :
                        correct = True

                elif self.game_mode_id == 4:
                    for a in self.answer:
                        if a == self.entry_b.get():
                            correct = True

                if self.check_var_a.get():
                    # エンドレスモードの処理
                    if correct :
                        self.score_b["text"] = f" 正解"
                        self.points += self.point_add # 加点
                        self.num_questions += 1
                    else :
                        self.score_b["text"] = f" はずれ"
                        self.points -= self.point_reduce # 減点
                        # エンドレスモードの際はチャンスを減らす
                        self.chance_point -= 1
                else :
                    # 通常モードの処理
                    if correct :
                        self.score_b["text"] = f" 正解"
                        self.points += self.point_add # 加点
                    else :
                        self.score_b["text"] = f" はずれ"
                        self.points -= self.point_reduce # 減点
                    # 回答数は非正解でもカウントされる
                    self.num_questions += 1

                if self.num_questions >= self.num_questions_max or self.chance_point <= 0:
                    # 問題数が達するか、チャンスがなくなったら遷移
                    self.state = State.GAME_PLAY_RESULT
                    self.after(self.time_next,self.game_result)
                else :
                    # 待って次
                    self.state = State.GAME_PLAY_NEXT
                    self.after(self.time_next,self.game_next)


            except :
                # エラーになった場合は入力を削除する
                self.entry_b.delete(0, tk.END)
                self.score_b["text"] = f" エラー"

                # エラーの文字を待って消す
                self.after(self.time_next,self.game_update)

    # タイマー関係
    def timer_start(self):
        self.startTime=time.time()
        self.playTime=True
    def timer_stop(self):
        if self.playTime:
            self.stopTime=time.time()-self.startTime
            self.playTime=False
        else :
            self.stopTime= 0.0
    
    # 記録・設定用jsonファイルの書き出し読み込み
    def import_json(self):
        """ 記録・設定読み込み """
        if os.path.exists(config_josn_path):
            file = open(config_josn_path, 'r')
            importData = json.load(file)
            self.time_next = importData["config"]["time_next"]
            self.num_questions_max = importData["config"]["num_questions_max"]
            self.point_max = importData["config"]["point_max"]
            self.chance_point_max = importData["config"]["chance_point_max"]
            
            self.game_mode_results = importData["log"]["game_mode_results"]
            self.game_endless_mode_results = importData["log"]["game_endless_mode_results"]

            return True
        else :
            return False
    def save_json(self):
        """ 記録・設定書き出し """
        saveData = {
            "config":{
                "time_next":self.time_next,
                "num_questions_max":self.num_questions_max,
                "point_max":self.point_max,
                "chance_point_max":self.chance_point_max,
            },
            "log":{
                "game_mode_results":self.game_mode_results,
                "game_endless_mode_results":self.game_endless_mode_results
            }
        }
        file = open(config_josn_path,'w')
        json.dump(saveData,file)

    # 初期化
    def __init__(self):
        super().__init__()
        self.title("脳トレゲーム")
        self.geometry("350x250")
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        if not self.import_json():
            # 設定ファイルが無かった場合の初期値
            # 切り替わりまでの時間(Tick)
            self.time_next = 1000
            # 回答数
            self.num_questions_max = 5
            # 点数最大数
            self.point_max = 100
            # エンドレスモードの際間違ってもいい数
            self.chance_point_max = 5
            # 記録初期化
            self.game_mode_results = [[], [], [], [], []]
            self.game_endless_mode_results = [[], [], [], [], []]
        # チャレンジ数初期化
        self.chance_point = 0
        # 加点数と減点数を設定
        self.point_add = self.point_max / self.num_questions_max
        self.point_reduce = self.point_add * 0.5
        # 難易度用のレベル初期化
        self.game_level = 0
        # タイマー用に初期化
        self.playTime = False
        # ゲームモード初期化
        self.game_mode = game_mode[0]
        # ==== レイアウト ====
        # ==== セレクト画面のフレーム ====
        self.screen_a = tk.Frame(self)
        self.screen_a.grid(row=0, column=0, sticky="nsew")

        self.element_a = tk.Frame(self.screen_a)
        # self.element_a.configure(bg="blue") 確かめ用の色付け
        self.element_a.pack(fill = tk.X)

        # 終了ボタン
        self.end_button_a = tk.Button(self.element_a, text="終了", font = ('MS Gothic', 12), command=self.quit)
        self.end_button_a.pack(side = tk.RIGHT)
        
        # タイトル
        self.title_a = tk.Label(self.element_a, text="ゲームセレクト", font = ('MS Gothic', 20))
        self.title_a.pack()

        self.element_b = tk.Frame(self.screen_a)
        self.element_b.pack(fill=tk.BOTH, expand=True)

        self.element_sub1_b = tk.Frame(self.element_b)
        self.element_sub1_b.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        self.element_sub2_b = tk.Frame(self.element_b)
        self.element_sub2_b.pack(fill=tk.BOTH, expand=True)

        # テキスト1
        self.subtext1_a = tk.Label(self.element_sub1_b, text="記録", font = ('MS Gothic', 10))
        self.subtext1_a.pack(side=tk.TOP)
        # リスト
        self.list_a_cnames = tk.StringVar()
        self.list_a = tk.Listbox(self.element_sub1_b, listvariable=self.list_a_cnames)
        self.list_a.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        # テキスト1
        self.subtext1_a = tk.Label(self.element_sub2_b, text="モード選択", font = ('MS Gothic', 10))
        self.subtext1_a.pack(side=tk.TOP)
        # 選択ボックス
        self.combo_a = ttk.Combobox(self.element_sub2_b ,state="readonly", values=game_mode)
        self.combo_a.set("足し算")
        self.combo_a.bind("<<ComboboxSelected>>",lambda event: self.score_list_updated())
        self.combo_a.pack(expand=True)

        # エンドレスモード用
        self.check_var_a = tk.BooleanVar()
        self.check_a = tk.Checkbutton(self.element_sub2_b ,text = 'エンドレスモード', variable=self.check_var_a, command=self.score_list_updated)
        self.check_a.pack(expand=True)

        # ボタン
        self.button_a = tk.Button(self.element_sub2_b, text="スタート", font = ('MS Gothic', 15), command=self.show_game)
        self.button_a.pack(fill=tk.BOTH, expand=True)


        # ==== ゲーム画面のフレーム ====
        self.screen_b = tk.Frame(self)
        self.screen_b.grid(row=0, column=0, sticky="nsew")

        # タイトル
        self.label_b = tk.Label(self.screen_b, text="○○ゲーム", font = ('MS Gothic', 20))
        self.label_b.pack()

        # フレーム1
        self.element_b = tk.Frame(self.screen_b)
        # self.element_b.configure(bg="blue") #確かめ用の色付け
        self.element_b.pack(fill=tk.Y, expand=True)

        # 計算問題テキスト
        self.problem_b = tk.Label(self.element_b, text="??+??=", font = ('MS Gothic', 12))
        self.problem_b.pack(side = tk.LEFT)

        # フレーム2
        self.element_sub_b = tk.Frame(self.element_b)
        self.element_sub_b.pack(side = tk.LEFT)

        # 回答入力
        self.entry_b = tk.Entry(self.element_sub_b, width=5, textvariable=tk.StringVar(), font = ('MS Gothic', 12))
        self.entry_b.pack(side = tk.LEFT)
        self.entry_b.bind("<Return>",lambda event: self.checking_answers())

        # 点数
        self.score_b = tk.Label(self.element_sub_b, text=" 00点", font = ('MS Gothic', 12))
        self.score_b.pack(side = tk.LEFT)

        #ボタン
        self.button_b = tk.Button(self.screen_b, text="スタート", font = ('MS Gothic', 15), command=self.game_play)
        self.button_b.pack()

        # セレクト画面のフレームを表示
        self.show_select()
    

if __name__ == "__main__":
    app = App()
    app.resizable(width=False, height=False) #ウィンドウを固定サイズに
    app.mainloop()