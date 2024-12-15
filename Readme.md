# Vex V5 Brain External Communications

This project is a side mission for a University project. The Main project is to create a robot that can compete in the vex u over under compertision. As part of this project we found it nessisary to parse informarion from another control unit in to the Vex V5 Brain. For example an Arduino Uno or a raspberry pi collecting information from a sensor, then sending the information to the V5 brain.

# Investigation

There are three physical ways to get informatiojn into the V5 brain:

1. The usb port
2. The smart ports
3. The Three wire ports

Several hours was spend looking at forums for the ways to parse information into the usb port and the smart ports. No method found could be reproducted in the class room. It seams the python code for the v5 brain does not allow for low level access to either the USB or the Smart ports.

### The Three wire port.

#### Analogue Read

A quick investigation was carried out into whether the 5v Brain can accuratly read a PWM sing as a voltage.

The results indicated that the v5 brain could not reliably read PWM signals as voltages. Looking back the addition of a capasitor might have made the readings more stable.

[analogue read.py](V5_Brain_Code\XX_analogue.py)

#### PWM

During the in person week, an investigation was carried out to get some kind of information from an arduino to the V5 brain. The initial investigation was to use a communication proticol simlar to PWM, where the information is carried in the time a pin is held high. ie pin a is 5v for 200 ms there for the value sent is 200.

for more information see [PWM code.py](V5_Brain_Code\XX_PWM_investigation.py)

The arduino used to send the information was flashed with the basic 'blink' code and the delay parameter was changed to change the values being sent

The code worked well, however the following issues were discovered.

1. The 5v brain seams to hold time information to the nearest 5ms with a repeatability error of arround 5ms.
2. The pulses of the system regulalery had and error of about 5ms. This could be cause by the arduino or the time it takes for the interupts to be acctioned.

To send data accruratly it whold be advised to drop the first decimal, and only send data in multiples of 10ms.

This means values in the range of 100, would take a second to be sent.

# Development of a new communications protocol

The limitations of the V5 hardware are the timing, however the interupts seam to work flawlessly.

#### Problems from bad timing

A protocol where the sender changes the data signal at know interval, and the read polls the data at the same interval might result in the reader missing a data point. This could be reduced by increasing the time between readings, but this will affect the data rate.

#### Ideas for using the Interupts.

An interupt can be made when a pin, lets call it a clock pin is pulled high. The interupt can cause the 5v brain to carry out some action, lets say read the value of the data pin.

## I2c

The idea for using a protocol simlar to i2c was considered. Where the clock pin syncs the timing of the v5 brain with the sender. ie When the clock pin is pulled high the v5 Brain reads the data pin.

This would require the 5v brain to make some sort of judgement on when the data transmission has finished and when to decode the payload. This could either be done on every falling slope interup the clock pin the data is analyised or with regular polling.

Checking the lenght of the data on every clock pulse is a waste of processing power. At this point the idea of using a protocol simlar to SPI was considered.

## SPI

The idea for this porticol is that the data is read by the v5 brain then the clock pin is pulled high, however the addtion of a chip select pin is used.

The chipselect pin is pulled high the entirety of the the data transmittion. When the chip select pin is pulled low the 5v Brain knows to analylise the data.

The follwing interupts can be made to read to transmit data from the sender to the v5 brain.

1. Clock_pin when pulled high the data pin is read
2. Chip select when pulled high the buffer is cleared
3. chip select when pulled low, the data in the buffer is analyised.

# Objectives

- [x] fast reliable data tranfer between Vex 5v brain and raspberry pi or arduino
- [x] a means to reject error in transmition
- [x] wrap the code in some wrapper so that it is easy to use
- [x] write the code in such a way, that it can be tested on micropython
- [ ] Arduino
- [x] Micropython
- [ ] Raspberry Pi
- [ ] VexV5 Brain