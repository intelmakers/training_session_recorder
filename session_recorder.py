import os
import socket
import time
import sys
import thread
import threading
import signal
import curses
import subprocess
import datetime

import io
import wiringpi

import picamera
#install audio utils: arecord, etc.
#sudo apt-get install alsa
#install video Tools
#sudo apt-get install libav-tools
#sudo apt-get install ffmpeg
# ffmpeg compiling: http://www.jeffreythompson.org/blog/2014/11/13/installing-ffmpeg-for-raspberry-pi/
# enable microphone
#http://www.g7smy.co.uk/2013/08/recording-sound-on-the-raspberry-pi/

#microphone example
#http://scruss.com/blog/2012/11/20/raspberry-pi-as-a-usb-audio-capture-device/
#arecord -D 'pulse' -V stereo -c 2 -f dat -d 10 bbb.wav

#microphone recording recipes
#http://www.g7smy.co.uk/2013/08/recording-sound-on-the-raspberry-pi/
# arecord -l
# arecord -D plughw:1 --duration=10 -f cd -vv ~/rectest.wav

#http://blog.tkjelectronics.dk/2013/06/how-to-stream-video-and-audio-from-a-raspberry-pi-with-no-latency/
#http://www.google.co.uk/search?q=raspberry+pi+record+video+audio+microphone&btnG=Search


#commands
#https://www.element14.com/community/thread/49732/l/high-quality-hd-audio-and-video-recorder-using-the-raspberry-pi?displayFullThread=true
# raspivid -t 10 -n -w 1280 -h 720 -fps 25 -o aaa.h264 & arecord -Dhw:sndrpiwsp -d 10 -c 2 -f s16_LE -r 8000 > aaa.wav

# http://raspberrypi.stackexchange.com/questions/23420/problem-recording-video-with-audio-from-usb-soundcard-using-avconv
# raspivid -t 0 -fps 25 -o - -h 480 -w 640 | avconv -i pipe: -f alsa -ac 1 -i hw:0,0 -vcodec copy -acodec aac -strict experimental test.mp4 

#Sync Audio and Video
# http://raspberrypi.stackexchange.com/questions/25962/sync-audio-video-from-pi-camera-usb-microphone

class StrmServer :
    led_grn_gpio5=24
    led_red_gpio4=23
    led_red_pin = None
    led_grn_pin = None

    _format = 'mjpeg'
    #_format = 'h264'
    _camera = None
    _stop_server = False
    _main_thread = None
    _irw_thread = None
    _last_btn = ""
    def __init__(self):
        self.led_red_pin = self.init_gpio_out_pin(self.led_red_gpio4)
        self.led_grn_pin = self.init_gpio_out_pin(self.led_grn_gpio5)
        self.led_grn_pin.digitalWrite(self.led_grn_gpio5, self.led_grn_pin.HIGH)

    def init_gpio_out_pin(self, pin):
        os.system("gpio export %s out"%pin)
        pin_obj = wiringpi.GPIO(wiringpi.GPIO.WPI_MODE_SYS)  
        pin_obj.pinMode(pin,pin_obj.OUTPUT)
        wiringpi.pinMode(pin,pin_obj.OUTPUT)
        return pin_obj

    def IRWThread(self):
        #irw 2>1 | tee keys.txt > /dev/null
        #stdbuf -oL irw &> keys.txt
        os.system("irw 2>1 | tee keys.txt > /dev/null")

    def _start_ir(self):
        self._irw_thread = threading.Thread(target=self.IRWThread)
        self._irw_thread.start()
        
    def Run(self):
        self._start_ir()
        self._main_thread = threading.Thread(target=self.ControlThread)
        self._main_thread.start()

    def Stop(self):
        self._stop_server=True
        self._main_thread.join()
        
    def _get_last_button_press(self):
        line = subprocess.check_output(['tail', '-1', "keys.txt"])
        ls = line.split(" ")
        if len(ls) >=3:
            return ls[2]
        return ""
            
    def ControlThread(self):
        input_str = ''
        waiting_notified = False
        print("server started")

        while (self._stop_server == False):
            time.sleep(1)
            btn = self._get_last_button_press()
            print(btn)
            if(btn != self._last_btn):
                self._last_btn = btn
                if(btn == "KEY_A") or (btn == "KEY_B") or (btn == "KEY_C"):
                    self.led_red_pin.digitalWrite(self.led_red_gpio4, self.led_red_pin.HIGH)
                    print(btn)
                elif (btn == "KEY_D"):
                    self.led_red_pin.digitalWrite(self.led_red_gpio4, self.led_red_pin.LOW)
                    print(btn)
                    os.system("pkill raspivid")

                now = datetime.datetime.now()
                fname = "/home/pi/recordings/{}-{}-{}_{}.{}.{}_sambo.h264".format(now.year,now.month,now.day,now.hour,now.minute,now.second)                    
                if(btn == "KEY_A"):
                    os.system("raspivid -t 0 -o " + fname + " &")
            
        try:               
            self._camera.close()
        except Exception as e:
            pass
        
        print("server stopped")



if __name__ == "__main__":
    srv = StrmServer()
    srv.Run()
    #srv.StreamingThread()
