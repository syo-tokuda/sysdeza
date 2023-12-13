import time
import smbus
import serial
import requests
import datetime
import schedule

moisture_data = 0             #土壌水分センサの値を保存する変数。初期値は’0’。
before_moisture_judge = 0														#追加！！！！！！！！土壌水分センサの前回の値を保存する変数。初期値は’0’。
temperature_data = 0          #土壌温度センサの値を保存する変数。初期値は’0’。
salt_content = 0              #コンポスト内の塩分量を保存する変数。初期値は’0’。
moisture_judge = 0            #土壌水分センサの値から判断した，土の状態を保存する変数。初期値は’0’。
temperature_judge_1 = 0       #土壌温度センサの値から判断した，土の状態を保存する変数。土の温度が60度以上となっている状態が7日間続いたかを確認する。初期値は’0’。
temperature_judge_2 = 0       #土壌温度センサの値から判断した，土の状態を保存する変数。土の温度が65度に達した後外気温付近まで低下したかを確認する。初期値は’0’。

automatic = false            #自動攪拌機能がONかOFFかを保存する変数。初期値は’偽’
Arduino_connect = false      #Arduinoと通信できたかを保存する変数。初期値は’偽’。
moisture_connect = false     #土壌水分センサの値が読めたかを保存する変数。初期値は’偽’。
temperature_connect = false  #土壌温度センサの値が読めたかを保存する変数。初期値は’偽’。
barcode_connect = false      #バーコードリーダーと通信できたかを保存する変数。初期値は’偽’。
barcode_collation = true    #バーコードリーダーで読み取ったコードがデータベースにあるかを保存する変数。初期値は’真’。

start_button = 20 #変数追加　ピン番号は変更要！
stop_button = 21
agitation_button = 22
salt_reset_button = 23
salt_LED = 24
low_moisture_LED = 25
high_moisture_LED = 26
LCD_addr = 0x3e
Arduino_addr = 0x04

bus=smbus.SMBus(1)
ACCESS_TOKEN = "XXXXXXXXXX"
headers = {"Authorization": f"Bearer {ACCESS_TOKEN}"}

