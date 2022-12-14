from discord.ext import commands
import discord

class Utility(commands.Cog):
   def __init__(self, bot):
      self.bot = bot

   @commands.command()
   async def help(self, ctx):
      embed = discord.Embed(description=(
         "All bot comands are listed below"), color=discord.Color(value=int("36393f", 16)))
      embed.set_author(
         name="StockCEO", icon_url="https://cdn.discordapp.com/avatars/1018489544292712518/eececb83f2bb0bb0b63c8129d0657678.png")
      embed.add_field(name=":chart_with_upwards_trend: Stocks",
                     value="`$stats [stock ticker]`\n\n`$graph [stock ticker]`\n`$graph [stock ticker] [duration]`", inline=False)
      embed.add_field(name=":stopwatch: Alerts",
                     value="`$addalert [stock ticker] [% change]`\n`$addalert [stock ticker] [target price]`\n\n`$removealert [stock ticker] [alert price]`\n`$removealerts [stock ticker]`\n`$clearalerts`\n\n`$viewalerts`", inline=False)
      embed.add_field(name=":wrench: Other", value="`$ping`", inline=False)

      await ctx.send(embed=embed)

   @commands.command()
   async def ping(self, ctx):
      before_ws = int(round(self.bot.latency * 1000, 1))
      await ctx.send(f"{before_ws}ms")

async def setup(bot):
   bot.remove_command("help")
   await bot.add_cog(Utility(bot))