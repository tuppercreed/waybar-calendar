import sys
import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gio, GLib

from cal import Calendar, Calendars


class DialogCal(Gtk.Dialog):
    def __init__(self, parent, calendars):
        super().__init__(title="Select active calendars", transient_for=parent, flags=0)
        self.set_border_width(10)

        self.add_buttons(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_OK, Gtk.ResponseType.OK)

        box = self.get_content_area()

        box.set_spacing(6)

        header = Gtk.Label(label="Selected Calendars", xalign=0)
        box.pack_start(header, True, True, 0)

        listbox = Gtk.ListBox()
        listbox.set_selection_mode(Gtk.SelectionMode.NONE)
        box.pack_start(listbox, True, True, 0)

        self.switches = {}

        for calendar in calendars:
            row = Gtk.ListBoxRow()
            row.set_margin_start(5)
            hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=25)
            row.add(hbox)
            label = Gtk.Label(label=calendar.name, xalign=0)
            label.set_max_width_chars(15)
            label.set_line_wrap(True)
            switch = Gtk.Switch()
            switch.set_active(calendar.active)
            hbox.pack_start(label, True, True, 0)
            hbox.pack_start(switch, False, True, 0)

            self.switches[calendar.id] = switch

            listbox.add(row)

        self.show_all()


class MyWindow(Gtk.Window):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.set_border_width(10)

        self.set_resizable(False)

        box_outer = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        self.add(box_outer)

        button = Gtk.Button(label="open dialog")
        button.connect("clicked", self.on_button_clicked)
        box_outer.pack_start(button, True, True, 0)

    def on_button_clicked(self, widget):
        calendars = Calendars()

        dialog = DialogCal(self, calendars)
        response = dialog.run()

        if response == Gtk.ResponseType.OK:
            print("Ok")
            results = {key: switch.get_active() for key, switch in dialog.switches.items()}

            overwrites = []
            for i, cal in enumerate(calendars):
                if cal.active != results[cal.id]:
                    overwrites.append(
                        (
                            i,
                            Calendar(
                                id=cal.id,
                                name=cal.name,
                                description=cal.description,
                                time_zone=cal.time_zone,
                                active=results[cal.id],
                            ),
                        )
                    )

            for overwrite in overwrites:
                calendars[overwrite[0]] = overwrite[1]
            if len(overwrites) > 0:
                calendars.write()
        elif response == Gtk.ResponseType.CANCEL:
            print("cancel")

        dialog.destroy()

        """def sort_func(row_1, row_2, data, notify_destroy):
            text_1 = row_1.get_child().get_children()[0].get_text()
            text_2 = row_2.get_child().get_children()[0].get_text()
            return text_1 > text_2

        listbox.set_sort_func(sort_func, None, False)"""


class Application(Gtk.Application):
    def __init__(self, *args, **kwargs):
        super().__init__(
            *args, application_id="org.example.myapp", flags=Gio.ApplicationFlags.HANDLES_COMMAND_LINE, **kwargs
        )
        self.window = None

        self.add_main_option("test", ord("t"), GLib.OptionFlags.NONE, GLib.OptionArg.NONE, "Command line test", None)

    def do_startup(self):
        Gtk.Application.do_startup(self)

    def do_activate(self):
        if not self.window:
            # Windows are spawned from Application, when last window closes, application closes
            self.window = MyWindow(application=self, title="MyWindow")
            self.window.show_all()

        self.window.present()

    def do_command_line(self, command_line):
        options = command_line.get_options_dict()
        # convert GVariantDict -> GVariant -> dict
        options = options.end().unpack()

        if "test" in options:
            print("Test argument received: %s" % options["test"])

        self.activate()

        return 0


if __name__ == "__main__":
    app = Application()
    app.run(sys.argv)
