# ionitron-issues

*Ionic's proof-of-concept utility for automatically ranking and responding to GitHub Issues*

__IMPORTANT__: This is not a supported project. We will not be able to respond to issues or PRs. Feel free to fork and customize for your project


### Overview:

ionitron-github is a github bot that watches the Ionic repo, and will take action when certain **webhook** events are received. Ionitron also performs a number of repo maintenance tasks that are triggered by daily **cronjobs**. All actions can be customized by changing the variables in `config.py`. See [config.py](https://github.com/driftyco/ionitron-issues/blob/master/config.py) for a full list of options. Below is a checklist outlining current and future features.


### Requires
 - python
 - pip
 - virtualenv
 - postgres `brew install postgresql`
 - [redis-server](http://redis.io/topics/quickstart)


### Running Locally / Development:

**1)** Install/create [Virtual Environments](http://docs.python-guide.org/en/latest/dev/virtualenvs/):

    pip install virtualenv
    cd ionitron-issues
    virtualenv venv


**2)** Start `virtualenv`

    source venv/bin/activate


**3)** Install the Python (2.7.3) dependencies:

    pip install -r requirements.txt


**4)** Add the same environmental variables that are assigned in the Heroku app

*The template variables can be changed to point to a local file to test messages on a test repo. This is useful to test repo webhooks, and the responses that should be returned.*


**5)** Install [redis-server](http://redis.io/topics/quickstart). This is used as a task queue for cron jobs such as removing old issues, updating issue scores, etc. It is also used as a cache; issue data is persisted and updated daily, or when the issue receives an update event. Finally, redis stores common data about the repo, organization, contributors, etc. Redis-server needs to be started in the background before the app can be run:

    redis-server


**4)** Start the app server:

    python main.py


### Test Github API Access

    Run the app server, then visit `/api/test`


### Run Unit Tests

    python -m unittest discover


### Debug Mode:
If `debug=True`, all of the cronjob tasks below will *run*, but won't take action to close/warn the issues. Instead, the issues that would have been closed/warned are printed out to the console. This is useful if you want to tweak the configurations, and see how the changes impact what should be closed/warned, without actually doing it.

### API Testing

 - Manually run one issue's maintenance: `https://ionitron-issues.herokuapp.com/api/driftyco/ionic/200/maintenance`
 - Manually run all maintenance: `https://ionitron-issues.herokuapp.com/api/maintenance`
 - Issue scores: `https://ionitron-issues.herokuapp.com/api/driftyco/ionic/issue-scores`



### Deploying:

    heroku git:remote -a ionitron-issues && git push heroku master

Check out [this article](https://devcenter.heroku.com/articles/git) for more info. The redis-to-go addon must be configured if starting from a new Heroku app.



### Tasks:

- Close github issues older than $CLOSE_INACTIVE_AFTER days. Adds a comment based on the remote markdown template defined in $CLOSING_TEMPLATE.
- Remove the 'needs reply' label if the user replied since the label was added.
- Close github issues that haven't received a reply after $CLOSE_NOREPLY_AFTER days after the `needs reply` label has been added. Adds a comment based on the remote markdown template defined in $CLOSING_NOREPLY_TEMPLATE.
- Add a comment to all issues not submitted through Ionic's [issue submit form](http://ionicframework.com/submit-issue/) containing a link to resubmit the issue. Also adds the *ionitron: please resubmit* label to the issue.
- Remove the *ionitron: please resubmit* label if the user updated their issue through the custom form.
- Delete any issues labeld with *ionitron: please resubmit* after 7 days
- Score each issue daily and when updated.
- Get a list of all open issue scores.
- Run maintenance tasks on all open issues daily.
- Manually add templated comments and ability to close issues from the issues app, as Ionitron