GPIO.setup(start_button, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)  # if(GPIO.input(start_button) == 1)
GPIO.setup(stop_button, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.setup(agitation_button, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.setup(salt_reset_button, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.setup(salt_LED, GPIO.OUT)
GPIO.setup(low_moisture_LED, GPIO.OUT)
GPIO.setup(high_moisture_LED, GPIO.OUT)

i2c.write_byte_data(LCD_addr, 0x00, 0x38)
time.sleep(0.01)
i2c.write_byte_data(LCD_addr, 0x00, 0x39)
time.sleep(0.01)
i2c.write_byte_data(LCD_addr, 0x00, 0x14)
time.sleep(0.01)
i2c.write_byte_data(LCD_addr, 0x00, 0x73)
time.sleep(0.01)
i2c.write_byte_data(LCD_addr, 0x00, 0x56)
time.sleep(0.01)
i2c.write_byte_data(LCD_addr, 0x00, 0x6c)
time.sleep(0.01)
i2c.write_byte_data(LCD_addr, 0x00, 0x38)
time.sleep(0.01)
i2c.write_byte_data(LCD_addr, 0x00, 0x01)
time.sleep(0.01)
i2c.write_byte_data(LCD_addr, 0x00, 0x0f)
time.sleep(0.01)


def Arduino_receive():
	#Arduinoと通信をして土壌水分センサと土壌温度センサの値，それぞれのセンサの値が読めたかどうかのデータを受け取る。Raspberry PiとArduinoの通信にはI2Cを用いる。土壌水分センサの値をmoisture_data変数に，土壌温度センサの値をtemperature_data変数に保存する。土壌水分センサの値が読めればmoisture_connect変数へ’真’を，読めなければ’偽’を代入する。土壌温度センサの値が読めればtemperature_connect変数へ’真’を，読めなければ’偽’を代入する。Arduinoと通信できればArduino_connect変数へ’真’を，できなければ’偽’を代入する。
    try:
        receive_data = bus.read_word_data(Arduino_addr, 0)
        Arduino_connect = false
		moisture_data = receive_data & 0x7F
        if bin(receive_data >> 7) & 0x01 == 1 :
            moisture_connect = true
        else :
            moisture_connect = false

		temperature_data = bin(receive_data >> 8) & 0x7F
		if bin(receive_data >> 15) & 0x01 == 1 :
            temperature_connect = true
        else :
            temperature_connect = false
    except:
        Arduino_connect = true
    

def moisture_judgement():
	#moisture_data変数の値から土の水分が少ないか，適しているか，多いかを判断してmoisture_judge変数に代入する。水分が少ない（45%未満）と’0’，適切（45%以上55%未満）だと’1’，多い（55%以上）と’2’を代入する。
	before_moisture_judge = moisture_judge
	if(moisture_data < 45):
		moisture_judge = 0
	elif(moisture_data >= 45 and moisture_data < 55):
		moisture_judge = 1
	else:
		moisture_judge = 2


def temperature_judgement ():
	#temperature _data変数の値から堆肥の完成度を判断してtemperature_judge_1変数とtemperature_judge_2変数の値を変更する。temperature_judge_1は，作り始めは’0’，温度が60度以上になれば’1’，値が’1’の状態が7日続けば’2’とする。temperature_judge_2は，温度が65度以上になれば’1’，値が’1’になった後に温度が外気温付近（35度以下）まで低下した場合は’2’とする。
	if(temperature_data >= 60 and temperature_judge_1 = 0):
		temperature_judge_1 = 1
		seven_day_start = time.time()
	elif(temperature_judge_1 = 1 and time.time() - seven_day_start >= 604800):
		temperature_judge_1 = 2
	if(temperature_data >= 65 and temperature_judge_2 = 0):
		temperature_judge_2 = 1
	elif(temperature_judge_2 = 1 and temperature_data <= 35):
		temperature_judge_2 = 2
	

def barcode_read():
	#バーコードリーダーでバーコードを読み取り，読み取れた場合はCSVファイルのデータベース内のコードとの照合を行う。そして商品の塩分量を確認してsalt_calculation関数を実行する。バーコードリーダーと通信できていればbarcode_connect変数へ’真’を，できていなければ’偽’を代入する。バーコードリーダーで読み取ったコードがCSVファイルのデータベースにある場合はbarcode_collation変数へ’真’を，できていなければ’偽’を代入する。
	salt_data = 0 #salt_dataは読み取った塩分量
	return salt_data

def salt_calculation():
	#barcode_read関数で読み取った商品の塩分量をsalt_content変数に加算する。
	# int salt_data：barcode_read関数で読み取った商品の塩分量
	salt = barcode_read()
	salt_content = salt_content + salt
	

def display(moisture_data,salt_content):
	#ディスプレイに現在の水分量moisture_dataと塩分量salt_content，塩分基準量（35g）からsalt_contentを引いた残り投入可能な塩分量を表示する。
	i2c.write_byte_data(LCD_addr, 0x80, code)
	time.sleep(0.01)
	message = "スイブン" + str(moisture_data) + "%"
	mojilist=[]
    for moji in message:
        mojilist.append(ord(moji)) 
    i2c.write_i2c_block_data(LCD_addr, 0x00, mojilist)
	time.sleep(0.01)
	
	i2c.write_byte_data(LCD_addr, 0x80, code)
	time.sleep(0.01)
	message = "エンブン" + str(salt_content) + "g ノコリ" + str(35-salt_content) + "g"
	mojilist=[]
    for moji in message:
        mojilist.append(ord(moji)) 
    i2c.write_i2c_block_data(LCD_addr, 0x00, mojilist)
		

def LED_flash():
	#moisture_judgeの値から適した水分管理用LEDを点灯させる。また，salt_contentが塩分基準量（35g）を超えているか判断し，超えていれば塩分管理用LEDを点灯させる。
	if(moisture_judge < 45):
		GPIO.output(25,1)	#赤点灯
	elif(moisture_judge >= 45 and moisture_judge < 55):
		GPIO.output(25,0)	#赤消灯
		GPIO.output(26,0)	#白消灯
	elif(moisture_judge >= 55):
		GPIO.output(26,1)	#白点灯
	if(salt_content > 35):
		GPIO.output(24,1)	#緑点灯
	else:
		GPIO.output(24,0)	#緑消灯
	

def salt_reset():
	#塩分量リセットボタンが押されているかを判断し，押されていればsalt_content変数に’0’を代入，temperature_judge_1変数とtemperature_judge_2変数に’0’を代入する。
	if(GPIO.input(salt_reset_button) == 1):
		salt_content = 0
		temperature_judge_1 = 0
		temperature_judge_2 = 0


def mode_button_check():
	#始めにautomaticの真偽を判断する。
	#・’真’の場合
	#　ストップボタンが押されているかを判定する。
	#　　・押されている場合
	#automatic変数を’偽’にする。
	#　　・押されていない場合
	#　　　time_check関数を実行する。
	#・’偽’の場合
	#　スタートボタンが押されているかを判定する。
	#　・押されている場合
	#　　　automatic変数を’真’にする。
	#　　・’押されていない場合
	#　　　攪拌ボタンが押されているかを判定する。
	#・押されている場合
	#　　　　agitation関数を実行する。
	#　　　・押されていない場合
	#　　　　何もしない。
	if(automatic == true):
		if(GPIO.input(stop_button) == 1):
			automatic = false
		else:
			time_check()
	else:
		if(GPIO.input(start_button) == 1):
			automatic = true
		else:
			if(GPIO.input(agitation_button) == 1):
				agitation()


def time_check():
	#現在の時間を確認し，毎時00分である場合はagitation関数を実行する。
	schedule.every().hour.at(":00").do(agitation())
	

def agitation():
	#始めにモータを正回転させる。モータを回転させる際に加えたパルス数を計算しておき，コンポストの1周するパルス数まで加算された場合，次は逆方向にモータを回転させる。そして元の位置まで戻ると，再度モータを正回転させる。これを繰り返し，3回目に元の位置に戻ってきた際にモータを停止させる。



def transmit_judgement():
	#利用者の端末に通知をするかどうかを判断し，通知する場合はその内容を決定してtransmit関数で通知する。int moisture_judge変数を確認して，前回と値が変わっていれば通知をする。また，通知後3時間経過しても値が’0‘または’2’の場合は同様の通知をする。加えてtemperature_judge_1変数とtemperature_judge_2変数がともに’2’になった際も通知をする。
	transmit_time = 0

	if(not(moisture_judge == before_moisture_judge)):
		if(moisture_judge == 0):
			transmit(1)
		elif(moisture_judge == 1):
			transmit(3)
		else:
			transmit(2)
		transmit_time = time.time()
	
	if((time.time() - transmit_time) >= 10800):
		if(moisture_judge == 0):
			transmit(1)
			transmit_time = time.time()
		elif(moisture_judge == 2):
			transmit(2)
			transmit_time = time.time()
		

	if(temperature_judge_1 == 2 and temperature_judge_2 ==2):
		transmit(4)
		

def error_check():
	#Arduino_connect変数，moisture_connect変数，temperature_connect変数，barcode_connect変数，barcode_collation変数を確認し，値が’偽’に変わっている変数があればtransmit関数でエラーメッセージを利用者の端末に通知する。
	if(Arduino_connect = false):
		transmit(5)
	if(moisture_connect = false):
		transmit(6)
	if(temperature_connect = false):
		transmit(7)
	if(barcode_connect = false):
		transmit(8)
	if(barcode_collation = false):
		transmit(9)

def transmit(int transmit_code):
#利用者の端末にLINEで通知をする。transmit_codeの値に応じて対応したメッセージを送信する。
# 　int transmit_code：どのメッセージを送信するかを決めるための値．値と対応する送信メッセージを表19に示す。
    data = {"message": "メッセージ内容"}
    requests.post(
        "https://notify-api.line.me/api/notify",
        headers=headers,
        data=data,
    )
