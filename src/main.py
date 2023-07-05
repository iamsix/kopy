import asyncio
import aiohttp
from attr import dataclass, field
from jsonrpc_websocket import Server
from nicegui import app, ui
from typing_extensions import Self
from typing import Optional, Type
from types import TracebackType
import functools

from datetime import datetime, timedelta

# https://kodi.wiki/view/JSON-RPC_API/Examples
# https://forum.kodi.tv/showthread.php?tid=157996

#TODO : Bind some labels/etc to this data
#@dataclass
class PlayStatus:
    time_seconds = 0
    duration_seconds = 0
    muted = False
    paused = False
    now_playing = False
    active_player_id = 0
    playing_title = "This.Is.A.Really.Long.Fake.Movie.Name.For.Testing.2020.INTERNAL.x265.1080p.WEBRip-ASDF.mkv"
    # TODO: Do a getter on time_str that returns formatted
    # possibly a different getter for a duration delta but 
    # can probably do that entirely internally
    time_str = "00:00:00"
    duration_str = "02:00:00 (12:00 PM)"

    playing_data = {}

ITEM_PROPS = ["album","albumartist","artist","episode","art","file","genre","plot","rating","season","showtitle","studio","tagline","title","track","year","streamdetails","originaltitle","playcount","runtime","duration","cast","writer","director","userrating","firstaired","displayartist","uniqueid"]
PLAYER_PROPS = ["audiostreams","canseek","currentaudiostream","currentsubtitle","partymode","playlistid","position","repeat","shuffled","speed","subtitleenabled","subtitles","time","totaltime","type","videostreams","currentvideostream"]
FILE_PROPS = ["title","rating","genre","artist","track","season","episode","year","duration","album","showtitle","playcount","file","mimetype","size","lastmodified","resume","art","runtime","displayartist"]
class Remote:
    status = PlayStatus
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
        ui.run(dark=True, title="Kopy", favicon="🚀")

       
        #await asyncio.sleep(5)
        #print("aftrsleep")
        #ui.button("test", on_click=self.kodi.GUI.ShowNotification)#self.test)
        #ui.run()

    async def notification(self, data, sender):
        print(data)
        print(sender)
        if 'title' in data['item']:
            self.nowplaying.set_text(data['item']['title'])
            self.nowplaying.tooltip(data['item']['title'])
        else:
            self.nowplaying.set_text(data['item']['id'])


    async def volchange(self, data, sender):
        self.status.muted = data['muted']
        if data['muted']:
            self.mutebtn.props('color=red')
        else:
            self.mutebtn.props('color=default')

    def notifyall(self, **kwargs):
        print("Notifyall", kwargs)

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
        # Technically only need the timer active while playing
        # can use the websocket callbacks to activate/deactivate
        
        await self.update_kodi_state(update_item=True)

        ui.timer(1.0, self.update_kodi_state)

        self.kodi.Player.OnPlay = self.notification
        self.kodi.Player.OnStop = self.notification
        self.kodi.Player.OnPause = self.notification
        self.kodi.Player.OnResume = self.notification
        self.kodi.Player.OnSeek = self.notification
        self.kodi.Player.OnPropertyChanged = self.notifyall
        self.kodi.Application.OnVolumeChanged = self.volchange
        
        self.kodi.JSONRPC.NotifyAll = self.notifyall
        self.buttons = {
            "volume_down": [self.kodi.Input.ExecuteAction, 'volumedown'],
            "volume_off": [self.kodi.Application.SetMute, {'mute': 'toggle'}],
            "volume_up": [self.kodi.Input.ExecuteAction, 'volumeup'],
            "fullscreen": [self.kodi.Input.ButtonEvent, {"button" : "display", "keymap": 'R1'} ],
         #   "fullscreen": [self.kodi.Input.ExecuteAction, 'togglefullscreen'],

            'call_to_action': [self.kodi.Input.ButtonEvent, {"button" : "menu", "keymap": 'R1'}],
            'format_list_bulleted': [self.kodi.Input.ButtonEvent, {"button" : "title", "keymap": 'R1'}],
            'info': [self.kodi.Input.ButtonEvent, {"button" : "info", "keymap": 'R1'}],

            'expand_less': [self.kodi.Input.ButtonEvent, {"button" : "up", "keymap": 'R1'}], #UP
            'chevron_left': [self.kodi.Input.ButtonEvent, {"button" : "left", "keymap": 'R1'}], # [self.kodi.Input.Left, None], #LEFT
            'circle': [self.kodi.Input.ButtonEvent, {"button" : "select", "keymap": 'R1'}], # OK / Select
            'chevron_right': [self.kodi.Input.ButtonEvent, {"button" : "right", "keymap": 'R1'}], #Right
            'arrow_back': [self.kodi.Input.ButtonEvent, {"button" : "back", "keymap": 'R1'}], # Back
            'expand_more': [self.kodi.Input.ButtonEvent, {"button" : "down", "keymap": 'R1'}], # DOWN

            'pause_circle_filled': [self.kodi.Player.PlayPause, {"playerid" : self.status.active_player_id}],
            'play_circle_filled': [self.kodi.Player.PlayPause, {"playerid" : self.status.active_player_id}],
        
        } 

    async def on_pause(self, data, sender):
        pass

    async def btn_dis(self, button):
        #print(button.sender)
        cmd, arg = self.buttons[button.sender._props['icon']]
        #print("id", button.sender.id)
        #print(arg)

        if type(arg) is dict:
            await cmd(**arg)
        elif not arg:
            await cmd()
        else:
            await cmd(arg)
       # 
        #await self.kodi.Input.ExecuteAction('volumedown')

       
    def seconds_to_time(self, seconds: int):
        hours = int(seconds // 3600)
        seconds = seconds - (hours * 3600)
        minutes = int(seconds // 60)
        seconds = int(seconds - (minutes * 60))
        return f"{hours:02}:{minutes:02}:{seconds:02}"

    def progress_format(self, val):
        #TODO: The opposite of this during on_change
        if self.status.time_seconds and self.status.duration_seconds:
            ratio:float = self.status.time_seconds / self.status.duration_seconds
            return int(10000 * ratio)
        else:
            return 0

    async def update_kodi_state(self, update_item=False):
        if not self.kodi.connected:
            print("Client is closed")
            return
        
        players = await self.kodi.Player.GetActivePlayers()
        #print(players)
        if players:
            # If there's a player we must be playing
            self.status.now_playing = True
            self.status.active_player_id = playerid=players[0]['playerid']

            if update_item:
                itemdata = await self.kodi.Player.GetItem(playerid=self.status.active_player_id, properties=ITEM_PROPS)
                #print(itemdata)
                if itemdata:
                    self.status.playing_title = itemdata['item']['label']
            playerdata = await self.kodi.Player.GetProperties(playerid=self.status.active_player_id, properties=PLAYER_PROPS)
            #print(playerdata)
            speed = playerdata['speed']
            if not speed:
                self.status.paused = True
            else:
                self.status.paused = False

            await self.toggle_playpause_button()
            npt = timedelta(**playerdata['time'])
            self.status.time_seconds = int(npt.total_seconds())
            play_ts = self.seconds_to_time(npt.total_seconds())
            dur = timedelta(**playerdata['totaltime'])
            self.status.duration_seconds = int(dur.total_seconds())
            self.status.time_str = play_ts

            # Should be no need to redo this every second... 
            endtime = (datetime.now() + (dur - npt)).strftime("%I:%M %p")
            self.status.duration_str =  f"{self.seconds_to_time(dur.total_seconds())} ({endtime})"

            # TODO - do this on mouseover/events and such instead of every second
            #self.progress.props(f'label label-value="{play_ts}"')

    async def toggle_playpause_button(self):
        #self.playpausebtn.set_visibility(False)
        if self.status.now_playing and self.status.paused:
            self.playpausebtn._props['icon'] = "play_circle_filled"
        elif self.status.now_playing and not self.status.paused:
            self.playpausebtn._props['icon'] = "pause_circle_filled"
        self.playpausebtn.update()

    async def downlaod_subs(self):
        await self.kodi.GUI.ActivateWindow("subtitlesearch")
            

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
                self.mutebtn = ui.button(icon="volume_off", on_click=self.btn_dis).classes("text-2xl")
                ui.button(icon="volume_up", on_click=self.btn_dis).classes("text-2xl")
                ui.button(icon='fullscreen', on_click=self.btn_dis).classes("text-xl")
                ui.button(icon='info', on_click=self.btn_dis).classes("text-xl")
                # TODO: This button. It does some 'send text' thing....
                ui.button(icon='keyboard', on_click=self.btn_dis).classes("text-xl").disable() #???
                # ------
                ui.button(icon='call_to_action', on_click=self.btn_dis).classes("text-xl")
                ui.button(icon='format_list_bulleted', on_click=self.btn_dis).classes("text-xl")
     
            # # TEST ==============
            # self.rptcounter = 0
            # self.repeatbutton = False
            # async def repeattest(button):
            #     print(button)
            #     self.repeatbutton = True
            #     #while self.repeatbutton:
            #     #    await asyncio.sleep(0.2)
            #     #    await self.btn_dis(button)

            # async def stoprepeat(button):
            #     self.repeatbutton = False


            # # -----------------
            with ui.grid(columns=3).classes('absolute-bottom-right q-mb-xl q-mr-sm'):
                ui.label("")
                ui.button(icon="expand_less", on_click=self.btn_dis).classes("text-3xl").props("v-touch-repeat")
                ui.label("")
           
                ui.button(icon="chevron_left", on_click=self.btn_dis).classes("text-3xl").props("push v-touch-repeat.mouse")
                test = ui.button(icon="circle", on_click=self.btn_dis).classes("text-3xl").props('v-touch-repeat')
                #self.buttons[test.id] = [self.kodi.Input.ButtonEvent, {"button" : "select", "keymap": 'R1'}]
                ## ========== TEST ==========
                #ui.button(icon="chevron_right").on('mousedown', repeattest).on('mouseup', stoprepeat).classes("text-3xl").props('push v-touch-repeat.mouse')
                
                ui.button(icon="chevron_right", on_click=self.btn_dis).classes("text-3xl").props('push v-touch-repeat.mouse')

                ui.button(icon="arrow_back", on_click=self.btn_dis).classes("text-xl").props('v-touch-repeat')
                ui.button(icon="expand_more", on_click=self.btn_dis).classes("text-3xl").props('v-touch-repeat')



        with ui.footer().style("gap: 0; padding: 0; background-color: #222").classes('items-center') as footer:
            #TODO: Change a lot of this data to bind to the class data
            with ui.column().classes('w-3/5').style("gap: 0; padding: 0"):
                self.progress = slider = ui.slider(min=0, max=10000, value=50).bind_value_from(self.status, 'time_seconds', self.progress_format) #. label-value="00:32:10"')
                with ui.row().classes("w-full justify-between"):
                    self.timestamp = ui.label().bind_text_from(self.status, 'time_str') ##.bind_text_from(slider, 'value')
                    
                    self.vidlength = ui.label("00:00:00 (--:-- PM)").bind_text(self.status, 'duration_str')
                self.nowplaying = ui.label().classes('w-full text-bold text-lg truncate').bind_text(self.status, 'playing_title').tooltip(self.status.playing_title)
        # ui.element('q-separator').props('vertical').style("margin-left: 10px")

            #TODO: make the small buttons vertical bigger/squarish
            with ui.row().style("gap: 0;").classes('items-center absolute-right'):
                ui.button(icon="skip_previous").classes("text-xs").props('flat color=white').style("padding-top: 2em;padding-bottom: 2em")
                ui.button(icon="fast_rewind").classes("text-xs").props('flat color=white').style("padding-top: 2em;padding-bottom: 2em")
                self.playpausebtn = ui.button(icon="play_circle_filled", on_click=self.btn_dis).classes("text-xl").props('flat color=white').style("padding-top: 1em;padding-bottom: 1em")
                ui.button(icon="fast_forward").classes("text-xs").props('flat color=white').style("padding-top: 2em;padding-bottom: 2em")
                ui.button(icon="skip_next").classes("text-xs").props('flat color=white').style("padding-top: 2em;padding-bottom: 2em")
                ui.button(icon="stop").classes("text-xs").props('flat color=white').style("padding-top: 2em;padding-bottom: 2em")
                # TODO: This pops a menu with Subtitles/Audio/Video/etc
                # clicking one of those pops a dialog with the various panels of each
                with ui.button(icon="more_vert").classes("text-xs").props('flat color=white').style("padding-top: 2em;padding-bottom: 2em"):
                    with ui.menu().props(remove='no-parent-event') as menu:
                        ui.menu_item('Subtitles', on_click=self.downlaod_subs)
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
        videodb = {"file": "videoDB://", 'label': "- Database"}
    # print(sources)
        self.content.clear()
        sources['sources'].insert(0, videodb)
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
        files = await self.kodi.Files.GetDirectory(path, "video",FILE_PROPS ,{"method":"date","order":"descending"} )
        
        with self.content:
            #might change these to q-list but I'm not sure how to clear it afterwards
            # as far as I can tell the element thing can clear()
            for file in files['files']:
                if file['filetype'] == "directory":
                    
                    callback = functools.partial(self.list_files, file['file'])
                    with ui.row().on("mousedown", callback).style("width:100%;").classes('ma-none'):
                        ui.icon("folder").classes('text-2xl')
                        ui.label(file['label'])
                        ui.label(file['lastmodified']).classes("ml-auto")
                elif file['filetype'] == "file":
                    #print(file)
                    #TODO - handle episodes / movies /etc here
                    # {"jsonrpc":"2.0","id":"1","method":"Player.Open","params":{"item":{"file":"Media/Big_Buck_Bunny_1080p.mov"}}}
                    params = {"item": {"file" : file['file']}}
                    callback = functools.partial(self.kodi.Player.Open, **params)
                    with ui.row().on("mousedown", callback).style("width:100%;"):
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