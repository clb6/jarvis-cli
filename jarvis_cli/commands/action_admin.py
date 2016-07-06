import click
from tabulate import tabulate
from jarvis_cli import client, admin, config

@click.group(name="admin")
def do_action_admin():
    """Perform administrative operations"""
    pass

@do_action_admin.command(name="status")
@click.pass_context
def show_status(ctx):
    """Show the Jarvis data api status"""
    conn = ctx.obj["connection"]
    columns = list(client.get_data_summary("tags", conn).keys())
    summaries = [ list(client.get_data_summary(rt, conn).values())
            for rt in ["tags", "logentries", "events"] ]
    print(tabulate(summaries, columns, tablefmt="simple"))

@do_action_admin.command(name="backup")
@click.pass_context
def backup(ctx):
    """Create a new snapshot"""
    environment = ctx.obj["environment"]
    config_map = ctx.obj["config_map"]
    filepath = admin.create_snapshot(environment, config_map)

    if filepath:
        print("Backing up successful: {0}".format(filepath))
    else:
        print("Backing up failed")

@do_action_admin.command(name="restore")
@click.option('--snapshot-path', required=True, help='Path to snapshot used to restore')
@click.pass_context
def restore(ctx, snapshot_path):
    """Restore an existing snapshot"""
    config_map = ctx.obj["config_map"]
    if admin.restore_snapshot(config_map, snapshot_path):
        print("Restore successful")
    else:
        print("Restore failed")

@do_action_admin.command(name="migrate")
@click.option('-s', '--environment-source', required=True,
        help='Jarvis environment name found in the cli_config.ini')
@click.pass_context
def migrate(ctx, environment_source):
    """Perform a data migration"""
    conn = ctx.obj["connection"]
    config_path = ctx.obj["config_path"]
    config_map_prev = config.get_config_map(environment_source, config_path)
    conn_prev = config.get_client_connection(config_map_prev)
    admin.migrate(conn_prev, conn)
