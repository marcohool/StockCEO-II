from discord.ext import commands
import yfinance as yf
import yfinance.shared as shared
import plotly.graph_objs as go
import mplfinance as fplt
import os
import discord

class Stocks(commands.Cog):
   def __init__(self, bot):
      self.bot = bot

   @commands.command()
   async def stats(self, ctx, ticker: str):
      data = yf.download(tickers = ticker, period='1y', interval='1d')

      # If ticker not found
      if list(shared._ERRORS.keys()):
         await ctx.send("Stock ticker not found")
         return

      # Get ticker      
      ticker = yf.Ticker(ticker)

      # Shorten description to one sentence
      desc = ticker.info.get('longBusinessSummary')
      
      # If ticker doesn't have longBusinessSumarry
      if desc:
         desc = desc.split('.').pop(0)
         # If company as Inc. in description, ignore full stop
         if desc.endswith("Inc"):
            desc += f". {ticker.info['longBusinessSummary'].split('.').pop(1)}."
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
            ylabel_lower='Volume',
            xrotation = 0,
            scale_padding={'left': 0, 'top': 0, 'right': 0.75, 'bottom': 0.2},
            ylabel= f"Share Price ({ticker.info['currency']})",
            savefig='./images/graph.png'
        )

      # Build Discord embedded message
      embed = discord.Embed(title=(f"{ticker.info['shortName']} | {ticker.info['currency']}"),
                              description = desc)

      # Send image to Discord
      # embed = discord.Embed(
      #       title=(f"{ticker.info['shortName']} | {ticker.info['currency']}"), color=discord.Color(value=int("7EE622", 16)))
      file = discord.File("images/graph.png", filename="graph.png")
      embed.set_image(url="attachment://graph.png")
      await ctx.send(file=file, embed=embed)


async def setup(bot):
   await bot.add_cog(Stocks(bot))