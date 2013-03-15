# -*- coding:utf-8 -*-
import json
import urllib
import logging
import twitter
from twitter import Status, User
from time import time

from zope import schema
from zope.formlib import form
from zope.interface import alsoProvides
from zope.schema.vocabulary import SimpleVocabulary
from zope.schema.interfaces import IContextSourceBinder
from zope.interface import implements
from zope.component import getUtility

from plone.memoize import ram
from plone.registry.interfaces import IRegistry
from plone.portlets.interfaces import IPortletDataProvider
from plone.app.portlets.portlets import base

from collective.prettydate.interfaces import IPrettyDate

from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile

from cienciasalud.bluetheme import _

logger = logging.getLogger('cienciasalud.bluetheme')
LIMIT = 3
SECONDS = 60

ONLY_SELF = False  # Only get statuses submitted by me

MAX_FETCHES = 3


def TwitterAccounts(context):
    registry = getUtility(IRegistry)
    accounts = registry['collective.twitter.accounts']
    if accounts:
        vocab = accounts.keys()
    else:
        vocab = []

    return SimpleVocabulary.fromValues(vocab)


alsoProvides(TwitterAccounts, IContextSourceBinder)


class ISocialPortlet(IPortletDataProvider):
    """A portlet
    It inherits from IPortletDataProvider because for this portlet, the
    data that is being rendered and the portlet assignment itself are the
    same.
    """

    search_text = schema.TextLine(
        title=_(u'Text to search'),
        required=False,
    )

    search_account = schema.Bool(
        title=_(u'Search in account'),
        required=False,
    )

    account = schema.Choice(
        title=_(u'Twitter account'),
        description=_(u"Which twitter account to use."),
        required=False,
        source=TwitterAccounts
    )

    limit = schema.Int(
        title=_(u'Number of tweets to show'),
        required=False,
    )


class Assignment(base.Assignment):
    """Portlet assignment.

    This is what is actually managed through the portlets UI and associated
    with columns.
    """

    implements(ISocialPortlet)

    show_dates = True
    pretty_date = True

    def __init__(self, search_text='', search_account='', account='', limit=4, **kwargs):
        self.search_text = search_text
        self.search_account = search_account
        self.account = account
        self.limit = limit

    @property
    def title(self):
        """This property is used to give the title of the portlet in the
        "manage portlets" screen.
        """
        return _(u"Social Portlet Twitter")


def cache_key_simple(func, var):
    #let's memoize for 5 minutes or if any value of the tile is modified.
    timeout = time() // (60 * 5)
    return (timeout,)


