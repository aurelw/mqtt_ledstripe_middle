#!/usr/bin/python3

###
# Copyright 2015, Aurel Wildfellner.
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software Foundation,
# Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#

import time
import argparse
import os

import mosquitto
import topicconfig
import time
from topictypes import TopicTypes


class LedStripe:



    def __init__(self, client):
        #self.stripedata = b"\xff"*150
        self.stripelength = 50
        self.stripestring = "r"*self.stripelength
        self.client = client
        self.topic = "devlol/things/18:FE:34:9C:5D:09/set"

        self._callstack = []

    def pushPixel(self, pixel):
        self.stripedata = (pixel + self.stripedata)[:self.stripelength*3]
        print("stripedata:", self.stripedata)
        #self.client.publish(self.topic, bytearray(self.stripedata))

    def _pubStripeString(self):
        print("pub")
        self.client.publish(self.topic, self.stripestring)

    def pushPalette(self, color):
        self.stripestring = (color + self.stripestring)[:self.stripelength]
        self._pubStripeString()

    def setStripe(self, color):
        self.stripedata = color*self.stripelength
        self._pubStripeString()

    def animateClear(self):
        a = 1  #leds per second**2
        for i in range(1,self.stripelength+1):
            self.pushPalette("n")
            time.sleep( 1.0 / (1.0 + a*i))


    def animateBlink(self):
        self._callstack.insert(len(self._callstack), self._animateBlink)

    def _animateBlink(self):
        sstring = self.stripestring
        speed = 10.0
        for i in range(100):
            self.pushPalette("n")
            time.sleep(1.0 / speed)
            self.pushPalette("n")
            time.sleep(1.0 / speed)
            self.pushPalette("w")
            time.sleep(1.0 / speed)

        self.stripestring = sstring
        self._pubStripeString()


    def doAnimations(self):
        for f in self._callstack:
            f()
        self._callstack = []




def on_message(client, ledstripe, msg):
    """ Callback for mqtt message."""
    payload = msg.payload.decode("utf-8")
    for ctopic in topicconfig.ledstripe_topics:
        
        if ctopic['topic'] == msg.topic:
            
            if ctopic['type'] == TopicTypes.PUSH_PIXEL_ON_PAYLOAD:
                if "payload" in ctopic.keys() and payload == ctopic['payload']:
                    ledstripe.pushPalette(ctopic['pcolor'])

            if ctopic['type'] == TopicTypes.ANIMATE_CLEAR_ON_TOPIC:
                ledstripe.animateClear()
                    
            if ctopic['type'] == TopicTypes.ANIMATE_BLINK_ON_PAYLOAD:
                if "payload" in ctopic.keys() and payload == ctopic['payload']:
                    print("Animate Blink")
                    ledstripe.animateBlink()
                    


def on_disconnect(client, userdata, foo):
    connected = False
    while not connected:
        try:
            client.reconnect()
            connected = True
            # resubscribe to the topics
            for ctopic in topicconfig.ledstripe_topics:
                client.subscribe(ctopic['topic'])
        except:
            print("Failed to reconnect...")
            time.sleep(1)


def main():

    ## Command line arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="test.mosquitto.org")

    args = parser.parse_args() 
    brokerHost = args.host

    ## setup MQTT client
    client = mosquitto.Mosquitto()
    client.on_message = on_message
    client.on_disconnect = on_disconnect

    ## Led Stripe
    ledstripe = LedStripe(client)
    client.user_data_set(ledstripe)

    try:
        client.connect(brokerHost)
    except:
        print("failed to connect")
        on_disconnect(client, None, None)

    ## subscribe to topics
    for ctopic in topicconfig.ledstripe_topics:
        client.subscribe(ctopic['topic'])

    while True:
        
        client.loop()
        ledstripe.doAnimations()


if __name__ == "__main__":
    main()

