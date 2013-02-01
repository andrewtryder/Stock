Supybot-Stock
=============

    Supybot plugin for displaying stock and financial information.

History

    This was my first big plugin. I had made a plugin because all of the Supybot plugins for displaying
    stock symbol / ticker information were screen scraping hacks. Moreoever, each one I tested was broken.

    I have methods for Google's stock API and Yahoo via YQL. At certain times, and depending on the symbol, one
    or the other works. So, I did two methods and linked them into a main command called "quote".

Instructions

    No setup. I suggest adding an alias from quote to stock.

Future

    I have plans to add in oil/metals prices as I have decyphered the futures contract method and have
    a crude method to implement this. Once you can get a reliable contract source, YQL has the quotes
    available from the exchanges.

Notes

    If you ran this plugin from the past, I had a much more comprehensive quant/info getopts for Yahoo.
    I found nobody was using this, so I removed.
