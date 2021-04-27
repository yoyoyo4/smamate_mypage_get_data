'''
スマメイトのマイページから戦績データを取得し、テキストファイルとして定期的に出力するプログラム
入力 : スマメイトのマイページURL
処理 : マイページにアクセスし戦績情報を抽出、計算
出力 : マイページURL、今期レート、今期順位、今期勝利数、今期敗北数、連勝数、今期対戦数、今期勝率の各テキストファイル。本pyファイルと同じディレクトリに格納。一定秒数ごとに更新する
'''

import os, time

import requests
import PySimpleGUI as sg
from bs4 import BeautifulSoup


# 入力されたURLがスマメイトマイページのものかどうかをTrue/Falseで返す
def can_access_mypage(mypage_url:str):
	try:
		html=requests.get(mypage_url)
		soup = BeautifulSoup(html.text,"html.parser")
		if "さんのユーザーページ スマメイト" in soup.title.text:
			return True
		else:
			raise Exception
	except:
		return False


# マイページURLを記録したテキストファイルの存在をチェック
# ある場合は中身のURLにアクセスできることを確認してURLを返す
# 無い場合、またはアクセスできない場合は空のテキストを返す
def existing_mypage_URL():
	try:
		with open('マイページURL.txt', mode='r', encoding='UTF-8') as f:
			mypage_url = f.readline()
			if can_access_mypage(mypage_url):
				return mypage_url
			else:
				raise Exception
	except:
		return ""


# マイページ入力ウィンドウを表示し、入力URLからHTMLテキストを取得できるか確認する
# 成功した場合、入力URLをテキストファイルに保存し、入力URLをそのまま返す
# 失敗した場合、URL再入力を求める
# URL修正用にする場合は、old_mypage_urlに修正前のマイページURLを入力する
# 修正用の場合、入力ウィンドウを☓で閉じた場合に修正前のURLを返す
def mypage_URL_input(old_mypage_url:str=""):
	layout = [[sg.Text('スマメイトのマイページURLを入力してください\n例:https://smashmate.net/user/23240/')], 
				[sg.Input(key='-IN-')], 
				[sg.Button('OK', bind_return_key=True)]]
	window = sg.Window('smamate_mypage_get_data', layout)
	while True:
		event, values = window.read()
		if event == sg.WIN_CLOSED:
			if old_mypage_url: # 修正用のウィンドウを閉じたかキャンセルした場合、元々のURLを返す
				return old_mypage_url
			else: # 修正用ではないウィンドウが閉じられた場合、プログラム全体を終了
				exit()
		elif event == "OK":
			mypage_url = values['-IN-']
			if can_access_mypage(mypage_url):
				window.close()
				with open('マイページURL.txt', mode='w', encoding='UTF-8') as w: # アクセス確認したマイページURLを出力
					w.write(mypage_url)
				return mypage_url
			else:
				sg.popup("戦績を取得できません。URLを確認して再入力してください", no_titlebar=True)


# マイページURLにアクセスし、HTMLテキストを返す
def fetch_mypage_text(mypage_url:str):
	html=requests.get(mypage_url)
	soup = BeautifulSoup(html.text,"html.parser")
	return str(soup)


