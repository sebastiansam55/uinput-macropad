# uinput-macropad
Grabs an entire `/dev/input/event` device to be used as a "macropad". You can run commands on key press as well as rudimentary key event send support. More features are always coming!

## Requirements
Python version >=3.9

## Installation
If necessary, run `pip3 install evdev`. After that copy the file `macropad.py` wherever you want and set the executable flag. If you choice a folder in your PATH, then you'll be able to launch the program as a normal command without specifying the complete path.

## Permissions
Make sure that your user is in the `input` group. If it's not already so, type the following commands:  
1. `sudo usermod -a -G input <user>` (substitute <user> with your username)  
2. Reboot.  

If it is still giving you troubles, you have to:  
1. Create e new group `uinput` with the comand `sudo groupdadd -f uinput`  
2. Add yourself to the new group with the comand `sudo gpasswd -a <user> uinput` (substitute <user> with your username)  
3. In `/etc/udev/rules.d/` create a new rule file (for example `99-uinput.rules`) and within put the row `KERNEL=="uinput", GROUP="uinput", MODE="0660"`  
4. Reboot  
 
**WARNING:** you can also just always run the program as root, but understand that any scripts/files run by the program will ALSO be run as root, and generally this is a **BIG SECURITY THREAT!**

## Usage
If you already set the executable flag and put the program's folder in PATH then you can simply type `macropad.py`, else you need to type `python3 /full/path/to/macropad.py`, where `/full/path/to/` is the full path to the folder where you put the program file.

`macropad.py -h` will show a short message help.

While creating your config file in JSON format, make particular attention if you are grabbing the main keyboard that you use for input, as this can lock you without a way to kill the program.

Assuming you have your config file created correctly;  
1. If the config file is `~/.config/uinput-macropad/config.json` then you can simply run `macropad.py`  
2. If the config file is elsewhere, then you have to run `macropad.py -c /full/path/to/<config file name>`  

## Config file format without layer's commands
There is an example config provided in this repo (`config.json`).
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
    * a list of events. There are currently 4 different events you can send depending on the data type used. 
        - If item in the list is a `int` it will be sent as an keydown or keyup signal depending on the sign. (+/- -> down/up)
        - If the item is a `float` (has a decimal point) it will be used to sleep the program for the specified amount of time. This is useful for macros that are can't be sent all at once. Generally 0.25 is usually enough for most programs.
        - If the item is a `list` the program will send the events in a similar fashion as to the `keylist` type of macro.
    * A keydown event is sent by the keycode being positive; a keyup event is sent for negative keycodes.
    * If you wanted to send Ctrl+A: 
        - `[29,30,-29,-30]`
        - `29` is the keycode for left ctrl, since it is positive it will be sent as a key down event.
        - `30` is the keycode for "a", since it is positive it will be sent as a key down event.
        - `-29` sends the up signal for the left ctrl key
        - `-30` sends the up signal for the "a" key.
    * This system is also how you can send capital/shifted characters:
        - `[42,30,-42,-30]` will send "A"
        - `[42,30,-30,31,-31,2,-2,-42]` sends "AS!"
5. `button`
    * Created quickly for use with the hscroll wheel in a mx master 3. May rename later.
        - The idea is that you can map the key code and value (1 or -1 for the hscroll wheel) for EV_REL type events (like scroll wheels and sticks)
6. `dispose`
    * Will dispose of events compelety when used in combination with `full_grab`

If you want to find out more about what codes are sent when you press keys, you can monitor your "main" keyboards output with `evtest`. In order to debug the output of your macros you can also monitor the output of the device created by this program with `evtest`.

Each layer can be configured to be swapped to with the press of a button[s]. This is controlled in the `dev_name` variable. In order to determine the name of your device you can run `evtest` with it unplugged and then with it plugged in, comparing the list to find the new device.

`full_grab` - All signals are sent to this program only. Useful for disabling keys.

Determines if the `evdev` device is "grabbed". If this is not set as true the key events generated naturally through the use of the device will also be sent. (this is not recommended unless you know what you are doing.). By default this will be set to True.

`only_defined` - Will unmapped keystrokes be sent?

Determines if the key events that are not bound to a macro are still sent. This means that if you had say a full size keyboard with a numpad you could macro-define all of the keypad keys and set `only_defined` to false and still have regular use of the rest of the keyboard!  By default this will be set to False

`clone` - Whether the created UInput device will clone the capabilities of the device you are grabbing.
May be needed if you are having issues with mouse events.  By default this will be set to True

