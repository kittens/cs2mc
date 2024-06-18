## Install libs
```
pip install winrt.windows.media.control winrt.windows.foundation pycaw
```
## Config
1. Open Steam
2. Right click CS2
3. Press Properties
4. Press Installed Files
5. Press Browse
6. Open game > csgo > cfg
7. Place the given .cfg file there
## Use
1. Open main.py and edit the Vol as you like
2. Edit the logging too...if you want
3. The program will start playing music, if nothing is currently playing, to disable make self.allow_auto_play False
4. Edit the Fade duration (Music will slowly go silent)
5. If the Program can't match the Volume source with the playing Application, you need to add a Alias for the .exe....Program will remind you tho
   - Only needed if you really want a Fade, start stopping should work
   - Works with Spotify and Brave on default, Firefox seems to not work
## GG! Issues & PRs are very welcome..
