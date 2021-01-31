import os
import sys
import time
import argparse
import json
import subprocess

import evdev
from evdev import ecodes as e

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
            if mname and (time.time()-toggle_time)>=toggle_delay:
                toggle_time = time.time()
                mtype, minfo = get_macro_info(mname, layer)
                if mtype == "cmd":
                    print("Executing macro: ", mname, " Command:", minfo)
                    subprocess.Popen(minfo)
                elif mtype == "key":
                    print("Executing macro: ", mname, " Key:", minfo)
                    ui.write(e.EV_KEY, minfo[0], 1)
                    ui.write(e.EV_KEY, minfo[0], 0)
                    ui.write(e.EV_SYN, 0, 0)
                elif mtype == "keylist":
                    print("Executing macro: ", mname, " keylist:", minfo)
                    for keycode in minfo:
                        ui.write(e.EV_KEY, keycode, 1)
                        ui.write(e.EV_KEY, keycode, 0)
                    ui.write(e.EV_SYN, 0, 0)
                elif mtype == "keycomb":
                    for keycode in minfo:
                        # for keycode in keyset:
                        if keycode>0:
                            ui.write(e.EV_KEY, keycode, 1) #down
                        else:
                            ui.write(e.EV_KEY, -keycode, 0) #up
                    ui.write(e.EV_SYN, 0, 0)
                        # time.sleep(0.01)

            if not only_defined and not mname:
                ui.write(ev.type, ev.code, ev.value)
            print(ev)
    except OSError:
        print("device disconnected!")

parser = argparse.ArgumentParser(description="""UInput Macropad""")
parser.add_argument('config', help="Path to config file")

args = parser.parse_args()


if args.config:
    print("Loading config from:", args.config)
    # try:
    f = open(args.config, 'r')
    data = json.loads(f.read())
    dev_name = data.get("dev_name")
    if data.get("full_grab") is not None:
        full_grab = data.get("full_grab")
    else:
        full_grab = True
    if data.get("only_defined") is not None:
        only_defined = data.get("only_defined")
    else:
        only_defined = True
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

            
    print("Macro list by layer:", macros)
    print("Layer swap hotkey list: ",layer_info)

    # except:
        # sys.exit("Error loading config files")

ui = evdev.UInput(name="Macropad Output")

time.sleep(1)

while True:
    devices = get_devices()
    dev = grab_device(devices, dev_name)
    if dev is not None:
        print("GRABBING FOR REMAPPING: "+str(dev))
        if full_grab: dev.grab()
        event_loop(dev, layer_info, macros)
    print("Device probably was disconnected")
    time.sleep(5)