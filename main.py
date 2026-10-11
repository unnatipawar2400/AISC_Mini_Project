
import json
import subprocess
import sys
import webbrowser
from pathlib import Path
from datetime import datetime

PROJECT_DIR = Path(__file__).resolve().parent
DATA_FILE = PROJECT_DIR / "current_input.json"


def ask_int(prompt, minimum=0, maximum=500):
    while True:
        try:
            value = int(input(prompt))
            if minimum <= value <= maximum:
                return value
            print(f"Enter a whole number from {minimum} to {maximum}.")
        except ValueError:
            print("Please enter a valid whole number.")


def ask_float(prompt, minimum=0, maximum=50):
    while True:
        try:
            value = float(input(prompt))
            if minimum <= value <= maximum:
                return value
            print(f"Enter a value between {minimum} and {maximum}.")
        except ValueError:
            print("Please enter a valid number.")


def get_yes_no(prompt):
    while True:
        answer = input(prompt + " (yes/no): ").strip().lower()
        if answer in ("yes", "y"):
            return True
        if answer in ("no", "n"):
            return False
        print("Please type yes or no.")


def make_recommendations(
    students, temperature, lights, fans, acs,
    projectors, computers, other, daylight,
    teaching_projector, cooling_needed
):
    tips = []
    total = lights + fans + acs + projectors + computers + other

    # Recommendations based on room occupancy
    if students == 0:
        tips.append(
            "The classroom is empty. Switch off non-essential "
            "lights, fans, projectors and computers."
        )
    else:
        tips.append(
            f"The classroom/Office has {students} students/employees. "
            "Keep sufficient lighting and airflow for everyone."
        )

    # Lighting
    if lights > 0 and daylight:
        tips.append(
            f"{lights} lights are active and daylight is available. "
            "Check the brightness in different areas and switch off "
            "only lights in areas that remain adequately lit."
        )
    elif lights >= 8:
        tips.append(
            f"{lights} lights are active. Inspect the room layout "
            "and identify any unnecessarily illuminated areas."
        )
    elif lights == 0 and students > 0:
        tips.append(
            "No lights are active. Check that classroom lighting "
            "is sufficient for students to read and work safely."
        )

    # Fans
    if fans > 0 and students > 0:
        tips.append(
            f"{fans} fans are active for {students} students. "
            "Check airflow and which areas each fan serves before "
            "deciding whether any fan can be switched off."
        )

    # Air conditioning
    if acs > 0:
        if temperature >= 30 and cooling_needed:
            tips.append(
                f"{temperature}°C is warm and cooling is needed. "
                "Keep appropriate cooling; check the set temperature "
                "and close doors or windows where suitable."
            )
        elif not cooling_needed:
            tips.append(
                f"{acs} AC units are active, but cooling was marked "
                "as not needed. Consider switching off an unused unit."
            )
        else:
            tips.append(
                f"{acs} AC units are active. Check room comfort and "
                "whether every unit is required."
            )

    # Projectors
    if projectors > 0:
        if teaching_projector:
            tips.append(
                "A projector is needed for teaching. Keep the "
                "required projector on and switch off any additional "
                "projector that is not being used."
            )
        else:
            tips.append(
                f"{projectors} projector(s) are active but not needed "
                "for teaching. Switch off unused projector(s)."
            )

    # Computers
    if computers > 0:
        tips.append(
            f"{computers} computers are active. Close unused systems "
            "and shut down computers that are not needed for the class."
        )

    # Other equipment
    if other > 0:
        tips.append(
            f"{other} other appliance(s) are active. Review each one "
            "and switch off only equipment that is not required."
        )

    # General recommendation
    if total >= 12:
        tips.append(
            f"There are {total} active appliances. Perform an "
            "appliance-by-appliance review rather than switching "
            "off a fixed number without checking their purpose."
        )
    elif total == 0 and students > 0:
        tips.append(
            "No appliances are reported as active. Confirm that "
            "essential classroom equipment is available."
        )
    else:
        tips.append(
            f"Review the {total} reported active appliances and "
            "prioritize equipment that is currently unused."
        )

    return tips


def main():
    print("\n==========================================")
    print(" SMART BUILDING ENERGY OPTIMIZER")
    print(" Enter classroom details in the terminal")
    print("==========================================")

    print("\nRoom type:")
    print("1. Classroom")
    print("2. Computer Lab")
    print("3. Office")

    while True:
        choice = input("Choose room type (1-3): ").strip()
        if choice in ("1", "2", "3"):
            room_type = {
                "1": "Classroom",
                "2": "Computer Lab",
                "3": "Office"
            }[choice]
            break
        print("Enter 1, 2, or 3.")

    students = ask_int("Number of students/occupants: ")
    temperature = ask_float("Room temperature in Celsius: ")

    print("\nEnter the number currently switched ON:")
    lights = ask_int("Lights: ")
    fans = ask_int("Fans: ")
    acs = ask_int("AC units: ")
    projectors = ask_int("Projectors: ")
    computers = ask_int("Computers: ")
    other = ask_int("Other appliances: ")

    daylight = get_yes_no(
        "Is there sufficient natural daylight in the room?"
    ) if lights > 0 else False

    teaching_projector = get_yes_no(
        "Is a projector currently needed for teaching?"
    ) if projectors > 0 else False

    cooling_needed = get_yes_no(
        "Is cooling currently needed for comfort?"
    ) if acs > 0 else False

    total = lights + fans + acs + projectors + computers + other

    # Simple illustrative estimate, not measured energy consumption.
    energy = (
        lights * 0.04
        + fans * 0.075
        + acs * 1.2
        + projectors * 0.25
        + computers * 0.15
        + other * 0.1
    )
    energy = round(energy, 2)

    if energy <= 1:
        level = "Low"
    elif energy <= 3:
        level = "Medium"
    else:
        level = "High"

    tips = make_recommendations(
        students, temperature, lights, fans, acs,
        projectors, computers, other, daylight,
        teaching_projector, cooling_needed
    )

    data = {
        "room_type": room_type,
        "temperature": temperature,
        "people": students,
        "appliances": total,
        "estimated_energy": energy,
        "energy_level": level,
        "recommendations": tips,
        "appliance_breakdown": {
            "Lights": lights,
            "Fans": fans,
            "AC units": acs,
            "Projectors": projectors,
            "Computers": computers,
            "Other": other
        },
        "updated_at": datetime.now().strftime(
            "%d %b %Y, %I:%M:%S %p"
        )
    }

    DATA_FILE.write_text(
        json.dumps(data, indent=4),
        encoding="utf-8"
    )

    print("\n========== ANALYSIS ==========")
    print("Room:", room_type)
    print("Students/occupants:", students)
    print("Active appliances:", total)
    print("Estimated energy:", energy, "kW")
    print("Estimated energy level:", level)

    print("\nRecommendations:")
    for number, tip in enumerate(tips, start=1):
        print(f"{number}. {tip}")

    print("\nOpening webpage...")

    server = subprocess.Popen(
        [
            sys.executable, "-m", "http.server",
            "8765", "--bind", "127.0.0.1"
        ],
        cwd=str(PROJECT_DIR),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )

    try:
        webbrowser.open("http://127.0.0.1:8765/index.html")
        input("\nKeep this terminal open. Press Enter to stop the server...")
    finally:
        server.terminate()
        server.wait()


if __name__ == "__main__":
    main()
