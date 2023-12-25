import time
import smbus
import serial
import requests
import datetime
import schedule
import threading
import csv
import pyautogui as pgui
import RPi.GPIO as GPIO

moisture_data = 0             #土壌水分センサの値を保存する変数。初期値は’0’。
before_moisture_judge = 0														#追加！！！！！！！！土壌水分センサの前回の値を保存する変数。初期値は’0’。
temperature_data = 0          #土壌温度センサの値を保存する変数。初期値は’0’。
salt_content = 0              #コンポスト内の塩分量を保存する変数。初期値は’0’。
moisture_judge = 0            #土壌水分センサの値から判断した，土の状態を保存する変数。初期値は’0’。
temperature_judge_1 = 0       #土壌温度センサの値から判断した，土の状態を保存する変数。土の温度が60度以上となっている状態が7日間続いたかを確認する。初期値は’0’。
temperature_judge_2 = 0       #土壌温度センサの値から判断した，土の状態を保存する変数。土の温度が65度に達した後外気温付近まで低下したかを確認する。初期値は’0’。
transmit_time = 0                                                               #水分の通知送信時間を保存する変数。初期値は’0’。

automatic = False            #自動攪拌機能がONかOFFかを保存する変数。初期値は’偽’

Arduino_connect = False      #Arduinoと通信できたかを保存する変数。初期値は’偽’。
before_Arduino_connect = False                                                  #Arduino_connectの前回の状態を保存する変数。初期値は’偽’。
moisture_connect = False     #土壌水分センサの値が読めたかを保存する変数。初期値は’偽’。
before_moisture_connect = False                                                  #moisture_connectの前回の状態を保存する変数。初期値は’偽’。
temperature_connect = False  #土壌温度センサの値が読めたかを保存する変数。初期値は’偽’。
before_temperature_connect = False                                                  #temperature_connectの前回の状態を保存する変数。初期値は’偽’。
barcode_connect = False      #バーコードリーダーと通信できたかを保存する変数。初期値は’偽’。
before_barcode_connect = False                                                  #barcode_connectの前回の状態を保存する変数。初期値は’偽’。
barcode_collation = True     #バーコードリーダーで読み取ったコードがデータベースにあるかを保存する変数。初期値は’真’。
barcode_error = True                                                            #バーコードの読み取りエラーを保存する変数。初期値は’真’。

start_button = 20 #変数追加　ピン番号は変更要！
stop_button = 21
agitation_button = 22
salt_reset_button = 23
salt_LED = 24
low_moisture_LED = 25
high_moisture_LED = 26
direction = 7 
step = 8
LCD_addr = 0x3e
Arduino_addr = 0x04

i2c=smbus.SMBus(1)
ACCESS_TOKEN = "w6afHKxOdcZdub77XWlUgKYVvjgUnVzLiSvuZm6b5iA"
headers = {"Authorization": f"Bearer {ACCESS_TOKEN}"}

