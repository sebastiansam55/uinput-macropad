# uinput-macropad
Grabs an entire `/dev/input/event` device to be used as a "macropad". You can run commands on key press as well as rudimentary key event send support. More features are always coming!

## Installation
`pip3 install evdev`

Make sure that your user is in the `input` group:

`sudo usermod -a -G input <user>`

REBOOT.

If it is still giving you trouble I have had to `chmod 660 /dev/input` before in some of my testing. Also reboot after you do this. Always reboot.

You can also just always run the program as root. Understanding that any scripts/files run by the program will ALSO be run as root.

## Usage
Make sure you are not grabbing the main keyboard that you use for input as this can lock you with out a way to kill the program. 

Assuming you have your config file created correctly;

`python3 macropad.py config.json`

Is all that you need to run. See section below for config file format. There is an example config provided in this repo as well.



## config file format
```
{
    "macros": {
        "<layername>": [
            ["<macroname>", [<hotkeylist>], "<type>", "<typeinfo>"],
            ["<macroname>", [<hotkeylist>], "<type>", "<typeinfo>"]
        ],
        "<layername>": [
            ["<macroname>", [<hotkeylist>], "<type>", "<typeinfo>"],
            ["<macroname>", [<hotkeylist>], "<type>", "<typeinfo>"]
        ]
    },
    "layers": [
        ["<layername>":[<hotkeylist>]],
        ["<layername>":[<hotkeylist>]]
    ],
    "dev_name": "<nameofdevicetouse>",
    "only_defined": boolean,
    "full_grab": boolean
}
```

There are currently 4 different types of macros supported;
1. `cmd`
    * A [subprocess.Popen](https://docs.python.org/3/library/subprocess.html#subprocess.Popen) list of commands. These can be anything `Popen` can run so the possibilities are endless!
2. `key`
    * A single keycode to send.
    * EX: [2] -> sends a "1" via the keyboard
3. `keylist`
    * A list of keys to be sent in quick succession (not to be used for hotkeys!)
4. `keycomb`
    * a list of keys to be sent, needs to have the "up" and "down" signals for every key.
    * A keydown event is sent by the keycode being negative; a keyup event is sent for positive keycodes.
    * If you wanted to send Ctrl+A: 
        - `[29,30,-29,-30]`
        - `29` is the keycode for left ctrl, since it is positive it will be sent as a key down event.
        - `30` is the keycode for "a", since it is positive it will be sent as a key down event.
        - `-29` sends the up signal for the left ctrl key
        - `-30` sends the up signal for the "a" key.
    * This system is also how you can send capital/shifted characters:
        - `[42,30,-42,-30]` will send "A"
        - `[42,30,-30,31,-31,2,-2,-42]` sends "AS!"


If you want to find out more about what codes are sent when you can monitor your "main" keyboards output with `evtest`. In order to debug the output of your macros you can also monitor the output of the device created by this program with `evtest`.

Each layer can be configured to be swapped to with the press of a button[s]. This is controlled in the `dev_name` variable. In order to determine the name of your device you can run `evtest` with it unplugged and then with it plugged in, comparing the list to find the new device.

`full_grab` determines if the `evdev` device is "grabbed". If this is not set as true the key events generated naturally through the use of the device will also be sent. (this is not recommended unless you know what you are doing.). By default this will be set to True.

`only_defined` determines if the key events that are not bound to a macro are still sent. This means that if you had say a full size keyboard with a numpad you could macro-define all of the keypad keys and set `only_defined` to false and still have regular use of the rest of the keyboard! 

Very cool. I have it set to default to true however.


## Notes:

The program is written based on my [uinput-keyboard-mapper]() meaning it is able to survive device disconnects. 


## Too complicated?
Understandable! Checkout [AutoKey](https://github.com/autokey/autokey) for easier macro stuff on linux.

While this is considerably more complicated it offers a number of features that AutoKey does not in it's current form; AutoKey is largely based on `X11` meaning that it will not work in either `wayland` or the `TTY`. Because as you may have guessed from the name, this program is based on `uinput` meaning that it will work in both `X11`, `wayland` as well as the `TTY` console.