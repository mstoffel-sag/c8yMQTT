from sense_hat import SenseHat


class Sense:
    def __init__(self, c8y):
        self.sense = SenseHat()
        self.c8y = c8y

    def send(self):
        self.c8y.logger.debug("Sending called: ")
        self.sendTemperature()
        self.sendHumidity()
        self.sendPressure()
        self.sendAcceleration()
        self.sendGyroscope()

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