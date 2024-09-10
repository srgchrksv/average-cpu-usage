import gi
import subprocess
import random

gi.require_version("Gtk", "3.0")
import time
from gi.repository import Gtk, GLib


class TreeViewFilterWindow(Gtk.Window):
    def __init__(self):
        super().__init__(title="Avg CPU Usage")
        self.set_border_width(10)
        self.process_info = {}
        self.prev_process_info = {}
        self.new_process_info = set()
        self.time_label = Gtk.Label()
        self.start_time = time.time()

        # Setting up the self.grid in which the elements are to be positioned
        self.grid = Gtk.Grid()
        self.grid.set_column_homogeneous(True)
        self.grid.set_row_homogeneous(True)
        self.add(self.grid)

        # Creating the ListStore model
        self.software_liststore = Gtk.ListStore(str, int, float, str)
        self.avg_cpu()

        self.sorted_model = Gtk.TreeModelSort(model=self.software_liststore)
        self.sorted_model.set_sort_column_id(2, Gtk.SortType.DESCENDING)

        # creating the treeview, making it use the sorted model, and adding the columns
        self.treeview = Gtk.TreeView(model=self.sorted_model)
        for i, column_title in enumerate(["process", "PID", "avg_cpu", "command"]):
            renderer = Gtk.CellRendererText()
            column = Gtk.TreeViewColumn(column_title, renderer, text=i)
            column.set_resizable(True)  # Make the column resizable

            column.set_sort_column_id(i)  # Make the column sortable
            self.treeview.append_column(column)

        # setting up the layout, putting the treeview in a scrollwindow, and the buttons in a row
        self.scrollable_treelist = Gtk.ScrolledWindow()
        self.scrollable_treelist.set_vexpand(True)
        self.scrollable_treelist.set_hexpand(True)
        # Calculate the number of columns in the treeview
        num_columns = len(self.treeview.get_columns())

        self.scrollable_treelist.add(self.treeview)



        # Creating the ListStore model for the additional table
        self.additional_liststore = Gtk.ListStore(str)

        # Creating the TreeView for the additional table
        self.additional_treeview = Gtk.TreeView(model=self.additional_liststore)

        # Creating the column for the additional table
        additional_renderer = Gtk.CellRendererText()
        additional_column = Gtk.TreeViewColumn("new Processes",additional_renderer, text=0)
        additional_column.set_resizable(True)

             # setting up the layout, putting the treeview in a scrollwindow, and the buttons in a row
        self.additional_scrollable_treelist = Gtk.ScrolledWindow()
        self.additional_scrollable_treelist.set_hexpand(True)
        self.additional_scrollable_treelist.set_vexpand(True)

        self.additional_treeview.append_column(additional_column)
        self.additional_scrollable_treelist.add(self.additional_treeview)

        self.update_time_label()


        # Adding the additional table to the grid
        self.grid.attach(self.time_label, 0, 0, 1, 1)
        self.grid.attach(self.additional_scrollable_treelist, 0, 1, 1, 10)
        self.grid.attach(self.scrollable_treelist, 2, 1, 3, 10)
        # Calculate the number of buttons needed to fit the screen

        # Set the width and height of the window to fit all elements
        self.set_default_size(num_columns * 100, 600)

        self.show_all()
        # Add a timeout to update
        GLib.timeout_add(1000, self.update_cpu_usage)
        GLib.timeout_add(1000 * 5, self.clear_process_info)
        GLib.timeout_add(1000 * 10, self.update_time_label)

    def update_time_label(self):
        # Calculate the time since running in minutes
        time_since_running = round((time.time() - self.start_time) / 60, 2)
        self.time_label.set_text(f"Time since running: {time_since_running} minutes")
        return True

    def update_cpu_usage(self):
        self.software_liststore.clear()
        self.avg_cpu()
        return True

    def clear_process_info(self):
        self.prev_process_info = self.process_info
        self.process_info = {}
        return True

    def avg_cpu(self):
        # Run the 'ps' command to get the list of running processes and their CPU usage
        result = subprocess.run(
            ["ps", "-eo", "comm,pid,%cpu,command"], capture_output=True, text=True
        )

        # Split the output into lines
        lines = result.stdout.splitlines()
        # Skip the header line
        for line in lines[1:]:
            try:
                # Split the line into command name, PID, CPU usage, and command line
                parts = line.split(maxsplit=3)
                command_name = parts[0]
                pid = int(parts[1])
                cpu_percent = float(parts[2])
                command_line = parts[3] if len(parts) > 3 else ""
                if (
                    float(cpu_percent) == 0.0
                    or "ps -eo comm,pid,%cpu,command" == command_line
                ):
                    continue
                # Store the process information in the dictionary
                self.process_info[pid] = {
                    "cpu_percent": (
                        self.process_info[pid]["cpu_percent"] + [cpu_percent]
                        if pid in self.process_info
                        else [cpu_percent]
                    ),
                    "command_name": command_name,
                    "command_line": command_line,
                }
            except (ValueError, IndexError):
                # Ignore any lines that cannot be parsed
                pass

        for pid, info in self.process_info.items():
            if self.prev_process_info and pid not in self.prev_process_info:
                info["command_name"] = info["command_name"].upper()
                to_add = [f"{info['command_name']}-{pid}-{info['command_line']}"]
                if pid not in self.new_process_info:
                    self.new_process_info.add(pid)
                    self.additional_liststore.append(to_add)

            row = [
                info["command_name"],
                pid,
                round(sum(info["cpu_percent"]) / len(info["cpu_percent"]), 2),
                info["command_line"],
            ]
            self.software_liststore.append(row)


win = TreeViewFilterWindow()
win.connect("destroy", Gtk.main_quit)
win.show_all()
Gtk.main()
