"""
Copyright (C) 2021 ほーずき(ver1.00-1.04)、YON(ver2.00-2.01)

スマメイトのマイページから戦績データを一定間隔で取得し、テキストファイルとして出力するプログラム
入力 : スマメイトのマイページURL 例:https://smashmate.net/user/23240/
処理 : マイページにアクセスし戦績情報を抽出、計算
出力1 : output_smamate_mypage_get_dataフォルダ。exeファイルと同じディレクトリに作成
出力2 : 設定、レート、順位、前日比、勝利数、敗北数、連勝数、対戦数、勝率の各ファイル。一定秒数ごとに更新。output_smamate_mypage_get_data内
"""

import os, sys, time, webbrowser, pickle

import requests
import PySimpleGUI as sg
from bs4 import BeautifulSoup


this_software_ver = "2.01"
this_software_name = "smamate_mypage_get_data"
default_settings_dict = {"check_update":True, "mypage_url":""}
settings_dict = default_settings_dict.copy()


# 設定を記録した辞書を返す。見つからない場合は初期設定辞書を返す
def load_settings():
	try:
		with open("settings.pkl", "rb") as f:
			return pickle.load(f)
	except:
		return default_settings_dict.copy()


# 現verより新しいverが見つかった場合、アップデート確認ポップアップを出す
# アップデートする場合、最新版のzipファイルを規定のブラウザでDLしてTrueを返す
# アップデートしない場合、現verが最新と確認できた場合、確認不能の場合、Falseを返す
def gonna_update():
	global settings_dict
	if settings_dict["check_update"]:
		try:
			check_url = "https://raw.githubusercontent.com/yoyoyo4/smamate_mypage_get_data/master/README.txt"
			html = requests.get(check_url)
			soup = BeautifulSoup(html.text, "html.parser")
			latest_ver = str(soup)
			latest_ver = latest_ver[latest_ver.find("■最新バージョン"):latest_ver.find("■更新履歴")]
			latest_ver = latest_ver[latest_ver.find("ver")+3:latest_ver.find(".")+3] # READMEの最新バージョン欄ver?.??の?.??の表記を抜き出す
		except: # アクセス失敗など
			return False

		if float(this_software_ver) >= float(latest_ver): # 最新版を使っている場合
			return False

		layout = [[sg.Text("ver" + latest_ver + "が公開されています。ダウンロードしますか？")],
				[sg.Button("スキップ", bind_return_key=True), sg.Button("スキップ(次回から確認しない)"), sg.Button("ダウンロード")]]
		window = sg.Window(this_software_name, layout)
		while True:
			event, values = window.read()
			if event == sg.WIN_CLOSED:
				sys.exit()
			elif event == "スキップ":
				window.close()
				return False
			elif event == "スキップ(次回から確認しない)": # 今後もアップデートしない場合、設定辞書に反映
				window.close()
				settings_dict["check_update"] = False
				return False
			elif event == "ダウンロード": # 規定のブラウザでアップデートzipファイルのURLを直接開き、ダウンロードする。レポジトリのページも開く
				window.close()
				try:
					webbrowser.open("https://github.com/yoyoyo4/smamate_mypage_get_data")
					webbrowser.open("https://github.com/yoyoyo4/smamate_mypage_get_data/archive/refs/heads/master.zip")
					sg.popup("ver"+latest_ver+"のzipファイルをダウンロードしました。解凍して使用してください\nプログラムを終了します", no_titlebar=True)
					return True
				except:
					sg.popup("ver"+latest_ver+"のダウンロードに失敗しました\nアップデートせずプログラムを続行します", no_titlebar=True)
					return False


# 入力されたURLがスマメイトマイページのものかどうかをTrue/Falseで返す
def can_access_mypage(mypage_url:str):
	try:
		html = requests.get(mypage_url)
		soup = BeautifulSoup(html.text,"html.parser")
		if "さんのユーザーページ スマメイト" in soup.title.text:
			return True
		else:
			raise Exception
	except: # アクセスできない場合orアクセス先のタイトルに｢さんのユーザーページ スマメイト｣が無い場合
		return False


