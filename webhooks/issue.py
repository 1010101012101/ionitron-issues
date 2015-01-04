import re
import github3
import requests
from config import CONFIG_VARS as cvar


def flag_if_submitted_through_github(payload):
    """
    Flags any issue that is submitted through github's UI, and not the Ionic site.
    Adds a label, as well as a comment, to force the issue through the custom form.
    @return: whether or not the issue was flagged (bool)
    """

    gh = github3.login(cvar['GITHUB_USERNAME'], cvar['GITHUB_PASSWORD'])
    i = gh.issue(cvar['REPO_USERNAME'], cvar['REPO_ID'], payload['issue']['number'])

    if i.labels:
        labels = [l.name for l in i.labels]
    else:
        labels = []

    # Do not take action if already flagged, or is submitted with custom form
    if (i.body_html[3:24] == u'<strong>Type</strong>' or cvar['NEEDS_RESUBMIT_LABEL'] in labels):
        return False

    # Issue submitted through github, close and add comment
    try:  # Read message templates from remote URL
        msg = requests.get(cvar['RESUBMIT_TEMPLATE']).text
    except:  # Read from local file
        msg = open(cvar['RESUBMIT_TEMPLATE']).read()

    msg = re.sub(r'<%= issue.number %>', str(payload['issue']['number']), msg)
    msg = re.sub(r'<%= user.login %>', str(payload['issue']['user']['login']), msg)
    i.add_labels(cvar['NEEDS_RESUBMIT_LABEL'])
    i.create_comment(msg)

    return True