#!/usr/bin/env python3

## Copyright (C) 2020 David Miguel Susano Pinto <carandraug@gmail.com>
## Copyright (C) 2020 Julio Mateos Langerak <julio.mateos-langerak@igh.cnrs.fr>
## Copyright (C) 2020 Mick Phillips <mick.phillips@gmail.com>
##
## Adapted by Benedict Diederich
##
## This file is part of Microscope.
##
## Microscope is free software: you can redistribute it and/or modify
## it under the terms of the GNU General Public License as published by
## the Free Software Foundation, either version 3 of the License, or
## (at your option) any later version.
##
## Microscope is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with Microscope.  If not, see <http://www.gnu.org/licenses/>.


import logging

import serial
import time

import microscope
import microscope.abc

_logger = logging.getLogger(__name__)


'''
All commands accepted by the ESP32:
const char *CMD_DRVX =    "DRVX";
const char *CMD_DRVY =   "DRVX";
const char *CMD_DRVZ =   "DRVZ";
const char *CMD_LENS1X =  "LENS1X";
const char *CMD_LENS1Z =  "LENS1Z";
const char *CMD_LENS2X =  "LENS2X";
const char *CMD_LENS2Z =  "LENS2Z";
const char *CMD_LAS1 =    "LAS1";
const char *CMD_LAS2 =    "LAS2";
const char *CMD_LED1 =    "LED1";
const char *CMD_LX_SOFI =  "LX_SOFI";
const char *CMD_LZ_SOFI =  "LZ_SOFI";
const char *CMD_LX_SOFI_A =  "LX_SOFI_A";
const char *CMD_LZ_SOFI_A =  "LZ_SOFI_A";
'''

class ESPLaser(microscope.abc.SerialDeviceMixin, microscope.abc.LightSource):
    delim_strt = "*"
    delim_stop = "#"
    delim_cmds = ";"
    delim_inst = "+"

    def __init__(self, com, baud=115200, timeout=0.5, connection=None, maxpower=100, pwmresolution=2**10, cmdprefix="LASERRED", **kwargs) -> None:
        super().__init__(**kwargs)
        if connection is None:
            self.connection = serial.Serial(
            port=com,
            baudrate=baud,
            timeout=timeout,
            stopbits=serial.STOPBITS_ONE,
            bytesize=serial.EIGHTBITS,
            parity=serial.PARITY_NONE,
        )
        # Alternatively use an already established serial connection
        # e.g. if laser, lens and led are connected to one µControler
        self.connection = connection
        # Start a logger.
        self._max_power_mw = float(maxpower)
        self._cmdprefix = cmdprefix
        self.outBuffer = ""

    def isEmpty(self, byte_list):
        if (byte_list):
            cutoff = len(self.delim_strt) + len(self.delim_stop)
            byte_list = byte_list[cutoff:]
            return (byte_list.count(255) == len(byte_list))
        return False

    def sendEvent(self, value):
        """Package and Send command"""
        try:
            self.outBuffer = self.delim_strt + str(value) + self.delim_stop
            print("Printing Buffer: "+self.outBuffer)
            self.outBuffer = [ord(x) for x in self.outBuffer]
            self._write(self.outBuffer)
            time.sleep(.001)
            self.outBuffer = "" # reset
        except Exception as e:
            print("Unknown error {0} occured on send to address {1}".format(
                e, hex(self.address)))
        return

    def extractCommand(self, args):
        """Decode received Command"""
        cmd = ""
        delim = self.delim_inst
        for i, arg in enumerate(args):
            if type(arg) == list:
                sep = [str(x) for x in arg]
                cmd += delim.join(sep)
            else:
                cmd += str(arg)
            cmd += delim

        return cmd[:-1]

    def send(self, *args):
        cmd = self.extractCommand(args)
        print("Sending:   {0}".format(cmd))
        _logger.info("Sending:   {0}".format(cmd))
        self.sendEvent(cmd)

    def request(self):
        ans = self.requestEvent()
        if ans and (ans != "BUSY"):
            print("Receiving: {0}".format(ans))
            return ans

    def sendCommand(self, *args):
        """Send and receive command."""
        self.send(*args)
        time.sleep(0.0025)
        return self.request()

    def _write(self, command):
        """Send a command."""
        response = self.connection.write(command)
        return response

    def _readline(self):
        """Read a line from connection without leading and trailing whitespace.
        We override from SerialDeviceMixin
        """
        response = self.connection.readline().strip()
        return response

    def _flush_handshake(self):
        self.connection.readline()

    @microscope.abc.SerialDeviceMixin.lock_comms
    def get_status(self):
        result = []
        stat_cmd = "STATUS"
        result = self.send(stat_cmd, int(0))
        print("STATUS: "+result)
        return result

    @microscope.abc.SerialDeviceMixin.lock_comms
    def enable(self):
        """Turn the laser ON. Return True if we succeeded, False otherwise."""
        _logger.info("Turning laser ON.")
        return True

    def _do_shutdown(self) -> None:
        self.disable()
        # We set the power to a safe level
        self._set_power_mw(0)

    def initialize(self):
        # self.flush_buffer()
        print("Initializiation - Nothing to do here")

    @microscope.abc.SerialDeviceMixin.lock_comms
    def disable(self):
        """Turn the laser OFF. Return True if we succeeded, False otherwise."""
        _logger.info("Turning laser OFF.")
        # Turning LASER OFF
        self._set_power_mw(0)
        return True

    @microscope.abc.SerialDeviceMixin.lock_comms
    def is_alive(self):
        print("Not yet iplemented...")
        '''
        self._write(b"*IDN?")
        reply = self._readline()
        # 'Coherent, Inc-<model name>-<firmware version>-<firmware date>'
        return reply.startswith(b"Coherent, Inc-")
        '''
        return True

    @microscope.abc.SerialDeviceMixin.lock_comms
    def get_is_on(self):
        """Return True if the laser is currently able to produce light."""
        print("Not yet iplemented...")
        '''
        self._write(b"SOURce:AM:STATe?")
        response = self._readline()
        _logger.info("Are we on? [%s]", response.decode())
        return response == b"ON"
        '''
        return True

    @microscope.abc.SerialDeviceMixin.lock_comms
    def _get_power_mw(self):
        print("Not yet iplemented...")
        '''
        if not self.get_is_on():
            return 0.0
        self._write(b"SOURce:POWer:LEVel?")
        response = self._readline()
        return float(response.decode())
        '''
        return self._max_power_mw

    @microscope.abc.SerialDeviceMixin.lock_comms
    def _set_power_mw(self, mw):
        power_w = mw
        self.send(self._cmdprefix, int(power_w))
        _logger.info("Setting laser power to %.7sW", power_w)
        self._flush_handshake()

    def _do_set_power(self, power: float) -> None:
        self._set_power_mw(power * self._max_power_mw)

    def _do_get_power(self) -> float:
        return self._get_power_mw() / self._max_power_mw
