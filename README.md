Supybot-Stock
=============

    Supybot plugin for displaying stock and financial information.

History

    This was my first big plugin. I had made a plugin because all of the Supybot plugins for displaying
    stock symbol / ticker information were screen scraping hacks.

    I decided to make my own.

    One big problem: while the data for quotes has become more liberated, there still is not some abundant API.
    Mainly, this has to do with the fact of the money invovled and how much quotes cost.

    I found Yahoo and Google "APIs", except each returns different information and also has different symbols.
    Many also want to know some of the simple quotes like oil, gold, etc. I figured out how to make a look-up
    table for doing these quotes.

Instructions

    No setup. Should work fine out of a 2.6+ setup.
    I suggest adding an alias from quote to stock:

    /msg <bot> Alias add stock quote


Notes

    If you ran this plugin from the past, I had a much more comprehensive quant/info getopts for Yahoo.
    I found nobody was using this, so I removed.

