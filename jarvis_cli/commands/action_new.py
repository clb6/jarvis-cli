import pprint
import click
import jarvis_cli as jc
from jarvis_cli import config, client, formatting
import jarvis_cli.file_helper as fh
from jarvis_cli import interactive as jci


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
    occurred = jci.prompt_event_occurred()
    category = jci.prompt_event_category()
    weight = jci.prompt_event_weight(category)
    description = jci.edit_event_description(occurred)
    artifacts = jci.prompt_event_artifacts()

    request = { "occurred": occurred.isoformat(), "category": category,
            "source": jc.EVENT_SOURCE, "weight": weight, "description": description,
            "artifacts": artifacts }

    pprint.pprint(formatting.format_event_request(request), width=120)

    def prompt_create_log(connection, author, event_id):
        while True:
            should_create_log = input("Create log entry? [Y/N]: ")

            if should_create_log == "Y":
                fh.create_file_log(connection, author, event_id)
                break
            elif should_create_log == "N":
                break

    while True:
        should_publish = input("Publish? [Y/N]: ")

        if should_publish == "Y":
            connection = ctx.obj["connection"]
            response = client.post_event(connection, request)

            if response:
                event_id = response.get("eventId")
                print("Created new event: {0}".format(event_id))
                author = config.get_author(ctx.obj["config_map"])
                prompt_create_log(connection, author, event_id)
            else:
                print("Something unexpected happened while publishing the event.")
            break
        elif should_publish == "N":
            print("Canceled event publish")
            break
