#!/usr/bin/env python

import os, subprocess, argparse
from datetime import datetime


if "__main__" == __name__:
    parser = argparse.ArgumentParser(description='Jarvis is used for personal information management')

    subparsers = parser.add_subparsers(help='Actions for Jarvis',
            dest='action_name')

    parser_new = subparsers.add_parser('new', help='Create an information element')
    subparsers_new = parser_new.add_subparsers(help='Types of new information element',
            dest='element_type')
    parser_new_log = subparsers_new.add_parser('log', help='Create a new log entry')
    parser_new_tag = subparsers_new.add_parser('tag', help='Create a new tag element')
    parser_new_tag.add_argument('tag_name', help='Tag name')

    parser_show = subparsers.add_parser('show', help='Show information elements')
    subparsers_show = parser_show.add_subparsers(help='Types of show actions',
            dest='show_type')
    parser_show_tags = subparsers_show.add_parser('tags', help='Show tags')

    args = parser.parse_args()

    # NOTE: Argparse should filter and validate and ensure that only the known
    # choices get through to this point.
    # UPDATE: There is a case where the subsubparser allows for Nones to slip
    # through. The required flag doesn't seem to be reinforced so the following
    # is acceptable to Argparse which sucks for me:
    #   jarvis.py new

    if args.action_name == 'new':
        # TODO: Make a test mode where it writes to a test directory.
        env_dir_jarvis_root = os.environ['JARVIS_DIR_ROOT']
        env_author = os.environ['JARVIS_AUTHOR']
        env_version = "0.1.0"

        created = datetime.utcnow().replace(microsecond=0)

        def create_stub_file(subdir_name, filename):
            dir_target = "{0}/{1}".format(env_dir_jarvis_root, subdir_name)

            filepath = "{0}/{1}.md".format(dir_target, filename)

            if os.path.isfile(filepath):
                raise IOError("File already exists! {0}".format(filepath))

            with open(filepath, 'w') as f:
                f.write("Author: {0}\n".format(env_author))
                f.write("Created: {0}\n".format(created.isoformat()))
                f.write("Version: {0}\n".format(env_version))
                f.write("Tags: \n")

            return filepath

        if args.element_type == 'log':
            # datetime.fromtimestamp(0) is not Unix epoch and returns
            # 1969-12-31 19:00 instead.
            epoch = datetime(1970, 1, 1)

            filepath = create_stub_file('LogEntries',
                int((created - epoch).total_seconds()))
        elif args.element_type == 'tag':
            filepath = create_stub_file('Tags', args.tag_name)

            # Add the title which should be the tag name
            with open(filepath, 'a') as f:
                # TODO: Would be very cool to reinforce camel case for the file
                # name and canonical for title.
                f.write("\n# {0}\n".format(args.tag_name))
        else:
            raise NotImplementedError("Unknown information type: {0}"
                    .format(args.element_type))

        if filepath:
            subprocess.call(["vim", filepath])
            print("Created: {0}, {1}".format(args.element_type, filepath))
        else:
            print("Failed to create new information element")
    elif args.action_name == 'show':

        if args.show_type == 'tags':
            print('Show me the tags')
        else:
            raise NotImplementedError("Unknown show type: {0}"
                    .format(args.show_type))
