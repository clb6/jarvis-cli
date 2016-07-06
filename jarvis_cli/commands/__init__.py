import click
from jarvis_cli import config
from jarvis_cli.commands import action_new, action_edit, action_show, action_list, \
    action_admin

@click.group()
@click.option('-e', '--environment', default="default",
        help="Path to Jarvis cli configuration file")
@click.option('--config-path', default=config.JARVIS_CLI_CONFIG_PATH,
            help="Path to Jarvis cli configuration file")
# This is sweet
@click.version_option()
@click.pass_context
def cli(ctx, environment, config_path):
    config_map = config.get_config_map(environment, config_path)
    ctx.obj = { "config_map": config_map, "config_path": config_path,
            "connection": config.get_client_connection(config_map),
            "environment": environment }

cli.add_command(action_new.do_action_new)
cli.add_command(action_edit.do_action_edit)
cli.add_command(action_show.do_action_show)
cli.add_command(action_list.do_action_list)
cli.add_command(action_admin.do_action_admin)
