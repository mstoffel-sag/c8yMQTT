# SmartRest Templates
id = 's/ut/pi'
templates = '''10,991,POST,MEASUREMENT,false,c8y_Acceleration,,c8y_Acceleration.accelerationX.value,NUMBER,,c8y_Acceleration.accelerationY.value,NUMBER,,c8y_Acceleration.accelerationZ.value,NUMBER,
10,992,POST,MEASUREMENT,false,c8y_HumidityMeasurement,,c8y_HumidityMeasurement.h.value,NUMBER,
10,993,POST,MEASUREMENT,false,c8y_GyroscopeMeasurement,,c8y_GyroscopeMeasurement.pitch.value,NUMBER,,c8y_GyroscopeMeasurement.roll.value,NUMBER,,c8y_GyroscopeMeasurement.yaw.value,NUMBER,
10,994,POST,MEASUREMENT,false,c8y_PressureMeasurement,,c8y_Pressure.hpa.value,NUMBER,
10,995,POST,MEASUREMENT,false,CPULoad,,CPULoad.L.value,NUMBER,,CPULoad.L.unit,STRING,%
10,996,POST,MEASUREMENT,false,MemoryUsage,,Memory.total.value,INTEGER,,Memory.total.unit,STRING,MB,Memory.available.value,INTEGER,,Memory.available.unit,STRING,MB,Memory.swap.value,INTEGER,,Memory.swap.unit,STRING,MB
10,997,POST,EVENT,false,c8y_Joystick,,,action,STRING,,direction,STRING,
11,1001,c8y_Message,c8y_Message,text,
11,520,,c8y_SendConfiguration,description,status,
11,1003,,c8y_RemoteAccessConnect,c8y_RemoteAccessConnect.hostname,c8y_RemoteAccessConnect.port,c8y_RemoteAccessConnect.connectionKey,'''

