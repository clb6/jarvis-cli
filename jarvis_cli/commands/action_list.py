import re, pprint
from itertools import islice
import click
import dateparser
from tabulate import tabulate
import jarvis_cli as jc
from jarvis_cli import client, formatting


@click.group(name="list")
def do_action_list():
    """Query and list Jarvis resources"""
    pass

def _create_summary_of_log_entry(conn, log_entry):
    """
    Form a summary representation of the log file.
    """
    try:
        event_id = log_entry["event"]
        event = client.get_event(conn, event_id)
    except Exception as e:
        pprint.pprint(log_entry)
        raise e

    def format_ids():
        return "{0} -e {1}".format(log_entry["id"], log_entry["event"])

    def format_timestamps():
        def iso_to_datetime(str_datetime):
            # dateparser cannot handle microseconds apparently
            dt = dateparser.parse(str_datetime)
            if dt:
                return dt
            elif "." in str_datetime:
                stripped_ms = str_datetime[:str_datetime.index(".")]
                return iso_to_datetime(stripped_ms)


        created = iso_to_datetime(log_entry['created'])
        occurred = iso_to_datetime(event['occurred'])
        delta = (created - occurred).total_seconds()
        dates = { "created": log_entry["created"],
                "occurred": event["occurred"],
                "delta": int(delta/3600) }

        return "Occurred: {0}, Created: {1}, Delta: {2}hrs" \
            .format(dates["occurred"], dates["created"], dates["delta"])

    def format_tags():
        return "Tags: {0}".format(", ".join(log_entry["tags"]))

    def format_blurb():
        return log_entry['body'].split('\n')[0][0:250]

    return "\n".join([func() for func in [format_ids, format_timestamps,
        format_tags, format_blurb]])

def format_log_entry(conn, log_entry, search_term=None):
    if search_term:
        # This regex will look for a search term and grab 60 characters
        # around the matched term.
        search_regex = re.compile('.{{0,30}}\S*{0}\S*.{{0,30}}'
                .format(search_term), re.IGNORECASE)

        def find_search_term(log_entry):
            """
            :return: List of the matched strings
            """
            return [ m.group(0) for m in
                    search_regex.finditer(log_entry['body']) ]

        def format_matches(matches):
            if matches:
                return "\n".join([ "[{0}]: \"{1}\"".format(i, matches[i])
                    for i in range(0, len(matches)) ])
            else:
                return "No matches"

        return "\n\nSearch matches:\n".join([
            _create_summary_of_log_entry(conn, log_entry),
            format_matches(find_search_term(log_entry)) ])
    else:
        return _create_summary_of_log_entry(conn, log_entry)

@do_action_list.command(name="logs")
@click.option('-t', '--tag-name', help='Search by tag name')
@click.option('-s', '--search-term', help='Search term')
@click.pass_context
def list_log_entries(ctx, tag_name, search_term):
    """Query and list log entries"""
    conn = ctx.obj["connection"]
    logs = client.query_log_entries(conn, [("tags", tag_name),
        ("searchterm", search_term)])

    if logs:
        logs = [ format_log_entry(conn, log, search_term)
                for log in reversed(logs) ]
        print("\n\n".join(logs))
        print("\n\nLog entries found: {0}".format(len(logs)))
    else:
        print("No log entries found")

@do_action_list.command(name="tags")
@click.option('-t', '--tag-name', help='Search by tag name')
@click.option('-a', '--associated-tag-names', help='Search by associated tags')
@click.pass_context
def list_tags(ctx, tag_name, associated_tag_names):
    """Query and list tags"""
    conn = ctx.obj["connection"]
    tags = client.query("tags", conn, [("name", tag_name),
        ("tags", associated_tag_names)])

    if tags:
        tags = [ [tag['name'], ",".join(tag['tags'])] for tag in tags ]
        print(tabulate(tags, ["tag name", "tags"], tablefmt="simple"))
    else:
        print("No tags found")

@do_action_list.command(name="events")
@click.option('-c', '--category', type=click.Choice(jc.EVENT_CATEGORIES), help='Event category')
@click.option('-w', '--weight', type=int, help='Event weight lower bound')
@click.pass_context
def list_events(ctx, category, weight):
    """Query and list events"""
    # TODO: Show table view vs list view
    query_params = [('category', category), ('weight', weight)]
    query_params = [ qp for qp in query_params if qp[1] != None ]

    conn = ctx.obj["connection"]
    events = client.query('events', conn, query_params)

    if events:
        fields = ['category', 'occurred', 'weight', 'description',
                '#logs', '#artifacts', 'eventId']

        def format_event(e):
            return [ e['category'], e['occurred'], e['weight'],
                    formatting.truncate_long_text(e['description'], 40),
                    len(e['logEntrys']), len(e['artifacts']),
                    e['eventId'] ]

        def slice_and_display_ievents(ievents, step_size=25):
            events_sliced = list(islice(ievents, step_size))
            events_print = [ format_event(e) for e in events_sliced ]
            print(tabulate(events_print, fields, tablefmt="simple"))
            return events_sliced

        ievents = iter(events)
        events_sliced = slice_and_display_ievents(ievents)

        while True:
            if events_sliced:
                operation = input("What's next? {more/show/log/done}: ")

                if operation == "more":
                    events_sliced = slice_and_display_ievents(ievents)
                elif operation == "show":
                    # Show event in more details
                    index = int(input("Which?: "))
                    pprint.pprint(formatting.format_event(events_sliced[index]),
                            width=120)
                elif operation == "log":
                    # Create log
                    # TODO
                    pass
                elif operation == "done":
                    break
            else:
                break
    else:
        print("No events found")
