from datetime import datetime
import click
# REVIEW: dateparser vs dateutil
import dateparser
import jarvis_cli as jc
from jarvis_cli import config, client
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
    fh.create_file_log(ctx.obj["connection"], event_id)

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
        fh.create_file_tag(conn, tag_name)

@do_action_new.command(name="event")
@click.pass_context
def create_event(ctx):
    """Create a new event"""
    occurred = dateparser.parse(input("When occurred [default: now]?: "))
    occurred = occurred or datetime.utcnow()

    while True:
        category = input("Event category [options: {0}]: ".format(jc.EVENT_CATEGORIES))

        if category in jc.EVENT_CATEGORIES:
            break

    while True:
        default = jc.EVENT_CATEGORIES_TO_DEFAULTS.get(category)
        weight = input("Event weight [default: {0}]: ".format(default)) or default

        try:
            weight = int(weight)
            break
        except:
            pass

    filepath = fh.create_filepath("/tmp",
            "jarvis_event_{0}".format(fh.generate_id(occurred)))
    fh.open_file_in_editor(filepath)

    with open(filepath, 'r') as f:
        description = f.read()

    request = { "occurred": occurred.isoformat(), "category": category,
            "source": jc.EVENT_SOURCE,
            "weight": weight, "description": description }
    response = client.post_event(ctx.obj["connection"], request)

    if response:
        print("Created: {0}".format(response.get("eventId")))