class Renderer(base.Renderer):
    """Portlet renderer.

    This is registered in configure.zcml. The referenced page template is
    rendered, and the implicit variable 'view' will refer to an instance
    of this class. Other methods can be added and referenced in the template.
    """

    render = ViewPageTemplateFile('social.pt')

    LIMIT = 4

    def get_limit(self):
        limit = self.LIMIT
        if self.data.limit:
            limit = self.data.limit
        return int(limit)

    def get_account(self):
        registry = getUtility(IRegistry)
        accounts = registry.get('collective.twitter.accounts', None)
        account = None
        if accounts and len(accounts.values()) > 0:
            account_key = self.data.account
            if not account_key or account_key not in accounts.keys():
                account_key = accounts.keys()[0]
                account = {accounts.keys()[0]: accounts[account_key]}
            else:
                account = {account_key: accounts[account_key]}
        return account

    def get_search_str(self):
        text = self.data.search_text
        if not text:
            text = None
        return text

    def get_search_account(self):
        search = self.data.search_account
        return search

    @ram.cache(cache_key_simple)
    def get_twitts(self):
        results = self.get_twitter_results()
        return results

    def get_twitter_results(self):
        logger.debug("Getting tweets.")
        accounts = self.get_account()
        if accounts and len(accounts.values()) > 0:
            tw_user = accounts.keys()[0]
            account = accounts[tw_user]
            results = []
            logger.debug("Got a valid account.")
            logger.debug("consumer_key = %s" % account.get('consumer_key'))
            logger.debug("consumer_secret = %s" % account.get('consumer_secret'))
            logger.debug("access_token_key = %s" % account.get('oauth_token'))
            logger.debug("access_token_secret = %s" % account.get('oauth_token_secret'))
            tw = twitter.Api(consumer_key=account.get('consumer_key'),
                             consumer_secret=account.get('consumer_secret'),
                             access_token_key=account.get('oauth_token'),
                             access_token_secret=account.get('oauth_token_secret'),)
            tw_user = accounts.keys()[0]

            max_results = self.get_limit()
            search_str = self.get_search_str()
            try:
                if search_str:
                    if self.get_search_account():
                        results = self.GetSearch(tw, search_str,
                                                 per_page=max_results,
                                                 lang="all",
                                                 from_account=tw_user)
                        pagination = 2
                        while len(results) != max_results and pagination != 10:
                            search_res = self.GetSearch(tw, search_str,
                                                        per_page=max_results,
                                                        lang="all",
                                                        page=pagination,
                                                        from_account=tw_user)
                            results = results + search_res
                            pagination += 1
                    else:
                        results = self.GetSearch(tw, search_str,
                                                 per_page=max_results,
                                                 lang="all")
                else:
                    results = tw.GetUserTimeline(tw_user, count=max_results)
                logger.debug("%s results obtained." % len(results))
            except Exception, e:
                logger.debug("Something went wrong: %s." % e)
                results = []
            return results

    def GetSearch(self, tw, term=None, geocode=None, since_id=None,
                  per_page=15, page=1, lang="en", show_user="true",
                  from_account=None, query_users=False):
        # Build request parameters
        parameters = {}

        if since_id:
            parameters['since_id'] = since_id

        if term is None and geocode is None:
            return []
        if term is not None:
            parameters['q'] = term

        if geocode is not None:
            parameters['geocode'] = ','.join(map(str, geocode))

        parameters['show_user'] = show_user
        parameters['lang'] = lang
        parameters['rpp'] = per_page
        parameters['page'] = page
        if from_account:
            parameters['from'] = from_account

        # Make and send requests
        url = 'http://search.twitter.com/search.json'
        json_result = tw._FetchUrl(url, parameters=parameters)
        data = tw._ParseAndCheckTwitter(json_result)

        results = []

        for x in data['results']:
            temp = Status.NewFromJsonDict(x)

            if query_users:
                # Build user object with new request
                temp.user = tw.GetUser(urllib.quote(x['from_user']))
            else:
                temp.user = User(screen_name=x['from_user'], profile_image_url=x['profile_image_url'])
            results.append(temp)

        # Return built list of statuses
        return results

    def get_tweet(self, result):
        # We need to make URLs, hastags and users clickable.
        URL_TEMPLATE = """
        <a href="%s">%s</a>
        """
        HASHTAG_TEMPLATE = """
        <a href="http://twitter.com/search?q=%s" target="blank_">%s</a>
        """
        USER_TEMPLATE = """
        <a href="http://twitter.com/%s" target="blank_">%s</a>
        """

        full_text = result.GetText()
        split_text = full_text.split(' ')

        # Now, lets fix links, hashtags and users
        for index, word in enumerate(split_text):
            if word.startswith('@'):
                # This is a user
                split_text[index] = USER_TEMPLATE % (word[1:], word)
            elif word.startswith('#'):
                # This is a hashtag
                split_text[index] = HASHTAG_TEMPLATE % ("%23" + word[1:], word)
            elif word.startswith('http'):
                # This is a hashtag
                split_text[index] = URL_TEMPLATE % (word, word)

        return "<p>%s</p>" % ' '.join(split_text)

    def get_tweet_url(self, result):
        return "https://twitter.com/%s/status/%s" % (result.user.screen_name,
                                                     result.id)

    def get_reply_tweet_url(self, result):
        return "https://twitter.com/intent/tweet?in_reply_to=%s" % result.id

    def get_re_tweet_url(self, result):
        return "https://twitter.com/intent/retweet?tweet_id=%s" % result.id

    def get_fav_tweet_url(self, result):
        return "https://twitter.com/intent/favorite?tweet_id=%s" % result.id

    def get_pretty_date(self, date):
        date_utility = getUtility(IPrettyDate)
        date = date_utility.date(date)

        return date


class AddForm(base.AddForm):
    """Portlet add form.

    This is registered in configure.zcml. The form_fields variable tells
    zope.formlib which fields to display. The create() method actually
    constructs the assignment that is being added.
    """
    form_fields = form.Fields(ISocialPortlet)

    def create(self, data):
        return Assignment(**data)


class EditForm(base.EditForm):
    """Portlet edit form.

    This is registered with configure.zcml. The form_fields variable tells
    zope.formlib which fields to display.
    """
    form_fields = form.Fields(ISocialPortlet)
