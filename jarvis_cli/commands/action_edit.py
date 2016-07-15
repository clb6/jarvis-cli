from functools import partial
import pprint
import click
import jarvis_cli as jc
from jarvis_cli import client, config, formatting
from jarvis_cli import file_helper as fh
from jarvis_cli import interactive as jci
from jarvis_cli.client import log_entry as cle


@click.group(name="edit")
def do_action_edit():
    """Edit an existing Jarvis resource"""
    pass

def _edit_resource(conn, get_func, put_func, edit_file_func, show_file_func,
        post_edit_func, resource_id):
    resource = get_func(conn, resource_id)

    if resource:
        filepath = edit_file_func(resource, resource_id)

        if filepath:
            json_object = fh.convert_file_to_json(filepath)
            json_object = post_edit_func(json_object)

            resource = put_func(conn, resource_id, json_object)

            if resource:
                show_file_func(resource, resource_id)
                print("Editted: {0}".format(resource_id))

@do_action_edit.command(name="log")
@click.argument('log-entry-id')
@click.option('-e', '--event-id', prompt=True, help="Associated event")
@click.pass_context
def edit_log_entry(ctx, log_entry_id, event_id):
    """Edit an existing log entry"""
    author = config.get_author(ctx.obj["config_map"])
    conn = ctx.obj["connection"]

    def post_edit_log(json_object):
        # WATCH! This specialty code here because the LogEntry.id
        # is a number.
        json_object["id"] = int(json_object["id"])
        fh.check_and_create_missing_tags(conn, author, json_object)

        # Change from log entry to log entry request
        json_object.pop('created', None)
        json_object.pop('id', None)
        json_object.pop('version', None)
        return json_object

    # TODO: There must be a easier way to get event id.
    get_func = partial(cle.get_log_entry, event_id)
    put_func = partial(cle.put_log_entry, event_id)

    _edit_resource(conn, get_func, put_func, fh.edit_file_log,
            fh.show_file_log, post_edit_log, log_entry_id)

@do_action_edit.command(name="tag")
@click.argument('tag-name')
@click.pass_context
def edit_tag(ctx, tag_name):
    """Edit an existing tag"""
    author = config.get_author(ctx.obj["config_map"])
    conn = ctx.obj["connection"]

    def post_edit_tag(json_object):
        fh.check_and_create_missing_tags(conn, author, json_object)

        # Change from tag to tag request
        json_object.pop("created", None)
        json_object.pop("version", None)
        return json_object

    conn = ctx.obj["connection"]
    _edit_resource(conn, client.get_tag, client.put_tag, fh.edit_file_tag,
            fh.show_file_tag, post_edit_tag, tag_name)

@do_action_edit.command(name="event")
@click.argument('event-id')
@click.pass_context
def edit_event(ctx, event_id):
    """Edit an existing event"""
    conn = ctx.obj["connection"]

    event = client.get_event(conn, event_id)

    occurred = jci.prompt_event_occurred(event["occurred"])
    category = jci.prompt_event_category(event["category"])
    weight = jci.prompt_event_weight(category, event["weight"])
    description = jci.edit_event_description(occurred, event["description"])
    artifacts = jci.prompt_event_artifacts(event["artifactLinks"])

    # TODO: DRY request creation with action_new.event
    request = { "occurred": occurred.isoformat(), "category": category,
            "source": jc.EVENT_SOURCE, "weight": weight, "description": description,
            "artifacts": artifacts }

    pprint.pprint(formatting.format_event_request(request), width=120)

    while True:
        should_publish = input("Publish update? [Y/N]: ")

        if should_publish == "Y":
            response = client.put_event(conn, event_id, request)

            if response:
                print("Updated event: {0}".format(response.get("eventId")))
            break
        elif should_publish == "N":
            print("Canceled event update")
            break
