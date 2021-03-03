from sense_hat import SenseHat
import shlex


class Sense:
    def __init__(self, c8y,serviceRestart):
        self.sense = SenseHat()
        self.c8y = c8y
        self.reset = 0
        self.resetMax = 3
        self.serviceRestart = serviceRestart

    def send(self):
        self.c8y.logger.debug("Sensehat Sending called: ")
        self.sendTemperature()
        self.sendHumidity()
        self.sendPressure()
        self.sendAcceleration()
        self.sendGyroscope()
        self.listenForJoystick()

    def sendTemperature(self):
        tempString = "211," + str(self.sense.get_temperature())
        self.c8y.logger.debug("Sending Temperature  measurement: " + tempString)
        self.c8y.publish("s/us", tempString)


    def sendHumidity(self):
        tempString = "992,," + str(self.sense.get_humidity())
        self.c8y.logger.debug("Sending Humidity  measurement: " + tempString)
        self.c8y.publish("s/uc/pi", tempString)


    def sendPressure(self):
        tempString = "994,," + str(self.sense.get_pressure())
        self.c8y.logger.debug("Sending Pressure  measurement: " + tempString)
        self.c8y.publish("s/uc/pi", tempString)


    def sendAcceleration(self):
        acceleration = self.sense.get_accelerometer_raw()
        x = acceleration['x']
        y = acceleration['y']
        z = acceleration['z']
        accString = "991,," + str(x) + "," + str(y) + "," + str(z)
        self.c8y.logger.debug("Sending Acceleration measurement: " + accString)
        self.c8y.publish("s/uc/pi", accString)


    def sendGyroscope(self):
        o = self.sense.get_orientation()
        pitch = o["pitch"]
        roll = o["roll"]
        yaw = o["yaw"]
        gyString = "993,," + str(pitch) + "," + str(roll) + "," + str(yaw)
        self.c8y.logger.debug("Sending Gyroscope measurement: " + gyString)
        self.c8y.publish("s/uc/pi", gyString)

    def displayMessage(self,message):
        messageArray =  shlex.shlex(message, posix=True)
        messageArray.whitespace =',' 
        messageArray.whitespace_split =True 
        msg = str(list(messageArray)[-1])
        self.c8y.logger.info("Display message: " + msg )
        self.sense.show_message(msg)
        self.sense.clear

    def listenForJoystick(self):
        self.c8y.logger.info("listenForJoystick")
        for event in self.sense.stick.get_events():
            text = "The joystick was {} {}".format(event.action, event.direction)
            self.c8y.logger.debug(text)
            self.c8y.publish("s/uc/pi", "997,{},,{},{}".format(text,event.action, event.direction))
            if event.action == 'pressed' and event.direction == 'middle':
                self.reset
                self.resetMax
                self.reset += 1
                if self.reset >= self.resetMax:
                    self.c8y.logger.info('Resetting c8y.properties initializing re-register device....')
                    self.c8y.reset()
                    self.serviceRestart('Joystick reset')