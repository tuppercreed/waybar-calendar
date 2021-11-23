import sys, importlib
from datetime import datetime, timedelta

import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gio, GLib

from cal import Calendar, Calendars, Event, Events

google_calendar = importlib.import_module("google_calendar", "waybar-calendar")

TZ_NAME = "Australia/Melbourne"


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

        for calendar in calendars.values():
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

        def sort_func(row_1, row_2, data, notify_destroy):
            text_1 = row_1.get_child().get_children()[1].get_active()
            text_2 = row_2.get_child().get_children()[1].get_active()
            return text_1 < text_2

        listbox.set_sort_func(sort_func, None, False)


class MyWindow(Gtk.Window):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.set_border_width(10)

        self.set_resizable(False)

        self._calendars = Calendars()

        box_outer = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        self.add(box_outer)

        start = datetime.utcnow()
        end = start + timedelta(150)
        events = Events(window=(start, end), limit=10)

        blurb = Gtk.Label(label="Upcoming events:", xalign=0)
        box_outer.pack_start(blurb, True, True, 0)

        for group, events in events.group(TZ_NAME).items():
            dt = events[0].local_start(TZ_NAME)
            if 4 <= dt.day % 100 <= 20:
                day_tag = "th"
            else:
                day_tag = {1: "st", 2: "nd", 3: "rd"}.get(dt.day % 10, "th")
            group_label = f"{dt:%A}, {dt:%-d}{day_tag} of {dt:%B}"
            frame = Gtk.Frame(label=group_label)
            frame.set_shadow_type(Gtk.ShadowType.ETCHED_IN)
            box_event_group = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=3)

            # widgets_group.append(Gtk.Label(label=group, xalign=0))

            for event in events:

                box_event = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=1)
                box_event.set_margin_start(10)
                box_event.set_margin_end(10)

                widgets = []
                widgets.append(Gtk.Label(label=event.name, xalign=0))
                # widgets.append(Gtk.Label(label=event.local_start(TZ_NAME).strftime("%Y-%m-%d"), xalign=0))
                if type(event.start) is datetime:
                    widgets.append(
                        Gtk.Label(
                            label=f"{event.local_start(TZ_NAME).strftime('%H:%M')} - {event.local_end(TZ_NAME).strftime('%H:%M')}",
                            xalign=1,
                        )
                    )
                if event.description is not None:
                    widgets.append(Gtk.Label(label=event.description, xalign=0))

                for widget in widgets:
                    box_event.pack_start(widget, True, True, 0)

                box_event_group.pack_start(box_event, True, True, 0)

            frame.add(box_event_group)
            box_outer.pack_start(frame, True, True, 5)

        box_buttons = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=3)

        button_configure = Gtk.Button(label="Configure Calendars")
        button_configure.connect("clicked", self.on_configure_clicked)
        box_buttons.pack_start(button_configure, True, True, 0)

        button_sync_calendars = Gtk.Button(label="Sync Calendars")
        button_sync_calendars.connect("clicked", self.on_sync_clicked)
        box_buttons.pack_start(button_sync_calendars, True, True, 0)

        button_sync_events = Gtk.Button(label="Sync Events")
        button_sync_events.connect("clicked", self.on_sync_events_clicked)
        box_buttons.pack_start(button_sync_events, True, True, 0)

        box_outer.pack_start(box_buttons, True, True, 0)

    def on_configure_clicked(self, widget):

        dialog = DialogCal(self, self._calendars)
        response = dialog.run()

        if response == Gtk.ResponseType.OK:
            print("Ok")
            results = {key: switch.get_active() for key, switch in dialog.switches.items()}

            overwrites = []
            for i, cal in self._calendars.items():
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
                self._calendars[overwrite[0]] = overwrite[1]
            if len(overwrites) > 0:
                self._calendars.write()
        elif response == Gtk.ResponseType.CANCEL:
            print("cancel")

        dialog.destroy()

        """def sort_func(row_1, row_2, data, notify_destroy):
            text_1 = row_1.get_child().get_children()[0].get_text()
            text_2 = row_2.get_child().get_children()[0].get_text()
            return text_1 > text_2

        listbox.set_sort_func(sort_func, None, False)"""

    def on_sync_clicked(self, widget):
        dialog = Gtk.MessageDialog(
            transient_for=self,
            flags=0,
            message_type=Gtk.MessageType.INFO,
            buttons=Gtk.ButtonsType.OK,
            text="Completed Sync",
        )

        cals = google_calendar.sync_calendars()

        dialog.run()
        dialog.destroy()

    def on_sync_events_clicked(self, widget):
        dialog = Gtk.MessageDialog(
            transient_for=self,
            flags=0,
            message_type=Gtk.MessageType.INFO,
            buttons=Gtk.ButtonsType.OK,
            text="Completed Sync",
        )

        events = google_calendar.sync_events(self._calendars)

        dialog.run()
        dialog.destroy()


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
