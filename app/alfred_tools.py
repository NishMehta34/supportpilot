"""Day 11: a tiny re-implementation of the Hugging Face Agents Course 'Alfred'
exercise, using OUR OWN agent loop from Day 4 instead of a framework.

Alfred is a butler preparing Bruce Wayne's party. The tools are deliberately
simple and self-contained, the same style as Day 3/4's fake business data.
"""

GUESTS = {
    "lady whistledown": {"name": "Lady Whistledown", "relation": "gossip columnist",
                          "dietary": "none", "plus_one": False},
    "bruce wayne": {"name": "Bruce Wayne", "relation": "host", "dietary": "none", "plus_one": False},
    "selina kyle": {"name": "Selina Kyle", "relation": "guest of honour",
                    "dietary": "vegetarian", "plus_one": True},
}

WEATHER = {
    "gotham": {"condition": "light rain", "temp_c": 14},
    "metropolis": {"condition": "clear", "temp_c": 22},
}

MENUS = {
    "italian": ["Bruschetta", "Risotto ai Funghi", "Tiramisu"],
    "vegetarian": ["Stuffed Peppers", "Wild Mushroom Risotto", "Panna Cotta (veg-friendly)"],
}

PLAYLISTS = {
    "elegant": ["Clair de Lune - Debussy", "Gymnopedie No.1 - Satie"],
    "upbeat": ["Uptown Funk - Bruno Mars", "Don't Stop Me Now - Queen"],
}


def check_weather(city: str) -> dict:
    return WEATHER.get(city.strip().lower()) or {"error": f"No weather data for '{city}'"}


def check_guest(name: str) -> dict:
    return GUESTS.get(name.strip().lower()) or {"error": f"No guest named '{name}' on the list"}


def suggest_menu(style: str) -> dict:
    items = MENUS.get(style.strip().lower())
    return {"style": style, "items": items} if items else {"error": f"No menu style '{style}'"}


def suggest_playlist(mood: str) -> dict:
    tracks = PLAYLISTS.get(mood.strip().lower())
    return {"mood": mood, "tracks": tracks} if tracks else {"error": f"No playlist for mood '{mood}'"}


ALFRED_TOOL_FUNCTIONS = {
    "check_weather": check_weather,
    "check_guest": check_guest,
    "suggest_menu": suggest_menu,
    "suggest_playlist": suggest_playlist,
}


def _schema(name, description, arg_name, arg_description):
    return {
        "type": "function",
        "function": {
            "name": name, "description": description,
            "parameters": {"type": "object",
                           "properties": {arg_name: {"type": "string", "description": arg_description}},
                           "required": [arg_name]},
        },
    }


ALFRED_TOOL_SCHEMAS = [
    _schema("check_weather", "Check the weather in a city for party planning.",
            "city", "e.g. Gotham"),
    _schema("check_guest", "Look up a guest's relation to the host and dietary needs.",
            "name", "e.g. Selina Kyle"),
    _schema("suggest_menu", "Suggest a menu for a given style.",
            "style", "e.g. italian, vegetarian"),
    _schema("suggest_playlist", "Suggest a playlist for a given mood.",
            "mood", "e.g. elegant, upbeat"),
]


def execute_alfred_tool(name, arguments):
    function = ALFRED_TOOL_FUNCTIONS.get(name)
    if function is None:
        return {"error": f"Unknown tool: {name}"}
    try:
        return function(**arguments)
    except TypeError as error:
        return {"error": f"Invalid arguments for {name}: {error}"}
    except Exception as error:
        return {"error": f"Tool {name} failed: {error}"}
