from discord.ext import commands
import yfinance as yf
import pymysql
import yaml

class Alerts(commands.Cog):
   def __init__(self, bot):
      self.bot = bot

   @commands.command()
   async def addAlert(self, ctx, ticker = None, difference = None):
      
      # Validate if ticker argument is given
      if ticker is None:
         await ctx.send("Please enter a stock ticker")
         return

      # Validate if ticker exists
      stock = yf.Ticker(ticker)
      if stock.history(peroid="1d").empty:
         await ctx.send("Could not find the entered stock ticker")
         return
      
      # Validate if difference argument is given
      if difference is None:
         await ctx.send("Please enter the difference in price you want to set the alert for ($addalert aapl +5%")
         return
      
      # Acknowledge and remove '-' or '+' from difference string
      if difference[0] == '-' or difference[0] == '+':
         negativeChange = difference[0] == '-'
         difference = difference[1:]
      
      # Remove '%' char if included
      if difference[-1] == '%':
         difference = difference[:-1]

      # Validate difference is a number
      if not difference.isnumeric():
         await ctx.send("Please enter a valid number for the difference")
         return
      
      # Validate difference range
      if int(difference) > 25:
         await ctx.send("The maximum difference to set an alert for is +/- 25%")
         return

      # Calculate target price
      if negativeChange:
         targetPrice = int(stock.info.get('regularMarketPrice')) * (1 - (int(difference)/100))
      else:
         targetPrice = int(stock.info.get('regularMarketPrice')) * (1 + (int(difference)/100))

      # Open config file
      with open("./config.yml", "r", encoding="utf-8") as file:
         config = yaml.load(file, Loader=yaml.FullLoader)

      # Connect to database
      connection = pymysql.connect(host=config["DB-Host"],
         user=config["DB-User"],
         password=config["DB-Password"],
         database=config["DB-Name"],
         cursorclass=pymysql.cursors.DictCursor)

      # Insert alert into database
      with connection:
         with connection.cursor() as cursor:
            sql = f"INSERT INTO alerts (stock_ticker, set_price, target_price, user_id, channel_id) VALUES (%s, %s, %s, %s, %s)"
            cursor.execute(sql, (ticker, difference, targetPrice, ctx.author.id, ctx.channel.id))
            connection.commit()
      
      await ctx.send(f"Alert added for {ticker}, you will be notifed once the price hits {targetPrice}")

async def setup(bot):
   await bot.add_cog(Alerts(bot))