# マイページ入力ウィンドウを表示し、入力URLからHTMLテキストを取得できるか確認する
# 成功した場合、入力URLをテキストファイルに保存し、入力URLをそのまま返す
# 失敗した場合、URL再入力を求める
# URL修正用にする場合は、old_mypage_urlに修正前のマイページURLを入力する
# 修正用の場合、入力ウィンドウを☓で閉じた場合に修正前のURLを返す
def mypage_URL_input(old_mypage_url:str=""):
	layout = [[sg.Text("スマメイトのマイページURLを入力してください\n例:https://smashmate.net/user/23240/")],
				[sg.Input(key="-IN-")],
				[sg.Button("OK", bind_return_key=True)]]
	window = sg.Window(this_software_name, layout)
	while True:
		event, values = window.read()
		if event == sg.WIN_CLOSED:
			if old_mypage_url: # 修正用のウィンドウを閉じたかキャンセルした場合、元々のURLを返す
				return old_mypage_url
			else: # 修正用ではないウィンドウが閉じられた場合、プログラム全体を終了
				sys.exit() # sys.exit()でないとexe化後にエラーウィンドウが出る
		elif event == "OK":
			mypage_url = values["-IN-"]
			if can_access_mypage(mypage_url):
				window.close()
				return mypage_url
			else:
				sg.popup("戦績を取得できません。マイページのURLを確認して再入力してください", no_titlebar=True)


# マイページURLにアクセスし、HTMLテキストを返す
def fetch_mypage_text(mypage_url:str):
	html = requests.get(mypage_url)
	soup = BeautifulSoup(html.text, "html.parser")
	return str(soup)


# マイページのHTMLテキストから、出力するデータの辞書を作成して返す
# データ取得に完全に失敗した場合、空の辞書を返す
def make_data_dict(mypage_text:str):
	record_text = mypage_text[mypage_text.find("<h2>レーティング対戦</h2>"):mypage_text.find("""<h2 class="mt-5">プロフィール</h2>""")] # 戦績だけ抽出
	record_text = BeautifulSoup(record_text,"html.parser").get_text(strip=True).replace("\t","") # 例:レーティング対戦今期レート1357 (12035位)前日比：-17今期対戦成績43勝 55敗現在2連勝！動画化許可する
	data_dict = {}
	rate_idx = record_text.find("今期レート")
	
	if 0 < rate_idx: # 対戦記録があるとき
		data_dict["今期レート"] = record_text[rate_idx+5:rate_idx+9]
		data_dict["今期順位"] = record_text[record_text.find("(")+1:record_text.find("位")]
		data_dict["今期勝利数"] = record_text[record_text.find("今期対戦成績")+6:record_text.find("勝")] # ｢連勝｣の｢勝｣もあるが、より手前にある戦績の｢勝｣がヒットする
		data_dict["今期敗北数"] = record_text[record_text.find("勝")+2:record_text.find("敗")]
		data_dict["今期対戦数"] = str(int(data_dict["今期勝利数"]) + int(data_dict["今期敗北数"]))
		data_dict["今期勝率"] = str(int(round(100*int(data_dict["今期勝利数"])/int(data_dict["今期対戦数"])))) + "%"

		winning_streak_idx = record_text.find("連勝") # ｢連勝｣の表記があれば連勝中
		if 0 < winning_streak_idx:
			data_dict["連勝数"] = record_text[record_text.find("現在")+2:winning_streak_idx]
		else:
			data_dict["連勝数"] = "-"

		comp_idx = record_text.find("前日比：") # ｢前日比｣があれば記録(初日または前日と全く同じレートの場合表記が無い)
		if 0 < comp_idx:
			data_dict["前日比"] = record_text[comp_idx+4:record_text.find("今期対戦成績")]
		else:
			data_dict["前日比"] = "-"

	elif 0 < record_text.find("初期レート"): # サブシーズン0戦状態
		data_dict = {"今期順位":"-", "前日比":"-", "今期勝利数":"0", "今期敗北数":"0", "連勝数":"-", "今期対戦数":"0", "今期勝率":"0%"}
		ini_rate_idx = record_text.find("初期レート")
		data_dict["今期レート"] = record_text[ini_rate_idx+5:ini_rate_idx+9] # 初期レートを今期レートとして表示

	elif 0 < record_text.find("レーティング対戦"): # メインシーズン0戦状態
		data_dict = {"今期レート":"1500", "今期順位":"-", "前日比":"-", "今期勝利数":"0", "今期敗北数":"0", "連勝数":"-", "今期対戦数":"0", "今期勝率":"0%"}

	else: # 全くデータを取得できなかったとき。混雑時の専用ページを想定
		data_dict = {}

	return data_dict


# データ辞書の各値を別々のテキストファイルに出力
def output_data(data_dict:dict):
	for s in data_dict.keys():
		with open(s +".txt", mode="w", encoding="UTF-8") as w:
			w.write(data_dict[s])