## Config file format with layer's commands
There is an example config provided in this repo (`layers-commands.json`).
```
{
    "macros": {
        "test1": [
            ["macro1-1", [2], "cmd", ["python3", "test.py"]]
        ],
        "test2": [
            ["macro2-1", [2], "cmd", ["python3", "test2.py"]]
        ]
    },
    "layers": [
        ["test1",[59], ["zenity", "--info", "--title=\"Layer swap\"", "--text=\"Layer 'test1'\"", "--timeout=2"]],
        ["test2",[60], ["zenity", "--info", "--title=\"Layer swap\"", "--text=\"Layer 'test2'\"", "--timeout=2"]]
    ],
    "dev_name": "AT Translated Set 2 keyboard",
    "only_defined": false,
    "full_grab": true,
    "clone": false
}
```
When the program start and set the first layer and whenever you swap layer, the associated command will be executed. For example, with this config file, when you select the first layer "test1", the command `zenity --info --title"Layer swap" --text"Layer 'test1'" --timeout=2` will be executed and, if you have 'zenity' installed, for two seconds will be showed a little dialog with the text `Layer 'test1'`.  
Associated commands are not mandatory, so you can have config files with some layer with commands and other layers without any, as well all layers with commands or without any. All combinations are possible.  
All other settings are the same as explained before.  

## Keycodes
If you need to find the exact keycode that you want to use, both in a hotkey as output key, you can consult the following page:  
[input-event-codes.h](https://github.com/torvalds/linux/blob/master/include/uapi/linux/input-event-codes.h)  

## Real world usage example:
For example, to use the livereload and live preview plugins when writing readmes (including this one!). This macro is included in the config, It's recommended to spacing it in similar fashion as below, breaking it up step by step makes it much easier to understand what is or is not happening. It's better to punctuate each step with a `0.25`s wait.


The process to enable them is as follows;
| Step | Step details | json |
| :--: | :----------: | :--: |
| 1. | Open command palette (Ctrl-Shift-P) | `29, 42, 25, -29, -42, -25, 0.25,` |
| 2. | Type "livereload" | `[38,23,47,18,19,18,38,24,30,32], 0.25,` |
| 3. | Move down 5 times | `[108, 108, 108, 108, 108], 0.25,` |
| 4. | Press enter | `[28], 0.25,` |
| 5. | Move down 4 times | `[108, 108, 108, 108], 0.25,` |
| 6. | Press enter | `[28], 0.25,` |
| 7. | Reopen command palette | `29, 42, 25, -29, -42, -25, 0.25,` |
| 8. | Type "browser" | `[25, 19, 18, 47, 23, 18, 17], 0.25,` |
| 9. | Press enter | `[28], 0.25,` |
| 10. | Press enter | `[28], 0.25` |


Note the liberal usage of the sleep function. They could probably be tuned to make the macro go faster but it's preferable reliability over speed. 10 steps with a 0.25 delay is 2.5 seconds. Compared to the 10+ it takes otherwise (not to mention remembering what the names of the plugins are) it is a definite win. 

## Logitech MX Master 3 mods
There's a config file in this repo (logimxmaster3.json) that describes some remaps that can be useful. It's self explanatory if you've programmed it.
macros on layer1:
* copy - remaps the "back" button to be ctrl C via the "keycomb" functionality, basically it presses down ctrl then c and then releases in the same order. This makes a ctrl-c function that is nearly indistinguishable from genine ones.
* paste - remaps the "forward" button to send ctrl V via the "keycomb" functionality.
* hscoll - converts the side way scroll wheel to do arrow keys. The best part is that the arrow keys will essentially scroll any where the regular hscroll would but it comes with the added benefit of it passing through virtualbox and any RDP client. 
* disablehscroll - disposes of the scroll events that are normally sent.

## Notes:

The program is written based on sebastiansam55's [uinput-keyboard-mapper]() meaning it is able to survive device disconnects. 

## TODO:
Suggestions welcome!

Prebuilt configs that are general enough to have mass appeal can be added as PRs if any one is adventerous enough to do so. 

## Breaking changes
Nothing is guaranteed compatibitly wise 


## Too complicated?
Understandable! Checkout [AutoKey](https://github.com/autokey/autokey) for easier macro stuff on linux.

While this is considerably more complicated it offers a number of features that AutoKey does not in it's current form; AutoKey is largely based on `X11` meaning that it will not work in either `wayland` or the `TTY`. Because as you may have guessed from the name, this program is based on `uinput` meaning that it will work in both `X11`, `wayland` as well as the `TTY` console.