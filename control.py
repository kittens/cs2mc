import asyncio
import time
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
from winrt.windows.media.control import \
    GlobalSystemMediaTransportControlsSessionManager as MediaManager
from winrt.windows.media.control import \
    GlobalSystemMediaTransportControlsSessionPlaybackStatus as PlaybackStatus
import traceback
import math


class control:
    def __init__(self, fade_duration, log, allow_auto_play) -> None:
        self.fade_duration = fade_duration
        self.log = log
        self.allow_auto_play = allow_auto_play

        self.last_notification = None
        self.old_title = None
        self.stopped_by_us = False

        self.aliases = {
            "AyuGram.exe": ["telegram"],
            "firefox.exe": ["308046B0AF4A39CB"]

        }  # aliases incase source_app_user_model_id does not match with session.Process.name()

    def round_up_to_2_digits(self, number):
        return math.ceil(number * 100) / 100

    async def get_current_session(self):
        """Return currently playing audio session"""
        sessions = await MediaManager.request_async()
        return sessions.get_current_session()  # return sessions.get_sessions()

    def get_app_volume_control(self, app_name):
        sessions = AudioUtilities.GetAllSessions()
        for session in sessions:
            if session.Process:
                if session.Process and session.Process.name() == app_name:
                    volume = session.SimpleAudioVolume
                    return volume
                else:
                    try:
                        if any(alias.lower() in app_name.lower() for alias in self.aliases[str(session.Process.name())]):
                            volume = session.SimpleAudioVolume
                            return volume
                    except KeyError:
                        pass

        print(
            f"Couldn't match Volume Source with a application, please add a Alias for {app_name}:")
        print("- " + "\n- ".join([f"{str(x.Process.name())}, {str(x.Process.exe())}"
                                  for x in AudioUtilities.GetAllSessions() if x.Process is not None]))
        return None

    def fade_volume(self, volume_control, target_volume, duration=None):
        if duration is None:
            duration = self.fade_duration

        if target_volume > 1.0:
            target_volume = target_volume / 100.0

        current_volume = volume_control.GetMasterVolume()
        if current_volume == target_volume:
            if self.last_notification != target_volume:
                if self.log:
                    print(
                        f"Volume is already at {target_volume * 100:.0f}%! Not changing anything.")
            self.last_notification = current_volume
            return

        if duration != 0.0:
            volume_difference = self.round_up_to_2_digits(
                abs(target_volume - current_volume))
            # print("vol diff", volume_difference)
            # 100 steps per 1.0 volume difference

            per_step = 2
            steps = int(volume_difference * (100 / per_step))
            if steps == 0:
                steps = 1

            step_duration = self.round_up_to_2_digits(
                duration / steps)  # time per step
            # print("sleep per step", step_duration)
            # volume increment per step
            step = self.round_up_to_2_digits(volume_difference / steps)
            # print("1 step is", step)

            for _ in range(steps):
                if target_volume > current_volume:
                    current_volume = current_volume + step
                else:
                    current_volume = current_volume - step
                    # print("curr", current_volume, "step",
                    #   step, "target", target_volume)

                if current_volume <= 1.00 and current_volume >= 0.00:
                    volume_control.SetMasterVolume(current_volume, None)
                    time.sleep(step_duration)

        volume_control.SetMasterVolume(target_volume, None)  # failsafe

    def adjust_volume(self, volume, fade):
        try:
            asyncio.run(self.control_music(volume, fade))
            return True
        except Exception as e:
            traceback.print_exc()
            print(e)
            return False

    async def start(self, current_session):
        await current_session.try_play_async()

    async def pause(self, current_session, volume=None):
        self.stopped_by_us = True
        await current_session.try_pause_async()
        await asyncio.sleep(1)
        if volume:
            self.fade_volume(volume, 1.0, duration=0)

    async def control_music(self, set_volume, fade):
        # for current_session in await get_current_session():
        current_session = await self.get_current_session()
        if current_session:
            info = await current_session.try_get_media_properties_async()
            playback_info = current_session.get_playback_info()

            app_name = current_session.source_app_user_model_id.split('!')[
                0] + (".exe" if ".exe" not in str(current_session.source_app_user_model_id) else "")

            # info_dict = {song_attr: info.__getattribute__(
            #     song_attr) for song_attr in dir(info) if song_attr[0] != '_'}

            # print(info_dict)
            volume = self.get_app_volume_control(app_name)
            if not self.allow_auto_play:
                if playback_info.playback_status != PlaybackStatus.PLAYING and self.stopped_by_us is False:
                    print(
                        "Music is currently not playing, please play some music to start!")
                    return

            if self.log:
                if self.old_title != (info.title, info.artist):
                    self.old_title = (info.title, info.artist)
                    print(
                        f"Playing {info.title} by {info.artist} on {app_name.split('.exe')[0]}")

            if volume:
                if set_volume == 0:
                    self.fade_volume(volume, set_volume, duration=fade)
                    await self.pause(current_session, volume)

                else:
                    if playback_info.playback_status != PlaybackStatus.PLAYING:
                        await self.start(current_session)
                        self.fade_volume(volume, set_volume,
                                         duration=fade)
            else:
                if set_volume == 0:
                    await self.pause(current_session)
                else:
                    if playback_info.playback_status != PlaybackStatus.PLAYING:
                        await self.start(current_session)

        else:
            print("No current media session found.")