# アクセス先と次回更新までの秒数を表示しつつ、テキストファイルを更新し続ける
def update_text_files_while_showing_status(mypage_url:str):
	global settings_dict

	mypage_text = fetch_mypage_text(mypage_url)
	data_dict = make_data_dict(mypage_text)
	output_data(data_dict)

	soup = BeautifulSoup(mypage_text, "html.parser")
	access_timeout_sec = 30 # この秒数ごとに更新。30未満の値には設定しないこと！
	layout = [[sg.Text("アクセス先\n" + soup.title.text + "\n" + mypage_url + "\n", key="text_access")],
				[sg.Text("下記フォルダにテキストファイルを出力中\n配信ソフトのテキストオブジェクトのソースとして設定してください\n" + os.getcwd())],
				[sg.Text("                                                                        ", key="error_msg")], # 最初に文字列スペースを確保する
				[sg.Text("次回更新まであと" + str(access_timeout_sec) + "秒", key="text_update")],
				[sg.Button("終了"), sg.Button("アクセスページ変更")]]
	window = sg.Window(this_software_name, layout)
	start_time = int(time.time())

	while True:
		event, _ = window.read(timeout=100)
		if event in [sg.WIN_CLOSED, "終了"]: # ウィンドウを閉じたor終了を押したとき、プログラム全体を終了
			sys.exit()

		elif event == "アクセスページ変更":
			old_mypage_url = mypage_url
			mypage_url = mypage_URL_input(old_mypage_url)
			if mypage_url == old_mypage_url: # 変更連打で連続アクセスしないように処理
				pass
			else: # URLを修正して各種変数とテキストファイルを更新
				settings_dict["mypage_url"] = mypage_url
				with open("settings.pkl","wb") as f: # 設定辞書を保存
					pickle.dump(settings_dict, f)
				mypage_text = fetch_mypage_text(mypage_url)
				data_dict = make_data_dict(mypage_text)
				output_data(data_dict)
				soup = BeautifulSoup(mypage_text, "html.parser")
				window["text_access"].update("アクセス先\n" + soup.title.text + "\n" + mypage_url + "\n")

		elif access_timeout_sec <= int(time.time()) - start_time: # 更新秒数以上経ったらテキストファイルを更新
			mypage_text = fetch_mypage_text(mypage_url)
			data_dict = make_data_dict(mypage_text)
			if len(data_dict):
				output_data(data_dict)
				window["error_msg"].update("")
			else: # データを取得できなかったとき、その旨を表示して更新をスキップする
				window["error_msg"].update("※前回の更新に失敗しました")
			start_time = int(time.time())

		else:
			window["text_update"].update("次回更新まで あと" + str(access_timeout_sec - (int(time.time()) - start_time)) + "秒")



def main():
	global settings_dict
	try:
		# os.chdir(os.path.dirname(sys.executable)) # exeファイルから実行する場合のディレクトリ移動。pyファイルから実行する場合は不要
		os.chdir(os.path.dirname(os.path.abspath(__file__))) # pyファイルから直接実行する場合のディレクトリ移動。exe化時は不要
		textfile_folder_name = "output_smamate_mypage_get_data"
		os.makedirs(textfile_folder_name, exist_ok=True)
		os.chdir(textfile_folder_name) # 出力用のフォルダを作成して移動

		settings_dict = load_settings()
		if gonna_update(): # アプデする場合は終了
			sys.exit()

		mypage_url = settings_dict["mypage_url"] # 保存されたマイページURLを読み込む
		if not mypage_url: # 読み込めないときは新規入力
			mypage_url = mypage_URL_input()
			settings_dict["mypage_url"] = mypage_url # 設定辞書にマイページURLを保存

		with open("settings.pkl","wb") as f: # 設定辞書を保存
			pickle.dump(settings_dict, f)

		update_text_files_while_showing_status(mypage_url)

	except SystemExit: # sys.exit()
		pass

	except: # 何らかの想定外エラー
		sg.popup("エラーが発生しました。下記の方法を試して再実行してください\
			\n-exeファイルを別のディレクトリに置いて実行する\
			\n-output_smamate_mypage_get_dataフォルダを削除する\
			\n-セキュリティソフトの設定でsmamate_mypage_get_data.exeの動作を許可する\
			\n-exeファイルを右クリック→｢管理者として実行(A)｣を選択する\
			\n\nエラー詳細\n"\
			+ str(sys.exc_info()[0]) + "\n" + str(sys.exc_info()[2].tb_lineno), no_titlebar=True)

if __name__ == "__main__":
	main()