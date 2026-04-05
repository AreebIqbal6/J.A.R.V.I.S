import os
import sys
import re
import subprocess
import fastf1
import fastf1.plotting
import datetime
import warnings
import matplotlib.pyplot as plt

# Suppress pandas/fastf1 warnings to keep the terminal clean
warnings.filterwarnings("ignore")

# ==========================================
# --- SECURE TELEMETRY CACHE ---
# ==========================================
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
F1_CACHE_DIR = os.path.join(BASE_DIR, "Data", "F1_Cache")
CHART_DIR = os.path.join(BASE_DIR, "Data", "Charts")
REPLAY_DIR = os.path.join(BASE_DIR, "f1-race-replay") # Path to the new visualizer
os.makedirs(F1_CACHE_DIR, exist_ok=True)
os.makedirs(CHART_DIR, exist_ok=True)

# Enable the cache
fastf1.Cache.enable_cache(F1_CACHE_DIR)

class RaceEngineer:
    def __init__(self):
        self.current_year = datetime.datetime.now().year
        print(">> [F1 ENGINEER]: Pit wall telemetry & Visualizer link established.")
        
        # --- DRIVER TRANSLATION MAP ---
        self.DRIVER_MAP = {
            "VER": "Max Verstappen", "PER": "Sergio Perez", "HAM": "Lewis Hamilton",
            "RUS": "George Russell", "LEC": "Charles Leclerc", "SAI": "Carlos Sainz",
            "NOR": "Lando Norris",   "PIA": "Oscar Piastri",  "ALO": "Fernando Alonso",
            "STR": "Lance Stroll",   "GAS": "Pierre Gasly",   "OCO": "Esteban Ocon",
            "ALB": "Alexander Albon","TSU": "Yuki Tsunoda",   "LAW": "Liam Lawson",
            "HUL": "Nico Hulkenberg","BEA": "Oliver Bearman", "ANT": "Kimi Antonelli",
            "DOO": "Jack Doohan",    "BOR": "Gabriel Bortoleto", "COL": "Franco Colapinto",
            "BOT": "Valtteri Bottas", "ZHO": "Zhou Guanyu",   "MAG": "Kevin Magnussen"
        }

    def get_next_race(self, offset=0):
        try:
            schedule = fastf1.get_event_schedule(self.current_year)
            now = datetime.datetime.now()
            upcoming = schedule[schedule['EventDate'] > now]
            if len(upcoming) <= offset:
                return "Sir, there are no further races scheduled for this timeframe."
            next_event = upcoming.iloc[offset]
            event_name = next_event['EventName']
            event_date = next_event['EventDate'].strftime("%B %d, %Y")
            location = next_event['Location']
            if offset == 0:
                return f"The next race is the {event_name} in {location}, scheduled for {event_date}."
            else:
                return f"Following that, the {event_name} will take place in {location} on {event_date}."
        except Exception as e:
            return f"Error accessing FIA schedule: {e}"

    def get_last_race_results(self):
        try:
            now = datetime.datetime.now()
            schedule = fastf1.get_event_schedule(self.current_year)
            completed_races = schedule[(schedule['EventDate'] < now) & (schedule['EventFormat'] != 'testing')]
            if completed_races.empty:
                year_to_fetch = self.current_year - 1
                schedule = fastf1.get_event_schedule(year_to_fetch)
                completed_races = schedule[(schedule['EventDate'] < now) & (schedule['EventFormat'] != 'testing')]
            else:
                year_to_fetch = self.current_year
            last_event = completed_races.iloc[-1]
            round_num = last_event['RoundNumber']
            race_name = last_event['EventName']
            session = fastf1.get_session(year_to_fetch, round_num, 'R')
            session.load(telemetry=False, weather=False, messages=False) 
            if session.results is None or session.results.empty:
                return "Sir, the FIA servers have not uploaded the data for this race yet."
            results = session.results
            summary = f"Here are the top 5 results for the {race_name}:\n"
            for i in range(min(5, len(results))):
                driver = results.iloc[i]
                position = driver['Position']
                name = driver['FullName']
                team = driver['TeamName']
                status = driver['Status']
                if status == "Finished" or "Lap" in str(status):
                    summary += f"P{int(position)}: {name} ({team})\n"
                else:
                    summary += f"P{int(position)}: {name} ({team}) - {status}\n"
            return summary.strip()
        except Exception as e:
            return f"Error accessing race results: {e}"

    def analyze_telemetry(self):
        try:
            now = datetime.datetime.now()
            schedule = fastf1.get_event_schedule(self.current_year)
            completed_races = schedule[(schedule['EventDate'] < now) & (schedule['EventFormat'] != 'testing')]
            if completed_races.empty:
                year_to_fetch = self.current_year - 1
                schedule = fastf1.get_event_schedule(year_to_fetch)
                completed_races = schedule[(schedule['EventDate'] < now) & (schedule['EventFormat'] != 'testing')]
            else:
                year_to_fetch = self.current_year
            last_event = completed_races.iloc[-1]
            round_num = last_event['RoundNumber']
            race_name = last_event['EventName']
            session = fastf1.get_session(year_to_fetch, round_num, 'R')
            session.load(telemetry=True, weather=False, messages=False)
            p1_driver = session.results.iloc[0]['Abbreviation']
            p2_driver = session.results.iloc[1]['Abbreviation']
            p1_lap = session.laps.pick_driver(p1_driver).pick_fastest()
            p2_lap = session.laps.pick_driver(p2_driver).pick_fastest()
            tel_p1 = p1_lap.get_telemetry()
            tel_p2 = p2_lap.get_telemetry()
            fastf1.plotting.setup_mpl(color_scheme='fastf1')
            fig, ax = plt.subplots(figsize=(12, 6))
            color_p1 = fastf1.plotting.get_driver_color(p1_driver, session)
            color_p2 = fastf1.plotting.get_driver_color(p2_driver, session)
            style_p1 = 'solid'
            style_p2 = 'solid' if color_p1 != color_p2 else 'dashed'
            ax.plot(tel_p1['Distance'], tel_p1['Speed'], color=color_p1, linestyle=style_p1, label=p1_driver)
            ax.plot(tel_p2['Distance'], tel_p2['Speed'], color=color_p2, linestyle=style_p2, label=p2_driver)
            ax.set_xlabel('Distance (meters)', fontsize=12)
            ax.set_ylabel('Speed (km/h)', fontsize=12)
            ax.set_title(f"{race_name} {year_to_fetch} - Fastest Lap Overlay\n{p1_driver} vs {p2_driver}", fontsize=14, fontweight='bold')
            ax.legend(loc='lower right')
            file_path = os.path.join(CHART_DIR, "F1_Latest_Telemetry.png")
            plt.savefig(file_path, bbox_inches='tight', dpi=300)
            plt.close()
            if os.path.exists(file_path):
                os.startfile(file_path)
            return f"Sir, I have rendered the telemetry overlay for the {race_name}. I am displaying the fastest lap speed traces of {p1_driver} and {p2_driver} on your screen now."
        except Exception as e:
            return f"Sir, there was an error generating the F1 telemetry: {str(e)}"

    # ==========================================
    # --- NEW VISUALIZER MODULE ---
    # ==========================================
    def launch_race_visualizer(self, query):
        """Extracts the year and location/round, finds the round number, and launches the external Arcade viewer."""
        try:
            print(">> [F1 ENGINEER]: Booting external race visualization protocols...")
            query_lower = query.lower()
            
            # 1. Extract the Year (Default to current year if not mentioned)
            year_match = re.search(r'\b(201\d|202\d)\b', query_lower)
            year = int(year_match.group(1)) if year_match else self.current_year

            round_num = None
            event_name = None

            # SCENARIO A: User said "last" anywhere in the query (Bulletproof catch)
            if "last" in query_lower:
                now = datetime.datetime.now()
                schedule = fastf1.get_event_schedule(year)
                completed = schedule[(schedule['EventDate'] < now) & (schedule['EventFormat'] != 'testing')]
                if completed.empty:
                     return f"Sir, there are no completed races to replay for the {year} season yet."
                event = completed.iloc[-1]
                round_num = event['RoundNumber']
                event_name = event['EventName']

            # SCENARIO B: Extract Round Number (e.g., "round 5")
            elif "round" in query_lower:
                round_match = re.search(r'round\s*(\d+)', query_lower)
                if round_match:
                    round_num = int(round_match.group(1))
                    try:
                        event = fastf1.get_event(year, round_num)
                        event_name = event['EventName']
                    except fastf1.core.InvalidEventError:
                        return f"I'm sorry sir, but I could not find Round {round_num} in the {year} calendar."
            
            # SCENARIO C: Fuzzy Match by Location
            else:
                # Clean punctuation and filler words
                filler_words = ["show", "me", "the", "race", "trace", "of", "in", "replay", "visualize", "jarvis", str(year), "?", "."]
                clean_query = query_lower
                for word in filler_words:
                    clean_query = clean_query.replace(word, "").strip()
                
                location = clean_query
                
                if not location:
                    # If they just said "visualize the race" with no location, default to last
                    now = datetime.datetime.now()
                    schedule = fastf1.get_event_schedule(year)
                    completed = schedule[(schedule['EventDate'] < now) & (schedule['EventFormat'] != 'testing')]
                    if completed.empty:
                         return f"Sir, there are no completed races to replay for the {year} season yet."
                    event = completed.iloc[-1]
                else:
                    event = fastf1.get_event(year, location)

                round_num = event['RoundNumber']
                event_name = event['EventName']

            # 5. Launch the external Python script safely using Subprocess
            if not os.path.exists(os.path.join(REPLAY_DIR, "main.py")):
                return "Sir, I cannot locate the F1 Race Replay module. Please ensure the repository is cloned into the main directory."

            cmd = [sys.executable, "main.py", "--viewer", "--year", str(year), "--round", str(round_num)]
            subprocess.Popen(cmd, cwd=REPLAY_DIR)

            return f"Right away, sir. Launching the tactical track visualization for the {year} {event_name}."

        except fastf1.core.InvalidEventError:
            return f"I'm sorry sir, but I could not find a race matching that location or round in the {year} calendar."
        except Exception as e:
            return f"Sir, an error occurred while launching the visualizer: {str(e)}"

    def process_query(self, query):
        """Smarter NLP router to handle conversational F1 questions with Acronym Translation."""
        query = query.lower()
        response = ""
        
        # Check for Telemetry/Graphs FIRST (so "show telemetry" doesn't launch a replay)
        if any(word in query for word in ["telemetry", "graph", "speed", "compare", "chart", "analyze", "visual", "overlay"]):
            response = self.analyze_telemetry()
            
        # Check for Visualizer Launch NEXT (Smarter catch for "show" + "race" or "trace")
        elif any(word in query for word in ["replay", "visualize"]) or ("show" in query and ("race" in query or "trace" in query)) or "round" in query:
             response = self.launch_race_visualizer(query)
            
        # Check for past/results
        elif any(word in query for word in ["last", "result", "won", "winner", "who", "past"]):
            response = self.get_last_race_results()
            
        # Check for the race AFTER next
        elif any(word in query for word in ["after", "following", "then"]):
            response = self.get_next_race(offset=1)
            
        # Check for future/schedule
        elif any(word in query for word in ["next", "when", "schedule", "upcoming"]):
            response = self.get_next_race(offset=0)
            
        else:
            response = "Sir, I currently only have access to the schedule, recent race results, telemetry comparisons, and 2D track replays."

        # --- THE TRANSLATION ENGINE ---
        for acronym, full_name in self.DRIVER_MAP.items():
            response = response.replace(f" {acronym} ", f" {full_name} ")
            response = response.replace(f"{acronym} and", f"{full_name} and")

        return response