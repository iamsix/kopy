### TESTING JSON RPC CLIENTS

# I kind of like jsonrpclient
#  but not sure how to get messages from the server
# seems like it's not quite designed to stay persistent?

# fastapi-websocket-rpc is weird.. it connects etc but the way
# it does methods/etc seems weird
# 

import asyncio
import logging
#from fastapi_websocket_rpc import RpcMethodsBase, WebSocketRpcClient
from nicegui import app, ui
from jsonrpcclient import Ok, parse_json, request_json
import websockets
from functools import partial
# fastapi_websocket_rpc import RpcMethodsBase, WebSocketRpcClient, logger
#logger.logging_config.set_mode(logger.LoggingModes.UVICORN, logger.logging.DEBUG)
class X:
    
    def __init__(self):
        
       # self.wsc =

        print("init")
       
        asyncio.get_event_loop().run_until_complete(self.connect())

        ui.run()
        #callback = partial(self.ws.send, request_json("GUI.ShowNotification", params=['test1', 'test2']))
        ui.button("test",on_click=self.test)
        

    async def test(self, x):
        pass
        res = await self.ws.send(request_json("GUI.ShowNotification", params=['test1', 'test2']))
        print("res", res)
        response = parse_json(await self.ws.recv())
        print("response", response)
        #self.server.other.GUI.ShowNotification(["test", "kodi"])

    async def connect(self):
        print("connect")
        uri = 'ws://192.168.1.22:9090/jsonrpc'
        self.ws = await websockets.connect(uri)
        #await self.ws.send(request_json("GUI.ShowNotification", params=['test1', 'test2']))
        #
        

        await self.test(self.ws)

        

        #if isinstance(response, Ok):
        #    print(response.result)
        #else:
        #    logging.error(response.message)
        #ui.button("test2")
        #try async with
    
     #   
        

    
server = X()

#asyncio.get_event_loop().run_until_complete(server.server.GUI.ShowNotification("test", "kodi"))
print("after")