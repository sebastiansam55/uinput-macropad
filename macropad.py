#!/usr/bin/env python3
# -*- coding: utf-8 *-*
#
# UInput-macropad
# Version: 0.1
# Date: 20 Aug. 2023
# Copyright: 2021, 2022 sebastiansam55
# Copyright: 2023 Lurgainn
#
# LICENSE:
#
# This file is part of UInput-macropad.
#
# UInput-macropad is free software: you can redistribute it and/or modify it under the terms of the
# GNU General Public License as published by the Free Software Foundation, either
# version 3 of the License, or (at your option) any later version.
#
# UInput-macropad is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR A
# PARTICULAR PURPOSE. See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with UInput-macropad.
# If not, see <https://www.gnu.org/licenses/>. 
#

# Imports
import os
import sys
import time
import argparse
import json
import subprocess

import evdev
from evdev import ecodes as e

# Constants
PROGNAME = 'UInput Macropad'
VERSION = '0.1'
DEFAULT_CONFIG_FILE = '~/.config/uinput-macropad/config.json'

def get_devices():
    return [evdev.InputDevice(path) for path in evdev.list_devices()]

def grab_device(devices, descriptor):
    #determine if descriptor is a path or a name
    return_device = None
    if len(descriptor) <= 2: #assume that people don't have more than 99 input devices
        descriptor = "/dev/input/event"+descriptor
    if "/dev/" in descriptor: #assume function was passed a path
        for device in devices:
            if descriptor==device.path:
                device.close()
                return_device = evdev.InputDevice(device.path)
            else:
                device.close()
    else: #assume that function was passed a plain text name
        for device in devices:
            if descriptor==device.name:
                device.close()
                return_device = evdev.InputDevice(device.path)
            else:
                device.close()

    return return_device

def check_held(held_keys, key_list):
    all_held = True
    for key in key_list:
        if key not in held_keys:
            all_held=False
            break
    return all_held


def check_held_keys(held_keys, macros):
    # returns activated macro if any found
    for macro in macros:
        keylist = macro['keys']
        all_held = True
        for key in keylist:
            if key not in held_keys:
                all_held = False
                break
        if all_held:
            return macro['name']
    return None

def get_macro_info(mname, layer):
    for macro in layer:
        if macro['name']==mname:
            if(args.verbose):
                print("MACRO FOUND")
            return macro['type'], macro['info']
    return None

def switch_layer(name, macros):
    for layer in macros:
        if layer.get(name):
            return layer.get(name)
    return None


def event_loop(keybeeb, layers, macros):
    try:
        held_keys = []
        toggle_time = time.time()
        toggle_delay = 0.25
        layer = macros[0][layers[0]['name']] #grab first layer name
        print("Current layer:",layer)

        for ev in keybeeb.read_loop():
            mname = None
            layer_swap = None
            layer_swap = check_held_keys(keybeeb.active_keys(), layers)
            if layer_swap and (time.time()-toggle_time)>=toggle_delay:
                toggle_time = time.time()
                layer = switch_layer(layer_swap, macros)
                print("Layer Swap", layer)

            mname = check_held_keys(keybeeb.active_keys(), layer)
            if mname == None: # if none returned check if raw key code is present
                mname = check_held_keys([ev.code], layer)
                if mname:
                    mtype, minfo = get_macro_info(mname, layer)
                    if mtype=="button":
                        print(f"Executing button macro: {mname} Command: {minfo}")
                        if(str(ev.value) in minfo):
                            ui.write(e.EV_KEY, minfo[str(ev.value)], 1)
                            ui.write(e.EV_KEY, minfo[str(ev.value)], 0)
                            ui.write(e.EV_SYN, 0, 0)
                            continue
                    elif mtype=="dispose": 
                        print(f"Disposing of event: {mname}")
                        continue
                mname = None
            if mname and (time.time()-toggle_time)>=toggle_delay:
                toggle_time = time.time()
                mtype, minfo = get_macro_info(mname, layer)
                if mtype == "cmd":
                    print(f"Executing macro: ", mname, " Command:", minfo)
                    subprocess.Popen(minfo, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, preexec_fn = os.setpgrp)
                elif mtype == "key":
                    print("Executing macro: ", mname, " Key:", minfo)
                    ui.write(e.EV_KEY, minfo[0], 1)
                    ui.write(e.EV_KEY, minfo[0], 0)
                    ui.write(e.EV_SYN, 0, 0)
                elif mtype == "keylist":
                    print(f"Executing macro: {mname} keylist: {minfo}")
                    for keycode in minfo:
                        ui.write(e.EV_KEY, keycode, 1)
                        ui.write(e.EV_KEY, keycode, 0)
                    ui.write(e.EV_SYN, 0, 0)
                elif mtype == "keycomb":
                    for keycode in minfo:
                        # for keycode in keyset:
                        if type(keycode) is int:
                            if keycode>0:
                                ui.write(e.EV_KEY, keycode, 1) #down
                            else:
                                ui.write(e.EV_KEY, -keycode, 0) #up
                        elif type(keycode) is float: #sleep
                            ui.write(e.EV_SYN, 0, 0)
                            time.sleep(keycode)
                        elif type(keycode) is list:
                            for k in keycode:
                                ui.write(e.EV_KEY, k, 1)
                                ui.write(e.EV_KEY, k, 0)
                            ui.write(e.EV_SYN, 0, 0)


                    ui.write(e.EV_SYN, 0, 0)
                        # time.sleep(0.01)

                elif mtype == "dispose":
                    print(f"Disposing of event: {mname}")
                    continue

            if (not only_defined and not mname):
                if args.verbose:
                    print(f"Command - TYPE:{ev.type} CODE:{ev.code} VALUE:{ev.value}")
                ui.write(ev.type, ev.code, ev.value)
            #print(ev)
    except OSError:
        print("device disconnected!")

