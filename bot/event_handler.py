import json
import logging
import re

from commands.hi import Hi
from commands.gala_wit import GalaWit

logger = logging.getLogger(__name__)


class RtmEventHandler(object):
    def __init__(self, slack_clients, msg_writer):
        self.clients = slack_clients
        self.msg_writer = msg_writer
        self.commands = [Hi(), GalaWit(msg_writer)]

    def handle(self, event):

        if 'type' in event:
            self._handle_by_type(event['type'], event)

    def _handle_by_type(self, event_type, event):
        # See https://api.slack.com/rtm for a full list of events
        if event_type == 'error':
            # error
            self.msg_writer.write_error(event['channel'], json.dumps(event))
        elif event_type == 'message':
            # message was sent to channel
            self._handle_message(event)
        elif event_type == 'channel_joined':
            # you joined a channel
            Hi().do_it(self.msg_writer,event)
        elif event_type == 'group_joined':
            # you joined a private group
            Hi().do_it(self.msg_writer,event)
        else:
            pass

    def _handle_message(self, event):
        # Filter out messages from the bot itself
        # Event won't have a user if slackbot is unfurling messages for you
        if event.has_key('user') and not self.clients.is_message_from_me(event['user']):
            msg_txt = event['text']

            # Filter out any messages where this bot isn't mentioned
            if not self.clients.is_bot_mention(msg_txt):
                return

            bot_uid = self.clients.bot_user_id()
            channel_id = event['channel']

            if re.search('help$', msg_txt):
                self.msg_writer.write_help(channel_id, self.commands)
                return

            found_command = False
            for c in self.commands:
                if c.allowed(channel_id):
                    if c.matches(event):
                        found_command = True
                        c.do_it(self.msg_writer,event)
                        break

            if not found_command:
                self.msg_writer.write_prompt(channel_id)

