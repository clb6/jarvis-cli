from datetime import datetime
import time
# REVIEW: dateparser vs dateutil
import dateparser
import validators
import jarvis_cli as jc
from jarvis_cli import file_helper as fh
from jarvis_cli.exceptions import JarvisPromptError
from jarvis_cli.formatting import truncate_long_text

# REVIEW: Look more into using prompt-kit to help with building the prompts. It
# provides things like validators, highlighting (look at pygments doesn't have Markdown
# though), bells-whistles. First look showed it as more of a convenience thing
# right now.


def _print_answer(answer):
    print("> {0}\n".format(answer))

def _print_answer_truncated(answer, max_length=80):
    answer = truncate_long_text(answer, max_length)
    _print_answer(answer)

def _display_usage(usage_lines):
    usage = "\n".join(usage_lines)
    print("\n{0}\n".format(usage))


def prompt_event_occurred(current=None):
    default = dateparser.parse(current) \
            if current else datetime.utcnow().replace(microsecond=0)
    message = "When the event occurred [{0}]?: ".format(default.isoformat())

    while True:
        answer = input(message)

        if answer == "help":
            _display_usage([
                "Event occurrrence date & time in UTC",
                "Recommended input format ISO-8601 - YYYY-MM-DDTHH:MM",
                "Default value is {0}".format(default.isoformat())
                ])
        else:
            occurred = dateparser.parse(answer) if answer else default
            _print_answer(occurred)
            return occurred

def prompt_event_category(current=None):
    default = current
    message = "Event category"
    message += " [{0}]: ".format(default) if default else ": "

    while True:
        answer = input(message)

        if answer == "help":
            _display_usage([
                "Event category used to classify this event",
                "Valid options include -\n"
                "{0}".format(jc.EVENT_CATEGORIES)
                ])
        else:
            category = answer if answer and answer in jc.EVENT_CATEGORIES \
                    else default

            if category:
                _print_answer(category)
                return category
            else:
                print("Unknown category\n")

def prompt_event_weight(category, current=None):
    if category not in jc.EVENT_CATEGORIES_TO_DEFAULTS:
        raise JarvisPromptError("Invalid event category: {0}".format(category))

    default = current \
            if current else jc.EVENT_CATEGORIES_TO_DEFAULTS.get(category)
    message = "Event weight [{0}]: ".format(default)

    while True:
        answer = input(message)

        if answer == "help":
            import pprint
            _display_usage([
                "Event weight is a specified number to designate a magnitude for this event",
                "Each event category has a default value:",
                "{0}".format(pprint.pformat(jc.EVENT_CATEGORIES_TO_DEFAULTS))
                ])
        else:
            try:
                weight = answer if answer else default
                weight = int(weight)
                _print_answer(weight)
                return weight
            except:
                pass

def edit_event_description(occurred, current=None):
    print("Describe the event. Opening text editor.")
    time.sleep(1)

    filepath = fh.create_event_description_path(fh.generate_id(occurred))

    if current:
        with open(filepath, 'w') as f:
            f.write(current)

    fh.open_file_in_editor(filepath)

    with open(filepath, 'r') as f:
        description = f.read()
        _print_answer_truncated(description)
        return description

def _prompt_event_add_artifact(current):
    count = len(current)+1

    def get_parameter(param, validator_func):
        while True:
            result = input("[Artifact #{0}] {1}: ".format(count, param))

            if validator_func and validator_func(result):
                return result
            elif not validator_func:
                return result

    params = dict([(param.lower(), get_parameter(param, vfunc))
        for param, vfunc in [("Name", None), ("URL", validators.url),
            ("Source", None), ("Filetype", None)]])

    rel = "{0}-{1}".format(params["source"], params["filetype"])
    artifact = { "title": params["name"], "rel": rel, "href": params["url"] }

    current.append(artifact)
    return current

def _prompt_event_remove_artifact(current):
    if not current:
        print("No artifacts to remove")
        return current

    while True:
        try:
            artifact_index = int(input("Remove artifact number: "))
        except:
            continue

        if artifact_index >= 0 and artifact_index < len(current):
            del current[artifact_index]
            return current

def _display_artifacts(artifacts):
    # TODO: Definitely improve this. Maybe display in table?
    import pprint
    print("\nEvent artifacts:")
    pprint.pprint(artifacts)
    print("\n")

def prompt_event_artifacts(current=[]):
    while True:
        _display_artifacts(current)
        operation = input("Change event artifacts? {add/remove/done}: ")

        if operation == "add":
            current = _prompt_event_add_artifact(current)
        elif operation == "remove":
            current = _prompt_event_remove_artifact(current)
        elif operation == "done":
            return current
