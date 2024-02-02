import asyncio
from aiortc import RTCIceCandidate, RTCPeerConnection, RTCSessionDescription
from aiortc.sdp import candidate_from_sdp, candidate_to_sdp
from aiortc.contrib.media import MediaPlayer
import sys
import aiohttp
import json
from configparser import ConfigParser

config = ConfigParser()
config.read("config.ini")

rtspURL = config.get("main", "rtspURL")

djangoURL = config.get("main", "djangoURL")
async def run_offer():
    pc = RTCPeerConnection()
    channel = pc.createDataChannel("chat")
    transceiver = pc.addTransceiver(trackOrKind="video", direction="sendonly")
    transceiver.direction = "sendonly"
    local_video = MediaPlayer(sys.argv[1]).video
    #local_video = MediaPlayer(rtspURL).video
    transceiver.sender.replaceTrack(local_video)
    print("channel created by local party")
    async def send_pings():
        while True:
            channel.send("message")
            await asyncio.sleep(1)
    @channel.on("open")
    def on_open():
        asyncio.ensure_future(send_pings())
    @channel.on("message")
    def on_message(message):
        print("<", message)
    await pc.setLocalDescription(await pc.createOffer())
    print("-- Please send this message to the remote party --")
    message = {"sdp": pc.localDescription.sdp, "type": pc.localDescription.type}
    msg = json.dumps(message, sort_keys=True)
    print(msg+ "\n")
    print()
    print("-- Please enter a message from remote party --")

    data = msg
    fullData = {"offer": data, "username": "amitpatange", "password": "password"}
    payload = json.dumps(fullData)
    print(payload, "\n")

    

    def object_from_string(message_str):
        message = json.loads(message_str)
        if message["type"] in ["answer", "offer"]:
            return RTCSessionDescription(**message)



    async with aiohttp.ClientSession() as session:
        print('reached here')
        async with session.post(
            djangoURL, data=payload
        ) as response:
            # loop = asyncio.get_event_loop()
            # data = await loop.run_in_executor(None, input)
            # print()
            # html = await response.text()
            html = await response.text()
            await pc.setRemoteDescription(object_from_string(html))
            print("remote des:", pc.remoteDescription)
            # html = json.dumps(html)
            # obj =  RTCSessionDescription(**message)
            # await pc.setRemoteDescription(obj)
            await loop.run_in_executor(None, input)
if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(run_offer())
    except KeyboardInterrupt:
        pass
