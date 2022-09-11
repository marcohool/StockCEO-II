from discord.ext import commands
import yfinance as yf
import yfinance.shared as shared
import plotly.graph_objs as go

class Stocks(commands.Cog):
   def __init__(self, bot):
      self.bot = bot

   @commands.command()
   async def stats(self, ctx, ticker: str):
      data = yf.download(tickers = ticker, period='30d', interval='60m')

      # If ticker not found
      if list(shared._ERRORS.keys()):
         await ctx.send("Stock ticker not found")
         return

      # Get stock name      
      ticker = yf.Ticker(ticker)

      # Get company name
      company = ticker.info['shortName']

      # Generate graph
      fig = go.Figure()

      # Candle sticks
      fig.add_trace(go.Candlestick(x = data.index, open = data['Open'], high = data['High'], low = data['Low'], close = data['Close'], name = "Market Data"))

      # Add titles
      fig.update_layout(dict(xaxis=dict(type="category")), title = company, yaxis_title = f"Stock Price ({ticker.info['currency']})")
      fig.update_xaxes(visible=False)

      # Show graph
      fig.show()


async def setup(bot):
   await bot.add_cog(Stocks(bot))