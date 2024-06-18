from http.server import BaseHTTPRequestHandler, HTTPServer
from control import control
import traceback
import json

port = 1337


class cs2mc:
    def __init__(self):
        self.allow_auto_play = True  # allow program to start playing stopped music
        # log
        self.log_vol = True  # volume changes
        self.log_mus = True  # log playing music and app
        self.log_gsi = False  # game state integration data
        # volume
        self.vol_base = 100  # default volume
        self.vol_menu = self.vol_base
        self.vol_game = 0
        self.vol_buyp = 30  # buy period
        self.vol_warm = 40  # warmup
        self.vol_spec = 40

        self.dur_fade = 1  # fade duration

        # trash
        self.old = None
        self.current_volume = None

        ctrl = control(self.dur_fade, self.log_mus, self.allow_auto_play)
        self.adjust_volume = ctrl.adjust_volume

    def volume(self, set_volume, why):
        why_dict = {
            "menu": "We're in the menu",
            "spec": "Spectating",
            "buyp": "Game not live yet",
            "dead": "We're dead",
            "game": "We're playing",
            "warm": "We're warming up",
            "play": "We're deciding on or switching a team"
        }

        if set_volume != self.current_volume:
            if self.log_vol:
                print(why_dict[why] + ",", "setting volume to",
                      str(set_volume) + "%")
            self.current_volume = set_volume
            self.adjust_volume(volume=set_volume, fade=self.dur_fade)

    def get_data(self, post_data):
        try:
            return json.loads(post_data.decode('utf-8'))
        except Exception:
            traceback.print_exc()

    def main(self, data):
        try:
            if data["provider"]["appid"] == 730:
                my_id = data["provider"]["steamid"]
                if data["player"]["activity"] == "menu":
                    try:
                        data['player']['state']
                    except KeyError:
                        self.volume(self.vol_menu, "menu")
                elif data["player"]["steamid"] != my_id:
                    self.volume(self.vol_spec, "spec")
                elif data["round"]["phase"] != "live":
                    self.volume(self.vol_buyp, "buyp")
                elif data["player"]["state"]["health"] == 0:
                    self.volume(self.vol_spec, "dead")
                else:
                    self.volume(self.vol_game, "game")

                if self.log_gsi:
                    # remove timestamps so it does not spam
                    del data["provider"]
                    if data != self.old:
                        self.old = data
                        print(json.dumps(data, indent=4, sort_keys=True))

            else:
                # ignore data that isn't from cs2
                pass

        except KeyError as e:
            if "'round'" == str(e):
                self.volume(self.vol_warm, "warm")
            elif "'player'" == str(e):
                self.volume(self.vol_warm, "play")
            elif "'state'" == str(e):
                pass

            else:
                print("KeyError:", e)

        except Exception:
            traceback.print_exc()


mc = cs2mc()


class RequestHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        return

    def do_POST(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(b'Hello, World!')
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)

        mc.main(mc.get_data(post_data))


def run_server(server_class=HTTPServer, handler_class=RequestHandler, port=port):
    server_address = ('', port)
    httpd = server_class(server_address, handler_class)
    print(f"Server running on http://127.0.0.1:{port}")
    httpd.serve_forever()


run_server()
