import datetime
import re
from config.config import CONFIG_VARS as cvar
import util


class ScoreCalculator():
    """
    An abstraction over a github issue object used to calculate a score.
    """

    def __init__(self, number=None, data={}):
        self.number = number
        self.data = data

        self.score = 0
        self.number_of_comments = 0
        self.score_data = {}

        self.issue = self.data.get('issue', {})
        self.title = self.issue.get('title')
        if not self.title:
            self.title = ''
        self.body = self.issue.get('body')
        if not self.body:
            self.body = ''
        self.user = self.issue.get('user', {})
        self.login = self.user.get('login', '') or ''
        self.avatar = self.user.get('avatar_url', '') or ''

        self.assignee = ''
        assignee = self.issue.get('assignee')
        if assignee:
            self.assignee = assignee.get('login', '') or ''

        self.milestone = ''
        milestone = self.issue.get('milestone')
        if milestone:
            self.milestone = milestone.get('title', '') or ''

        self.references = 0

        self.created_at = util.get_date(self.issue.get('created_at'))
        self.updated_at = util.get_date(self.issue.get('updated_at'))

        self.comments = self.data.get('issue_comments')
        if not self.comments or not isinstance(self.comments, list):
            self.comments = []

        self.number_of_comments = len(self.comments)

        self.org_members = self.data.get('org_members', [])


    def load_scores(self):
        """
        Calculates an opinionated score for an issue's priority.
        Priority score will start at 50, and can go up or down.
        Each function may or may not update the score based on it's result.
        The algorithm can be tweaked by changing values passed to each method.

        Not the most DRY, but it's explicit and obvious, and beats using a
        messy hack to call/chain all methods of the instance.
        @return: the issue's priority score, higher is better
        """

        try:
            self.core_team_member()
            self.each_contribution()
            self.short_title_text()
            self.short_body_text()
            self.every_x_characters_in_body()
            self.daily_decay_since_creation()
            self.daily_decay_since_last_update()
            self.high_priority()
            self.awaiting_reply()
            self.each_unique_commenter()
            self.each_comment()
            self.code_snippets()
            self.code_demos()
            self.videos()
            self.images()
            self.forum_links()
            self.links()
            self.issue_references()

            return True

        except Exception as ex:
            print 'load_scores error: %s' % ex

        return False

    def to_dict(self):
        return {
            'number': self.number,
            'score': self.score,
            'title': self.title,
            'comments': self.number_of_comments,
            'references': self.references,
            'assignee': self.assignee,
            'milestone': self.milestone,
            'created': self.created_at.isoformat(),
            'updated': self.updated_at.isoformat(),
            'username': self.login,
            'avatar': self.avatar,
            'score_data': self.score_data,
        }


    ### Repo / Organization

    def core_team_member(self, add=cvar['CORE_TEAM']):
        if self.login in self.org_members:
            self.score += add
            self.score_data['core_team_member'] = add


    def each_contribution(self, add=cvar['CONTRIBUTION'], max_contribution=cvar['CONTRIBUTION_MAX']):
        if self.login in self.org_members:
            return
        contributors = self.data.get('contributors')
        if not contributors or not isinstance(contributors, list):
            return
        contrib = [c for c in contributors if self.login == c.get('login')]
        if contrib and len(contrib):
            contributions = contrib[0].get('contributions')
            if contributions:
                val = int(min(max_contribution, (int(contributions)*add)))
                self.score += val
                if val > 0:
                    self.score_data['each_contribution'] = val



    ### Issue

    def short_title_text(self, subtract=cvar['SHORT_TITLE_TEXT_SUBTRACT'], short_title_text_length=cvar['SHORT_TITLE_TEXT_LENGTH']):
        if len(self.title) < short_title_text_length:
            self.score -= subtract
            self.score_data['short_title_text'] = subtract * -1


    def short_body_text(self, subtract=cvar['SHORT_BODY_TEXT_SUBTRACT'], short_body_text_length=cvar['SHORT_BODY_TEXT_LENGTH']):
        if len(self.body) < short_body_text_length:
            self.score -= subtract
            self.score_data['short_body_text'] = subtract * -1


    def every_x_characters_in_body(self, add=cvar['BODY_CHAR_ADD'], x=cvar['BODY_CHAR_X'], max=cvar['BODY_CHAR_MAX']):
        val = min(self.every_x_chacters(self.body, add, x), max)
        if val > 0:
            self.score += val
            self.score_data['every_x_characters_in_body'] = val


    def every_x_characters_in_comments(self, add=cvar['COMMENT_CHAR_ADD'], x=cvar['COMMENT_CHAR_X'], max=cvar['COMMENT_CHAR_MAX']):
        val = 0
        for c in self.comments:
            comment_login = c.get('user', {}).get('login')
            if comment_login and comment_login not in self.org_members:
                val += self.every_x_chacters(c.get('body'), add, x)

        val = min(val, max)
        if val > 0:
            self.score += val
            self.score_data['every_x_characters_in_comments'] = val


    def every_x_chacters(self, text, add, x):
        if text:
            return int(float(len(text)) / float(x)) * add
        return 0


    def daily_decay_since_creation(self, exp=cvar['CREATION_DECAY_EXP'], start=cvar['CREATED_START'], now=datetime.datetime.now()):
        if not self.created_at:
            return
        days_since_creation = abs((now - self.created_at).days)
        val = int(float(start) - min((float(days_since_creation)**exp), start))
        self.score += val
        if val > 0:
            self.score_data['daily_decay_since_creation'] = val
        return {
            'days_since_creation': days_since_creation,
            'exp': exp,
            'start': start,
            'score': val
        }


    def daily_decay_since_last_update(self, exp=cvar['LAST_UPDATE_DECAY_EXP'], start=cvar['UPDATE_START'], now=datetime.datetime.now()):
        if not self.updated_at:
            return
        days_since_update = abs((now - self.updated_at).days)
        val = int(float(start) - min((float(days_since_update)**exp), start))
        self.score += val
        if val > 0:
            self.score_data['daily_decay_since_last_update'] = val
        return {
            'days_since_update': days_since_update,
            'exp': exp,
            'start': start,
            'score': val
        }


    def high_priority(self, add=cvar['HIGH_PRIORITY']):
        issue_labels = self.issue.get('labels')
        if issue_labels:
            label_set = set([l['name'] for l in issue_labels])
            if cvar['HIGH_PRIORITY_LABEL'] in label_set:
                self.score += add
                self.score_data['high_priority'] = add


    def awaiting_reply(self, subtract=cvar['AWAITING_REPLY']):
        issue_labels = self.issue.get('labels')
        if issue_labels:
            label_set = set([l['name'] for l in issue_labels])
            if cvar['NEEDS_REPLY_LABEL'] in label_set:
                self.score -= subtract
                self.score_data['awaiting_reply'] = subtract * -1


    def each_unique_commenter(self, add=cvar['UNIQUE_USER_COMMENT']):
        comments = self.data.get('issue_comments')
        if not comments:
            return

        commenters = []
        for comment in comments:
            comment_login = comment.get('user', {}).get('login')
            if comment_login and comment_login not in commenters and comment_login not in self.org_members:
                if comment_login != self.login:
                    commenters.append(comment_login)

        val = len(commenters) * add
        if val > 0:
            self.score += val
            self.score_data['each_unique_commenter'] = val


    def each_comment(self, add=cvar['COMMENT']):
        val = len(self.data.get('issue_comments', [])) * add
        if val > 0:
            self.score += val
            self.score_data['each_comment'] = val


    def code_snippets(self, add=cvar['SNIPPET'], per_line=cvar['SNIPPET_LINE'], line_max=cvar['SNIPPET_LINE_MAX']):
        total_code_lines = self.total_code_lines(self.body)

        for c in self.comments:
            total_code_lines += self.total_code_lines(c.get('body'))

        if total_code_lines > 0:
            val = add
            val += min(total_code_lines * per_line, line_max)

            self.score += val
            self.score_data['code_snippets'] = val


    def total_code_lines(self, text):
        total = 0
        text = text.replace('```', '\n```')
        lines = text.split('\n')
        ticks_on = False
        for line in lines:
            if line.startswith('```'):
                if ticks_on == False:
                    ticks_on = True
                else:
                    ticks_on = False

            if ticks_on:
                total += 1

        for line in lines:
            if line.startswith('    '):
                total += 1

        return total


    def videos(self, add=cvar['VIDEO']):
        all_videos = get_videos(self.body)

        for c in self.comments:
            all_videos += get_videos(c.get('body'))

        videos = []
        for video in all_videos:
            if video not in videos:
                videos.append(video)

        val = len(videos) * add
        self.score += val
        if val > 0:
            self.score_data['videos'] = val


    def images(self, add=cvar['IMAGE']):
        all_images = get_images(self.body)

        for c in self.comments:
            all_images += get_images(c.get('body'))

        images = []
        for image in all_images:
            if image not in images:
                images.append(image)

        val = len(images) * add
        self.score += val
        if val > 0:
            self.score_data['images'] = val


    def forum_links(self, add=cvar['FORUM_LINK'], forum_url=cvar['FORUM_URL']):
        all_links = get_links(self.body)

        for c in self.comments:
            all_links += get_links(c.get('body'))

        links = []
        for link in all_links:
            if link not in links and is_forum_link(link, forum_url):
                links.append(link)

        val = len(links) * add
        self.score += val
        if val > 0:
            self.score_data['forum_links'] = val


    def code_demos(self, add=cvar['DEMO'], demo_domains=cvar['DEMO_DOMAINS']):
        all_demos = get_code_demos(self.body)

        for c in self.comments:
            all_demos += get_code_demos(c.get('body'))

        demos = []
        for demo in all_demos:
            if demo not in demos and not is_image(demo) and not is_video(demo) and not is_forum_link(demo):
                demos.append(demo)

        val = len(demos) * add
        self.score += val
        if val > 0:
            self.score_data['code_demos'] = val


    def links(self, add=cvar['LINK']):
        all_links = get_links(self.body)

        for c in self.comments:
            all_links += get_links(c.get('body'))

        links = []
        for link in all_links:
            if link not in links and not is_image(link) and not is_video(link) and not is_forum_link(link) and not is_code_demo(link):
                links.append(link)

        val = len(links) * add
        self.score += val
        if val > 0:
            self.score_data['links'] = val


    def issue_references(self, add=cvar['ISSUE_REFERENCE']):
        all_issue_references = get_issue_references(self.body)

        for c in self.comments:
            all_issue_references += get_issue_references(c.get('body'))

        references = []
        for reference in all_issue_references:
            if reference not in references:
                references.append(reference)

        self.references = len(references)

        val = len(references) * add
        self.score += val
        if val > 0:
            self.score_data['issue_references'] = val