# マイページのHTMLテキストから、出力するデータの辞書を作成して返す
def make_data_dict(mypage_text:str):
	record_text = mypage_text[mypage_text.find("<h2>レーティング対戦</h2>"):mypage_text.find("""<h2 class="mt-5">プロフィール</h2>""")] # 戦績だけ抽出
	record_text = BeautifulSoup(record_text,"html.parser").get_text(strip=True).replace("\t","") # 例:レーティング対戦今期レート1357 (12035位)前日比：-17今期対戦成績43勝 55敗現在2連勝！動画化許可する
	data_dict = {}
	data_dict["今期レート"] = record_text[record_text.find("今期レート")+5:record_text.find("今期レート")+9]
	if data_dict["今期レート"] == "": # 0戦状態のとき
		data_dict = {"今期レート":"1500", "今期順位":"-", "今期勝利数":"0", "今期敗北数":"0", "連勝数":"0", "今期対戦数":"0", "今期勝率":"0%"}
	else:
		data_dict["今期順位"] = record_text[record_text.find("(")+1:record_text.find("位")]
		data_dict["今期勝利数"] = record_text[record_text.find("今期対戦成績")+6:record_text.find("勝")] # ｢連勝｣の｢勝｣もあるが、より手前にある戦績の｢勝｣がヒットする
		data_dict["今期敗北数"] = record_text[record_text.find("勝")+2:record_text.find("敗")]

		winning_streak_idx = record_text.find("連勝") # ｢連勝｣の表記があれば連勝中
		if 0 < winning_streak_idx:
			data_dict["連勝数"] = record_text[record_text.find("現在")+2:winning_streak_idx]
		else:
			data_dict["連勝数"] = "0"

		data_dict["今期対戦数"] = str(int(data_dict["今期勝利数"]) + int(data_dict["今期敗北数"]))
		data_dict["今期勝率"] = str(int(round(100*int(data_dict["今期勝利数"])/int(data_dict["今期対戦数"])))) + "%"

	return data_dict


# データ辞書の各値を別々のテキストファイルに出力
def output_data(data_dict:dict):
	for s in data_dict.keys():
		with open(s+'.txt', mode='w', encoding='UTF-8') as w:
			w.write(data_dict[s])


# アクセス先と次回更新までの秒数を表示しつつ、テキストファイルを更新し続ける
def update_text_files_while_showing_status(mypage_url:str):
	mypage_text = fetch_mypage_text(mypage_url)
	soup = BeautifulSoup(mypage_text, "html.parser")
	access_timeout_sec = 30 # この秒数ごとに更新。30未満の値には設定しないこと！
	layout = [[sg.Text('以下のページにアクセス中\n\n' + soup.title.text + "\n" + mypage_url + "\n", key="text_access")], 
				[sg.Text('次回更新まであと' + str(access_timeout_sec) + "秒", key="text_update")], 
				[sg.Button('終了'), sg.Button('アクセスページ変更')]]
	window = sg.Window('smamate_mypage_get_data', layout)
	start_time = int(time.time())

	while True:
		event, _ = window.read(timeout=100)
		if event in [sg.WIN_CLOSED, "終了"]: # ウィンドウを閉じたor終了を押したとき、プログラム全体を終了
			exit()

		elif event == "アクセスページ変更":
			old_mypage_url = mypage_url
			mypage_url = mypage_URL_input(old_mypage_url)
			if mypage_url == old_mypage_url: # キャンセル連打で連続アクセスしないように処理
				pass
			else: # URLを修正して各種変数とテキストファイルを更新
				mypage_text = fetch_mypage_text(mypage_url)
				data_dict = make_data_dict(mypage_text)
				output_data(data_dict)
				soup = BeautifulSoup(mypage_text, "html.parser")
				window['text_access'].update('以下のページにアクセス中\n\n' + soup.title.text + "\n" + mypage_url + "\n")

		elif access_timeout_sec <= int(time.time()) - start_time: # 更新秒数以上経ったらテキストファイルを更新
			mypage_text = fetch_mypage_text(mypage_url)
			data_dict = make_data_dict(mypage_text)
			output_data(data_dict)
			start_time = int(time.time())

		else:
			window['text_update'].update('次回更新まで あと' + str(access_timeout_sec - (int(time.time()) - start_time)) + "秒")



def main():
	os.chdir(os.path.dirname(os.path.abspath(__file__))) # 本pyファイルのディレクトリに移動
	mypage_url = existing_mypage_URL() # 保存されたマイページURLを読み込む
	if not mypage_url: # 読み込めないときは新規入力
		mypage_url = mypage_URL_input()
	update_text_files_while_showing_status(mypage_url)

if __name__ == '__main__':
    main()