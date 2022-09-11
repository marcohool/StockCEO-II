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
      data = yf.download(tickers = ticker, period='30d', interval='1h')

      # If ticker not found
      if list(shared._ERRORS.keys()):
         await ctx.send("Stock ticker not found")
         return

      # Get stock name      
      ticker = yf.Ticker(ticker)

      # Get company name
      company = ticker.info['shortName']

      # Set plot 
      fplt.plot(
            data,
            type='candle',
            style='charles',
            mav = 4,
            figsize = (12, 9),
            volume = True,
            ylabel_lower='Volume',
            scale_padding={'left': -0.25, 'top': 0, 'right': 0.75, 'bottom': 0.05},
            ylabel= f"Share Price ({ticker.info['currency']})",
            savefig='./images/graph.png'
        )

      # Send image to Discord
      embed = discord.Embed(
            title=(f"{company} | {ticker.info['currency']}"), color=discord.Color(value=int("7EE622", 16)))
      file = discord.File("images/graph.png", filename="graph.png")
      embed.set_image(url="attachment://graph.png")
      await ctx.send(file=file, embed=embed)


async def setup(bot):
   await bot.add_cog(Stocks(bot))