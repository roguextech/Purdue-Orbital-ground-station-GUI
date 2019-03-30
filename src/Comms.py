from Mode import Mode
from communications.RadioModule import Module


class Comm:
    __instance = None

    def get_instance(self):
        if Comm.__instance is None:
            Comm()
        return Comm.__instance

    def __init__(self):
        if Comm.__instance is not None:
            raise Exception("Constructor should not be called")
        else:
            Comm.__instance = CommSingleton()


class CommSingleton:
    def __init__(self):
        self.__mode = Mode.STANDBY
        self.__radio = Module()

    def standby(self):
        self.__mode = Mode.STANDBY

    def testing(self):
        self.__mode = Mode.TESTING

    def flight(self):
        self.__mode = Mode.FLIGHT

    def send(self, command):
        if self.__mode == Mode.STANDBY:
            # discard command
            print("Standby")

        if self.__mode == Mode.TESTING:
            print(command)

        if self.__mode == Mode.FLIGHT:
            print("Flight")
            self.__radio.send("test")

            # TODO Send command
