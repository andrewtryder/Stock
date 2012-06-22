# -*- coding: utf-8 -*-

import supybot.utils as utils
from supybot.commands import *
import supybot.plugins as plugins
import supybot.ircutils as ircutils
import supybot.callbacks as callbacks

import string

import urllib
import urllib2
import json

# for millify
import math

# for changing symbols
import re

# for google stockquote
from lxml import etree

# for Yahoo! Financial News
import feedparser

#libraries for time_created_at
import time
from datetime import tzinfo, datetime, timedelta


class Stock(callbacks.Plugin):
    threaded = True

    # change color of %/last depending on if ↑pos or ↓ neg - other chars ▾/▴ ▲ ▼
    # http://stackoverflow.com/questions/2701192/ascii-character-for-up-down-triangle-arrow-to-display-in-html
    def _colorify(self, string):
      if float(str(string).replace('%','')) > 0:
        string = ircutils.mircColor(string, 'green').replace('+', u'▴')
      else:
        string = ircutils.mircColor(string, 'red').replace('-', u'↓')
      return string

    # millify - a very nice/clean function from:
    # http://stackoverflow.com/questions/3154460/python-human-readable-large-numbers
    def _millify(self, n):
      millnames=['','k','M','B','T']
      millidx=max(0,min(len(millnames)-1, int(math.floor(math.log10(abs(n))/3.0))))
      return '%.1f%s'%(n/10**(3*millidx),millnames[millidx])

    # input splitter for seperators.
    def _splitinput(self, txt, seps):
      default_sep = seps[0]
      for sep in seps[1:]: 
        txt = txt.replace(sep, default_sep)
      return [i.strip() for i in txt.split(default_sep)]

    # relative_time
    def _time_created_at(self, s):
        """
        returns relative time string from now.
        """

        plural = lambda n: n > 1 and "s" or ""

        try:
            ddate = time.strptime(s, "%a, %d %b %Y %H:%M:%S GMT")[:-2]
        except ValueError:
            return "", ""

        created_at = datetime(*ddate, tzinfo=None)
        d = datetime.utcnow() - created_at

        if d.days:
            rel_time = "%s days ago" % d.days
        elif d.seconds > 3600:
            hours = d.seconds / 3600
            rel_time = "%s hour%s ago" % (hours, plural(hours))
        elif 60 <= d.seconds < 3600:
            minutes = d.seconds / 60
            rel_time = "%s minute%s ago" % (minutes, plural(minutes))
        elif 30 < d.seconds < 60:
            rel_time = "less than a minute ago"
        else:
            rel_time = "less than %s second%s ago" % (d.seconds, plural(d.seconds))
        return rel_time


    # generalized yql query and abstraction idea/code from: http://bit.ly/Ln47gt
    def _yql_query(self, query):
      YQL_URL = "http://query.yahooapis.com/v1/public/yql?"
      YQL_PARAMS = {"q":"",
                    "format":"json",
                    "env":"store://datatables.org/alltableswithkeys",
                   }
      try:
        YQL_PARAMS["q"] = query
        params = urllib.urlencode(YQL_PARAMS)
        string_result = urllib.urlopen(YQL_URL+params).read()
        result = json.loads(string_result)
        if result.has_key('query') and result["query"].has_key('results') and result["query"]["results"] and result["query"]["count"] >= 1:
          return_value = result["query"]["results"]
        else:
          self.log.info(result)
      except Exception, err:
        irc.reply(query)
      finally:
        pass

      return return_value

    def _googlequote(self, symbol):
      """<symbols>
      Fetch quotes from hidden Google Stock API. For indices.
      """

      url = "http://www.google.com/ig/api?stock=%s" % urllib2.quote(symbol)

      try:
        xml = etree.parse(url)
      except:
        irc.reply("Failed to open: %s" % (url))
        return

      root = xml.getroot()
      finance = root[0]

      data = dict()
      for elem in finance:
        data[elem.tag] = elem.attrib['data']

      if data['symbol']:
        pretty_symbol = data['symbol']
        company = data['company']
        last = data['last']
        high = data['high']
        low = data['low']
        volume = data['volume']
        change = data['change']
        perc_change = data['perc_change']
        trade_timestamp = data['trade_timestamp']
      else:
        irc.reply("Failed to find data for: %s" % (symbol))

      return pretty_symbol, company, last, high, low, volume, change, perc_change, trade_timestamp
    
    # function to handle google's output so we don't have to repeat.
    def _format_google_output(self, pretty_symbol, company, last, high, low, volume, change, perc_change, trade_timestamp):
      output = ircutils.underline(pretty_symbol) + " (" + ircutils.bold(company) + ")" + " last: " + ircutils.bold(last)
      output += " " + self._colorify(change) + " (" + self._colorify(perc_change) + ")"
      output += "  Daily range:(" + low + "-" + high + ")"
      output += "  Volume: " + ircutils.mircColor(self._millify(float(volume)), 'purple')
      output += "  Last trade: " + ircutils.mircColor(trade_timestamp, 'blue')
      return output
    
    # indices to cover the indexes
    def indices(self, irc, msgs, args):
      """
      Displays the three major indices for the US Stock Market. Dow Jones Industrial Average, NASDAQ, and S&P500
      """

      indices = ['.DJI','.IXIC','.INX']

      for index in indices:
        pretty_symbol, company, last, high, low, volume, change, perc_change, trade_timestamp = self._googlequote(index)
        output = self._format_google_output(pretty_symbol, company, last, high, low, volume, change, perc_change, trade_timestamp)
        irc.reply(output)
    
    indices = wrap(indices)
    
    # public frontend to googlequote.
    def googlequote(self, irc, msgs, args, symbols):
      """<symbols>
      Display's a quote from Google for a stock. Can specify multiple stocks. Separate by a space
      """

      symbols = self._splitinput(symbols, [' ',','])

      for symbol in symbols:
        pretty_symbol, company, last, high, low, volume, change, perc_change, trade_timestamp = self._googlequote(symbol)
        output = self._format_google_output(pretty_symbol, company, last, high, low, volume, change, perc_change, trade_timestamp)
        irc.reply(output)

    googlequote = wrap(googlequote, ['text'])

    def _googleShorten(self, url):
      """<url>
      Shorten URL using google.
      """
      _gooApi = 'https://www.googleapis.com/urlshortener/v1/url'
      _headers = {'Content-Type' : 'application/json'}
      _data = {'longUrl' : utils.web.urlquote(url)}

      request = urllib2.Request(_gooApi,json.dumps(_data),_headers)
      response = urllib2.urlopen(request)
      response_data = response.read()
      shorturi = json.loads(response_data)['id']

      return shorturi

    def currency(self, irc, msg, args, currencies):
      """<CURCUR>
      Example: EURUSD (Euro to US Dollar)
      Yields currency exchange rates from one currency to another. 
      """

      currencies = self._splitinput(currencies, [' ',','])

      for currency in currencies:
        currency_query = "SELECT * from yahoo.finance.xchange WHERE pair in ('%s')" % currency  
        result = self._yql_query(currency_query)

        name = result['rate']['Name'] 

        currencycheck = currency + "=X"

        if name != currencycheck:
          rate = result['rate']['Rate']
          date = result['rate']['Date']
          time = result['rate']['Time']
          ask = result['rate']['Ask']
          bid = result['rate']['Bid']

          output = ircutils.bold(ircutils.underline(name)) + ": " 
          output += ircutils.mircColor(rate, 'red') + " "
          output += ircutils.bold(ircutils.underline("Ask")) + ": " + ask + " "
          output += ircutils.bold(ircutils.underline("Bid")) + ": " + bid + " "
          output += ircutils.bold(ircutils.underline("Time")) + ": " + ircutils.mircColor(date + " " + time, 'blue')

          irc.reply(output)
        else:
          irc.reply("Invalid currency conversion query: " + ircutils.bold(ircutils.underline(currency)))

    currency = wrap(currency, ['text'])


    def quote(self, irc, msg, args, opts, symbols):
        """<company symbol(s)>
        Gets the information about the current price and change from the
        previous day of a given company (represented by a stock symbol).
        Separate multiple SYMBOLs by spaces.

        Options: --fundamentals for fundamentals. --movingaverage for moving averages. --quant for quant options
        and --extra and --info for more options.
        """

        opts = dict(opts)
        Fundamentals,MovingAverage,Extra,Info,Quant = False, False, False, False, False

        if 'movingaverage' in opts:
          MovingAverage = True
        if 'extra' in opts:
          Extra = True
        if 'fundamentals' in opts:
          Fundamentals = True
        if 'info' in opts:
          Info = True
        if 'quant' in opts:
          Quant = True

        symbollist = self._splitinput(symbols, [' ', ','])

        for symbol in symbollist:
          stock_query = "SELECT * FROM yahoo.finance.quotes where symbol ='%s'" % symbol
          result = self._yql_query(stock_query)
          data = result['quote']

          #self.log.info(json.dumps(data, indent=4))
          
          company = data['Name']

          if company == symbol:
            irc.reply("No company found for: %s" % (symbol))
          else:
            symbol = str.upper(symbol)
            last = data['LastTradePriceOnly']
            high = data['DaysHigh']
            low = data['DaysLow']
            volume = data['Volume']
            market_cap = data['MarketCapitalization']
            change = data['Change']
            perc_change = data['ChangeinPercent'].replace('%','')
            LastTradeTime = data['LastTradeTime']
            LastTradeDate = data['LastTradeDate']
            yearhigh = data['YearHigh']
            yearlow = data['YearLow']


            # start output
            output = ircutils.underline(symbol) + " (" + ircutils.bold(company) + ")" + " last: " + ircutils.bold(last)

            # basic change/percent with color
            output += " " + self._colorify(change) + " (" + self._colorify(perc_change) + ")"

            # should we display daily high-low? 
            displayDailyHighLow = self.registryValue('displayDailyHighLow', msg.args[0])
            if displayDailyHighLow:
              if low != None and high != None:
                output += " Daily range: (" + low + "-" + high + ")"

            # should we display yearly high-low?
            displayYearlyHighLow = self.registryValue('displayYearlyHighLow', msg.args[0])
            if displayYearlyHighLow:
              output += " Yearly range: (" + yearlow + "-" + yearhigh + ")"

            if volume != None and volume != "0":
              output += "  Volume: " + ircutils.mircColor(self._millify(float(volume)), 'purple') 

            if market_cap != None:
              output += "  Market Cap: " + ircutils.mircColor(market_cap, 'orange')

            if LastTradeDate != None and LastTradeTime != None:
              output += "  Last trade: " + ircutils.mircColor(LastTradeDate + " " + LastTradeTime, 'blue')

            # finally output everything.
            irc.reply(output)

            # conditionals section

            if Fundamentals:
              symbol = str.upper(symbol)
              last = data['LastTradePriceOnly']
              pricesales = data['PriceSales']
              pricebook = data['PriceBook']
              peratio = data['PERatio']
              pegratio = data['PEGRatio']
              bookvalue = data['BookValue']
              eps = data['EarningsShare']

              # output time
              output = ircutils.underline(symbol) + " (" + ircutils.bold(company) + ")" + " :: "
              output += ircutils.bold(ircutils.underline("P/E:")) + " " + peratio + " "
              output += ircutils.bold(ircutils.underline("P/S:")) + " " + pricesales + " "
              output += ircutils.bold(ircutils.underline("P/B:")) + " " + pricebook + " "
              output += ircutils.bold(ircutils.underline("PE/G:")) + " " + pegratio + " "
              output += ircutils.bold(ircutils.underline("Bookvalue:")) + " " + bookvalue + " "
              output += ircutils.bold(ircutils.underline("EPS:")) + " " + eps + " "

              irc.reply(output)

            if MovingAverage:
              fiftyday = data['FiftydayMovingAverage']
              fiftyday_change = data['ChangeFromFiftydayMovingAverage']
              fiftyday_perc_change = data['PercentChangeFromFiftydayMovingAverage']
              twohundredday = data['TwoHundreddayMovingAverage']
              twohundredday_change = data['ChangeFromTwoHundreddayMovingAverage']
              twohundredday_perc_change = data['PercentChangeFromTwoHundreddayMovingAverage']

              output = ircutils.underline(symbol) + " (" + ircutils.bold(company) + ")" + " :: Moving Averages :: "
              output += ircutils.bold(ircutils.underline("50day:")) + " " + fiftyday + " " + self._colorify(fiftyday_change) + " (" + self._colorify(fiftyday_perc_change) + ") "
              output += ircutils.bold(ircutils.underline("200day:")) + " " + twohundredday + " " + self._colorify(twohundredday_change) + " (" + self._colorify(twohundredday_perc_change) + ")"

              irc.reply(output)
            if Extra:
              EBITDA = data['EBITDA']
              DividendYield = data['DividendYield']
              DividendShare = data['DividendShare']
              OneyrTargetPrice = data['OneyrTargetPrice']
              ShortRatio = data['ShortRatio']
              PriceEPSEstimateCurrentYear = data['PriceEPSEstimateCurrentYear']


              output = ircutils.underline(symbol) + " (" + ircutils.bold(company) + ") "

              # conditionals since some are empty.
              if EBITDA != None:
                output += ircutils.bold(ircutils.underline("EBITDA:")) + " " + EBITDA + " "
              if DividendShare != None and DividendShare != "0.00":
                output += ircutils.bold(ircutils.underline("Dividend Share:")) + " " + DividendShare + " "
              if DividendYield != None and DividendYield != "0.00":
                output += ircutils.bold(ircutils.underline("Dividend Yield:")) + " " + DividendYield + " "
              if OneyrTargetPrice != None:
                output += ircutils.bold(ircutils.underline("One Year Target Price:")) + " " + OneyrTargetPrice + " "
              if ShortRatio != None:
                output += ircutils.bold(ircutils.underline("Short Ratio:")) + " " + ShortRatio + " "
              if PriceEPSEstimateCurrentYear != None:
                output += ircutils.bold(ircutils.underline("Price EPS (Current Year):")) + " " + PriceEPSEstimateCurrentYear + " "

              irc.reply(output)

            if Info:
              company_query = "SELECT * from yahoo.finance.stocks WHERE symbol='%s'" % symbol
              companydata = self._yql_query(company_query)
              companydata = companydata['stock']

              try:
                start = companydata['start']
              except:
                start = None
              try:
                end = companydata['end']
              except:
                end = None
              try:
                sector = companydata['Sector']
              except:
                sector = None
              try:
                Industry = companydata['Industry']
              except:
                Industry = None
              try:
                FTE = companydata['FullTimeEmployees']
              except:
                FTE = None

              if start != None:
                output = ircutils.underline(symbol) + " (" + ircutils.bold(company) + ") "
                output += ircutils.bold(ircutils.underline("IPO:")) + " " + start + " "
              if end != None:
                output += ircutils.bold(ircutils.underline("End:")) + " " + end + " "
              if sector != None:
                output += ircutils.bold(ircutils.underline("Sector:")) + " " + sector + " "
              if Industry != None:
                output += ircutils.bold(ircutils.underline("Industry:")) + " " + Industry + " "
              if FTE != None:
                output += ircutils.bold(ircutils.underline("FullTime Employees:")) + " " + FTE + " "

              irc.reply(output)

            if Quant:
              quant_query = "SELECT * from yahoo.finance.quant WHERE symbol='%s'" % symbol
              quantdata = self._yql_query(quant_query)
              quantdata = quantdata['stock']
              ReturnOnEquity = quantdata['ReturnOnEquity']
              Stockholders = quantdata['Stockholders'].replace(',','')
              TotalAssets = quantdata['TotalAssets'].replace(',','')
              TrailingPE = quantdata['TrailingPE']
              EarningsGrowth = quantdata['EarningsGrowth']
              EbitMarge = quantdata['EbitMarge']

              output = ircutils.underline(symbol) + " (" + ircutils.bold(company) + ") "

              if ReturnOnEquity != None:
                output += ircutils.bold(ircutils.underline("Return On Equity:")) + " " + ReturnOnEquity + " "
              if Stockholders != None:
                output += ircutils.bold(ircutils.underline("Stockholders:")) + " " + self._millify(float(Stockholders)) + " "
              if TotalAssets != None:
                output += ircutils.bold(ircutils.underline("Total Assets:")) + " " + self._millify(float(TotalAssets)) + " "
              if TrailingPE != None:
                output += ircutils.bold(ircutils.underline("Trailing PE:")) + " " + TrailingPE + " "
              if EarningsGrowth != None:
                output += ircutils.bold(ircutils.underline("Earnings Growth:")) + " " + self._colorify(EarningsGrowth) + " "
              if EbitMarge != None:
                output += ircutils.bold(ircutils.underline("EBIT Margin:")) + " " + EbitMarge + " "

              irc.reply(output)
            # done quant

    quote = wrap(quote, [getopts({'extra': '', 'fundamentals': '', 'movingaverage': '', 'info': '', 'quant': ''}), ('text')])

    # metals fetcher.
    def metals(self, irc, msg, args):
      """
      Display the latest metal prices.
      """

      url = "http://drayah.no.de/metals/latest"
      metals_called = urllib.urlopen(url)
      json_response = metals_called.read()
      response_obj = json.loads(json_response)

      gold = response_obj['gold'].get('quote', None)
      silver = response_obj['silver'].get('quote', None)
      platinum = response_obj['platinum'].get('quote', None)
      palladium = response_obj['palladium'].get('quote', None)

      output = "Current metals prices (USD/oz): "

      if gold != None:
        output += ircutils.bold(ircutils.underline("Gold:"))
        output += " " + str(gold) + "  "

      if silver != None:
        output += ircutils.bold(ircutils.underline("Silver:"))
        output += " " + str(silver) + "  " 
      
      if platinum != None:
        output += ircutils.bold(ircutils.underline("Platinum:"))
        output += " " + str(platinum) + "  "
      
      if palladium != None:
        output += ircutils.bold(ircutils.underline("Palladium:"))
        output += " " + str(palladium) + "  "
      
      irc.reply(output)

    metals = wrap(metals)

    # company news
    def company(self, irc, msg, args, companyname):
      """<company name>
      Look up company name for the given stock symbol.
      """

      # {"symbol":"GOOG","name": "Google Inc.","exch": "NMS","type": "S","exchDisp":"NASDAQ","typeDisp":"Equity"},
      url = "http://d.yimg.com/autoc.finance.yahoo.com/autoc?query=%s&callback=YAHOO.Finance.SymbolSuggest.ssCallback" % (companyname)
      yahoo_called = urllib.urlopen(url)
      json_response = str(yahoo_called.read()).replace("YAHOO.Finance.SymbolSuggest.ssCallback(", "").replace(")","")
      response_obj = json.loads(json_response)
      results = response_obj.get("ResultSet").get("Result")

      #output = "{0:12} {1:16} {2:16} {3:16}".format("Symbol", "Name", "Type", "Exchange")

      for response in results:
        #if response.get("exch") == "NMS" or response.get("exch") == "NYQ" or response.get("exch") == "ASE":
        #{"symbol":"GLD","name": "SPDR Gold Shares","exch": "PCX","type": "E","typeDisp":"ETF"} 
          name = response.get("name").encode('utf-8')
          symbol = response.get("symbol").encode('utf-8')
          typeDisp = response.get("typeDisp").encode('utf-8')
          exchDisp = response.get("exch").encode('utf-8')

          output = "{0:9} {1:24} {2:16} {3:16}".format(symbol, name, typeDisp, exchDisp)
          irc.reply(output)

    company = wrap(company, ['text'])

    def companynews(self, irc, msg, args, symbol):
      """<symbol>
      Look up the latest news for a given stock symbol.
      Example: companynews GOOG
      """

      rss_url = 'http://finance.yahoo.com/rss/headline?s=%s' % symbol

      try:
        d = feedparser.parse(rss_url)
      except:
        self.log.warning('Failed to parse: %s' % (rss_url))
        irc.reply('Failed to parse: %s' % (rss_url))

      #if len(d.entries)  >= 1:
      #  self.log.warning('Failed to find any entries in: %s' % (rss_url))
      #  irc.reply('Failed to find any entries in: %s' % (rss_url))
      #  return

      entries = d['entries'][0:4] # max five.

      for entry in entries:
        title = entry['title']
        description = entry['description']

        # relative time and colorize
        pubDate = self._time_created_at(entry.published)
        pubDate = ircutils.mircColor(pubDate, 'light gray')

        # remove redirect, shorten and color.
        link = re.sub(r'^.*?/\*','',entry['link']).strip() # remove redirect.
        #link = self._googleShorten(link)
        link = ircutils.mircColor(link, 'blue')

        output = title
        output += " " + link
        output += " " + pubDate

        irc.reply(output)

    companynews = wrap(companynews, ['somethingWithoutSpaces'])

Class = Stock

# vim:set shiftwidth=2 softtabstop=2 expandtab textwidth=350:
