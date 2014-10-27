[![Build Status](https://travis-ci.org/reticulatingspline/Stock.svg?branch=master)](https://travis-ci.org/reticulatingspline/Stock)

# Limnoria plugin for displaying stocks and financial information

## Introduction

This was my first big plugin. I had made a plugin because all of the Supybot plugins for displaying
stock symbol / ticker information were screen scraping hacks.

I decided to make my own.

One big problem: while the data for quotes has become more liberated, there still is not some abundant API.
Mainly, this has to do with the fact of the money invovled and how much quotes cost.

I found Yahoo and Google "APIs", except each returns different information and also has different symbols.
Many also want to know some of the simple quotes like oil, gold, etc. I figured out how to make a look-up
table for doing these quotes.

NOTE: This is more of an information plugin. Real-time and better data, in the financial world, are only
available via private (paid and its not cheap $) APIs.

## Install

You will need a working Limnoria bot on Python 2.7 for this to work.

Go into your Limnoria plugin dir, usually ~/supybot/plugins and run:

```
git clone https://github.com/reticulatingspline/Stock
```

To install additional requirements, run:

```
pip install -r requirements.txt 
```

Next, load the plugin:

```
/msg bot load Stock
```

## Example Usage

```
<spline> @stock GOOG
<myybot> GOOG (Google Inc)  last: 544.49 ↓16.39 (↓2.92%)  Daily range:(544.05-565.13)  Yearly range:(502.80-604.83)  Volume: 3.08M  Last trade: Oct 10, 4:00PM EDT
<spline> @gold
<myybot> GCV14.CMX (Gold Oct 14)  last: 1221.40 ↓3.20 (↓0.26%)  Daily range:(1217.00-1223.50)  Volume: 186.0  Last trade: 1d ago
<spline> @indices
<myybot> .DJI (Dow Jones Industrial Average)  last: 16,544.10 ↓115.15 (↓0.69%)  Daily range:(16,543.91-16,757.60)  Yearly range:(14,806.39-17,350.64)  Volume: 136.37M  Lastrade: Oct 10, 4:28PM EDT
<mybott> .IXIC (NASDAQ Composite)  last: 4,276.24 ↓102.10 (↓2.33%)  Daily range:(4,276.24-4,380.51)  Yearly range:(3,650.03-4,610.57)  Volume: 2.76B  Last trade: Oct 10, 5:15PM EDT
<mybott> .INX (S&P 500)  last: 1,906.13 ↓22.08 (↓1.15%)  Daily range:(1,906.05-1,936.98)  Yearly range:(1,660.88-2,019.26)  Volume: 757.49M  Last trade: Oct 10, 4:28PM EDT
<spline> @oil
<myybot> CLX14.NYM (Crude Oil Nov 14)  last: 85.52 ↓0.25 (↓0.29%)  Daily range:(83.59-86.29)  Volume: 373.3k  Last trade: 1d ago
<spline> @yahooquote GOOG
<myybot>  GOOG (Google Inc.)  last: 544.49 ↓16.39 (↓2.92%)  Daily range:(544.05-565.1299)  Yearly range:(502.80-604.83)  Volume: 3.1M  MarketCap: 368.3B  P/E: 29.06  Last trade: 1d ago
```

## About

All of my plugins are free and open source. When I first started out, one of the main reasons I was
able to learn was due to other code out there. If you find a bug or would like an improvement, feel
free to give me a message on IRC or fork and submit a pull request. Many hours do go into each plugin,
so, if you're feeling generous, I do accept donations via PayPal below. 

I'm always looking for work, so if you are in need of a custom feature, plugin or something bigger, contact me via GitHub or IRC.

<form action="https://www.paypal.com/cgi-bin/webscr" method="post" target="_top">
<input type="hidden" name="cmd" value="_s-xclick">
<input type="hidden" name="encrypted" value="-----BEGIN PKCS7-----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-----END PKCS7-----
">
<input type="image" src="https://www.paypalobjects.com/en_US/i/btn/btn_donate_SM.gif" border="0" name="submit" alt="PayPal - The safer, easier way to pay online!">
<img alt="" border="0" src="https://www.paypalobjects.com/en_US/i/scr/pixel.gif" width="1" height="1">
</form>