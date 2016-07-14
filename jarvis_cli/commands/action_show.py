from functools import partial
import pprint
import click
from jarvis_cli import file_helper as fh
from jarvis_cli import client, formatting
from jarvis_cli.client import log_entry as cle

@click.group(name="show")
def do_action_show():
    """Display a Jarvis resource"""
    pass

def _get_and_show_resource(conn, get_func, show_file_func, resource_id):
    resource = get_func(conn, resource_id)
    show_file_func(resource, resource_id)

@do_action_show.command(name="log")
@click.argument('log-entry-id')
@click.option('-e', '--event-id', prompt=True, help="Associated event")
@click.pass_context
def show_log_entry(ctx, log_entry_id, event_id):
    """Display a log entry"""
    conn = ctx.obj["connection"]
    # TODO: There must be a easier way to get event id.
    get_func = partial(cle.get_log_entry, event_id)
    _get_and_show_resource(conn, get_func, fh.show_file_log, log_entry_id)

@do_action_show.command(name="tag")
@click.argument('tag-name')
@click.pass_context
def show_tag(ctx, tag_name):
    """Display a tag"""
    conn = ctx.obj["connection"]
    _get_and_show_resource(conn, client.get_tag, fh.show_file_tag, tag_name)

@do_action_show.command(name="event")
@click.argument('event-id')
@click.pass_context
def show_event(ctx, event_id):
    """Display an event"""
    conn = ctx.obj["connection"]
    event = client.get_event(conn, event_id)

    pprint.pprint(formatting.format_event(event), width=120)
    print("\n")

    section = input("Show more [description]?: ")

    if section == "description":
        tmpfile = fh.create_event_description_path(event_id)

        with open(tmpfile, 'w') as f:
            f.write(event[section])

        fh.just_show_file(tmpfile)
