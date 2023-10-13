from kivy.app import App
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.lang import Builder
from kivy.utils import platform
from kivy.uix.textinput import TextInput
from kivy.uix.boxlayout import BoxLayout
from functools import partial
from kivy.clock import Clock
from kivy.logger import Logger
from kivy.uix.dropdown import DropDown
from huami_token import HuamiAmazfit
import urls as urls
from kivy.core.clipboard import Clipboard
from kivy.storage.jsonstore import JsonStore

DEBUG=False
# DEBUG=True

def debug_print(*xargs):
    if DEBUG:
        print(*xargs)

SPACING=2
Builder.load_string('''
<MyInputy>:
    font_size: 30
    halign: 'left'
    color: 1,1,1,1
    bcolor: .1, 0, .6, 0
    canvas.before:
        Color:
            rgba: root.bcolor
        Rectangle:
            size: (self.width -2, self.height -2)
            pos: (self.x+1,self.y +1)


<MyLabel>:
    font_size: 30
    halign: 'center'
    bcolor: .7, .7, .7, 1
    canvas.before:
        Color:
            rgba: root.bcolor
        Rectangle:
            size: self.size
            pos: self.pos

<MyLeftLabel>:
    font_size: 30
    halign: 'left'
    bcolor: .7, .7, .7, 1
    canvas.before:
        Color:
            rgba: root.bcolor
        Rectangle:
            size: self.size
            pos: self.pos
<MyButton>:
    font_size: 30
    bcolor: .7, .7, .7, 1
    background_color: .1, 0, .5, 0
    canvas.before:
        Color:
            rgba: root.bcolor
        Rectangle:
            size: self.size
            pos: self.pos
            
<MyDDKeyButton>:
    bcolor: .7, .7, .7, 1
    background_color: .1, 0, .5, 0
    text_size: self.width, None
    canvas.before:
        Color:
            rgba: root.bcolor
        Rectangle:
            size: self.size
            pos: self.pos

    ''')
class MyLabel(Label):
    pass

class MyLeftLabel(Label):
    pass

class MyButton(Button):
    pass

class MyInput(TextInput):
    pass

class MyDDKeyButton(Button):
    def __init__(self, mac_, ak_, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.mac = mac_
        self.ak = ak_
        self.text = f'[{self.mac}]: {self.ak}'
    
    def cpy(self, button):
        self.text = button.text
        self.ak = button.ak
        self.mac = button.mac

class Main(App):
    def build(self):
        self.huamidevice=HuamiAmazfit()
        self.store = JsonStore('credentials.json')

        screen_layout = BoxLayout(orientation="vertical", spacing=SPACING)
        buttons_layout = BoxLayout(orientation="horizontal", spacing=SPACING)
        rows_layout = BoxLayout(orientation="vertical", spacing=SPACING)

        top_title_label=MyLeftLabel(text='Huafetcher', halign="left")
        self.instructions_label=MyLeftLabel(text='Press "Get token", sign in, copy URL and paste here', halign="left", valign="middle", padding_x="20")
        self.instructions_label.bind(size=self.instructions_label.setter('text_size'))
        rows_layout.add_widget(top_title_label)

        dropdown = DropDown()

        xiaomi_button = MyButton(text='Xiaomi', size_hint_y=None, height=150)
        xiaomi_button.bind(on_press=lambda a:self.set_login_method('xiaomi'))
        xiaomi_button.bind(on_release=lambda btn: dropdown.select(btn.text))
        amazfit_button = MyButton(text='Amazfit', size_hint_y=None, height=150)
        amazfit_button.bind(on_press=lambda a:self.set_login_method('amazfit'))
        amazfit_button.bind(on_release=lambda btn: dropdown.select(btn.text))

        dropdown.add_widget(xiaomi_button)
        dropdown.add_widget(amazfit_button)

        dropdown_button = MyButton(text='Login method')
        dropdown_button.bind(on_release=dropdown.open)
        #dropdown_button.bind(on_press=lambda x: setattr(dropdown_button,'text','Select'))
        dropdown.bind(on_select=lambda instance, x: setattr(dropdown_button, 'text', x))

        self.get_token_button = MyButton(text='Get token')
        self.get_token_button.bind(on_press=self.on_press_button_gettoken)

        self.fetch_key_button = MyButton(text='Fetch key')
        self.fetch_key_button.bind(on_press=self.on_press_button_fetch_key)
        self.fetch_key_button.disabled=True

        self.fetch_agps_button = MyButton(text='Fetch aGPS')
        self.fetch_agps_button.bind(on_press=self.on_press_button_agps)
        self.fetch_agps_button.disabled=True

        create_uihh_file_button = MyButton(text='Create UIHH')
        create_uihh_file_button.bind(on_press=self.create_uihh_agps_file)

        buttons_layout.add_widget(self.get_token_button)
        #buttons_layout.add_widget(login_button)
        buttons_layout.add_widget(self.fetch_key_button)
        buttons_layout.add_widget(self.fetch_agps_button)
        #sharing doesn't work
        buttons_layout.add_widget(create_uihh_file_button)

        self.paste_token_input_layout = BoxLayout(orientation="horizontal", spacing=SPACING)
        paste_token_input_label=MyLabel(text='URL result')
        self.paste_token_input_layout.disabled=True
        self.paste_token_input = MyInput(text='',
                multiline=False,
                )
        self.paste_token_input.bind(text=self.set_token)


        paste_token_url_button=MyButton(text='Paste', size_hint=(.3, 1))
        paste_token_url_button.bind(on_press=lambda instance: self.on_press_paste(self.paste_token_input) )

        self.paste_token_input_layout.add_widget(paste_token_input_label)
        self.paste_token_input_layout.add_widget(paste_token_url_button)
        self.paste_token_input_layout.add_widget(self.paste_token_input) 
        credentials_email_label=MyButton(text='Email' , size_hint=(.7, 1))

        self.credentials_email_input = MyInput(text='',
                multiline=False,
                )
        self.credentials_email_input.bind(text=lambda instance,x: setattr(self.huamidevice,'email',x))

        email_paste_button=MyButton(text='Paste', size_hint=(.3, 1))
        email_paste_button.bind(on_press=lambda instance: self.on_press_paste(self.credentials_email_input) )

        email_save_button=MyButton(text='Save', size_hint=(.3, 1))
        #load_button1.bind(on_press=lambda instance:  )
        email_save_button.bind(on_press=lambda instance: self.on_press_save(self.credentials_email_input, 'email') )



        self.credentials_email_layout = BoxLayout(orientation="horizontal", spacing=SPACING)
        self.credentials_email_layout.add_widget(credentials_email_label)
        #credentials_email_layout.add_widget(load_button1)
        self.credentials_email_layout.add_widget(email_save_button)
        self.credentials_email_layout.add_widget(email_paste_button)
        self.credentials_email_layout.add_widget(self.credentials_email_input)


        credentials_password_label=MyLabel(text='Password', size_hint=(.7, 1))

        self.credentials_password_input = MyInput(text='',
                multiline=False,
                )
        self.credentials_password_input.bind(text=lambda instance,x: setattr(self.huamidevice,'password',x))
        credentials_password_label.bind(on_press=self.on_press_paste_password)

        password_paste_button=MyButton(text='Paste', size_hint=(.3, 1))
        password_paste_button.bind(on_press=lambda instance: self.on_press_paste(self.credentials_password_input) )

        password_save_button=MyButton(text='Save', size_hint=(.3, 1))
        password_save_button.bind(on_press=lambda instance: self.on_press_save(self.credentials_password_input, 'password') )

        self.credentials_password_layout = BoxLayout(orientation="horizontal", spacing=SPACING)
        self.credentials_password_layout.add_widget(credentials_password_label)
        self.credentials_password_layout.add_widget(password_save_button)
        self.credentials_password_layout.add_widget(password_paste_button)
        self.credentials_password_layout.add_widget(self.credentials_password_input)

        rows_layout.add_widget(dropdown_button)
        rows_layout.add_widget(self.credentials_email_layout)
        rows_layout.add_widget(self.credentials_password_layout)
        rows_layout.add_widget(self.paste_token_input_layout)

        result_value_label=MyButton(text='Found key')
        self.result_value_value = MyDDKeyButton("No keys yet", "")
        self.ddown=DropDown()
        self.result_value_value.bind(on_release=self.ddown.open)
        self.ddown.bind(on_select=lambda instance, x: self.result_value_value.cpy(x))


        copy_key_button=MyButton(text='Copy', size_hint=(.3, 1))
        copy_key_button.bind(on_press=lambda instance: self.on_press_copy_result(self.result_value_value) )


        self.result_value_layout = BoxLayout(orientation="horizontal", spacing=SPACING)
        self.result_value_layout.add_widget(result_value_label)
        self.result_value_layout.add_widget(copy_key_button)
        self.result_value_layout.add_widget(self.result_value_value)
        result_value_label.bind(on_press=lambda instance: self.on_press_copy_result(self.result_value_value))
        self.result_value_layout.disabled=True


        rows_layout.add_widget(self.result_value_layout)


        rows_layout.add_widget(buttons_layout)

        rows_layout.add_widget(self.instructions_label)

        screen_layout.add_widget(rows_layout)

        self.on_press_load(self.credentials_email_input, 'email')
        self.on_press_load(self.credentials_password_input, 'password')
        #self.set_login_method('xiaomi')
        #dropdown_button.text='Xiaomi'
        self.set_login_method('amazfit')
        dropdown_button.text='Amazfit'

        return screen_layout

    def set_visibility(self, widget_id, hide=True):
        debug_print(hide)
        if hasattr(widget_id, 'saved_attrs'):
            debug_print(widget_id.saved_attrs)
            if not hide:
                widget_id.height, widget_id.size_hint_y, widget_id.opacity, widget_id.disabled = widget_id.saved_attrs
                del widget_id.saved_attrs
        elif hide:
            widget_id.saved_attrs = widget_id.height, widget_id.size_hint_y, widget_id.opacity, widget_id.disabled
            widget_id.height, widget_id.size_hint_y, widget_id.opacity, widget_id.disabled = 0, None, 0, True


    def set_login_method(self,method):
        debug_print(method)
        self.huamidevice.method=method
        if method == 'xiaomi':
            self.instructions_label.text='Press "Get token", sign in, copy URL and paste here'
            self.set_visibility(self.credentials_email_layout, hide=True)
            self.set_visibility(self.credentials_password_layout, hide=True)
            self.set_visibility(self.paste_token_input_layout, hide=False)
            self.set_visibility(self.result_value_layout, hide=False)
            self.get_token_button.disabled=False
            self.fetch_agps_button.disabled=True
            self.fetch_key_button.disabled=True
        else: #amazfit
            self.instructions_label.text='Email and password must be filled, then use Fetch key or Fetch aGPS'
            self.set_visibility(self.credentials_email_layout, hide=False)
            self.set_visibility(self.credentials_password_layout, hide=False)
            self.set_visibility(self.paste_token_input_layout, hide=True)
            #self.set_visibility(self.result_value_layout, hide=True)
            self.get_token_button.disabled=True
            self.fetch_agps_button.disabled=False
            self.fetch_key_button.disabled=False

    def set_token(self, instance, text):
        debug_print("got", text)
        debug_print(self.huamidevice)
        self.huamidevice.parse_token(text)
        debug_print(self.huamidevice)
        if self.huamidevice.access_token is not None:
            self.fetch_agps_button.disabled=False
            self.fetch_key_button.disabled=False
            self.instructions_label.text='now press "Fetch key" or "Fetch aGPS"'
        else:
            if self.paste_token_input_layout.disabled==False:
                self.instructions_label.text='token not found in the url, repeat sign in a copy/paste url'



    def on_press_button_gettoken(self, instance):
        debug_print('You pressed the button login!')
        self.result_value_value.text='No keys yet'
        self.paste_token_input.text=''
        self.fetch_agps_button.disabled=True
        self.fetch_key_button.disabled=True
        self.result_value_layout.disabled=True
        self.instructions_label.text="log in and paste url here"
        debug_print(self.huamidevice)
        if self.huamidevice.method == 'xiaomi':
            self.instructions_label.text="log in and paste url here"
            login_url = urls.URLS["login_xiaomi"]
            if ( platform != 'android' ):
                import webbrowser
                webbrowser.open(login_url, new = 2)
            else:
                from jnius import autoclass 
                from jnius import cast

                PythonActivity = autoclass('org.kivy.android.PythonActivity')
                Intent = autoclass('android.content.Intent')
                Uri = autoclass('android.net.Uri')
                intent = Intent()
                intent.setAction(Intent.ACTION_VIEW)
                intent.setData(Uri.parse(login_url))
                currentActivity = cast('android.app.Activity', PythonActivity.mActivity)
                currentActivity.startActivity(intent)
            self.paste_token_input_layout.disabled=False
            return
        else:
            #login method amazfit
            try:
                res=self.huamidevice.get_access_token()
                print("amazfit get access token result", res)
                if res:
                    #if self.huamidevice.user_id is not None:
                    #    self.instructions_label.text="Signed in as: {}, getting data".format(self.huamidevice.user_id)
                    #else:
                    #    self.instructions_label.text="You must sign in first"
                    self.fetch_key_button.disabled=False
                    self.fetch_agps_button.disabled=False

            except Exception as e:
                debug_print(e)
                self.instructions_label.text=f"{e}"

    def on_press_button_fetch_key(self, instance):
        debug_print('You pressed the button fetch!')

        if self.huamidevice.method=='amazfit':
            res=False
            try:
                res=self.huamidevice.get_access_token()
            except Exception as e:
                debug_print(e)
                self.instructions_label.text=f"{e}"
            if not res:
                self.instructions_label.text="amazfit login failed" 
        self.result_value_value.text='No keys yet'
        self.paste_token_input.text=''
        self.result_value_layout.disabled=True
        self.paste_token_input_layout.disabled=True
        if self.huamidevice.method!='amazfit':
            self.fetch_key_button.disabled=True
            self.fetch_agps_button.disabled=True
        debug_print(self.huamidevice)
        self.instructions_label.text="signing in and getting keys"
        Clock.schedule_once(self.fetch_keys, 1)

    def fetch_keys(self, *xargs):
        try:
            res=self.huamidevice.login()
            if res:
                self.instructions_label.text="Signed in as: {}, getting data".format(self.huamidevice.user_id)
        except Exception as e:
            debug_print(e)
            self.instructions_label.text=f"{e}"
            return


        device_keys = self.huamidevice.get_wearable_auth_keys()
        self.result_value_layout.disabled=False
        self.result_value_value.text="No keys yet"
        key_button = None
        for device_key in device_keys:
            debug_print(f"{device_key} {device_keys[device_key]}")
            key_button = MyDDKeyButton(device_key, device_keys[device_key], size_hint_y=None, height=44)
            key_button.bind(on_release=lambda btn: self.ddown.select(btn))
            
            self.ddown.add_widget(key_button)
            

        if key_button is None or key_button.text == "":
            self.instructions_label.text="No keys on the server"
        else:
            self.instructions_label.text="Got the keys, select one and use the Copy button"
        self.ddown.select(key_button) # last genereated key button, yes

        #Clock.schedule_once(partial(self.doit), 1)

    def on_press_paste_token(self, instance):
        self.paste_token_input.text=Clipboard.paste()

    def on_press_paste_email(self, instance):
        self.credentials_email_input.text=Clipboard.paste()

    def on_press_paste_password(self, instance):
        self.credentials_password_input.text=Clipboard.paste()

    def on_press_copy_result(self, instance):
        Clipboard.copy(self.result_value_value.ak)
        self.instructions_label.text='value copied to clipboard'
    
    def on_press_paste(self, instance):
        instance.text=Clipboard.paste()

    def on_press_copy(self, instance):
        Clipboard.copy(instance.text)
        self.instructions_label.text='value copied to clipboard'

    def on_press_load(self, instance, key):
        if self.store.exists(key):
            instance.text=self.store.get(key)["value"]

    def on_press_save(self, instance, key):
        self.store.put(key, value=instance.text)

    def on_press_button_agps(self, instance):
        debug_print('You pressed the button agps!')

        if self.huamidevice.method=='amazfit':
            res=False
            try:
                res=self.huamidevice.get_access_token()
            except Exception as e:
                debug_print(e)
                self.instructions_label.text=f"{e}"
            if not res:
                self.instructions_label.text="amazfit login failed" 
        self.result_value_value.text=''
        self.paste_token_input.text=''
        self.result_value_layout.disabled=True
        self.paste_token_input_layout.disabled=True
        if self.huamidevice.method!='amazfit':
            self.fetch_key_button.disabled=True
            self.fetch_agps_button.disabled=True
        debug_print(self.huamidevice)
        self.instructions_label.text="signing in and getting files" 
        Clock.schedule_once (self.get_agps_files, 1)

    def get_agps_files(self, *xargs):
        import zipfile
        import shutil
        import os
        try:
            res=self.huamidevice.login()
            if res:
                self.instructions_label.text="Signed in as: {}, getting data".format(self.huamidevice.user_id)
        except Exception as e:
            debug_print(e)
            self.instructions_label.text=f"{e}"
            return

        self.huamidevice.get_gps_data()
        agps_file_names = ["cep_alm_pak.zip"]
        agps_file_names = ["cep_1week.zip", "cep_7days.zip", "lle_1week.zip", "cep_pak.bin", "epo.zip"]
        data_dir="./tmp"
        if ( platform == 'android' ):
            from jnius import autoclass 
            from jnius import cast
            Environment = autoclass('android.os.Environment')
            File = autoclass('java.io.File')
            data_dir = Environment.getExternalStorageDirectory().getPath()
        elif not os.path.exists(data_dir):
            os.mkdir(data_dir)

        debug_print(data_dir)
        for filename in agps_file_names:
            sdpathfile = os.path.join(data_dir, filename)
            shutil.copyfile(filename, sdpathfile)
            print(f"process {filename}")
            if "zip" not in filename:
                continue
            if filename == "epo.zip":
                # epo zip files should not be extracted
                continue
            with zipfile.ZipFile(filename, "r") as zip_f:
                #zip_f.extractall()
                zip_f.extractall(data_dir)

        self.instructions_label.text="Files downloaded and extracted"
        #Clock.schedule_once(partial(self.doit), 1)

    def create_uihh_agps_file(self, *xargs):
        import typemap as tm
        import pathlib
        from binascii import crc32
        data_dir="./tmp"
        
        if ( platform == 'android' ):
            from jnius import autoclass 
            from jnius import cast
            Environment = autoclass('android.os.Environment')
            File = autoclass('java.io.File')
            data_dir = Environment.getExternalStorageDirectory().getPath()

        content = b""

        for typeID, inputfilename in tm.typemap.items():
            fullPathName = pathlib.Path(data_dir).joinpath(inputfilename)
            if not fullPathName.is_file():
                self.instructions_label.text=f"[E] File not found: {fullPathName}"
                return

            with open(fullPathName, "rb") as f:
                filecontent = f.read()

            print(f"[I] Packing {inputfilename}")
            fileheader =  chr(1).encode() +typeID.to_bytes(1,"big") + len(filecontent).to_bytes(4,"little") + crc32(filecontent).to_bytes(4,"little")
            content += fileheader + filecontent

        print("[I] Adding header")
        header = ["UIHH" , chr(0x04) , chr(0x00) , chr(0x00) , chr(0x00) , chr(0x00) , chr(0x00) , chr(0x00) , chr(0x01) , crc32(content).to_bytes(4,"little") , chr(0x00) , chr(0x00) , chr(0x00) , chr(0x00) , chr(0x00) , chr(0x00) , len(content).to_bytes(4,"little") , chr(0x00) , chr(0x00) , chr(0x00) , chr(0x00) , chr(0x00) , chr(0x00)]

        merged_header=b""
        for i in header:
            if isinstance(i, str):
                i=i.encode()
            merged_header+=i

        content = merged_header+content


        outputfile = pathlib.Path(data_dir).joinpath("aGPS_UIHH.bin")
        print(f"[I] Writing {outputfile}")
        with open(outputfile, "wb") as f:
            f.write(content)

        self.instructions_label.text="aGPS UIHH created"
        #Clock.schedule_once(partial(self.doit), 1)
    def on_press_button_share_agps(self, instance):
        #not working because android broke it
        if ( platform == 'android' ):
            import os
            from jnius import autoclass 
            from jnius import cast
            Environment = autoclass('android.os.Environment')
            File = autoclass('java.io.File')
            data_dir = Environment.getExternalStorageDirectory().getPath()

            PythonActivity = autoclass('org.kivy.android.PythonActivity')
            Intent = autoclass('android.content.Intent')
            Uri = autoclass('android.net.Uri')
            intent = Intent()
            intent.setAction(Intent.ACTION_VIEW)
            data_dir = getattr(self, 'user_data_dir')
            file_target=File(os.path.join(data_dir, "cep_pak.bin"))
            #target=Uri.parse(os.path.join("file:///", data_dir, "cep_pak.bin"))
            target=Uri.fromFile(file_target)
            #intent.setData(Uri.parse(os.path.join("file:///", data_dir, "cep_pak.bin")))
            #intent.setType("application/octet-stream")
            intent.setDataAndType(target, "application/octet-stream")
            intent.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)
            currentActivity = cast('android.app.Activity', PythonActivity.mActivity)
            currentActivity.startActivity(intent)

            #intent = Intent()
            #intent.setAction(Intent.ACTION_VIEW)
            #intent.setData(Uri.parse("gps_alm.bin"))
            #currentActivity = cast('android.app.Activity', PythonActivity.mActivity)
            #currentActivity.startActivity(intent)


    #def doit(self, *kargs):

    def openweb(url):
        debug_print("open ", url)

if __name__ == '__main__':
    app = Main()
    app.run()

