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
from topictypes import TopicTypes


class LedStripe:


    def __init__(self, client):
        #self.stripedata = b"\xff"*150
        self.stripestring = "r"*50
        self.client = client
        self.topic = "devlol/things/18:FE:34:9C:5D:09/set"

    def pushPixel(self, pixel):
        self.stripedata = (pixel + self.stripedata)[:150]
        print("stripedata:", self.stripedata)
        #self.client.publish(self.topic, bytearray(self.stripedata))

    def pushPalette(self, color):
        self.stripestring = (color + self.stripestring)[:50]
        self.client.publish(self.topic, self.stripestring)

    def setStripe(self, color):
        self.stripedata = color*50
        self.client.publish(self.topic, self.stripedata)



def on_message(client, ledstripe, msg):
    """ Callback for mqtt message."""
    payload = msg.payload.decode("utf-8")
    for ctopic in topicconfig.ledstripe_topics:
        
        if ctopic['topic'] == msg.topic:
            
            if ctopic['type'] == TopicTypes.PUSH_PIXEL_ON_PAYLOAD:
                if "payload" in ctopic.keys() and payload == ctopic['payload']:
                    ledstripe.pushPalette(ctopic['pcolor'])
                    


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


if __name__ == "__main__":
    main()

