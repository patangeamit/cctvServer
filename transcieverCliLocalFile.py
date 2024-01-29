import asyncio
from aiortc import RTCIceCandidate, RTCPeerConnection, RTCSessionDescription
from aiortc.sdp import candidate_from_sdp, candidate_to_sdp
import json
from aiortc.contrib.media import MediaPlayer
import aiohttp
import asyncio
import sys
# from customVideoTrackBnW import CustomVideoTrack
# http://54.85.151.78:8000/s2sOffer aws
import time
from configparser import ConfigParser
import multiprocessing

from customVideoTrack import CustomVideoTrack

config = ConfigParser()

config.read("config.ini")

djangoUrl = config.get("main", "djangoUrl")  # -> "value1"
print("asdfasd", djangoUrl)

# from pureRtsp import pureRtspOut


def object_from_string(message_str):
    message = json.loads(message_str)
    if message["type"] in ["answer", "offer"]:
        return RTCSessionDescription(**message)


def object_to_string(obj):
    if isinstance(obj, RTCSessionDescription):
        message = {"sdp": obj.sdp, "type": obj.type}
    return json.dumps(message, sort_keys=True)


async def run_offer(pc):
    channel = pc.createDataChannel("chat")
    transceiver = pc.addTransceiver(trackOrKind="video", direction="sendonly")
    transceiver.direction = "sendonly"
    # local_video = MediaPlayer(sys.argv[1]).video
    
    local_video = CustomVideoTrack(1)
    # local_video = pureRtspOut(framerate=1)
    # local_video = MediaPlayer("rtsp://192.168.0.126:1935/", decode=False).video
    transceiver.sender.replaceTrack(local_video)
    print("channel created by local party")

    async def send_pings():
        while True:
            msg = "ping"
            channel.send(msg)
            print(">", msg)
            await asyncio.sleep(1)

    @channel.on("open")
    def on_open():
        print('data channel open')
        asyncio.ensure_future(send_pings())

    @channel.on("close")
    def on_close():
        print("closing")

    @channel.on("message")
    def on_message(message):
        print("<", message)

        channel.send("got msg")

    await pc.setLocalDescription(await pc.createOffer())
    data = object_to_string(pc.localDescription)
    fullData = {"offer": data, "username": "amitpatange", "password": "password"}
    payload = json.dumps(fullData)
    print(payload, "\n")
    async with aiohttp.ClientSession() as session:
        print('reached here')
        async with session.post(
            "http://127.0.0.1:8000/s2sOffer", data=payload
        ) as response:
            print("Status:", response.status)
            print("Content-type:", response.headers["content-type"])
            html = await response.text()
            print("Body:", html)
            await pc.setRemoteDescription(object_from_string(html))
            print("remote des:", pc.remoteDescription)
    await loop.run_in_executor(None, input)


if __name__ == "__main__":
    multiprocessing.set_start_method('spawn') 

    pc = RTCPeerConnection()
    coro = run_offer(pc)
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(coro)
    except KeyboardInterrupt:
        pass
    finally:
        loop.run_until_complete(pc.close())
