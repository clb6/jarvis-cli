import re, pprint
from itertools import chain
import click
import dateparser
from tabulate import tabulate
import jarvis_cli as jc
import jarvis_cli.file_helper as fh
from jarvis_cli import client, formatting, config


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
@click.option('-s', '--search-term', default=None, help='Search term to search in event descriptions')
@click.option('--only-important', is_flag=True, default=False, help='Show only important events')
@click.pass_context
def list_events(ctx, category, search_term, only_important):
    """Query and list events"""
    weight = None
    query_params = [('category', category), ('searchterm', search_term),
            ('weight', weight)]
    query_params = [ qp for qp in query_params if qp[1] != None ]

    conn = ctx.obj["connection"]
    events_generator = client.query_generator('events', conn, query_params)

    def slice_and_display_events(events_generator, batch_size=20):
        """Slice events by using a the `query_generator` call with a specified
        number of calls `num_calls`, display the events indexed,
        and return the slice as a list"""
        events_sliced = []

        def is_important(e):
            category = e['category']
            return e['weight'] > jc.EVENT_CATEGORIES_TO_DEFAULTS[category]

        while True:
            try:
                current_batch = next(events_generator)

                if only_important:
                    events_sliced += list(filter(is_important, current_batch))
                else:
                    events_sliced += current_batch

                if len(events_sliced) >= batch_size:
                    break
            except StopIteration:
                # Have reached the end of the generator
                break

        def format_event(e):
            return [ e['category'], e['occurred'], is_important(e),
                    formatting.truncate_long_text(e['description'], 40),
                    len(e['logEntrys']), len(e['artifacts']) ]

        def chain_each_event(it):
            """Takes [[1], ["abc", "xyz"]] and produces [1, "abc", "xyz"]"""
            return list(chain.from_iterable(it))

        # Create indexed list of formatted event records
        events_print = [ format_event(e) for e in events_sliced ]
        indices = [ [i] for i in range(0, len(events_sliced)) ]
        events_print = list(map(chain_each_event, zip(indices, events_print)))

        fields = ['index', 'category', 'occurred', 'important', 'description',
                '#logs', '#artifacts']

        print(tabulate(events_print, fields, tablefmt="simple"))
        return events_sliced

    events_sliced = slice_and_display_events(events_generator)

    while True:
        if events_sliced:
            command = input("What's next? {more/show/log/done}: ")

            def determine_event_index(command):
                command = command.split(" ")

                if len(command) > 1:
                    try:
                        return int(command[1])
                    except:
                        pass
                return int(input("{0} which event? Give an index: ".format(
                    command[0].capitalize())))

            if command == "more":
                events_sliced = slice_and_display_events(events_generator)
            elif "show" in command:
                # Show an event in greater detail
                index = determine_event_index(command)
                pprint.pprint(formatting.format_event(events_sliced[index]),
                        width=120)
            elif "log" in command:
                # Create log associated with an event
                index = determine_event_index(command)
                event_id = events_sliced[index]["eventId"]
                author = config.get_author(ctx.obj["config_map"])
                fh.create_file_log(conn, author, event_id)
            elif command == "done":
                break
        else:
            break
