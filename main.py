from ulauncher.api.client.Extension import Extension
from ulauncher.api.client.EventListener import EventListener
from ulauncher.api.shared.event import KeywordQueryEvent, ItemEnterEvent, PreferencesUpdateEvent, PreferencesEvent
from ulauncher.api.shared.item.ExtensionResultItem import ExtensionResultItem
from ulauncher.api.shared.action.ExtensionCustomAction import ExtensionCustomAction
from ulauncher.api.shared.action.RenderResultListAction import RenderResultListAction
import logging
import io
import matplotlib.pyplot as plt
import matplotlib
from PIL import Image, ImageChops
import gi

gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk, GLib, GdkPixbuf

logger = logging.getLogger(__name__)


class MathExtension(Extension):

    def __init__(self):
        super(MathExtension, self).__init__()
        self.clipboard = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)
        self.subscribe(KeywordQueryEvent, KeywordQueryEventListener())
        self.subscribe(ItemEnterEvent, ItemEnterEventListener())

    @staticmethod
    def trim(im):
        bg = Image.new(im.mode, im.size, im.getpixel((0, 0)))
        diff = ImageChops.difference(im, bg)
        diff = ImageChops.add(diff, diff, 2.0, -100)
        bbox = diff.getbbox()
        if bbox:
            return im.crop(bbox)

    @staticmethod
    def generate_image(text):
        try:
            matplotlib.rcParams['mathtext.fontset'] = 'cm'
            fig = plt.figure(figsize=(200, 5))
            fig.text(0.5, 0.5, "$" + text + "$", size=100, ha='center', va='center', bbox={'fill': False, 'pad': 10})

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
        im = self.trim(image).convert("RGB")
        buf.close()

        im_data = im.tobytes()
        w, h = im.size
        im_data = GLib.Bytes.new(im_data)
        pixbuf = GdkPixbuf.Pixbuf.new_from_bytes(im_data, GdkPixbuf.Colorspace.RGB, False, 8, w, h, w * 3)
        self.clipboard.set_image(pixbuf)
        self.clipboard.store()


class ItemEnterEventListener(EventListener):

    def on_event(self, event, extension):
        extension.copy_to_clipboard(event.get_data())


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
