from discord.ext import commands
import yfinance as yf
import yfinance.shared as shared
import plotly.graph_objs as go
import mplfinance as fplt
import math
import discord

class Stocks(commands.Cog):
   def __init__(self, bot):
      self.bot = bot

   # Display statistics & 1 month price history candlestick chart of requested stock 
   @commands.command()
   async def stats(self, ctx, ticker = None):
      
      # Generate past 1 year graph image for ticker
      try:
         ticker = generateGraph(ticker, "1y")
      except TickerException:
         await ctx.send("Invalid ticker")
         return
      except ParameterException:
         await ctx.send("No ticker selected\n\nUse the command in the format `$graph [ticker] [(optional) period]`")
         return
      
      # Get long description for ticker
      desc = ticker.info.get('longBusinessSummary')
   
      # Shorten description to one sentence
      if desc:
         desc = desc.split('.').pop(0)
         # If company as Inc. in description, ignore full stop
         if desc.endswith("Inc"):
            desc += f". {ticker.info['longBusinessSummary'].split('.').pop(1)}."
      # If ticker doesn't have longBusinessSumarry, use description
      else:
         desc = ticker.info['description']

      # Get formatted market cap
      marketCap = ticker.info.get('marketCap')
      if marketCap:
         marketCap = format(ticker.info.get('marketCap'))

      # Build Discord embedded message
      embed = discord.Embed(title=(f"{ticker.info['shortName']} | {ticker.info['currency']}"),
                              description = desc)
      embed.add_field(name="Price", value=(ticker.info.get('regularMarketPrice')), inline=True)
      embed.add_field(name="Open", value=ticker.info.get('open'), inline=True)
      embed.add_field(name="Close", value=ticker.info.get('previousClose'), inline=True)
      embed.add_field(name="Day Low", value=ticker.info.get('dayLow'), inline=True)
      embed.add_field(name="Day High", value=ticker.info.get('dayHigh'), inline=True)
      embed.add_field(name="Market Cap", value=marketCap, inline=True)
      embed.add_field(name="52-Wk High", value=ticker.info.get('fiftyTwoWeekHigh'), inline=True)
      embed.add_field(name="52-Wk Low", value=ticker.info.get('fiftyTwoWeekLow'), inline=True)
      embed.add_field(name="Pre-market Price", value=ticker.info.get('preMarketPrice'), inline=True)
      embed.set_image(url="attachment://graph.png")

      # Send embed with file
      file = discord.File("images/graph.png", filename="graph.png")
      await ctx.send(file=file, embed=embed)


   # Display candlestick chart of selected stock and period (default 1 month)
   @commands.command()
   async def graph(self, ctx, ticker = None, period = "1mo"):

      # Generate graph and catch any raised exceptions
      try:
         ticker = generateGraph(ticker, period)
      except TickerException:
         await ctx.send("Invalid ticker")
         return
      except PeriodException:
         await ctx.send("Invalid period - Valid periods are: `1d`, `5d`, `1mo`, `3mo`, `6mo`, `1y`, `ytd`, `2y`, `5y`, `10y` & `max`")
         return
      except ParameterException:
         await ctx.send("No ticker selected\n\nUse the command in the format `$graph [ticker] [(optional) period]`")
         return

      # Build and send embed
      embed = discord.Embed(title=(f"{ticker.info['shortName']} | {ticker.info['currency']}"))
      embed.set_image(url="attachment://graph.png")
      file = discord.File("images/graph.png", filename="graph.png")
      await ctx.send(file=file, embed=embed)

# Generate graph image given selected stock and period
def generateGraph(ticker, period):
   
   # If no ticker is provided raise exception
   if ticker is None:
      raise ParameterException

   # Set period and interval for graph generation
   periodIntervals = { "1d" : "1m", "5d" : "5m", "1mo" : "30m", "3mo" : "1h", "6mo" : "1d", "1y" : "1d", "ytd" : "1d", "2y" : "1d", "5y" : "1wk", "10y" : "1wk", "max" : "1wk" }

   # Get interval from given period
   interval = periodIntervals.get(period)
   
   # Raise exception if interval is invalid
   if interval is None:
      raise PeriodException
      
   # Download data for given ticker
   data = yf.download(tickers = ticker, period = period, interval = interval)

   # If ticker not found
   if list(shared._ERRORS.keys()):
      raise TickerException

   # Get ticker      
   ticker = yf.Ticker(ticker)

   # Set plot 
   fplt.plot(
         data,
         type='candle',
         style='yahoo',
         #mav = 4,
         figsize = (12, 9),
         volume = True,
         title= f"{ticker.info.get('shortName')} | {data.index[0].date()} to {data.index[-1].date()}",
         ylabel_lower='Volume',
         xrotation = 0,
         warn_too_much_data = 1000,
         scale_padding={'left': 0, 'top': 0, 'right': 0.75, 'bottom': 0.2},
         ylabel= f"Share Price ({ticker.info['currency']})",
         savefig='./images/graph.png'
      )

   return ticker

# Format large number into more readable value
def format(n):
   millnames = ['',' Thousand',' Million',' Billion',' Trillion']

   n = float(n)
   millidx = max(0,min(len(millnames)-1,
      int(math.floor(0 if n == 0 else math.log10(abs(n))/3))))

   return '{:.0f}{}'.format(n / 10**(3 * millidx), millnames[millidx])


# Add cog to bot
async def setup(bot):
   await bot.add_cog(Stocks(bot))


# Exception raised upon recieving an invalid ticker
class TickerException(Exception):
   pass

# Exception raised upon recieving an invalid period request
class PeriodException(Exception):
   pass

# Exception raised upon recieving invalid or missing parameters in command request
class ParameterException(Exception):
   pass