GPIO.setup(start_button, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.setup(stop_button, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.setup(agitation_button, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.setup(salt_reset_button, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.setup(salt_LED, GPIO.OUT)
GPIO.setup(low_moisture_LED, GPIO.OUT)
GPIO.setup(high_moisture_LED, GPIO.OUT)
GPIO.setmode(GPIO.BCM)
GPIO.setup(direction, GPIO.OUT)
GPIO.setup(step, GPIO.OUT)

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
    global moisture_data
    global temperature_data
    global moisture_connect
    global temperature_connect
    global Arduino_connect
    try:
        receive_data = i2c.read_word_data(Arduino_addr, 0)
        Arduino_connect = False
        moisture_data = receive_data & 0x7F
        if bin(receive_data >> 7) & 0x01 == 1 :
            moisture_connect = True
        else :
            moisture_connect = False

        temperature_data = bin(receive_data >> 8) & 0x7F
        if bin(receive_data >> 15) & 0x01 == 1 :
            temperature_connect = True
        else :
            temperature_connect = False
    except:
        Arduino_connect = True


def moisture_judgement():
	#moisture_data変数の値から土の水分が少ないか，適しているか，多いかを判断してmoisture_judge変数に代入する。水分が少ない（45%未満）と’0’，適切（45%以上55%未満）だと’1’，多い（55%以上）と’2’を代入する。
    global moisture_judge
    if(moisture_data < 45):
        moisture_judge = 0
    elif(moisture_data >= 45 and moisture_data < 55):
        moisture_judge = 1
    else:
        moisture_judge = 2


def temperature_judgement ():
	#temperature _data変数の値から堆肥の完成度を判断してtemperature_judge_1変数とtemperature_judge_2変数の値を変更する。temperature_judge_1は，作り始めは’0’，温度が60度以上になれば’1’，値が’1’の状態が7日続けば’2’とする。temperature_judge_2は，温度が65度以上になれば’1’，値が’1’になった後に温度が外気温付近（35度以下）まで低下した場合は’2’とする。
    global temperature_judge_1
    global temperature_judge_2
    if(temperature_data >= 60 and temperature_judge_1 == 0):
        temperature_judge_1 = 1
        seven_day_start = time.time()
    elif(temperature_judge_1 == 1 and time.time() - seven_day_start >= 604800):
        temperature_judge_1 = 2
    if(temperature_data >= 65 and temperature_judge_2 == 0):
        temperature_judge_2 = 1
    elif(temperature_judge_2 == 1 and temperature_data <= 35):
        temperature_judge_2 = 2
	

def barcode_read():
	#バーコードリーダーでバーコードを読み取り，読み取れた場合はCSVファイルのデータベース内のコードとの照合を行う。そして商品の塩分量を確認してsalt_calculation関数を実行する。バーコードリーダーと通信できていればbarcode_connect変数へ’真’を，できていなければ’偽’を代入する。バーコードリーダーで読み取ったコードがCSVファイルのデータベースにある場合はbarcode_collation変数へ’真’を，できていなければ’偽’を代入する。
    global barcode_collation
    global barcode_connect
    barcode_collation = True
    barcode_error  = True
    barcode = None
    def myinput(st):
        nonlocal barcode
        barcode = input(st)
    t = threading.Thread(target=myinput, args=("",))
    t.setDaemon(True)
    t.start()
    t.join(timeout = 0.1)
    if barcode is None:
        pgui.typewrite('\n')
        barcode = None
        salt_data = -1
    else :
        barcode_connect = True
        salt_data = 0 #salt_dataは読み取った塩分量
        with open('barcode.csv','r') as f :
            reader = csv.reader(f)
            try :
                if int(barcode) < 1000000000000 :
                    barcode_error = False
                else :
                    for csv_list in reader :
                        if int(barcode) == int(csv_list[0])  :
                            saltdata = csv_list[1]
                    if salt_data <= 0 :
                        barcode_collation = False
            except :
                barcode_error = False
    return salt_data


def salt_calculation():
	#barcode_read関数で読み取った商品の塩分量をsalt_content変数に加算する。
	# int salt_data：barcode_read関数で読み取った商品の塩分量
    global salt_content
    salt = barcode_read()
    if salt > 0 :
        salt_content = salt_content + salt
	

def display():
	#ディスプレイに現在の水分量moisture_dataと塩分量salt_content，塩分基準量（35g）からsalt_contentを引いた残り投入可能な塩分量を表示する。
	i2c.write_byte_data(LCD_addr, 0x80, 0x0f)
	time.sleep(0.01)
	message = "スイブン" + str(moisture_data) + "%"
	mojilist=[]
	for moji in message:
		mojilist.append(ord(moji)) 
		i2c.write_i2c_block_data(LCD_addr, 0x00, mojilist)
	time.sleep(0.01)
	
	i2c.write_byte_data(LCD_addr, 0x80, 0x40+0x80)
	time.sleep(0.01)
	message = "エンブン" + str(salt_content) + "g ノコリ" + str(35-salt_content) + "g"
	mojilist=[]
	for moji in message:
		mojilist.append(ord(moji)) 
	i2c.write_i2c_block_data(LCD_addr, 0x00, mojilist)
		

def LED_flash():
	#moisture_judgeの値から適した水分管理用LEDを点灯させる。また，salt_contentが塩分基準量（35g）を超えているか判断し，超えていれば塩分管理用LEDを点灯させる。
	if(moisture_judge < 45):
		GPIO.output(low_moisture_LED, GPIO.HIGH)	#赤点灯
	elif(moisture_judge >= 45 and moisture_judge < 55):
		GPIO.output(low_moisture_LED, GPIO.LOW)	#赤消灯
		GPIO.output(high_moisture_LED, GPIO.LOW)	#白消灯
	elif(moisture_judge >= 55):
		GPIO.output(high_moisture_LED, GPIO.HIGH)	#白点灯
	if(salt_content > 35):
		GPIO.output(salt_LED, GPIO.HIGH)	#緑点灯
	else:
		GPIO.output(salt_LED, GPIO.LOW)	#緑消灯
	
	if(barcode_collation == False):
		for i in range(5):
			GPIO.output(salt_LED, GPIO.HIGH)	#緑消灯
			time.sleep(0.5)
			GPIO.output(salt_LED, GPIO.LOW)	#緑消灯
			time.sleep(0.5)
	if(barcode_error == False):
		for i in range(3):
			GPIO.output(salt_LED, GPIO.HIGH)	#緑消灯
			time.sleep(0.5)
			GPIO.output(salt_LED, GPIO.LOW)	#緑消灯
			time.sleep(0.5)
	

def salt_reset():
	#塩分量リセットボタンが押されているかを判断し，押されていればsalt_content変数に’0’を代入，temperature_judge_1変数とtemperature_judge_2変数に’0’を代入する。
    global salt_content
    global temperature_judge_1
    global temperature_judge_2
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
    global automatic
    if(automatic == True):
        if(GPIO.input(stop_button) == 1):
            automatic = False
        else:
            time_check()
    else:
        if(GPIO.input(start_button) == 1):
            automatic = True
        else:
            if(GPIO.input(agitation_button) == 1):
                agitation()


def time_check():
	#現在の時間を確認し，毎時00分である場合はagitation関数を実行する。
	schedule.every().hour.at(":00").do(agitation())
	

def agitation():
	#始めにモータを正回転させる。モータを回転させる際に加えたパルス数を計算しておき，コンポストの1周するパルス数まで加算された場合，次は逆方向にモータを回転させる。そして元の位置まで戻ると，再度モータを正回転させる。これを繰り返し，3回目に元の位置に戻ってきた際にモータを停止させる。
    step_count = 400 
    delay = .001
	
    for i in range(3) :
        GPIO.output(direction, 1)
        for x in range(step_count):
            GPIO.output(step, GPIO.HIGH)
            time.sleep(delay)
            GPIO.output(step, GPIO.LOW)
            time.sleep(delay)
        time.sleep(.5)
    
        GPIO.output(direction, 0)
        for x in range(step_count):
            GPIO.output(step, GPIO.HIGH)
            time.sleep(delay)
            GPIO.output(step, GPIO.LOW)
            time.sleep(delay)
        time.sleep(.5)
    

def transmit_judgement():
	#利用者の端末に通知をするかどうかを判断し，通知する場合はその内容を決定してtransmit関数で通知する。int moisture_judge変数を確認して，前回と値が変わっていれば通知をする。また，通知後3時間経過しても値が’0‘または’2’の場合は同様の通知をする。加えてtemperature_judge_1変数とtemperature_judge_2変数がともに’2’になった際も通知をする。
	global transmit_time
	global before_moisture_judge
	if(not(moisture_judge == before_moisture_judge)):
		if(moisture_judge == 0):
			transmit(1)
		elif(moisture_judge == 1):
			transmit(3)
		else:
			transmit(2)
		transmit_time = time.time()
	before_moisture_judge = moisture_judge
	
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
	if(Arduino_connect == False and before_Arduino_connect == True):
		transmit(5)
	before_Arduino_connect = Arduino_connect
	if(moisture_connect == False and before_moisture_connect == True):
		transmit(6)
	before_moisture_connect = moisture_connect
	if(temperature_connect == False and before_temperature_connect == True):
		transmit(7)
	before_temperature_connect = temperature_connect
	if(barcode_connect == False and before_barcode_connect == True):
		transmit(8)
	before_barcode_connect = barcode_connect
	if(barcode_collation == False):
		transmit(9)
	if(barcode_error == False):
		transmit(10)


def transmit(transmit_code):
#利用者の端末にLINEで通知をする。transmit_codeの値に応じて対応したメッセージを送信する。
# 　int transmit_code：どのメッセージを送信するかを決めるための値．値と対応する送信メッセージを表19に示す。
    match transmit_code:
        case 1:
            data = {"message": "水を補給してください"}
        case 2:
            data = {"message": "通気口を開いてください"}
        case 3:
            data = {"message": "通気口を閉じてください"}
        case 4:
            data = {"message": "コンポストの一次発酵が終了"}
        case 5:
            data = {"message": "Arduinoと通信ができません"}
        case 6:
            data = {"message": "土壌水分センサの値が読めません"}
        case 7:
            data = {"message": "土壌温度センサの値が読めません"}
        case 8:
            data = {"message": "バーコードリーダーと通信ができません"}
        case 9:
            data = {"message": "読み取ったバーコードがデータベースにありません"}
        case 10:
            data = {"message": "バーコードが正常に読み込めませんでした"}
    
    if not transmit_code == 0 :
        requests.post(
            "https://notify-api.line.me/api/notify",
            headers=headers,
            data=data,
        )


while True : #メイン処理
    Arduino_receive()
    moisture_judgement()
    temperature_judgement()
    salt_calculation()
    display()
    LED_flash()
    salt_reset()
    mode_button_check()
    transmit_judgement()
    error_check()
