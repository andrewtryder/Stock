# -*- coding: utf-8 -*-
###
# Copyright (c) 2013, spline
# All rights reserved.
###

# my libs
import string
import urllib
import urllib2
import json
import re
import math # for millify
# for google stockquote
try:
    import xml.etree.cElementTree as ElementTree
except ImportError:
    import xml.etree.ElementTree as ElementTree

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

    ####################
    # GOOGLE FUNCTIONS #
    ####################

    def _googlequote(self, symbol):
        """Return quote from Google."""

        url = "http://www.google.com/ig/api?stock=%s" % urllib.quote(symbol)
        try:
            request = urllib2.Request(url, headers={"Accept" : "application/xml"})
            u = urllib2.urlopen(request)
        except Exception, e:
            self.log.error("Error fetching Google stock quote opening {0} error {1}".format(url, e))
            return None

        tree = ElementTree.parse(u)
        document = tree.getroot()

        if document.find('finance') is None or document.tag != 'xml_api_reply':
            self.log.error("Something broke parsing {0}".format(url))
            return None
        if document.find("./finance/exchange").attrib['data'] == "UNKNOWN EXCHANGE":
            self.log.error("Error looking up symbol: {0}. Unknown symbol?".format(symbol))
            return None

        e = {}
        for elem in document.find('finance'):
            e[elem.tag] = elem.get('data', None)

        output = "{0} ({1})".format(self._bu(e['symbol']), self._bold(e['company']))
        if e['last']:
            output += "  last: {0}".format(self._bold(e['last']))
        if e['change'] and e['perc_change']:
            output += u" {0} ({1})".format(self._colorify(e['change']), self._colorify(e['perc_change'], perc=True))
        if e['low'] and e['high']:
            output += "  Daily range:({0}-{1})".format(self._bold(e['low']),self._bold(e['high']))
        if e['volume'] and e['volume'] != "0":
            output += "  Volume: {0}".format(self._orange(self._millify(float(e['volume']))))
        if e['trade_timestamp']:
            output += "  Last trade: {0}".format(self._blue(e['trade_timestamp']))

        return output

    ###########################
    # GOOGLE PUBLIC FUNCTIONS #
    ###########################

    def googlequote(self, irc, msgs, args, optsymbols):
        """<symbols>
        Display's a quote from Google for a stock.
        Can specify multiple stocks. Separate by a space. Ex: GOOG AAPL (max 5)
        """

        symbols = self._splitinput(optsymbols.upper(), [' ',','])
        for symbol in symbols[0:5]:
            output = self._googlequote(symbol)
            if output:
                irc.reply(output)
            else:
                irc.reply("ERROR fetching Google quote for: {0}. Unknown symbol?".format(symbol))

    googlequote = wrap(googlequote, ['text'])

    ##################################
    # GOOGLE PUBLIC MARKET FUNCTIONS #
    ##################################

    def intlindices(self, irc, msg, args):
        """
        Displays international market indicies.
        """

        indices = ['.HSI','SX5E','PX1','OSPTX','SENSEX','XJO','UKX','NI225','000001']
        for index in indices:
            output = self._googlequote(index)
            if output:
                irc.reply(output)
            else:
                irc.reply("ERROR fetching Google quote for: {0}".format(symbol))

    intlindices = wrap(intlindices)

    def indices(self, irc, msgs, args):
        """
        Displays the three major indices for the US Stock Market. Dow Jones Industrial Average, NASDAQ, and S&P500
        """

        indices = ['.DJI','.IXIC','.INX'] #'.HSI'] #,'NI225']
        for index in indices:
            output = self._googlequote(index)
            if output:
                irc.reply(output)
            else:
                irc.reply("ERROR fetching Google quote for: {0}".format(symbol))

    indices = wrap(indices)

    ###################
    # YAHOO FUNCTIONS #
    ###################

    def _yqlquery(self, query):
        """Perform and return YQL quote."""
        YQL_URL = "http://query.yahooapis.com/v1/public/yql?"
        YQL_PARAMS = {"q":query,
                    "format":"json",
                    "env":"store://datatables.org/alltableswithkeys"}

        try:
            request = urllib2.Request(YQL_URL+urllib.urlencode(YQL_PARAMS))
            u = urllib2.urlopen(request)
            return u.read()
        except Exception, e:
            self.log.error("Error fetching YQL {0} error {1}".format(url, e))
            return None

    def _yahooquote(self, symbol):
        """Internal Yahoo Quote function that wraps YQL."""

        # execute YQL and return.
        result = self._yqlquery("SELECT * FROM yahoo.finance.quotes where symbol ='%s'" % symbol)
        self.log.info(str(result))
        if not result:
            return None

        # Now that we have something, first check count.
        data = json.loads(result)
        if data['query']['count'] == 0:
            self.log.error("ERROR: Yahoo Quote count 0 executing on {0}".format(symbol))
            return None
        # simplify dict
        result = data['query']['results']['quote']
        # make sure symbol is valid
        if result['ErrorIndicationreturnedforsymbolchangedinvalid']:
            self.log.error("ERROR looking up Yahoo symbol {0}".format(symbol))
            return None

        # throw remainer into dict.
        e = {}
        for each in result:
            e[each] = result.get(each, None)

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
            output += "  P/E: {0}".format(e['PERatio'])
        #if e['StockExchange']:
        #    output += "  ex: {0}".format(self._teal(e['StockExchange']))
        #if e['LastTradeDate'] and e['LastTradeTime']:
        #    timestamp = e['LastTradeDate'] + " " + e['LastTradeTime']
        #    output += "  Last trade: {0}".format(self._blue(timestamp))

        return output

    ################
    # YAHOO PUBLIC #
    ################

    def yahooquote(self, irc, msg, args, optsymbols):
        """<symbols>
        Display's a quote from Yahoo for a stock.
        Can specify multiple stocks. Separate by a space. Ex: GOOG AAPL (max 5)
        """

        symbols = self._splitinput(optsymbols.upper(), [' ',','])
        for symbol in symbols[0:5]:
            output = self._yahooquote(symbol)
            if output:
                irc.reply(output)
            else:
                irc.reply("ERROR fetching Yahoo quote for: {0}".format(symbol))

    yahooquote = wrap(yahooquote, ['text'])

    #########################
    # PUBLIC STOCK FUNCTION #
    #########################

    def quote(self, irc, msg, args, optlist, optsymbols):
        """<ticker symbol(s)>
        Gets the information about the current price and change from the
        previous day of a given company (represented by a stock symbol).
        Separate multiple SYMBOLs by spaces (Max 5)
        """

        # setup args to manip output/fetching
        args = {'fundamentals':False, 'movingaverage':False, 'extra':False, 'info':False, 'quant':False}
        for (key, value) in optlist:
            if key:
                args[value] = True

        # make a list of symbols.
        symbols = self._splitinput(optsymbols.upper(), [' ', ','])

        # process each symbol
        for symbol in symbols[0:5]:
            output = self._googlequote(symbol)
            if not output:
                output = self._yahooquote(symbol)
                if not output:
                    irc.reply("ERROR: I could not find a quote for: {0}. Invalid symbol or service broken?".format(symbol))
                    return
            irc.reply(output)

    quote = wrap(quote, [getopts({'extra': '', 'fundamentals': '', 'movingaverage': '', 'info': '', 'quant': ''}), ('text')])

    #################################
    # MISC FRONTENDS FOR OIL/METALS #
    #################################

    def oil(self, irc, msg, args):
        """
        Display the price of oil.
        """

        irc.reply("I don't have a source.")

    oil = wrap(oil)

    ###########################################################
    # MISC FINANCIAL FUNCTIONS FOR SYMBOL SEARCH/COMPANY NEWS #
    ###########################################################

    def _companylookup(self, optinput):
        """
        Internal function to lookup company ticker symbols.
        """

        url = "http://d.yimg.com/autoc.finance.yahoo.com/autoc?query=%s&callback=YAHOO.Finance.SymbolSuggest.ssCallback" % utils.web.urlquote(optinput)
        try:
            request = urllib2.Request(url)
            u = urllib2.urlopen(request)
            response = str(u.read()).replace("YAHOO.Finance.SymbolSuggest.ssCallback(", "").replace(")","")
            data = json.loads(response)
            results = data.get("ResultSet").get("Result")
            if len(results) > 0:
                return results
            else:
                return None
        except Exception, e:
            self.log.error("Error opening {0} error {1}".format(url, e))
            return None

    def symbolsearch(self, irc, msg, args, optinput):
        """<company name>
        Look up company name for the given stock symbol.
        """

        results = self._companylookup(optinput)

        if not results or len(results) < 1:
            irc.reply("ERROR: I did not find any symbols for: {0}".format(optinput))
            return

        for r in results:
            symbol = r.get('symbol', None)
            typeDisp = r.get('typeDisp', None)
            exch = r.get('exch', None)
            name = r.get('name', None)
            if symbol and typeDisp and exch and name:
                irc.reply("{0:15} {1:12} {2:5} {3:35}".format(symbol, typeDisp, exch, name))

    symbolsearch = wrap(symbolsearch, ['text'])

Class = Stock

# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=350:
