from ulauncher.api.client.Extension import Extension
from ulauncher.api.client.EventListener import EventListener
from ulauncher.api.shared.event import KeywordQueryEvent, ItemEnterEvent, PreferencesUpdateEvent, PreferencesEvent
from ulauncher.api.shared.item.ExtensionResultItem import ExtensionResultItem
from ulauncher.api.shared.action.ExtensionCustomAction import ExtensionCustomAction
from ulauncher.api.shared.action.RenderResultListAction import RenderResultListAction
import logging
import subprocess
import shlex
import io
import matplotlib.pyplot as plt
import matplotlib
from PIL import Image, ImageChops

logger = logging.getLogger(__name__)


class MathExtension(Extension):

    def __init__(self):
        super(MathExtension, self).__init__()
        self.subscribe(KeywordQueryEvent, KeywordQueryEventListener())
        self.subscribe(ItemEnterEvent, ItemEnterEventListener())
        self.subscribe(PreferencesUpdateEvent, PreferencesUpdateEventListener())
        self.subscribe(PreferencesEvent, PreferencesEventListener())

    def trim(self, im):
        bg = Image.new(im.mode, im.size, im.getpixel((0, 0)))
        diff = ImageChops.difference(im, bg)
        diff = ImageChops.add(diff, diff, 2.0, -100)
        bbox = diff.getbbox()
        if bbox:
            return im.crop(bbox)

    def generate_image(self, text):
        try:
            matplotlib.rcParams['mathtext.fontset'] = 'cm'
            fig = plt.figure(figsize=(20, 5))
            fig.text(0.5, 0.5, "$" + text + "$", size=25, ha='center', va='center', bbox={'fill': False, 'pad': 10})

            buf = io.BytesIO()
            fig.savefig(buf, format='png')
            result = buf.getvalue()
            buf.close()
            return True, result
        except Exception as e:
            return False, str(e)

    def copy_to_clipboard(self, image_data):
        logger.debug("Copying generated image to clipboard")
        buf = io.BytesIO(image_data)
        buf.seek(0)
        image = Image.open(buf)
        im = self.trim(image)
        buf.close()

        buf = io.BytesIO()
        im.save(buf, format='PNG')

        clipboard_proc = subprocess.Popen(shlex.split(self.copy), stdin=subprocess.PIPE)
        clipboard_proc.communicate(buf.getvalue())
        buf.close()


class ItemEnterEventListener(EventListener):

    def on_event(self, event, extension):
        extension.copy_to_clipboard(event.get_data())


class PreferencesUpdateEventListener(EventListener):

    def on_event(self, event, extension):
        if event.id == "math_copy":
            extension.copy = event.new_value


class PreferencesEventListener(EventListener):

    def on_event(self, event, extension):
        extension.copy = event.preferences["math_copy"]


class KeywordQueryEventListener(EventListener):

    def on_event(self, event, extension):
        icon = "images/icon.png"
        items = []
        arg = event.get_argument()

        if arg is not None and len(arg) > 0:
            arg_string = ''.join(arg)
            success, result = extension.generate_image(arg_string)
            if success:
                items.append(ExtensionResultItem(icon=icon,
                                                 name=arg_string,
                                                 description="Press enter to copy generated image to clipboard.",
                                                 on_enter=ExtensionCustomAction(result, keep_app_open=False)))
            else:
                items.append(ExtensionResultItem(icon=icon,
                                                 name=arg_string,
                                                 description="Error: {}".format(result)))
        return RenderResultListAction(items)


if __name__ == '__main__':
    MathExtension().run()
