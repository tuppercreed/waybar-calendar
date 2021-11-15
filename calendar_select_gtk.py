import sys
import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gio, GLib


from calendar_select import sql_calendar


class MyWindow(Gtk.Window):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.set_border_width(10)

        self.set_resizable(False)

        box_outer = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        self.add(box_outer)

        listbox = Gtk.ListBox()
        listbox.set_selection_mode(Gtk.SelectionMode.NONE)
        box_outer.pack_start(listbox, True, True, 0)

        row = Gtk.ListBoxRow()
        hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=50)
        row.add(hbox)
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        hbox.pack_start(vbox, True, True, 0)

        label1 = Gtk.Label("asdfsf", xalign=0)
        label2 = Gtk.Label("label 2", xalign=0)
        vbox.pack_start(label1, True, True, 0)
        vbox.pack_start(label2, True, True, 0)

        switch = Gtk.Switch()
        switch.props.valign = Gtk.Align.CENTER
        hbox.pack_start(switch, False, True, 0)

        # listbox.add(row)

        cal = sql_calendar()
        names = cal.read()

        for name in names:
            row = Gtk.ListBoxRow()
            hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=50)
            row.add(hbox)
            label = Gtk.Label(name.summary, xalign=0)
            switch = Gtk.Switch()
            hbox.pack_start(label, True, True, 0)
            hbox.pack_start(switch, False, True, 0)

            listbox.add(row)

        def sort_func(row_1, row_2, data, notify_destroy):
            text_1 = row_1.get_child().get_children()[0].get_text()
            text_2 = row_2.get_child().get_children()[0].get_text()
            return text_1 > text_2

        listbox.set_sort_func(sort_func, None, False)

        # label = Gtk.Label(label="Hello World", angle=25, halign=Gtk.Align.END)

        # widget = Gtk.Box()
        # print("fs")

    def on_button_clicked(self, widget):
        print("Hello, World")


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
