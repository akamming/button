# button
Power Button script for a rpi4b powered Arcade machine

This script expects 
- an push button connected to ground and GPIO3. (GPIO3 is selected, cause pin 5 and 6 can also be used to powerup the pi after a halt.
- 2 relays connected to gpio 2 and 4 for powering switching the marquee and tv on and off.

functionality is simple. The are 4 states. 
0: TV and Marquee on. 
1: Only TV on (Marquee switched off)
2: Only Marquee on (TV switched off)
3: TV and Marquee switched off.

Every short push on the power button brings the arcade machine to the next state (e.g. if TV and Marquee are on, and you press the button, the machine will go to state 1, switching off the Marquee)

If power saving is enabled in the script, then state 3 will also put the cpu governer in power save mode.

