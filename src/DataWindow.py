import datetime
import time
import os
import queue
import random
import string
from tkinter import *
from tkinter import messagebox
from tkinter import simpledialog
from tkinter import ttk
import RPi.GPIO as GPIO

from Status import Status
from Timer import Timer
from Data import Data
from Mode import Mode
from Control import Control
from StatCounter import StatCounter
from CommunicationDriver import Comm
from QualityCheck import QualityCheck
from AltitudeGraph import AltitudeGraph
from AccelerometerGyroGraphs import AccelerometerGyroGraphs
from communications.RadioModule import Module
from Timer import ShutdownTimer


class DataWindow:
    def __init__(self, name, data_queue):
        """
        Init functions that sets up the general shape and feel of the window

        :param name: Name of the main window
        :param data_queue: queue used to communicate with the radio
        """
        self.queue = data_queue
        self.bg_color = "#484949"
        frames_bg = "#969694"
        self.framesBg = frames_bg
        self.frames_bg = frames_bg
        self.time_bg = "#1e1e1e"
        self.yellow = "#f8fc16"
        self.total_rows = 18

        # Random Vars to init for draw()
        self.start_timer = None
        self.timer = None
        self.dataRocket = None
        self.dataRocket = None
        self.altGraph = None
        self.dataBalloon = None
        self.sixGraph = None
        self.control = None
        self.altitude_graph = None
        self.quality_checks = None
        self.stability = None
        self.stability_button = None
        self.packets_sent = None
        self.packets_received = None
        self.received_percentage = None
        self.warningLabel = None

        # Random Vars for init_graph_stuff()
        self.balloon_acc_xQ = None
        self.balloon_acc_yQ = None
        self.balloon_acc_zQ = None
        self.balloon_gyro_xQ = None
        self.balloon_gyro_yQ = None
        self.balloon_gyro_zQ = None
        self.rocket_acc_xQ = None
        self.rocket_acc_yQ = None
        self.rocket_acc_zQ = None
        self.rocket_gyro_xQ = None
        self.rocket_gyro_yQ = None
        self.rocket_gyro_zQ = None
        self.altitudeQ = None
        self.acc_gyro_graphs = None

        # Base file writing from program's execution directory
        program_path = os.path.dirname(os.path.realpath(__file__))
        self.status_log_path = os.path.join(program_path, "../logs/status.log")
        self.image_folder_path = os.path.join(program_path, "../res/img")

        self.name = name

        # Prevents the user from resizing the window too small
        self.name.minsize(round(self.name.winfo_screenwidth() / 2), round(self.name.winfo_screenheight() / 2))

        # Set up
        self.test_mode = False
        self.abort_method = None
        self.radio = Module.get_instance(self)

        name.title("Ground Station Graphical User Interface v0.3-alpha")
        # name.iconbitmap(os.path.join(self.image_folder_path, "MyOrbital.ico"))

        # self.name.geometry('1000x600')
        self.name.configure(bg=self.bg_color)
        # name.attributes('-zoomed', True)
        # name.state('zoomed')
        # name.update_idletasks()

        # Set up GPIO pins for use, see documentation for pin layout
        # orange wire
        self.launch_signal = 11
        # yellow wire
        self.on_signal = 12
        # white wire
        self.gui_switch = 7

        GPIO.setmode(GPIO.BOARD)
        GPIO.setwarnings(False)
        GPIO.setup(self.launch_signal, GPIO.IN)
        GPIO.setup(self.on_signal, GPIO.OUT)
        GPIO.setup(self.gui_switch, GPIO.OUT)

        GPIO.output(self.on_signal, GPIO.HIGH)
        GPIO.output(self.on_signal, GPIO.LOW)
        GPIO.output(self.gui_switch, GPIO.LOW)

        GPIO.add_event_detect(11, GPIO.RISING, callback=self.launch)

        self.init_graph_stuff()
        self.draw()

        self.shutdown_timer = None

        # Running variable to see if program was terminated
        self.running = 1

    def draw(self):
        self.make_tool_bar()

        self.make_grid()

        # Make timer sections
        Label(self.name, text="Mission Clock:", font=('times', 16, 'bold'), bg=self.frames_bg). \
            grid(row=0, column=1, rowspan=2, columnspan=1, sticky=N + S + E + W)
        Label(self.name, text="Flight Clock:", font=('times', 16, 'bold'), bg=self.frames_bg). \
            grid(row=3, column=1, rowspan=2, columnspan=1, sticky=N + S + E + W)
        self.start_timer = Timer(self.name, 0, 2, 2, 2, self.time_bg)
        self.timer = Timer(self.name, 3, 2, 2, 2, self.time_bg)

        # Make data sections
        self.dataBalloon = Data(self.name, "Balloon Data", 6, 9, self.frames_bg)

        # Config button styles
        ttk.Style().configure("yellow.TButton", background=self.yellow)

        # Place Graph buttons
        # self.init_graph_queues()

        self.altGraph = ttk.Button(self.name, text="Altitude", style="yellow.TButton", command=self.open_altitude_graph)
        self.sixGraph = ttk.Button(self.name, text="Direction", style="yellow.TButton",
                                   command=self.open_acc_gyro_graphs)

        self.altGraph.grid(column=6, columnspan=4, row=11, rowspan=1, sticky=N + S + E + W)
        self.sixGraph.grid(column=6, columnspan=4, row=12, rowspan=1, sticky=N + S + E + W)

        # Adds our logo
        logo = PhotoImage(file=os.path.join(self.image_folder_path, "orbital-logo-reduced.gif"))
        logo_label = Label(self.name, image=logo, bg=self.bg_color)
        logo_label.image = logo
        logo_label.grid(row=14, column=6, rowspan=3, columnspan=4, sticky=N + S + E + W)

        self.control = Control(self.name, 6, 2, 1, self.frames_bg)

        # Adds Radio Counters
        self.packets_sent = StatCounter(self.name, "Packets Sent", 1, 10, self.frames_bg)
        self.packets_received = StatCounter(self.name, "Packets Received", 2, 10, self.frames_bg)

        # Create received percentage
        Label(self.name, text="Percent Received", font=('times', 12, 'underline'), bg=self.frames_bg). \
            grid(row=10, column=3, sticky=S + E + W)

        self.received_percentage = StringVar()
        self.calc_received_percentage()

        Label(self.name, textvariable=self.received_percentage, bg=self.frames_bg). \
            grid(row=11, column=3, sticky=N + E + W)

        # Place Quality Indicators and Labels
        self.quality_checks = [QualityCheck(self.name, "QDM", 1, 12, self.frames_bg),
                               QualityCheck(self.name, "Ignition", 2, 12, self.frames_bg),
                               QualityCheck(self.name, "Platform Stability", 1, 14, self.frames_bg),
                               QualityCheck(self.name, "GS Radio", 3, 12, self.frames_bg),
                               QualityCheck(self.name, "Platform Radio", 3, 14, self.frames_bg),
                               ]

        self.quality_checks[3].set_quality(self.radio.is_local_device_init)

        # Innit the warning label
        self.warningLabel = Label(self.name, text="WARNING: TEST MODE", bg="#ff0000", relief=RAISED,
                                  font=("Times", 30, "bold"))

        # Create Button for Stability Control
        self.stability = False
        self.stability_button = ttk.Button(text="Turn On Stabilization", style="yellow.TButton",
                                           command=self.stability_message_callback)
        self.stability_button.grid(column=1, columnspan=3, row=16, sticky=N + S + E + W)

        # Binds verify and control buttons
        self.control.verify_button.config(command=self.verify_message_callback)
        self.control.abort_button.config(command=self.abort_message_callback)

    def init_graph_stuff(self):
        """
        Sets up the graphs
        :return: None
        """
        # Create several queue that holds the number for each line in every graph
        self.balloon_acc_xQ = queue.Queue()
        self.balloon_acc_yQ = queue.Queue()
        self.balloon_acc_zQ = queue.Queue()
        self.balloon_gyro_xQ = queue.Queue()
        self.balloon_gyro_yQ = queue.Queue()
        self.balloon_gyro_zQ = queue.Queue()
        self.rocket_acc_xQ = queue.Queue()
        self.rocket_acc_yQ = queue.Queue()
        self.rocket_acc_zQ = queue.Queue()
        self.rocket_gyro_xQ = queue.Queue()
        self.rocket_gyro_yQ = queue.Queue()
        self.rocket_gyro_zQ = queue.Queue()
        self.altitudeQ = queue.Queue()

        amount_of_point_to_graph = 20
        for i in range(0, amount_of_point_to_graph):
            self.balloon_acc_xQ.put(0)
            self.balloon_acc_yQ.put(0)
            self.balloon_acc_zQ.put(0)
            self.balloon_gyro_xQ.put(0)
            self.balloon_gyro_yQ.put(0)
            self.balloon_gyro_zQ.put(0)
            self.rocket_acc_xQ.put(0)
            self.rocket_acc_yQ.put(0)
            self.rocket_acc_zQ.put(0)
            self.rocket_gyro_xQ.put(0)
            self.rocket_gyro_yQ.put(0)
            self.rocket_gyro_zQ.put(0)
            self.altitudeQ.put(0)

        self.altitude_graph = None
        self.acc_gyro_graphs = None

    def make_tool_bar(self):
        """
        Sets up the labels and buttons in the tool bar and binds them to respective functions
        :return: None
        """
        menu_bar = Menu(self.name)

        file_menu = Menu(menu_bar, tearoff=0)
        program_menu = Menu(menu_bar, tearoff=0)
        help_menu = Menu(menu_bar, tearoff=0)
        # test_menu = Menu(menu_bar, tearoff=0)

        menu_bar.add_cascade(label="File", menu=file_menu)
        menu_bar.add_cascade(label="Program", menu=program_menu)
        menu_bar.add_cascade(label="Help", menu=help_menu)
        # menu_bar.add_cascade(label="Test", menu=test_menu)

        file_menu.add_command(label="Restart", command=self.restart_program)

        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.close)

        program_menu.add_command(label="Start Mission", command=self.start_mission)
        program_menu.add_separator()
        program_menu.add_command(label="Toggle Test Mode", command=self.alter_test_mode)
        program_menu.add_command(label="Log", command=self.log_menu)
        program_menu.add_command(label="Reset Data", command=self.reset_variables_window)
        program_menu.add_command(label="Reset Radio", command=self.reset_radio)
        program_menu.add_command(label="Change Address", command=self.change_radio_address_callback)
        program_menu.add_command(label="Manual Override", command=self.manual_override_callback)

        help_menu.add_command(label="Help Index", command=self.help_window)
        # help_menu.add_separator()
        help_menu.add_command(label="About", command=self.about_menu)  # TODO: Put this back

        # test_menu.add_command(label="Launch", command=self.test_launch)
        # test_menu.add_command(label="Abort", command=self.test_abort)
        # test_menu.add_command(label="Stability On", command=self.test_stability)

        self.name.config(menu=menu_bar)

    def make_grid(self):
        """
        Sets the grid for the window, sets the background color for cells and determines which cells will resize
        to fill the window space
        :return: None
        """
        total_rows = self.total_rows
        total_columns = 11

        my_rows = range(0, total_rows)
        my_columns = range(0, total_columns)
        control_col = range(1, 4)

        for column in my_columns:
            self.name.columnconfigure(column, weight=1)

        for row in my_rows:
            self.name.rowconfigure(row, weight=4, uniform=1)

        self.name.rowconfigure(2, weight=1, uniform=0)
        self.name.rowconfigure(5, weight=1, uniform=0)

        for col in control_col:
            self.name.columnconfigure(col, minsize=100)
            for row in range(6, 16):
                color_frame = Label(self.name, bg=self.framesBg)
                color_frame.grid(row=row, column=col, sticky=N + S + E + W)

    def start_mission(self):
        """
        Method is called when start mission in tool bar is selected.
        Starts the mission clock, and enables verify and abort buttons
        Sends test command

        :return: None
        """
        if not self.start_timer.clock_run:
            self.start_timer.start = time.time()
            self.start_timer.clock_run = True
            self.start_timer.tick()

        self.control.verify_button.state(["!disabled"])
        self.control.abort_button.state(["!disabled"])

        Comm.get_instance(self).flight()

        self.shutdown_timer = ShutdownTimer(300, self.time_out)

    def launch(self):
        """
        Method is called when GPIO Pin 11 gets a rising edge.
        Checks if that mission has not started and mission is verified
        Starts the flight clock
        Changes status to LAUNCHED
        :return: None
        """
        # Using self.timer.clock_run as a launched bool
        # Not sure if there is something more proper to use
        if not self.timer.clock_run and self.control.mission_status == Status.VERIFIED:
            c = Comm.get_instance(self)
            c.send("Ignition")

            # Kind of puts the whole thread to sleep for 5 secs
            # But I think this is what the issue is asking for
            # time.sleep(5)

            self.timer.start = time.time()
            self.timer.clock_run = True
            self.timer.delay_tick()

            self.control.mission_status = Status.LAUNCHED
            self.control.verify_button.config(text="VERIFY")
            self.control.verify_button.config(state='disabled')

            self.log(self.control.mission_status)
            self.control.change_status_display(self.control.mission_status)

    def reset_variables_window(self):
        """
        Callback window asking the user if they really want to reset the data.
        If yes, logs a reset, and resets both balloon and rocket data
        :return: None
        """
        # Creates a pop up window that asks if you are sure that you want to rest the variables.
        # If yes then all the variables are reset
        reset_window = messagebox.askokcancel("Reset All Variables?", "Are you sure you want to reset all variables?")
        if reset_window:
            self.log(Status.RESET)
            self.dataBalloon.reset_variables()
            self.dataRocket.reset_variables()

    def log(self, status):
        """
        Records the data in status.log
        :param status: reason why the data was logged
        :return: None
        """
        fo = open(self.status_log_path, "a")

        current_date = datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')
        if status == Status.ABORT:
            fo.write("-------MISSION ABORTED-------\n")
        elif status == Status.VERIFIED:
            fo.write("-------STATUS VERIFIED-------\n")
        elif status == Status.MANUAL:
            fo.write("-----MANUAL LOG INVOKED------\n")
        elif status == Status.RESET:
            fo.write("-------VARIABLES RESET-------\n")
        elif status == Status.RESTART:
            fo.write("-------PROGRAM RESTART-------\n")
        elif status == Status.NOT_VERIFIED:
            fo.write("-----STATUS NOT VERIFIED-----\n")
        elif status == Status.LAUNCHED:
            fo.write("-------LAUNCHED-------\n")
        elif status == Status.TIMEOUT:
            fo.write("-------RADIO TIME OUT-------\n")

        fo.write("DATE:" + current_date + "\n")
        fo.write("MISSION START TIMESTAMP:" + repr(self.start_timer.current_time) + "\n")
        fo.write("LAUNCH START TIMESTAMP:" + repr(self.timer.current_time) + "\n")
        fo.write("*****************************\n")
        fo.write("----------LOGS START---------\n")
        fo.write("----------BALLOON DATA-------\n")
        fo.write("Longitude = " + repr(self.dataBalloon.longitude_data) + "\n")
        fo.write("Latitude = " + repr(self.dataBalloon.latitude_data) + "\n")
        fo.write("Gyro(X) = " + repr(self.dataBalloon.gyroX_data) + "\n")
        fo.write("Gyro(Y) = " + repr(self.dataBalloon.gyroY_data) + "\n")
        fo.write("Gyro(Z) = " + repr(self.dataBalloon.gyroZ_data) + "\n")
        fo.write("Temperature = " + repr(self.dataBalloon.temperature_data) + "\n")
        fo.write("Acceleration(X) = " + repr(self.dataBalloon.accelX_data) + "\n")
        fo.write("Acceleration(Y) = " + repr(self.dataBalloon.accelY_data) + "\n")
        fo.write("Acceleration(Z) = " + repr(self.dataBalloon.accelZ_data) + "\n")
        fo.write("----------LOGS END-----------\n")
        fo.write("-----------------------------\n\n")
        fo.close()

    def log_menu(self):
        """
        Logs data manually and a Pop up window informing user that data has been logged manually
        :return: None
        """
        log_window = Toplevel(self.name)
        log_window.title("Manual Log")
        logged_label = Label(log_window, text="The current variables have been logged in 'logs/status.log'")
        logged_label.pack()
        button = Button(log_window, text="Close", command=lambda: log_window.destroy())
        button.pack()
        self.log(Status.MANUAL)

    def about_menu(self):
        """
        Pop up window with about information
        :return: None
        """

        about_text = "Ground Station Graphical User Interface Version 0.3-alpha\n\n" \
                     "Author: Ken Sodetz, Matt Drozt, Jay Rixie, Emanuel Pituch, Connor Todd\n" \
                     "Since: 11/27/2018\n\n" \
                     "Created for Purdue Orbital Electrical and Software Sub team\n\n" \
                     "Parses and displays data from the a Raspberry Pi 3 to verbosely display all\n" \
                     "pertinent system data"

        about_window = Toplevel(self.name)
        about_window.title("About")
        about_window.resizable(width=False, height=False)
        text = Text(about_window)
        text.insert(INSERT, about_text)
        text.config(state=DISABLED)
        text.pack()
        self.name.img = img = PhotoImage(file=os.path.join(self.image_folder_path, "orbital-logo-reduced.gif"))
        logo = Label(about_window, image=img)
        logo.place(x=0, y=200)
        button = Button(about_window, text="Close", command=lambda: about_window.destroy())
        button.pack()

    def help_window(self):
        """
        Opens a window with a single button to close it. Used as a place holder for help index.
        Needs to be fleshed out or gotten rid of
        :return: None
        """
        file_window = Toplevel(self.name)
        button = Button(file_window, text="Close", command=lambda: file_window.destroy())
        button.pack()

    def restart_program(self):
        """
        Closes and restarts the program
        :return: None
        """
        python = sys.executable
        GPIO.output(self.gui_switch, GPIO.LOW)
        GPIO.cleanup()
        self.log(Status.RESTART)
        os.execl(python, python, *sys.argv)

    def alter_test_mode(self):

        # TODO use above mode defined in CommunicationDriver.py
        self.test_mode = not self.test_mode

        self.init_graph_stuff()
        self.dataBalloon.reset_variables()
        self.control.reset_status()
        self.timer.reset()
        self.start_timer.reset()
        self.packets_sent.reset()
        self.packets_received.reset()
        self.calc_received_percentage()
        c = Comm.get_instance(self)
        c.reset_counters()

        for check in self.quality_checks:
            check.reset_quality()

        if self.test_mode:
            self.name.rowconfigure(19, weight=2)
            self.warningLabel.grid(row=19, column=0, columnspan=11, sticky=N + S + E + W)

        else:
            self.name.rowconfigure(19, weight=2)
            self.warningLabel.grid_forget()

        if c.get_mode() == Mode.STANDBY:
            c.testing()

        elif c.get_mode() == Mode.TESTING:
            c.standby()

        else:
            print("\n*** CANNOT ENTER TEST MODE DURING FLIGHT ***")

    def is_test_mode(self):
        try:
            c = Comm.get_instance(self)
            return c.get_mode() == Mode.TESTING
        except Exception as e:
            print("Test Mode Error")
            print(e)

    def manual_override_callback(self):
        random_int = ""
        for i in range(6):
            random_int = random_int + random.SystemRandom().choice(string.digits)

        s = simpledialog.askstring("DANGER: Manual Override",
                                   "Please note that manual overrides are dangerous and should only be used in "
                                   + "a worst case scenario.\nPlease check with the launch director before proceeding."
                                   + "\n\n"
                                   + "To override please enter the following number: \n\n"
                                   + random_int)
        if s == random_int:
            self.launch()
            messagebox.showinfo("SUCCESS: Preforming Override", "Manual Override was Successful")
        elif s is not None:
            messagebox.showerror("ERROR: Bad Input", "Strings did not match.\nStopping Override.")
        else:
            messagebox.showerror("ERROR: Conditions Not Met", "Conditions not met for launch. Cancelling Override")

    def change_radio_address_callback(self):
        try:
            c = Comm.get_instance(self)
            a = simpledialog.askstring("Change Radio Address",
                                       "Type a hex number (1 - 9, A - F) for the radio address of the recieving radio" +
                                       "\n\n" + "The current address is: " + str(c.get_remote_node_address()))

            if a is None:
                return

            # TODO: Probably a better way to check if it is hex
            is_hex = True
            hex_char_set = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', 'A', 'B', 'C', 'D', 'E', 'F']
            for char in a:
                if char not in hex_char_set:
                    is_hex = False

            if len(a) != 16 or not is_hex:
                messagebox.showerror("ERROR: Invalid Address", "The provided hex number was invalid\n\n" +
                                     "Reverting to initial address")
            else:
                c.set_remote_node_address(a)
        except Exception as e:
            messagebox.showerror("ERROR: Something went wrong", "Something went wrong\n\nNot Changing the Address.")
            print(e)

    def verify_message_callback(self):
        """
        Call back for verifying and un-verifying the mission. Changes mission status and buttons as necessary
        :return: None
        """
        if self.control.mission_status == Status.NOT_VERIFIED:
            verify_response = messagebox.askyesno("Verify Mission?", "Do you want to verify the mission")
            if verify_response:
                self.control.mission_status = Status.VERIFIED
                self.control.change_status_display(self.control.mission_status)
                self.log(self.control.mission_status)
                GPIO.output(self.gui_switch, GPIO.HIGH)
                # self.timer.start = time.time()
                # self.timer.clock_run = True
                # self.timer.tick()
                self.control.verify_button.config(text="UNVERIFY")

        elif self.control.mission_status == Status.VERIFIED:
            verify_response = messagebox.askyesno("Unverify Mission?", "Do you want to unverify the mission")
            if verify_response:
                self.control.mission_status = Status.NOT_VERIFIED
                self.control.change_status_display(self.control.mission_status)
                self.log(self.control.mission_status)
                # self.timer.clock_run = False
                self.control.verify_button.config(text="VERIFY")

        elif self.control.mission_status == Status.ABORT:
            verify_response = messagebox.askyesno("Verify Mission?", "Do you want to verify the mission")
            if verify_response:
                self.control.mission_status = Status.VERIFIED
                self.control.change_status_display(self.control.mission_status)
                self.log(self.control.mission_status)
                # self.timer.start = time.time()
                # self.timer.clock_run = True
                # self.timer.tick()
                self.control.verify_button.config(text="UNVERIFY")

    def stability_message_callback(self):
        """
        Makes sure user wants to turn on/off stabilization
        :return: None
        """
        if self.stability:
            if messagebox.askyesno("Turn off Stabilization", "Do you want to turn off stabilization"):

                try:
                    c = Comm.get_instance(self)
                    if c.send("Stabilization off"):
                        self.stability_button.config(text="Turn On Stabilization")
                        self.stability = not self.stability
                        self.packets_sent.set_count(c.get_packets_sent())
                        self.packets_received.set_count(c.get_packets_received())
                        self.calc_received_percentage()
                    else:
                        self.quality_checks[4].set_quality(0)
                        messagebox.showerror("ERROR: Command Not Sent", "Command Not Sent")
                        c.packets_sent -= 1

                except Exception as e:
                    print("Stabilization Error")
                    print(e)

        else:
            if messagebox.askyesno("Turn on Stabilization", "Do you want to turn on stabilization"):

                try:
                    c = Comm.get_instance(self)
                    if c.send("Stabilization on"):
                        self.stability_button.config(text="Turn Off Stabilization")
                        self.stability = not self.stability
                        self.packets_sent.set_count(c.get_packets_sent())
                        self.packets_received.set_count(c.get_packets_received())
                        self.calc_received_percentage()
                    else:
                        self.quality_checks[4].set_quality(0)
                        messagebox.showerror("ERROR: Command Not Sent", "Command Not Sent")
                        c.packets_sent -= 1

                except Exception as e:
                    print("Stabilization Error")
                    print(e)

    def abort_message_callback(self):
        """
        Callback if the user decides to abort the mission
        :return: None
        """
        abort_response = messagebox.askyesno("Abort Mission?", "Do you really want to abort the mission?")
        if abort_response:
            self.select_qdm()

    def test_launch(self):
        try:
            c = Comm.get_instance(self)
            m = c.get_mode()

            c.testing()
            c.send("launch")
            self.packets_sent.set_count(c.get_packets_sent())
            self.packets_received.set_count(c.get_packets_received())
            self.calc_received_percentage()
            c.set_mode(m)
        except Exception as e:
            print("Test Launch Error")
            print(e)

    def test_abort(self):
        try:
            c = Comm.get_instance(self)
            m = c.get_mode()

            c.testing()
            c.send("abort")
            self.packets_sent.set_count(c.get_packets_sent())
            self.packets_received.set_count(c.get_packets_received())
            self.calc_received_percentage()
            c.set_mode(m)
        except Exception as e:
            print("Test Abort Error")
            print(e)

    def test_stability(self):
        try:
            c = Comm.get_instance(self)
            m = c.get_mode()

            c.testing()
            c.send("stability")
            self.packets_sent.set_count(c.get_packets_sent())
            self.packets_received.set_count(c.get_packets_received())
            self.calc_received_percentage()
            c.set_mode(m)
        except Exception as e:
            print("Test Stability Error")
            print(e)

    def select_cdm(self):
        # TODO: Are we using CDM at all??? Get rid of?
        c = Comm.get_instance(self)
        c.flight()
        c.send("cdm")
        self.packets_sent.set_count(c.get_packets_sent())
        self.packets_received.set_count(c.get_packets_received())
        self.calc_received_percentage()

        self.abort_method = "CDM"
        self.control.mission_status = Status.ABORT
        self.log(self.control.mission_status)
        self.timer.clock_run = False
        self.control.verify_button.config(text="VERIFY")
        self.control.change_status_display(self.control.mission_status)
        GPIO.output(self.gui_switch, GPIO.LOW)

    def select_qdm(self):
        """
        Method called sending a qdm command and logging the incident
        :return: None
        """

        print("QDM")
        # TODO Make Comms Global
        try:
            c = Comm.get_instance(self)
            c.flight()
            c.send("qdm")
            self.packets_sent.set_count(c.get_packets_sent())
            self.packets_received.set_count(c.get_packets_received())
            self.calc_received_percentage()
        except Exception as e:
            print(e)

        self.abort_method = "QDM"
        self.control.mission_status = Status.ABORT
        # self.timer.clock_run = False
        self.control.verify_button.config(text="VERIFY")
        self.control.verify_button.config(state='disabled')
        self.log(self.control.mission_status)
        self.control.change_status_display(self.control.mission_status)
        GPIO.output(self.gui_switch, GPIO.LOW)

    def time_out(self):
        # TODO: Needs a lot of testing
        self.control.mission_status = Status.TIMEOUT
        self.log(self.control.mission_status)
        self.control.change_status_display(self.control.mission_status)
        print("Mission Timeout")

    def process_incoming(self):
        """
        Updates data
        :return: None
        """
        # Process data in queue
        while self.queue.qsize():
            self.quality_checks[4].set_quality(1)
            try:
                if self.shutdown_timer is not None:
                    self.shutdown_timer.stop()
                self.shutdown_timer = ShutdownTimer(300, self.time_out)
                data_json = self.queue.get()
                print(data_json)

                origin = data_json["origin"]

                if origin == "balloon":
                    data = self.dataBalloon
                elif origin == "status":
                    self.quality_checks[0].set_quality(data_json["QDM"])
                    self.quality_checks[1].set_quality(data_json["Ignition"])
                    self.quality_checks[2].set_quality(data_json["Stabilization"])
                    self.quality_checks[4].set_quality(data_json["PlatRadio"])

                    return
                else:
                    print("JSON ORIGIN INCORRECT")
                    return

                gps_json = data_json["GPS"]
                data.longitude_data = gps_json["long"]
                data.latitude_data = gps_json["lat"]
                data.altitude_data = gps_json["alt"]

                gyro_json = data_json["gyro"]
                data.gyroX_data = gyro_json["x"]
                data.gyroY_data = gyro_json["y"]
                data.gyroZ_data = gyro_json["z"]

                data.temperature_data = data_json["temp"]

                acc_json = data_json["acc"]
                data.accelX_data = acc_json["x"]
                data.accelY_data = acc_json["y"]
                data.accelZ_data = acc_json["z"]

                data.display_variables()

                # insert it into the queues
                self.altitudeQ.get()
                self.altitudeQ.put(data.altitude_data)

                if self.altitude_graph is not None:
                    self.altitude_graph.update_altitude(self.altitudeQ)

                elif origin == "balloon":
                    self.balloon_acc_xQ.get()
                    self.balloon_acc_yQ.get()
                    self.balloon_acc_zQ.get()
                    self.balloon_gyro_xQ.get()
                    self.balloon_gyro_yQ.get()
                    self.balloon_gyro_zQ.get()
                    self.balloon_acc_xQ.put(data.accelX_data)
                    self.balloon_acc_yQ.put(data.accelY_data)
                    self.balloon_acc_zQ.put(data.accelZ_data)
                    self.balloon_gyro_xQ.put(data.gyroX_data)
                    self.balloon_gyro_yQ.put(data.gyroY_data)
                    self.balloon_gyro_zQ.put(data.gyroZ_data)
                    if self.acc_gyro_graphs is not None:
                        self.acc_gyro_graphs.update_balloon_acc(self.balloon_acc_xQ, self.balloon_acc_yQ,
                                                                self.balloon_acc_zQ)
                        self.acc_gyro_graphs.update_balloon_gyro(self.balloon_gyro_xQ, self.balloon_gyro_yQ,
                                                                 self.balloon_gyro_zQ)

                        # Set the data variables equal to the corresponding json entries
                        # self.data.temperature_data = data_json["temperature"]
                        # self.data.pressure_data = data_json["pressure"]
                        # self.data.humidity_data = data_json["humidity"]
                        # self.data.altitude_data = data_json["altitude"]
                        # self.data.direction_data = data_json["direction"]
                        # self.data.acceleration_data = data_json["acceleration"]
                        # self.data.velocity_data = data_json["velocity"]
                        # self.data.user_angle_data = data_json["user_angle"]
                        # Reload variables

            except queue.Empty:
                pass

    def close(self):
        """
        Closes the window
        :return: None
        """
        self.running = 0

    def open_altitude_graph(self):
        """
        Opens and instance of the altitude graph
        :return:None
        """
        self.altitude_graph = AltitudeGraph()
        self.altitude_graph.update_altitude(self.altitudeQ)

    def open_acc_gyro_graphs(self):
        """
        Opens an instance of the acceleration and gyro graphs
        :return: None
        """
        self.acc_gyro_graphs = AccelerometerGyroGraphs()

        self.acc_gyro_graphs.update_balloon_acc(self.balloon_acc_xQ, self.balloon_acc_yQ, self.balloon_acc_zQ)
        self.acc_gyro_graphs.update_balloon_gyro(self.balloon_gyro_xQ, self.balloon_gyro_yQ, self.balloon_gyro_zQ)

    def reset_radio(self):
        """
        Resets Radio
        :return: None
        """
        self.radio.reset_radio()

    def calc_received_percentage(self):
        """
        Calculates the received rate of the packets using the counter numbers
        :return: None
        """
        if self.packets_sent.get_count() == 0:
            self.received_percentage.set("NaN")
            return

        self.received_percentage.set(round(self.packets_received.get_count() * 100 / self.packets_sent.get_count(), 2))
