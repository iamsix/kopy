import asyncio
import aiohttp
from jsonrpc_websocket import Server
from nicegui import app, ui
from typing_extensions import Self
from typing import Optional, Type
from types import TracebackType
import functools

class Remote:
    _closed = True
    buttons = {}
    #kodi = None
    
    def __init__(self):
        
        pass

    async def __aenter__(self) -> Self:
        await self._async_setup_hook()
        return self
    
    async def __aexit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_value: Optional[BaseException],
        traceback: Optional[TracebackType],
    ) -> None:
        if not self.is_closed():
            await self.disconnect()

    async def _async_setup_hook(self) -> None:
        # Called whenever the client needs to initialise asyncio objects with a running loop
        loop = asyncio.get_running_loop()
        self.loop = loop
        #self.http.loop = loop
        #self._connection.loop = loop
        self._ready = asyncio.Event()

    def is_closed(self) -> bool:
        """:class:`bool`: Indicates if the websocket connection is closed."""
        return self._closed



    def run(self):
      #  ui.button("test", on_click=self.test)
        self.build_ui()
        
       
        async def runner():
            async with self:
                await self.start()
    
        try:
            asyncio.run(runner())
        except KeyboardInterrupt:
            pass

    async def test(self):
        await self.kodi.GUI.ShowNotification("test", "kodi")

    async def start(self):
        app.on_connect(self.connect)
        app.on_disconnect(self.disconnect)
        #
        #await self.connect()
        ui.run(native=True, dark=True, title="Kopy")

       
        #await asyncio.sleep(5)
        #print("aftrsleep")
        #ui.button("test", on_click=self.kodi.GUI.ShowNotification)#self.test)
        #ui.run()


    async def connect(self):
        print("Connect")
        self.kodi = Server(
            'ws://192.168.1.22:9090/jsonrpc',
            auth=aiohttp.BasicAuth('', ''))
        await self.kodi.ws_connect()
        self._closed = False
        await self.post_connect()

    async def disconnect(self):
        print("disconnect")
        #self.kodi.close()

    async def post_connect(self):
        self.buttons = {
            "volume_down": [self.kodi.Input.ExecuteAction, 'volumedown'],
            "volume_up": [self.kodi.Input.ExecuteAction, 'volumeup'],
            "fullscreen": [self.kodi.Input.ButtonEvent, {"button" : "display", "keymap": 'R1'} ],
         #   "fullscreen": [self.kodi.Input.ExecuteAction, 'togglefullscreen'],

            'call_to_action': [self.kodi.Input.ButtonEvent, {"button" : "menu", "keymap": 'R1'}],
            'format_list_bulleted': [self.kodi.Input.ButtonEvent, {"button" : "title", "keymap": 'R1'}],
            'info': [self.kodi.Input.ButtonEvent, {"button" : "info", "keymap": 'R1'}],

            'expand_less': [self.kodi.Input.Up, None], #UP
            'chevron_left': [self.kodi.Input.ButtonEvent, {"button" : "left", "keymap": 'R1'}], # [self.kodi.Input.Left, None], #LEFT
            'circle': [self.kodi.Input.Select, None], # OK / Select
            'chevron_right': [self.kodi.Input.Right, None], #Right
            'arrow_back': [self.kodi.Input.Back, None], # Back
            'expand_more': [self.kodi.Input.Down, None], # DOWN
        
        }   

    async def toggle_mute(self, button):
        res = await self.kodi.Application.SetMute(mute="toggle")
        if res:
            button.sender.props('color=default')
        
        else:
            button.sender.props('color=red')


    async def btn_dis(self, button):
        #print(button.sender)
        btn, arg = self.buttons[button.sender._props['icon']]
        #print(arg)

        if type(arg) is dict:
            await btn(**arg)
        elif not arg:
            await btn()
        else:
            await btn(arg)
       # 
        #await self.kodi.Input.ExecuteAction('volumedown')

    def build_ui(self):
        ui.add_head_html("<meta name='viewport' content='width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no'>")
        ui.add_head_html("<meta name='apple-mobile-web-app-capable' content='yes'>")
        ui.add_head_html("<meta name='apple-mobile-web-app-tatus-bar-style' content='black'>")

        with ui.header(elevated=True).style('background-color: #3874c8').classes('items-center justify-between'):
            ui.button(on_click=lambda: left_drawer.toggle(), icon='menu').props('flat color=white')
            self.header = ui.label('HEADER')
            ui.button(on_click=lambda: right_drawer.toggle(), icon="settings_remote")

     
            
        #   print("hide")
        with ui.left_drawer().style('padding: 0; background-color: #111').props('mini') as left_drawer:
            # props('mini')
        #     def pop():
        #         left_drawer.props(remove="mini")
        #     def unpop():
        #         left_drawer.props(add="mini")
        # # left_drawer
        #     left_drawer.on("mouseover", pop, throttle=1)
        #     left_drawer.on("mouseout", unpop, throttle=1)
            with ui.element('q-list').props('padding'):
                with ui.element('q-item').on("click", self.list_sources).props("clickable v-ripple").tooltip("Files") as files:
                    with ui.element('q-item-section').props('avatar'): 
                        ui.element('q-avatar').props('icon=folder') 
                    with ui.element('q-item-section'): 
                        ui.label('Files') 
                with ui.element('q-item').props('clickable v-ripple'): 
                    with ui.element('q-item-section').props('avatar'): 
                        ui.element('q-avatar').props('icon=settings_remote') 
                    with ui.element('q-item-section'): 
                        ui.label('Remote') 

        with ui.right_drawer(value=False).props("overlay") as right_drawer:
            
            with ui.row().style("gap: 0").classes("items-center justify-between"):
                ui.button(icon="home").classes("text-xs")
                ui.button(icon="movie").classes("text-xs")
                ui.button(icon="tv").classes("text-xs")
                ui.button(icon="headphones").classes("text-xs")
                ui.button(icon="photo").classes("text-xs")

            with ui.row().classes('items-center justify-between q-my-xl'):
                #voldn = functools.partial(self.kodi.Input.ExecuteAction, "volumedown")
                ui.button(icon="volume_down", on_click=self.btn_dis).classes("text-2xl")
                ui.button(icon="volume_off", on_click=self.toggle_mute).classes("text-2xl")
                ui.button(icon="volume_up", on_click=self.btn_dis).classes("text-2xl")
                ui.button(icon='fullscreen', on_click=self.btn_dis).classes("text-xl")
                ui.button(icon='info', on_click=self.btn_dis).classes("text-xl")
                ui.button(icon='keyboard', on_click=self.btn_dis).classes("text-xl")
                ui.button(icon='call_to_action', on_click=self.btn_dis).classes("text-xl")
                ui.button(icon='format_list_bulleted', on_click=self.btn_dis).classes("text-xl")


            with ui.grid(columns=3).classes('absolute-bottom-right q-mb-xl q-mr-sm'):
                ui.label("")
                ui.button(icon="expand_less", on_click=self.btn_dis).classes("text-3xl").props("v-touch-repeat")
                ui.label("")
           
                ui.button(icon="chevron_left", on_click=self.btn_dis).classes("text-3xl").props("push v-touch-repeat:0:100.mouse")
                ui.button(icon="circle", on_click=self.btn_dis).classes("text-3xl").props('v-touch-repeat')
                ui.button(icon="chevron_right", on_click=self.btn_dis).classes("text-3xl").props('push v-touch-repeat:0:100.mouse.enter.space="click"')

                ui.button(icon="arrow_back", on_click=self.btn_dis).classes("text-xl").props('v-touch-repeat')
                ui.button(icon="expand_more", on_click=self.btn_dis).classes("text-3xl").props('v-touch-repeat')
                

        with ui.footer().style("gap: 0; padding: 0; background-color: #222").classes('items-center') as footer:
            
            with ui.column().classes('w-3/5').style("gap: 0; padding: 0"):
                slider = ui.slider(min=0, max=100, value=50).props('label')# label-value="00:32:10"')
                with ui.row().classes("w-full justify-between"):
                    ui.label("00:00:35") ##.bind_text_from(slider, 'value')
                    
                    ui.label("02:45:33 (3:44 PM)")
                ui.label("And.You.Thought.Your.Parents.Were.Weird.1991.INTERNAL.720p.WEBRip-LAMA.mp4").classes('w-full text-bold text-lg truncate').tooltip("asdaf")
        # ui.element('q-separator').props('vertical').style("margin-left: 10px")

            #TODO: make the small buttons vertical bigger/squarish
            with ui.row().style("gap: 0;").classes('items-center absolute-right'):
                ui.button(icon="skip_previous").classes("text-xs").props('flat color=white')
                ui.button(icon="fast_rewind").classes("text-xs").props('flat color=white')
                ui.button(icon="play_circle_filled").classes("text-lg").props('flat color=white')
                ui.button(icon="fast_forward").classes("text-xs").props('flat color=white')
                ui.button(icon="skip_next").classes("text-xs").props('flat color=white')
                ui.button(icon="stop").classes("text-xs").props('flat color=white')
                # TODO: This pops a menu with Subtitles/Audio/Video/etc
                # clicking one of those pops a dialog with the various panels of each
                with ui.button(icon="more_vert").classes("text-xs").props('flat color=white'):
                    with ui.menu().props(remove='no-parent-event') as menu:
                        ui.menu_item('Subtitles')
                        ui.menu_item('Video')
                        ui.menu_item('Audio')
                

        # bottom control bar probably?
            # with ui.button(icon='subtitles').style('margin-left: 10px').classes('text-xs'):
            #     with ui.menu().props(remove='no-parent-event') as menu:
            #         ui.menu_item("Download")
            #         ui.select({1: 'One', 2: 'Two', 3: 'Three'}, value=1) #, on_change=menu.close)




        #ui.button('test', on_click=test)
        self.content = ui.column().style("width: 100%").classes('pa-none')

    async def list_sources(self):
        sources = await self.kodi.Files.GetSources("video")
    # print(sources)
        self.content.clear()
        # TODO : Add db sources manually here
        with self.content:
            for source in sources['sources']:
                callback = functools.partial(self.list_files, source['file'])
                ui.label(source['label']).on("mousedown", callback)

    async def list_files(self, path):
        #print("FILE PATH", path)
        #TODO some kind of .. or up-path thing
        self.header.set_text(path)
        self.content.clear()
        files = await self.kodi.Files.GetDirectory(path, "video",["title","rating","genre","artist","track","season","episode","year","duration","album","showtitle","playcount","file","mimetype","size","lastmodified","resume","art","runtime","displayartist"] ,{"method":"date","order":"descending"} )
        
        with self.content:
            for file in files['files']:
                if file['filetype'] == "directory":
                    #might change these to q-list
                    callback = functools.partial(self.list_files, file['file'])
                    with ui.row().on("mousedown", callback).style("width:100%;").classes('ma-none'):
                        ui.icon("folder").classes('text-2xl')
                        ui.label(file['label'])
                        ui.label(file['lastmodified']).classes("ml-auto")
                elif file['filetype'] == "file":
                    with ui.row():
                        ui.icon("description").classes('text-2xl')

                        ui.label(file['label']) #.tooltip(f"Watched: {file['playcount']}")

remote = Remote()
remote.run()


print("Happens?")
    

    #    await server.GUI.ShowNotification("test", "kodi")
      #  await server.Input.ExecuteAction("volumeup")
      #  await server.Input.ExecuteAction("browsesubtitle")
      #  await server.GUI.ActivateWindow("subtitlesearch")
 #       await ui.label('some label')

#    finally:
#        await server.close()















#asyncio.get_event_loop().run_until_complete(routine())