if __name__ == "__main__":
    # Create arguments parser
    parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter,\
        description = PROGNAME + "ver. " + VERSION + "\n(standard path of config file is " + DEFAULT_CONFIG_FILE + ")",\
        epilog = "Copyright: 2021, 2022 sebastiansam55\nCopyright: 2023 Lurgainn\nLicensed under the terms of the GNU General Public License version 3")
    # Set the arguments
    parser.add_argument('-f', '--file-config', help = "Path to alternative config file")
    parser.add_argument('-v', '--verbose', action = 'store_true', help = "Enable verbose logging (default = False)")
    # command line behavior wiil take priority over config file settings
    parser.add_argument('--full-grab', action = argparse.BooleanOptionalAction, help="Absorbs all signals coming from device (default = True)")
    parser.add_argument('--only-defined', action = argparse.BooleanOptionalAction, help="Determine if defined only keystrokes are sent (default = False)")
    parser.add_argument('--clone', action = argparse.BooleanOptionalAction, help = "Creates the UInput device with the capability of the device we're grabbing (default = True)")
    #TODO
    #parser.add_argument('-d', '--dev_name', help="The device name (in quotes) that you want to read/grab from")
    
    args = parser.parse_args()

    # Default path to config file
    config_file = os.path.expanduser(DEFAULT_CONFIG_FILE)
    # Set alternative path to config file
    if args.file_config is not None:
        config_file = args.file_config
    # Check if config file exists
    if os.path.isfile(config_file):
        print(f"Loading config from: {config_file}")
        if args.verbose:
            print(f"Command line args: {args}")
        # Load config file
        try:
            f = open(config_file, 'r')
            data = json.loads(f.read())
            f.close()
        except:
            print(f"Error loading config file '{config_file}'")
            sys.exit(2)
        # Get device to intercept
        dev_name = data.get("dev_name")

        # Set full_grab default value
        full_grab = True
        # Overwrite with config file if defined
        if data.get("full_grab") is not None:
            full_grab = data.get("full_grab")
        # Overwrite with argument value if existent
        if args.full_grab is not None:
            full_grab = args.full_grab
        
        # Set only_defined default value
        only_defined = False
        # Overwrite with config file if defined
        if data.get("only_defined") is not None:
            only_defined = data.get("only_defined")
        # Overwrite with argument value if existent
        if args.only_defined is not None:
            only_defined = args.only_defined
        
        # Set clone default value
        clone = True
        # Overwrite with config file if defined
        if data.get("clone") is not None:
            clone = data.get("clone")
        # Overwrite with argument value if existent
        if args.clone is not None:
            clone = args.clone

        print("Building macro list")
        layers = data["macros"]
        macros = []
        for layer in layers:
            layer_macros = []
            for macro_info in layers[layer]:
                # print(macro_info)
                macro = {"name":None, "keys":None, "type":None, "info":None}
                macro['name'] = macro_info[0]
                macro['keys'] = macro_info[1]
                macro['type'] = macro_info[2]
                macro['info'] = macro_info[3]

                layer_macros.append(macro)
            macros.append({layer:layer_macros})
            # macros.append(layer_macros)

        layer_info = []
        for layer in data['layers']:
            lay = {"name":None, "keys":None}
            lay['name'] = layer[0]
            lay['keys'] = layer[1]
            layer_info.append(lay)

        print(f"Macro list by layer: {macros}")
        print(f"Layer swap hotkey list: {layer_info}")

    else:
        print(f"Config file '{config_file}' not found!")
        sys.exit(1)


    time.sleep(1)

    while True:
        devices = get_devices()
        dev = grab_device(devices, dev_name)
        if dev is not None:
            print(f"GRABBING FOR REMAPPING: {str(dev)}")
            if clone:
                ui = evdev.UInput.from_device(dev, name="Macropad Output")
            else: #previous behavior
                ui = evdev.UInput(name="Macropad Output")
            if full_grab: dev.grab()
            event_loop(dev, layer_info, macros)
        print("Device probably was disconnected")
        time.sleep(5)