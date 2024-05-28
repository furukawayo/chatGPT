import openai
import subprocess
import socket
import re
import time

openai.api_key = "OpenAIのAPIのkey"

host = '127.0.0.1'   
port = 10500         
client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect((host, port))
time.sleep(3)
re_word = re.compile('WORD="([^"]+)"')

def jtalk(t):
    open_jtalk=['open_jtalk']
    mech=['-x','/var/lib/mecab/dic/open-jtalk/naist-jdic']
    htsvoice=['-m','/usr/share/hts-voice/nitech-jp-atr503-m001/nitech_jp_atr503_m001.htsvoice']
    speed=['-r','1.0']
    quolity=['-a','0.5']
    toon=['-fm','0.2']
    yokuyo=['-jf','1.0']
    outwav=['-ow','test.wav']
    cmd=open_jtalk+mech+htsvoice+speed+quolity+toon+yokuyo+outwav
    c = subprocess.Popen(cmd,stdin=subprocess.PIPE)
    c.stdin.write(t.encode('utf-8'))
    c.stdin.close()
    c.wait()
    aplay = ['aplay','-q','test.wav','-Dhw:0,0']
    wr = subprocess.Popen(aplay)

    command = b'TERMINATE\n'
    client.sendall(command)
    wr.wait()  
    command = b'RESUME\n'
    client.sendall(command)

def completion(new_message_text:str, settings_text:str = '', past_messages:list = []):
    if len(past_messages) == 0 and len(settings_text) != 0:
        system = {"role": "system", "content": settings_text}
        past_messages.append(system)
    new_message = {"role": "user", "content": new_message_text}
    past_messages.append(new_message)

    result = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=past_messages
    )
    response_message = {"role": "assistant", "content": result.choices[0].message.content}
    past_messages.append(response_message)
    response_message_text = result.choices[0].message.content
    return response_message_text, past_messages

def dialog():
    # 以下のsystem_settingsを変更することでキャラを変更できます
    system_settings = """
    あなたは関西人のタメ口で話します
    """
    messages = []
    recog_text = ""
    data = ""
    try:
        while recog_text != "終了":
            print("音声認識中...")
            while(data.find("</RECOGOUT>\n.") == -1):
                data += str(client.recv(1024).decode('shift_jis'))

            recog_text = "" # 単語を抽出
            for word in filter(bool, re_word.findall(data)):
                recog_text += word

            print("認識結果: " + recog_text)
            if recog_text == "リセット。":
                messages.clear()
                print("messages:",messages)
                recog_text = ""
                data = ""
                jtalk("システムをリセットしたよ。")
                continue

            new_message, messages = completion(recog_text, system_settings, messages)
            print("new_message:",new_message)

            jtalk(new_message)
            data = ""
    except KeyboardInterrupt:
        print('PROCESS END')
        command = b'DIE\n'
        client.send(command)
        client.close()

def main():
    data = ""
    try:
        while True:
            print("音声認識中...")
            while(data.find("</RECOGOUT>\n.") == -1):
                data += str(client.recv(1024).decode('shift_jis'))

            recog_text = "" # 単語を抽出
            for word in filter(bool, re_word.findall(data)):
                recog_text += word

            print("認識結果: " + recog_text)
            if recog_text == "おはよう":
                jtalk("システムを起動したよ。")
                dialog()

            data = ""
    except KeyboardInterrupt:
        print('PROCESS END')
        command = b'DIE\n'
        client.send(command)
        client.close()


if __name__ == '__main__':
    main()