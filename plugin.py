# -*- coding: utf-8 -*-
###
# Copyright (c) 2013-2014, spline
# All rights reserved.
###
# my libs
import json  # yahoo.
import re  # unicode replace.
import math  # for millify.
try:  # for google stockquote.
    import xml.etree.cElementTree as ElementTree
except ImportError:
    import xml.etree.ElementTree as ElementTree
import datetime  # futures math.
import pytz  # tzconv for relativetime.
# extra supybot libs
import supybot.ircmsgs as ircmsgs
# supybot libs.
import supybot.utils as utils
from supybot.commands import *
import supybot.plugins as plugins
import supybot.ircutils as ircutils
import supybot.callbacks as callbacks
from supybot.i18n import PluginInternationalization, internationalizeDocstring

_ = PluginInternationalization('Odds')

@internationalizeDocstring
class Stock(callbacks.Plugin):
    """Display stock and financial information."""
    threaded = True

    def __init__(self, irc):
        self.__parent = super(Stock, self)
        self.__parent.__init__(irc)

    def die(self):
        self.__parent.die()

    ######################
    # INTERNAL FUNCTIONS #
    ######################

    def _colorify(self, s, perc=False):
        """Change symbol/color depending on if gain is positive or negative."""

        s = s.replace('%','')
        if float(s) > 0:
            if perc:
                s = self._green(u'▴' + s.replace('+','') + "%")
            else:
                s = self._green(u'▴' + s.replace('+',''))
        elif float(s) < 0:
            if perc:
                s = self._red(u'↓' + s.replace('-','') + "%")
            else:
                s = self._red(u'↓' + s.replace('-',''))
        return s

    def _millify(self, n):
        """Display human readable numbers."""

        millnames=['','k','M','B','T']
        millidx=max(0,min(len(millnames)-1, int(math.floor(math.log10(abs(n))/3.0))))
        return '%.1f%s'%(n/10**(3*millidx),millnames[millidx])

    def _splitinput(self, txt, seps):
        """Split input depending on separators."""

        default_sep = seps[0]
        for sep in seps[1:]:
            txt = txt.replace(sep, default_sep)
        return [i.strip() for i in txt.split(default_sep)]

    def _httpget(self, url, h=None, d=None):
        """General HTTP resource fetcher. Supports b64encoded urls."""

        try:
            if h and d:
                page = utils.web.getUrl(url, headers=h, data=d)
            else:
                h = {"User-Agent":"Mozilla/5.0 (X11; Ubuntu; Linux i686; rv:17.0) Gecko/20100101 Firefox/17.0"}
                page = utils.web.getUrl(url, headers=h)
            return page
        except utils.web.Error as e:
            self.log.error("I could not open {0} error: {1}".format(url, e))
            return None

    def _out(self, irc, msg, txt):
        """Handle output."""

        # check if we should msg users for this channel
        if ircmsgs.isChannel(msg.args[0]):
            if self.registryValue('msgUsersOutput', msg.args[0]):# we're in a channel and True.
                irc.sendMsg(ircmsgs.privmsg(msg.nick, txt))  # send text to user.
            else:  # setting is off or not on a channel with it on.
                irc.sendMsg(ircmsgs.privmsg(msg.args[0], txt))
        else:  # in a privmsg.
            irc.sendMsg(ircmsgs.privmsg(msg.nick, txt))


    ########################
    # COLOR AND FORMATTING #
    ########################

    def _red(self, string):
        """Returns a red string."""
        return ircutils.mircColor(string, 'red')

    def _yellow(self, string):
        """Returns a yellow string."""
        return ircutils.mircColor(string, 'yellow')

    def _green(self, string):
        """Returns a green string."""
        return ircutils.mircColor(string, 'green')

    def _teal(self, string):
        """Returns a teal string."""
        return ircutils.mircColor(string, 'teal')

    def _blue(self, string):
        """Returns a blue string."""
        return ircutils.mircColor(string, 'blue')

    def _orange(self, string):
        """Returns an orange string."""
        return ircutils.mircColor(string, 'orange')

    def _bold(self, string):
        """Returns a bold string."""
        return ircutils.bold(string)

    def _ul(self, string):
        """Returns an underline string."""
        return ircutils.underline(string)

    def _bu(self, string):
        """Returns a bold/underline string."""
        return ircutils.bold(ircutils.underline(string))

    #####################################
    # GOOGLE FUNCTIONS - used ig before #
    # (later if initial breaks?) Code   #
    # from QSB - http://bit.ly/110PRAf  #
    #####################################

    def _XEncodeReplace(self, match_object):
        """Convert \\xnn encoded characters.

        Converts \\xnn encoded characters into their Unicode equivalent.

        Args:
        match: A string matched by an re pattern of '\\xnn'.

        Returns:
        A single character string containing the Unicode equivalent character
        (always within the ASCII range) if match is of the '\\xnn' pattern,
        otherwise the match string unchanged.
        """

        try:
            char_num_string = match_object.group(1)
            char_num = int(char_num_string, 16)
            replacement = chr(char_num)
            return replacement
        except:
            return match_object

    def _googlequote(self, symbol):
        """This uses a JSONP-like url from Google to return a stock Quote. (From QSB)"""

        # build url.
        url = 'https://www.google.com/finance/info?infotype=infoquoteall&q='
        url += utils.web.urlquote(symbol)
        # process "JSON".
        html = self._httpget(url)
        if not html:
            self.log.error("_googlequote: Failed on Google Quote for {0}".format(symbol))
            return None
        # \xnn problems.
        pattern = re.compile('\\\\x(\d{2})')
        # dict container for output.
        e = {}
        # iterate over each line. have to split on \n because html = str object.
        for line in html.split('\n'):  # splitlines() ?
            line = line.rstrip('\n')
            line_parts = line.split(': ')
            if len(line_parts) == 2:
                key, value = line_parts  # list back to string.
                key = key.replace(',"', '').replace('"','').strip()  # clean up key.
                value = value.replace('"', '')  # clean up value.
                value = pattern.sub(self._XEncodeReplace, value)  # Perform the \xnn replacements here.
                if (key and value and value != ""):  # if we still have, inject.
                    e[key] = value
        # with dict above, we construct a string conditionally.
        # {'c': '-6.77', 'ccol': 'chr', 'e': 'INDEXSP', 'name': 'S&P 500', 'lo': '1,755.72', 'lo52': '1,343.35',
        # 'l': '1,756.54', 'vo': '624.29M', 's': '0', 'lt': 'Oct 31, 4:30PM EDT', 't': '.INX', 'hi52': '1,775.22',
        # 'hi': '1,768.53', 'cp': '-0.38', 'type': 'Company', 'id': '626307', 'l_cur': '1,756.54', 'op': '1,763.24'}
        # {'el': '22.56', 'eccol': 'chr', 'ec': '-0.01', 'vo': '33.24M', 'eps': '1.86', 'inst_own': '75%', 'cp': '0.02',
        # CSCO
        # 'id': '99624', 'hi52': '26.49', 'lo': '22.40', 'yld': '3.01', 'shares': '5.38B', 'avvo': '39.16M',
        # 'lt': 'Nov 1, 4:00PM EDT', 'pe': '12.13', 'type': 'Company', 'elt': 'Nov 1, 4:43PM EDT',
        # 'beta': '1.26', 'hi': '22.68', 'ecp': '-0.02', 'l_cur': '22.56', 'c': '+0.01', 'e': 'NASDAQ',
        # 'name': 'Cisco Systems, Inc.', 'mc': '121.50B', 'lo52': '16.68', 'l': '22.57', 's': '2', 't': 'CSCO',
        # 'el_cur': '22.56', 'div': '0.17', 'ccol': 'chg', 'op': '22.66'}
        #The feed can return some or all of the following
        #keys:
        #
        #  avvo    * Average volume (float with multiplier, like '3.54M')
        #  beta    * Beta (float)
        #  c       * Amount of change while open (float)
        #  ccol    * (unknown) (chars)
        #  cl        Last perc. change
        #  cp      * Change perc. while open (float)
        #  e       * Exchange (text, like 'NASDAQ')
        #  ec      * After hours last change from close (float)
        #  eccol   * (unknown) (chars)
        #  ecp     * After hours last chage perc. from close (float)
        #  el      * After. hours last quote (float)
        #  el_cur  * (unknown) (float)
        #  elt       After hours last quote time (unknown)
        #  eo      * Exchange Open (0 or 1)
        #  eps     * Earnings per share (float)
        #  fwpe      Forward PE ratio (float)
        #  hi      * Price high (float)
        #  hi52    * 52 weeks high (float)
        #  id      * Company id (identifying number)
        #  l       * Last value while open (float)
        #  l_cur   * Last value at close (like 'l')
        #  lo      * Price low (float)
        #  lo52    * 52 weeks low (float)
        #  lt        Last value date/time
        #  ltt       Last trade time (Same as "lt" without the data)
        #  mc      * Market cap. (float with multiplier, like '123.45B')
        #  name    * Company name (text)
        #  op      * Open price (float)
        #  pe      * PE ratio (float)
        #  t       * Ticker (text)
        #  type    * Type (i.e. 'Company')
        #  vo      * Volume (float with multiplier, like '3.54M')

        output = "{0} ({1})".format(self._bu(e['t']), self._bold(e['name']))
        if 'l' in e:  # bold last.
            output += "  last: {0}".format(self._bold(e['l']))
        if ('c' in e and 'cp' in e):  # color percent changes.
            output += u" {0} ({1})".format(self._colorify(e['c']), self._colorify(e['cp'], perc=True))
        if ('lo' in e and 'hi' in e):  # bold low and high daily ranges.
            output += "  Daily range:({0}-{1})".format(self._bold(e['lo']),self._bold(e['hi']))
        if ('lo52' in e and e['lo52'] != "0" and 'hi52' in e and e['hi52'] != "0"):
            output += "  Yearly range:({0}-{1})".format(self._bold(e['lo52']),self._bold(e['hi52']))
        if ('vo' in e and e['vo'] != "0"):  # if we have volume, millify+orange.
            output += "  Volume: {0}".format(self._orange(e['vo']))
        if 'lt' in e:  # last trade.
            output += "  Last trade: {0}".format(self._blue(e['lt']))
        # now return the string.
        return output

    ###########################
    # GOOGLE PUBLIC FUNCTIONS #
    ###########################

    def googlequote(self, irc, msg, args, optsymbols):
        """<symbols>

        Display's a quote from Google for a stock.
        Can specify multiple stocks. Separate by a space.
        Ex: GOOG AAPL (max 5)
        """

        # make symbols upper, split on space or ,.
        symbols = self._splitinput(optsymbols.upper(), [' ', ','])
        for symbol in symbols[0:5]:  # max 5.
            output = self._googlequote(symbol)
            if output:  # if we get a quote back.
                self._out(irc, msg, output)
            else:  # something went wrong looking up quote.
                self._out(irc, msg, "ERROR fetching Google quote for: {0}. Unknown symbol?".format(symbol))

    googlequote = wrap(googlequote, ['text'])

    def intlindices(self, irc, msg, args):
        """
        Displays international market indicies from various countries outside the US.
        """

        indices = ['HSI', 'SX5E', 'PX1', 'OSPTX', 'SENSEX', 'XJO', 'UKX', 'NI225', '000001']
        for index in indices:  # iterate through quotes above.
            output = self._googlequote(index)
            if output:  # if we get a quote back.
                self._out(irc, msg, output)
            else:  # if something breaks.
                self._out(irc, msg, "ERROR fetching Google quote for: {0}".format(index))

    intlindices = wrap(intlindices)

    def indices(self, irc, msg, args):
        """
        Displays the three major indices for the US Stock Market:
        Dow Jones Industrial Average, NASDAQ, and S&P500
        """

        indices = ['.DJI', '.IXIC', '.INX']
        for index in indices:  # iterate through quotes above.
            output = self._googlequote(index)
            if output:  # if we get a quote back.
                self._out(irc, msg, output)
            else:  # if something breaks.
                self._out(irc, msg, "ERROR fetching Google quote for: {0}".format(index))

    indices = wrap(indices)

    ###################
    # YAHOO FUNCTIONS #
    ###################

    def _yqlquery(self, query):
        """Perform a YQL query for stock quote and return."""

        # base params.
        YQL_URL = "http://query.yahooapis.com/v1/public/yql?"
        YQL_PARAMS = {"q":query,
                      "format":"json",
                      "env":"store://datatables.org/alltableswithkeys"}
        # build and fetch url.
        url = YQL_URL + utils.web.urlencode(YQL_PARAMS)
        html = self._httpget(url)
        if not html:  # something broke.
            self.log.error("_yqlquery: Failed on YQLQuery for {0}".format(query))
            return None
        else:  # return YQL query.
            return html.decode('utf-8')

    def _yahoocurrency(self, symbol):
        """Internal Yahoo Currency function that wraps YQL."""

        # execute YQL and return.
        result = self._yqlquery("SELECT * from yahoo.finance.xchange where pair = '%s'" % symbol)
        if not result:  # returns None from yqlquery.
            self.log.error("_yahoocurrency: Failed on YQLQuery for {0}".format(symbol))
            return None
        # Try and load json. Do some checking. first check count.
        data = json.loads(result)
        if data['query']['count'] == 0:
            self.log.error("_yahoocurrency: ERROR: Yahoo Quote count 0 executing on {0}".format(symbol))
            self.log.error("_yahoocurrency: data :: {0}".format(data))
            return None
        result = data['query']['results']['rate']  # simplify dict
        # make sure symbol is valid
        if result['Rate'] == "0.00":
            self.log.error("_yahoocurrency: ERROR looking up currency {0}".format(symbol))
            return None
        # now that all is good, process results into dict for output.
        e = {}
        for each in result:
            e[each] = result.get(each)
        # now that we have a working currency translation, create output string.
        dt = "{0} {1}".format(e['Date'], e['Time'])  # create dtstring
        dt = self._timedelta(dt)  # convert to relative time.
        output = "{0} :: Rate: {1} | Bid: {2} | Ask: {3} | {4}".format(self._red(e['Name']), self._bold(e['Rate']), self._bold(e['Bid']), self._bold(e['Ask']), dt)
        # return.
        return output.encode('utf-8')

    def _timedelta(self, date):
        """Take a last trade date from Yahoo and return a relative date."""

        dt = datetime.datetime.strptime(date, '%m/%d/%Y %H:%M%p')  # 7/31/2013 5:55pm
        dt = pytz.timezone("US/Eastern").localize(dt)  # all times in "Eastern"
        utc_dt = pytz.utc.normalize(dt.astimezone(pytz.utc))  # go to UTC.

        # do the math.
        d = datetime.datetime.utcnow().replace(tzinfo = pytz.utc) - utc_dt
        # now parse and return.
        if d.days:
            rel_time = "%sd ago" % d.days
        elif d.seconds > 3600:
            rel_time = "%sh ago" % (d.seconds / 3600)
        elif 60 <= d.seconds < 3600:
            rel_time = "%sm ago" % (d.seconds / 60)
        else:
            rel_time = "%ss ago" % (d.seconds)
        return rel_time

    def _yahooquote(self, symbol):
        """Internal Yahoo Quote function that wraps YQL."""

        # execute YQL and return.
        result = self._yqlquery("SELECT * FROM yahoo.finance.quotes where symbol ='%s'" % symbol)
        if not result:  # returns None from yqlquery.
            self.log.error("_yahooquote: Failed on YQLQuery for {0}".format(symbol))
            return None
        # Try and load json. Do some checking. first check count.
        data = json.loads(result)
        if data['query']['count'] == 0:
            self.log.error("_yahooquote: ERROR: Yahoo Quote count 0 executing on {0}".format(symbol))
            self.log.error("_yahooquote: data :: {0}".format(data))
            return None
        result = data['query']['results']['quote']  # simplify dict
        # make sure symbol is valid
        if result['ErrorIndicationreturnedforsymbolchangedinvalid']:
            self.log.error("_yahooquote: ERROR looking up Yahoo symbol {0}".format(symbol))
            return None
        # now that all is good, process results into dict for output.
        e = {}
        for each in result:
            e[each] = result.get(each)
        # now that we have a working symbol, we'll need conditionals per.
        output = "{0} ({1})".format(self._bu(e['symbol']), self._bold(e['Name']))
        if e['LastTradePriceOnly']:
            output += "  last: {0}".format(self._bold(e['LastTradePriceOnly']))
        if e['Change'] and e['ChangeinPercent']:
            output += u" {0} ({1})".format(self._colorify(e['Change']), self._colorify(e['ChangeinPercent'], perc=True))
        if e['DaysLow'] and e['DaysHigh'] and e['DaysLow'] != "0.00" and e['DaysHigh'] != "0.00":
            output += "  Daily range:({0}-{1})".format(self._bold(e['DaysLow']), self._bold(e['DaysHigh']))
        if e['YearLow'] and e['YearHigh'] and e['YearLow'] != "0.00" and e['YearHigh'] != "0.00":
            output += "  Yearly range:({0}-{1})".format(self._bold(e['YearLow']),self._bold(e['YearHigh']))
        if e['Volume'] and e['Volume'] != "0":
            output += "  Volume: {0}".format(self._orange(self._millify(float(e['Volume']))))
        if e['MarketCapitalization']:
            output += "  MarketCap: {0}".format(self._blue(e['MarketCapitalization']))
        if e['PERatio']:
            output += "  P/E: {0}".format(self._teal(e['PERatio']))
        if e['LastTradeDate'] and e['LastTradeTime']:
            timestamp = "{0} {1}".format(e['LastTradeDate'], e['LastTradeTime'])
            timestamp = self._timedelta(timestamp)  # convert to relative time.
            output += "  Last trade: {0}".format(self._blue(timestamp))
        # now return the string.
        return output.encode('utf-8')

    ##########################
    # YAHOO PUBLIC FUNCTIONS #
    ##########################

    def yahooquote(self, irc, msg, args, optsymbols):
        """<symbols>

        Display's a quote from Yahoo for a stock.
        Can specify multiple stocks. Separate by a space.
        Ex: GOOG AAPL (max 5)
        """

        # make symbols upper, split on space or ,.
        symbols = self._splitinput(optsymbols.upper(), [' ', ','])
        for symbol in symbols[0:5]:  # limit on 5.
            output = self._yahooquote(symbol)
            if output:  # if we have output.
                self._out(irc, msg, output)
            else:  # if we don't have output.
                self._out(irc, msg, "ERROR fetching Yahoo quote for: {0}".format(symbol))

    yahooquote = wrap(yahooquote, ['text'])

    def bonds(self, irc, msg, args):
        """
        Displays the US Treasury Bonds Rates.
        """

        indices = ['^FVX', '^TNX', '^TYX']
        for index in indices:  # iterate through quotes above.
            output = self._yahooquote(index)
            if output:  # if we get a quote back.
                self._out(irc, msg, output)
            else:  # if something breaks.
                self._out(irc, msg, "ERROR fetching Google quote for: {0}".format(index))

    bonds = wrap(bonds)

    def currency(self, irc, msg, args, optsymbols):
        """<symbols>

        Display's a quote from Yahoo for a currency.
        Can specify multiple currencies. Separate by a space.
        Ex: USDCAD GBPUSD (max 5)
        """

        # http://openexchangerates.org/api/currencies.json
        # make symbols upper, split on space or ,.
        symbols = self._splitinput(optsymbols.upper(), [' ', ','])
        for symbol in symbols[0:5]:  # limit on 5.
            output = self._yahoocurrency(symbol)
            if output:  # if we have output.
                self._out(irc, msg, output)
            else:  # if we don't have output.
                self._out(irc, msg, "ERROR fetching Yahoo currency for: {0}".format(symbol))

    currency = wrap(currency, ['text'])

    #########################
    # PUBLIC STOCK FRONTEND #
    #########################

    def stock(self, irc, msg, args, optsymbols):
        """<ticker symbol(s)>

        Returns stock information about <ticker>.
        Separate multiple SYMBOLs by spaces (Max 5).
        Ex: GOOG AAPL (max 5)
        """

        # make a list of symbols after splitting on space or ,.
        symbols = self._splitinput(optsymbols.upper(), [' ', ','])
        # process each symbol.
        for symbol in symbols[0:5]:  # enforce max 5.
            output = self._googlequote(symbol)  # try google fetch first.
            if not output:  # if we don't, try yahoo.
                output = self._yahooquote(symbol)
                if not output:  # if not yahoo, report error.
                    self._out(irc, msg, "ERROR: I could not fetch a quote for: {0}. Check that the symbol is correct.".format(symbol))
                    continue
            # we'll be here if one of the quotes works. output.
            self._out(irc, msg, output)

    stock = wrap(stock, [('text')])

    ##########################################
    # FUTURES CONTRACTS INTERNAL/PUBLIC FUNC #
    # USES YAHOOQUOTE AFTER FIGURING OUT SYM #
    ##########################################

    def _futuresymbol(self, symbol):
        """This is a horribly inaccurate calculation method to determine the precise
        ticker symbol for a futures contract."""

        # k,v - symbol [prefix + exchange.]
        table = {'oil':['CL', 'NYM'],
                 'gold':['GC', 'CMX'],
                 'palladium':['PA', 'NYM'],
                 'platinum':['PL','NYM'],
                 'silver':['SI','CMX'],
                 'copper':['HG','CMX'],
                 'corn':['C', 'CBT'],
                 'oats':['O', 'CBT'],
                 'rice':['RR', 'CBT'],
                 'sbmeal':['SM', 'CBT'],
                 'sboil':['BO', 'CBT'],
                 'soybeans':['S', 'CBT']}
        # letter codes for months in oil/metals
        months = {'1':'F', '2':'G', '3':'H', '4':'J',
                  '5':'K', '6':'M', '7':'N', '8':'Q',
                  '9':'U', '10':'V', '11':'X', '12':'Z'}
        # now.
        now = datetime.datetime.now()
        # different calc, depending on the symbol.
        if symbol == "oil":
            if now.day > 20:  # 21st and on.
                mon = now + datetime.timedelta(days=40)
            else:  # 20th and before.
                mon = now + datetime.timedelta(days=30)
            # CONSTRUCT SYMBOL: table prefix + month code (letter) + YR + exchange suffix.
            contract = "{0}{1}{2}.{3}".format(table[symbol][0], months[str(mon.month)], mon.strftime("%y"), table[symbol][1])
        # palladium, copper, platinum, silver, palladium
        elif symbol in ['gold', 'silver', 'palladium', 'platinum', 'copper']:
            if now.day > 25:  # past 26th of the month.
                mon = now + datetime.timedelta(days=30)
            else:
                mon = now
            # CONSTRUCT SYMBOL: table prefix + month code (letter) + YR + exchange suffix.
            contract = "{0}{1}{2}.{3}".format(table[symbol][0], months[str(mon.month)], mon.strftime("%y"), table[symbol][1])
        # grains but only corn, oats, rice.
        elif symbol in ['corn', 'oats', 'rice']:
            # we have a specific table for these grains
            months = {'1':'H', '2':'H', '3':'H', '4':'K',
                      '5':'K', '6':'N', '7':'N', '8':'U',
                      '9':'U', '10':'Z', '11':'Z', '12':'Z'}
            if now.day > 13:  # past 26th of the month.
                mon = now + datetime.timedelta(days=30)
            else:
                mon = now
            # CONSTRUCT SYMBOL: table prefix + month code (letter) + YR + exchange suffix.
            contract = "{0}{1}{2}.{3}".format(table[symbol][0], months[str(mon.month)], mon.strftime("%y"), table[symbol][1])
        # soybeans + associated.
        elif symbol in ['sbmeal', 'soybeans', 'sboil']:
            months = {'1':'F', '2':'H', '3':'H', '4':'K',
                      '5':'K', '6':'N', '7':'N', '8':'Q',
                      '9':'U', '10':'X', '11':'X', '12':'Z'}
            if now.day > 13:  # past 26th of the month.
                mon = now + datetime.timedelta(days=30)
            else:
                mon = now
            contract = "{0}{1}{2}.{3}".format(table[symbol][0], months[str(mon.month)], mon.strftime("%y"), table[symbol][1])
        # finally, return contract.
        return contract

    def grains(self, irc, msg, args):
        """
        Display the latest quote for grains (corn, oats, rice).
        """

        for symbol in ['corn', 'oats', 'rice', 'sbmeal', 'sboil', 'soybeans']:
            symbol = self._futuresymbol(symbol)  # grab the proper symbol.
            output = self._yahooquote(symbol)
            if not output:  # if not yahoo, report error.
                self._out(irc, msg, "ERROR: I could not fetch a quote for: {0}. Check that the symbol is correct.".format(symbol))
            else:
                self._out(irc, msg, output)

    grains = wrap(grains)

    def oil(self, irc, msg, args):
        """
        Display the latest quote for Light Sweet Crude Oil (WTI).
        """

        symbol = self._futuresymbol('oil')  # get oil symbol.
        output = self._yahooquote(symbol)
        if not output:  # if not yahoo, report error.
            self._out(irc, msg, "ERROR: I could not fetch a quote for: {0}. Check that the symbol is correct.".format(symbol))
        else:
            self._out(irc, msg, output)

    oil = wrap(oil)

    def gold(self, irc, msg, args):
        """
        Display the latest quote for Gold Futures.
        """

        symbol = self._futuresymbol('gold')  # get gold symbol.
        output = self._yahooquote(symbol)
        if not output:  # if not yahoo, report error.
            self._out(irc, msg, "ERROR: I could not fetch a quote for: {0}. Check that the symbol is correct.".format(symbol))
        else:
            self._out(irc, msg, output)

    gold = wrap(gold)

    def metals(self, irc, msg, args):
        """
        Display the latest quote for metals (gold, silver, palladium, platinum, copper).
        """

        # do all metals @ once.
        for symbol in ['gold', 'silver', 'palladium', 'platinum', 'copper']:
            symbol = self._futuresymbol(symbol)
            output = self._yahooquote(symbol)
            if not output:  # if not yahoo, report error.
                self._out(irc, msg, "ERROR: I could not fetch a quote for: {0}. Check that the symbol is correct.".format(symbol))
            else:
                self._out(irc, msg, output)

    metals = wrap(metals)

    ###########################################################
    # MISC FINANCIAL FUNCTIONS FOR SYMBOL SEARCH/COMPANY NEWS #
    ###########################################################

    def _companylookup(self, optinput):
        """Internal function to lookup company ticker symbols."""

        # construct url
        url = "http://d.yimg.com/autoc.finance.yahoo.com/autoc?query=%s" % utils.web.urlquote(optinput)
        url += "&callback=YAHOO.Finance.SymbolSuggest.ssCallback"
        # try and fetch json.
        html = self._httpget(url)
        if not html:  # something broke.
            self.log.error("_companylookup: failed to get URL.")
            return None
        # decode
        html = html.decode('utf-8')
        # we need to mangle the JSONP into JSON here.
        html = html.replace("YAHOO.Finance.SymbolSuggest.ssCallback(", "").replace(")", "")
        # make sure the JSON is proper, otherwise return None.
        data = json.loads(html)
        results = data["ResultSet"]["Result"]
        if len (results) == 0:  # if we have no results, err.
            return None
        else:  # otherwise, return results. It's a list of dicts.
            # {u'typeDisp': u'Equity', u'name': u'Alcoa Inc.', u'symbol': u'AA', u'exchDisp': u'NYSE', u'type': u'S', u'exch': u'NYQ'}
            return results

    def symbolsearch(self, irc, msg, args, optinput):
        """<company name>

        Search for a stock symbol given company name.
        Ex: Google
        """

        results = self._companylookup(optinput)
        if not results:  # if we don't have any results.
            self._out(irc, msg, "ERROR: I did not find any symbols for: {0}".format(optinput))
            return
        # container for out.
        output = []
        # now iterate over and output each symbol/result.
        for r in results[0:5]:
            symbol = r.get('symbol').encode('utf-8')
            typeDisp = r.get('typeDisp').encode('utf-8')
            exch = r.get('exch').encode('utf-8')
            name = r.get('name').encode('utf-8')
            if symbol and typeDisp and exch and name:  # have to have all. display in a table.
                #output.append("{0:15} {1:12} {2:5} {3:40}".format(symbol, typeDisp, exch, name))
                output.append("{0} ({1}) {2} {3}".format(symbol, typeDisp, exch, name))
        # output as single line
        self._out(irc, msg, " | ".join(output))

    symbolsearch = wrap(symbolsearch, ['text'])

Class = Stock

# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=250:
