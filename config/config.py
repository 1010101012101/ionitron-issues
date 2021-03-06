from os import getenv as EV
from .score import SCORE_VARS
from .templates import TEMPLATE_VARS

CONFIG_VARS = {

    # bot will only execute actions if set to False
    'DEBUG': EV('DEBUG') != 'false',

    # bot's github username
    'GITHUB_USERNAME': EV('GITHUB_USERNAME'),

    # bot's github access token
    'GITHUB_ACCESS_TOKEN': EV('GITHUB_ACCESS_TOKEN'),

    # close after $X inactive days
    'CLOSE_INACTIVE_AFTER': 90,

    # close issues that haven't received a reply after $X days
    'CLOSE_NOREPLY_AFTER': 30,

    # remove ionitron's please resubmt through the form comment after X days
    'REMOVE_FORM_RESUBMIT_COMMENT_AFTER': 14,

    # do not close issues with $X+ comments
    'DO_NOT_CLOSE_MIN_COMMENTS': 0,

    # whether or not to ignore issues that have been referenced
    'DO_NOT_CLOSE_WHEN_REFERENCED': True,

    # do not close issues that have these labels
    'DO_NOT_CLOSE_LABELS': ['in progress', 'ready', 'high priority'],

    # label to add when issue is closed
    'ON_CLOSE_LABEL': 'ionitron:closed',

    # label saying its a feature request
    'FEATURE_REQUEST_LABEL': 'feature',

    # label for high priority issues
    'HIGH_PRIORITY_LABEL': 'high priority',

    # label that indicates we asked a question and need a response
    'NEEDS_REPLY_LABEL': 'needs reply',

    # hidden content to add to a comment that's requesting them to resubmit from the form
    'NEEDS_RESUBMIT_CONTENT_ID': 'ionitron-issue-resubmit',

    # hidden content to add to a comment that's requesting them to reply with more info
    'NEEDS_REPLY_CONTENT_ID': 'ionitron-needs-reply',

    # labels to automatically remove when replying/closing
    'AUTO_REMOVE_LABELS': ['ready', 'in progress', 'ionitron:warned', 'ionitron:please resubmit'],
}

CONFIG_VARS.update(SCORE_VARS)
CONFIG_VARS.update(TEMPLATE_VARS)
