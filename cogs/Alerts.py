from discord.ext import commands
import yfinance as yf
import pymysql
import yaml
import asyncio

class Alerts(commands.Cog):
   def __init__(self, bot):
      self.bot = bot

   @commands.command(aliases=['newAlert', 'setAlert'])
   async def addAlert(self, ctx, ticker = None, difference = None):
      
      # Validate if ticker argument is given
      if ticker is None:
         await ctx.reply("Please enter a stock ticker")
         return

      # Validate if ticker exists
      stock = yf.Ticker(ticker)
      if stock.history(peroid="1d").empty:
         await ctx.reply("Could not find the entered stock ticker")
         return
      
      # Ensure user has not surpased maximum alert limit
      noOfAlerts = len(getAllUserAlerts(ctx.author.id))
      
      if noOfAlerts >= 3:
         await ctx.reply("There is a maximum of 3 alerts per user. Otherwise my computer will crash")
         return
      
      # Validate if difference argument is given
      if difference is None:
         await ctx.reply("Please enter the difference in price you want to set the alert for (e.g. `$addalert aapl +5%`), or the exact price you want the stock to reach (e.g. `$addalert aapl 340`)")
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
         await ctx.reply("Please enter a valid number for the difference")
         return
      
      # If direct price is given, check it lies in boundary +- 25%
      if priceGiven:
         if currentPrice*1.25 < int(difference) or currentPrice*0.75 > int(difference):
            await ctx.reply("The maximum difference to set an alert for is +/- 25%")
            return
         else:
            targetPrice = int(difference)

      # Else if % change is given
      else:
       # Validate range difference
         if int(difference) > 25:
            await ctx.reply("The maximum difference to set an alert for is +/- 25%")
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
      await ctx.reply(f"Alert added for {ticker.upper()}, you will be notifed once the price hits {formatNumb(targetPrice)} {stock.info.get('currency')}")

   # Send message with all alerts a user has set
   @commands.command(aliases=['showAlerts', 'alerts'])
   async def viewAlerts(self, ctx):

      results = getAllUserAlerts(ctx.author.id)
            
      # If no alerts retreived
      if not results:
         await ctx.reply("You have no alerts set.\n\nYou can add alerts by using the command `$addalert [stock ticker] [% change]`")
         return
      
      # Get results
      resultsMessage = ""
      for result in results:
         ticker = yf.Ticker(result.get('stock_ticker'))
         resultsMessage += f"\n{ticker.info.get('shortName')} ({result.get('stock_ticker').upper()}) : **{formatNumb(result.get('target_price'))} {ticker.info.get('currency')}** *currently {formatNumb(round(ticker.info.get('regularMarketPrice'), 2))}*"
      
      await ctx.reply(f"Alerts for {ctx.author.mention}\n{resultsMessage}\n\nYou will be tagged in the channel you created the alert when the stocks reach their respective value.")

   # Delete specific or all of a users alerts
   @commands.command(aliases=['delete', 'deleteAlert', 'deleteAlerts', 'remove', 'removeAlerts', 'clearAlerts'])
   async def removeAlert(self, ctx, ticker = None, alertPrice = 0):

      # Check if message is from same user in same channel and y or n
      def check(msg):
         return msg.author == ctx.author and msg.channel == ctx.channel and msg.content.lower() in ['y', 'yes', 'n', 'no']

      # If no ticker selected, confirm delete all
      if ticker is None or ticker == "all":
         await ctx.reply("You are about to delete all your alerts. Are you sure you want to proceed? (Y/N)")

         # Await confirmation
         deleteAll = await getUserConfirmation(self, ctx)
         
         # Delete all alerts from user
         if deleteAll:
            deleteAlert(ctx.author.id)
            await ctx.reply("All your alerts have been deleted")
            return

      # If user has specified what ticker to remove
      else:

         # Get all of users alerts
         allUserAlerts = getAllUserAlerts(ctx.author.id)

         # Get user alerts of ticker provided
         relevantUserAlerts = []
         for alert in allUserAlerts:
            if alert['stock_ticker'] == ticker.lower():
               relevantUserAlerts.append(alert)

         # If no alerts retreived
         if not relevantUserAlerts:
            await ctx.reply(f"You have no alerts set for that ticker")
            return
         
         # If user has no specific price for alert selected
         elif alertPrice == 0:
            await ctx.reply(f"You are about to delete all alerts for {ticker.upper()}, are you sure you want to proceed? (Y/N)")
            
            # Await response 
            deleteSpecifcTicker = await getUserConfirmation(self, ctx)
            if deleteSpecifcTicker:
               # Delete all user alerts of provided ticker
               deleteAlert(ctx.author.id, ticker)
               await ctx.reply(f"All alerts for {ticker.upper()} have been deleted")
            
         # If user has provided the price and ticker symbol to be deleted
         else:
            if not any(alert['target_price'] == alertPrice for alert in relevantUserAlerts):
               await ctx.reply(f"No alerts found for {ticker.upper()} at that price. Use `$viewalerts` to see a list of your active alerts.")
               return 
            
            # Confirm remove chosen alert
            await ctx.reply(f"Are you sure you want to remove {ticker.upper()} at {alertPrice}? (Y/N)")
            
            # Await response 
            removeSpecificTickerPrice = await getUserConfirmation(self, ctx)
            
            if removeSpecificTickerPrice:
               # Delete chosen alert
               deleteAlert(ctx.author.id, ticker, alertPrice)
               await ctx.reply("Alert removed")

# Waits for user confirmation in channel and returns True or False based on user response
async def getUserConfirmation(client, ctx):

   # Verify message is sent by correct person and in correct channel
   def check(msg):
         return msg.author == ctx.author and msg.channel == ctx.channel and msg.content.lower() in ['y', 'yes', 'n', 'no']

   # Await response 
   try:
      msg = await client.bot.wait_for("message", check = check, timeout = 15)
   except asyncio.TimeoutError:
      return
   
   # If confirmation is yes return true
   if msg.content.lower() == "yes" or msg.content.lower() == 'y':
      return True

   # Else acknowledge message and return false
   await msg.add_reaction('\N{THUMBS UP SIGN}')
   return False

def getAllUserAlerts(user_id):

   # Get connection
   connection = getDBConnection()

   # Search database
   with connection:
      with connection.cursor() as cursor:
         sql = f"SELECT stock_ticker, target_price FROM alerts WHERE user_id = %s"
         cursor.execute(sql, user_id)
         return cursor.fetchall()

def deleteAlert(user_id, ticker = None, price = 0):

   connection = getDBConnection()

   # Delete all of users alerts
   if ticker is None and price == 0:
      sql = f"DELETE FROM alerts WHERE user_id = %s"
      executeTuple = (user_id)

   # Delete all of selected ticker
   elif ticker is not None and price == 0:
      sql = f"DELETE FROM alerts WHERE user_id = %s AND stock_ticker = %s"
      executeTuple = (user_id, ticker)
   
   # Delete specific alers
   elif ticker is not None and price != 0:
      sql = f"DELETE FROM alerts WHERE user_id = %s AND stock_ticker = %s AND target_price = %s"
      executeTuple = (user_id, ticker, price)

   with connection:
      with connection.cursor() as cursor:
         cursor.execute(sql, executeTuple)
         connection.commit()

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