from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse
import json
import os
from pathlib import Path

HOST = "0.0.0.0"
PORT = int(os.environ.get("PORT", 8765))

BASE_DIR = Path(__file__).resolve().parent
HTML_FILE = BASE_DIR / "index.html"
DATA_FILE = BASE_DIR / "current_input.json"


def analyze_energy(data):
    # Read form values
    room = data["room_type"]
    occupants = int(data["occupants"])
    temperature = float(data["temperature"])

    lights = int(data["lights"])
    fans = int(data["fans"])
    acs = int(data["acs"])
    projectors = int(data["projectors"])
    computers = int(data["computers"])
    other = int(data["other"])

    daylight = data["daylight"]
    cooling_needed = data["cooling"]

    # Illustrative appliance power assumptions (kW per appliance)
    energy = (
        lights * 0.04
        + fans * 0.075
        + acs * 1.2
        + projectors * 0.25
        + computers * 0.15
        + other * 0.1
    )

    active_appliances = (
        lights + fans + acs + projectors + computers + other
    )

    if energy < 1:
        level = "Low"
    elif energy <= 3:
        level = "Medium"
    else:
        level = "High"

    recommendations = []

    if occupants > 0:
        recommendations.append(
            f"The {room.lower()} has {occupants} occupants. "
            "Maintain suitable lighting and airflow for everyone."
        )

    if temperature >= 30 and cooling_needed == "yes":
        recommendations.append(
            f"At {temperature:.1f}°C, the room is warm. "
            "Use appropriate cooling and a reasonable set temperature."
        )
    elif cooling_needed == "no" and acs > 0:
        recommendations.append(
            "Cooling is not needed according to your input. "
            "Check whether the AC units need to remain on."
        )

    if daylight == "yes" and lights > 0:
        recommendations.append(
            "Natural daylight is sufficient. Consider switching off "
            "unneeded lights after checking the room's lighting needs."
        )
    elif daylight == "no":
        recommendations.append(
            "Natural daylight is insufficient. Keep adequate lighting "
            "for safe and comfortable use of the room."
        )

    if computers > 0:
        recommendations.append(
            f"{computers} computers are listed. Shut down unused "
            "systems when they are no longer needed."
        )

    if active_appliances > 0:
        recommendations.append(
            f"There are {active_appliances} active appliances. "
            "Review each appliance before deciding whether it can be switched off."
        )
    else:
        recommendations.append(
            "No appliances were entered. Check your appliance counts."
        )

    return {
        "room_type": room,
        "occupants": occupants,
        "temperature": temperature,
        "active_appliances": active_appliances,
        "estimated_energy": round(energy, 2),
        "energy_level": level,
        "recommendations": recommendations,
        "note": (
            "This estimate uses illustrative appliance power values. "
            "It is not a measured electricity reading or a trained "
            "machine-learning prediction."
        ),
    }


class EnergyHandler(BaseHTTPRequestHandler):

    def send_content(self, status, content, content_type):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(content)

    def do_GET(self):
        path = urlparse(self.path).path

        if path in ("/", "/index.html"):
            try:
                page = HTML_FILE.read_bytes()
                self.send_content(
                    200, page, "text/html; charset=utf-8"
                )
            except FileNotFoundError:
                self.send_content(
                    404, b"index.html was not found.",
                    "text/plain; charset=utf-8"
                )
        else:
            self.send_content(
                404, b"Page not found.",
                "text/plain; charset=utf-8"
            )

    def do_POST(self):
        if urlparse(self.path).path != "/analyze":
            self.send_content(
                404, b'{"error":"Not found"}',
                "application/json; charset=utf-8"
            )
            return

        try:
            length = int(self.headers.get("Content-Length", "0"))

            if length <= 0 or length > 100_000:
                raise ValueError("Invalid form submission.")

            raw = self.rfile.read(length)
            data = json.loads(raw.decode("utf-8"))

            # Validate form fields
            allowed_rooms = {"Classroom", "Computer Lab", "Office"}
            if data.get("room_type") not in allowed_rooms:
                raise ValueError("Choose a valid room type.")

            for field in (
                "occupants", "lights", "fans", "acs",
                "projectors", "computers", "other"
            ):
                value = int(data[field])
                if value < 0 or value > 10000:
                    raise ValueError(
                        f"{field} must be between 0 and 10000."
                    )
                data[field] = value

            data["temperature"] = float(data["temperature"])
            if not -20 <= data["temperature"] <= 80:
                raise ValueError("Enter a valid temperature.")

            if data.get("daylight") not in ("yes", "no"):
                raise ValueError("Choose a daylight option.")

            if data.get("cooling") not in ("yes", "no"):
                raise ValueError("Choose a cooling option.")

            result = analyze_energy(data)

            # Save inputs and results for reference
            with DATA_FILE.open("w", encoding="utf-8") as file:
                json.dump(
                    {"inputs": data, "results": result},
                    file,
                    indent=4
                )

            response = json.dumps(result).encode("utf-8")
            self.send_content(
                200, response, "application/json; charset=utf-8"
            )

        except (ValueError, KeyError, TypeError, json.JSONDecodeError) as error:
            response = json.dumps({"error": str(error)}).encode("utf-8")
            self.send_content(
                400, response, "application/json; charset=utf-8"
            )

    def log_message(self, format, *args):
        print(f"{self.address_string()} - {format % args}")


if __name__ == "__main__":
    server = HTTPServer((HOST, PORT), EnergyHandler)
    url = f"http://{HOST}:{PORT}"

    print(f"Smart Energy Advisor running at {url}")
    print("Keep this terminal open while using the webpage.")

    threading.Timer(
        1.0, lambda: webbrowser.open(url)
    ).start()

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped.")
    finally:
        server.server_close()
