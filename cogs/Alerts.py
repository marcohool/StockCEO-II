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

      # Set variables
      negativeChange = False
      priceGiven = True
      currentPrice = int(stock.info.get('regularMarketPrice'))

      # Acknowledge and remove '-' or '+' from difference string
      if difference[0] == '-' or difference[0] == '+':
         priceGiven = False
         negativeChange = difference[0] == '-'
         difference = difference[1:]
      
      # Remove '%' char if included
      if difference[-1] == '%':
         priceGiven = False
         difference = difference[:-1]

      # Validate difference is a number
      if not difference.isnumeric():
         await ctx.send("Please enter a valid number for the difference")
         return
      
      # If direct price is given, check it lies in boundary +- 25%
      if priceGiven:
         if currentPrice*1.25 < int(difference) or currentPrice*0.75 > int(difference):
            await ctx.send("The maximum difference to set an alert for is +/- 25%")
            return
         else:
            targetPrice = int(difference)

      # Else if % change is given
      else:
       # Validate range difference
         if int(difference) > 25:
            await ctx.send("The maximum difference to set an alert for is +/- 25%")
            return
         else:
            # Calculate target price
            if negativeChange:
               targetPrice = int(currentPrice) * (1 - (int(difference)/100))
            else:
               targetPrice = int(currentPrice) * (1 + (int(difference)/100))
      
      # Round to 2 d.p.
      targetPrice = round(targetPrice, 3)

      # Insert alert into database
      connection = getDBConnection()
      with connection:
         with connection.cursor() as cursor:
            sql = f"INSERT INTO alerts (stock_ticker, set_price, target_price, user_id, channel_id) VALUES (%s, %s, %s, %s, %s)"
            cursor.execute(sql, (ticker, difference, targetPrice, ctx.author.id, ctx.channel.id))
            connection.commit()
      
      # Send alert added message
      await ctx.send(f"Alert added for {ticker.upper()}, you will be notifed once the price hits {formatNumb(targetPrice)} {stock.info.get('currency')}")

   @commands.command()
   async def viewAlerts(self, ctx):

      connection = getDBConnection()

      # Search database
      with connection:
         with connection.cursor() as cursor:
            sql = f"SELECT stock_ticker, target_price FROM alerts WHERE user_id = %s"
            cursor.execute(sql, ctx.author.id)
            results = cursor.fetchall()
            
      # If no alerts retreived
      if cursor.rowcount == 0:
         await ctx.send("You have no alerts set.\n\nYou can add alerts by using the command `$addalert [stock ticker] [% change]`")
         return
      
      # Get results
      resultsMessage = ""
      for result in results:
         ticker = yf.Ticker(result.get('stock_ticker'))
         resultsMessage += f"\n{ticker.info.get('shortName')} ({result.get('stock_ticker').upper()}) : **{formatNumb(result.get('target_price'))} {ticker.info.get('currency')}** *currently {formatNumb(round(ticker.info.get('regularMarketPrice'), 2))}*"
      
      await ctx.send(f"**Alerts for {ctx.author.mention}**\n{resultsMessage}\n\nYou will be tagged in the channel you created the alert when the stocks reach their respective value.")

# Format large number into more readable value
def formatNumb(number):
   return "{:,}".format(number)

# Get connection object
def getDBConnection():

      # Open config file
      with open("./config.yml", "r", encoding="utf-8") as file:
         config = yaml.load(file, Loader=yaml.FullLoader)

      # Connect to database
      connection = pymysql.connect(host=config["DB-Host"],
         user=config["DB-User"],
         password=config["DB-Password"],
         database=config["DB-Name"],
         cursorclass=pymysql.cursors.DictCursor)
      
      # Return connection object
      return connection

async def setup(bot):
   await bot.add_cog(Alerts(bot))