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

   @commands.command()
   async def stats(self, ctx, ticker: str):
      
      # Set period and interval for graph generation
      period = "1y"
      interval = "1d"

      # Download data for given ticker
      data = yf.download(tickers = ticker, period = period, interval = interval)

      # If ticker not found
      if list(shared._ERRORS.keys()):
         await ctx.send("Stock ticker not found")
         return

      # Get ticker      
      ticker = yf.Ticker(ticker)

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

      # Set plot 
      fplt.plot(
            data,
            type='candle',
            style='yahoo',
            mav = 4,
            figsize = (12, 9),
            volume = True,
            title= f"{ticker.info.get('shortName')} | {data.index[0].date()} to {data.index[-1].date()}",
            ylabel_lower='Volume',
            xrotation = 0,
            scale_padding={'left': 0, 'top': 0, 'right': 0.75, 'bottom': 0.2},
            ylabel= f"Share Price ({ticker.info['currency']})",
            savefig='./images/graph.png'
        )

      # Build Discord embedded message
      embed = discord.Embed(title=(f"{ticker.info['shortName']} | {ticker.info['currency']}"),
                              description = desc)
      embed.add_field(name="Price", value=(ticker.info.get('regularMarketPrice')), inline=True)
      embed.add_field(name="Open", value=ticker.info.get('open'), inline=True)
      embed.add_field(name="Close", value=ticker.info.get('previousClose'), inline=True)
      embed.add_field(name="Day Low", value=ticker.info.get('dayLow'), inline=True)
      embed.add_field(name="Day High", value=ticker.info.get('dayHigh'), inline=True)
      embed.add_field(name="Market Cap", value=format(ticker.info.get('marketCap')), inline=True)
      embed.add_field(name="52-Wk High", value=ticker.info.get('fiftyTwoWeekHigh'), inline=True)
      embed.add_field(name="52-Wk Low", value=ticker.info.get('fiftyTwoWeekLow'), inline=True)
      embed.add_field(name="Pre-market Price", value=ticker.info.get('preMarketPrice'), inline=True)



      # Send image to Discord
      # embed = discord.Embed(
      #       title=(f"{ticker.info['shortName']} | {ticker.info['currency']}"), color=discord.Color(value=int("7EE622", 16)))
      file = discord.File("images/graph.png", filename="graph.png")
      embed.set_image(url="attachment://graph.png")
      await ctx.send(file=file, embed=embed)


# Format large number into more readable value
def format(n):
   millnames = ['',' Thousand',' Million',' Billion',' Trillion']

   n = float(n)
   millidx = max(0,min(len(millnames)-1,
      int(math.floor(0 if n == 0 else math.log10(abs(n))/3))))

   return '{:.0f}{}'.format(n / 10**(3 * millidx), millnames[millidx])


async def setup(bot):
   await bot.add_cog(Stocks(bot))