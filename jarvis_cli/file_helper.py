import os, subprocess, re
from functools import partial
import webbrowser
from datetime import datetime
from jarvis_cli import client
from jarvis_cli.client import log_entry as cle


def convert_file_to_json(file_path):
    """
    Form a json representation of a log file.

    Example of return response:

    {
        "author": "John Doe",
        "created": "2015-12-12T16:22:41",
        "occurred": "2015-11-25T00:00:00",
        "version": "0.2.0",
        "tags": ["Weather", "HelloWorld"],
        "parent": "123456789",
        "todo": "Read *War and Peace*",
        "setting": "Finished reading *The Cat and the Hat* while watching a very
        orange sunset.",
        "body": "Today was a bright and sunny day!"
    }

    :param file_path: full path of the file
    :type file_path: string

    :return: json
    """
    with open(file_path, 'r') as f:
        (metadata, body) = f.read().split('\n\n', maxsplit=1)

        def parse_metadata(line):
            """
            :param line: line for metadata e.g. "Author: John Doe"
            :type line: string

            :return: (key string, value string)
            """
            m = re.search('^(\w*): (.*)', line)
            # Watch! Stripping trailing whitespace because for some reason
            # certain field values are showing whitespace.
            return m.group(1).lower(), m.group(2).strip()

        t = [ parse_metadata(line) for line in metadata.split('\n') ]

        response = dict(t)

        if "tags" in response:
            response['tags'] = response['tags'].split(', ')
            # Handle scenario when there are no tags which will return an empty
            # string. Also strip the unnecessary whitespaces.
            response['tags'] = [ tag.strip() for tag in response['tags'] if tag ]
        if body.strip():
            response['body'] = body

        return response

def create_filepath(file_dir, file_name):
    """
    TODO: Need test
    """
    file_name = file_name if ".md" in file_name else "{0}.md".format(file_name)
    return os.path.join(file_dir, file_name)

def create_event_description_path(some_key):
    return create_filepath("/tmp", "jarvis_event_description_{0}".format(some_key))

def generate_id(some_datetime):
    # WATCH! datetime.fromtimestamp(0) is not Unix epoch and returns
    # 1969-12-31 19:00 instead.
    epoch = datetime(1970, 1, 1)
    return str(int((some_datetime - epoch).total_seconds()))


def open_file_in_editor(filepath):
    editor = os.environ['EDITOR']
    subprocess.call([editor, filepath])

# Modified not allowed for edits but want in reads. Split them up.
metadata_keys_tag_show = ["name", "author", "created", "modified", "version",
        "tags"]
metadata_keys_log_show = ["id", "author", "created", "modified", "version",
        "tags", "parent", "event", "todo"]
metadata_keys_tag_edit = [field for field in metadata_keys_tag_show if field
        not in ["modified"]]
metadata_keys_log_edit = [field for field in metadata_keys_log_show if field
        not in ["event", "modified"]]

def handle_jarvis_resource(metadata_keys, json_object, resource_id):
    if not json_object:
        return

    temp = "/tmp/{0}.md".format(resource_id)

    def convert_json_to_file(metadata_keys, json_object):
        def stringify(metadata_key):
            if metadata_key == "tags":
                return ", ".join(json_object.get(metadata_key))
            else:
                # Don't want to display literally "None" so check for None
                # and convert to empty string.
                v = json_object.get(metadata_key)
                return v if v else ""

        metadata = [ "{0}: {1}".format(k.capitalize(), stringify(k))
                for k in metadata_keys ]
        metadata = "\n".join(metadata)

        # Events don't have bodies
        if "body" in json_object:
            return "\n\n".join([ metadata, json_object.get("body") ])
        else:
            # HACK: The hardcoded "\n\n" is necessary bc
            # convert_file_to_json expects it.
            return metadata + "\n\n"

    with open(temp, 'w') as f:
        f.write(convert_json_to_file(metadata_keys, json_object))

    return temp

def edit_file(metadata_keys, json_object, resource_id):
    temp = handle_jarvis_resource(metadata_keys, json_object, resource_id)

    if temp:
        open_file_in_editor(temp)
        return temp

edit_file_tag = partial(edit_file, metadata_keys_tag_edit)
edit_file_log = partial(edit_file, metadata_keys_log_edit)

def just_show_file(file_path):
    if file_path:
        # Previews the markdown. This will require you to change the
        # mimeapps.list setting file in order to chose your markdown preview
        # tool.
        webbrowser.open("file://{0}".format(file_path))

def show_file(metadata_keys, json_object, resource_id):
    temp = handle_jarvis_resource(metadata_keys, json_object, resource_id)
    just_show_file(temp)

show_file_tag = partial(show_file, metadata_keys_tag_show)
show_file_log = partial(show_file, metadata_keys_log_show)

def check_and_create_missing_tags(conn, author, resource_request):
    for tag_name in resource_request['tags']:
        print("Checking if tag already exists: {0}".format(tag_name))
        if not client.get_tag(conn, tag_name.lower()):
            try:
                create_file_tag(conn, author, tag_name)
            except Exception as e:
                # TODO: Need to handle case when not all the tags gets created.
                print("Unexpected error creating tag: {0}, {1}".format(
                    tag_name, e))

def _create_file(conn, post_func, show_file_func, resource_id_key, local_path,
        author, stub_content):
    with open(local_path, 'w') as f:
        f.write(stub_content)

    open_file_in_editor(local_path)
    resource_request = convert_file_to_json(local_path)
    check_and_create_missing_tags(conn, author, resource_request)
    resource = post_func(resource_request)

    if resource:
        resource_id = resource[resource_id_key]
        show_file_func(resource, resource_id)
        print("Created: {0}".format(resource_id))

def create_file_log(conn, author, event_id):
    created = datetime.utcnow().replace(microsecond=0)

    metadata = [("Author", author), ("Tags", None), ("Parent", None),
            ("Todo", None)]
    metadata = [ "{0}: {1}".format(k, v if v else "")
            for k, v in metadata ]
    stub_content = "\n".join(metadata)

    # Need a temporary log id because the log id actually gets created by
    # the API.
    log_id_temp = "jarvis_log_{0}" \
        .format(generate_id(created))

    log_path = create_filepath("/tmp", log_id_temp)

    _create_file(conn, partial(cle.post_log_entry, event_id, conn), show_file_log,
            "id", log_path, author, stub_content)

def create_file_tag(conn, author, tag_name):
    metadata = [ "Name: {0}".format(tag_name), "Author: {0}".format(author),
            "Tags: " ]

    stub_content = "\n\n".join(["\n".join(metadata), "# {0}\n".format(tag_name)])
    tag_path = create_filepath("/tmp", tag_name)

    _create_file(conn, partial(client.post_tag, conn), show_file_tag, "name",
            tag_path, author, stub_content)
