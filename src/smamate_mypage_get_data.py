import os

import requests
from bs4 import BeautifulSoup

def main():
	os.chdir(os.path.dirname(os.path.abspath(__file__))) # 本pyファイルのディレクトリをカレントディレクトリとする

	# 戻り値1ならデータ取得を行わない
	get_data(pre_data())


def pre_data():
	# HTMLを読みだす
	# requests.getのかっこの中に書いてあるURLをご自身のスマメイトマイページに書き換えてください
	# サンプルはほーずきのマイページURLです
	html=requests.get("https://smashmate.net/user/23240/").text
	soup=BeautifulSoup(html,"html.parser")

	# タグを除外
	text=soup.get_text()

	# よしなに要素ごとに抽出
	lines= [line.strip() for line in text.splitlines()]

	text="\n".join(line for line in lines if line)

	# いったんファイルに書き出し
	with open('base.txt', mode='w', encoding='UTF-8') as b:
		b.writelines(text)

	# 今期レートという文言が見つかったら詳細処理、見つからない場合は0戦状態なので処理をスキップする
	with open('base.txt', mode='r', encoding='UTF-8') as f:
		check_word = f.readlines()
	
	check_word_position = [i for i, line in enumerate(check_word) if '今期レート' in line]
	check_word_position = str(check_word_position)
	check_word_position = check_word_position.strip('[') 
	check_word_position = check_word_position.strip(']') 

	if check_word_position == '':
		return 0
	else:
		return 1


def get_data(check_status):
	# 0 = レートデータがない場合はデータがないというデータ作成を行う
	# 1 = レートデータが見つかった場合はデータを作成する
	if check_status == 0:
		my_rate = '現在のレート：-'
		with open('now_rate.txt', mode='w', encoding='UTF-8') as w:
			w.write(my_rate)
		
		result_win_num = '現在の勝利数：-'
		with open('now_win_num.txt', mode='w', encoding='UTF-8') as w:
			w.write(result_win_num)
		
		result_lose_num = '現在の敗北数：-'
		with open('now_lose_num.txt', mode='w', encoding='UTF-8') as w:
			w.write(result_lose_num)
		
		result_total_match_num = '今期の総対戦数：-'
		with open('now_total_match_num.txt', mode='w', encoding='UTF-8') as w:
			w.write(result_total_match_num)
		
		result_my_win_rate = '現在の勝率：- ％'
		with open('now_my_win_rate.txt', mode='w', encoding='UTF-8') as w:
			w.write(result_my_win_rate)

	else:
		print_data()


def print_data():
	# base.txt読み込み
	with open('base.txt', mode='r', encoding='UTF-8') as f:
		mypage_data = f.readlines()
	
	# 今期レートの次の行要素を当てる
	# 現在のレートを切り出しし書き込み
	myrate_position = [i for i, line in enumerate(mypage_data) if '今期レート' in line]
	myrate_position = str(myrate_position)
	myrate_position = myrate_position.strip('[') 
	myrate_position = myrate_position.strip(']') 
	myrate_position = int(myrate_position)
	myrate_position = myrate_position + 1

	my_rate = mypage_data[myrate_position]
	my_rate = my_rate[:4]
	my_rate = '現在のレート：' + my_rate
	with open('now_rate.txt', mode='w', encoding='UTF-8') as w:
		w.write(my_rate)
	
	# 今期対戦成績の次の行要素を当てる
	win_lose_position = [i for i, line in enumerate(mypage_data) if '今期対戦成績' in line]
	win_lose_position = str(win_lose_position)
	win_lose_position = win_lose_position.strip('[') 
	win_lose_position = win_lose_position.strip(']') 
	win_lose_position = int(win_lose_position)
	win_lose_position = win_lose_position + 1

	# 今期の勝ち数を切り出しし書き込み
	my_win_num = mypage_data[win_lose_position]
	win_position = my_win_num.index('勝')
	my_win_num = my_win_num[:win_position]

	result_win_num = '現在の勝利数：' + my_win_num
	with open('now_win_num.txt', mode='w', encoding='UTF-8') as w:
		w.write(result_win_num)

	# 今期の負け数を切り出しし書き込み
	my_lose_num = mypage_data[win_lose_position]
	lose_position = my_lose_num.index('敗')
	cut_position = win_position + 2
	my_lose_num = my_lose_num[cut_position:lose_position]

	result_lose_num = '現在の敗北数：' + my_lose_num
	with open('now_lose_num.txt', mode='w', encoding='UTF-8') as w:
		w.write(result_lose_num)

	# 今期の対戦総数を算出し書き込み
	total_match_num = int(my_win_num) + int(my_lose_num)
	result_total_match_num = '今期の総対戦数：' + str(total_match_num)

	with open('now_total_match_num.txt', mode='w', encoding='UTF-8') as w:
		w.write(result_total_match_num)

	# 今期の勝率を算出し書き込み
	my_win_rate = round(( int(my_win_num) / int(total_match_num) ) * 100, 2)
	result_my_win_rate = '現在の勝率：' + str(my_win_rate) + '％'

	with open('now_my_win_rate.txt', mode='w', encoding='UTF-8') as w:
		w.write(result_my_win_rate)


if __name__ == '__main__':
    main()