def get_issue_references(text):
    words = get_words(text)
    references = []
    for word in words:
        word = word.replace('.', '')
        if re.findall(r'#\d+', word):
            if word not in references:
                references.append(word)
    return references


def get_words(text):
    if text is None or text == '':
        return []

    delimiters = ['\n', '\t', ' ', '"', "'", '\(', '\)', '\[', '\]']
    return re.split('|'.join(delimiters), text.lower())


def get_links(text):
    links = []
    words = get_words(text)
    for word in words:
        if word and len(word) > 12:
            if word.startswith('http://') or word.startswith('https://'):
                if word not in links:
                    links.append(word)
    return links


def get_code_demos(text):
    code_demos = []
    links = get_links(text)
    for link in links:
        if link not in code_demos and is_code_demo(link):
            code_demos.append(link)
    return code_demos


def get_videos(text):
    videos = []
    links = get_links(text)
    for link in links:
        if link not in videos and is_video(link):
            videos.append(link)
    return videos


def get_images(text):
    images = []
    links = get_links(text)
    for link in links:
        if link not in images and is_image(link):
            images.append(link)
    return images


def is_code_demo(link, demo_domains=cvar['DEMO_DOMAINS']):
    if link:
        for demo_domain in demo_domains:
            if demo_domain in link:
                return True
    return False


def is_forum_link(link, forum_url=cvar['FORUM_URL']):
    if link:
        return forum_url in link
    return False


def is_image(link):
    image_exts = ('.png', '.jpg', '.jpeg', '.gif', '.webp', '.svg', '.psd', '.ai')
    return is_file(link, image_exts)


def is_video(link):
    video_exts = ('.mov', '.qt', '.avi', '.wmv', '.mp4', '.m4p', '.m4v', '.mpg', '.mpeg', '.asf', '.webm')
    return is_file(link, video_exts)


def is_file(link, possible_extensions):
    link = link.strip().lower().split('?')[0].split('#')[0]
    for ext in possible_extensions:
        if link.endswith(ext):
            return True
    return False

