from datetime import datetime
import time, pprint
import click
# REVIEW: dateparser vs dateutil
import dateparser
import validators
import jarvis_cli as jc
from jarvis_cli import config, client, formatting
import jarvis_cli.file_helper as fh


@click.group(name="new")
def do_action_new():
    """Create a new Jarvis resource"""
    pass

@do_action_new.command(name="log")
@click.option('-e', '--event-id', prompt=True, help="Associated event")
@click.pass_context
def create_log_entry(ctx, event_id):
    """Create a new log entry"""
    author = config.get_author(ctx.obj["config_map"])
    fh.create_file_log(ctx.obj["connection"], author, event_id)

@do_action_new.command(name="tag")
@click.argument('tag-name')
@click.pass_context
def create_tag(ctx, tag_name):
    """Create a new tag"""
    print("Checking if tag already exists: {0}".format(tag_name))

    conn = ctx.obj["connection"]

    if client.get_tag(conn, tag_name.lower()):
        print("Tag already exists: {0}".format(tag_name))
    else:
        author = config.get_author(ctx.obj["config_map"])
        fh.create_file_tag(conn, author, tag_name)

@do_action_new.command(name="event")
@click.pass_context
def create_event(ctx):
    """Create a new event"""
    def print_answer(answer):
        print("> {0}\n".format(answer))

    occurred = dateparser.parse(input("When the event occurred [default: now]?: "))
    occurred = occurred or datetime.utcnow().replace(microsecond=0)
    print_answer(occurred)

    while True:
        category = input("Event category [options: {0}]: ".format(jc.EVENT_CATEGORIES))

        if category in jc.EVENT_CATEGORIES:
            print_answer(category)
            break

    while True:
        default = jc.EVENT_CATEGORIES_TO_DEFAULTS.get(category)
        weight = input("Event weight [default: {0}]: ".format(default)) or default

        try:
            weight = int(weight)
            print_answer(weight)
            break
        except:
            pass

    print("Describe the event. Opening text editor.")
    time.sleep(1)

    filepath = fh.create_event_description_path(fh.generate_id(occurred))
    fh.open_file_in_editor(filepath)

    with open(filepath, 'r') as f:
        description = f.read()
        print_answer(description)

    request = { "occurred": occurred.isoformat(), "category": category,
            "source": jc.EVENT_SOURCE, "weight": weight, "description": description,
            "artifacts": [] }

    # Add artifacts
    while True:
        should_add = input("Add an event artifact? [Y/N]: ")

        if should_add == "Y":
            count = len(request["artifacts"])+1

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

            request["artifacts"].append(artifact)

            pprint.pprint(artifact)
            print("\n")

        elif should_add == "N":
            print("\n")
            break

    pprint.pprint(formatting.format_event_request(request), width=120)

    while True:
        should_publish = input("Publish? [Y/N]: ")

        if should_publish == "Y":
            response = client.post_event(ctx.obj["connection"], request)

            if response:
                print("Created new event: {0}".format(response.get("eventId")))
            break
        elif should_publish == "N":
            print("Canceled event publish")
            break
