import discord
import hashlib
import sqlite3
import struct
from discord.ext import commands
from sys import argv

class FriendCode:
    """
    Stores and saves FC's in a database.
    """
    def __init__(self, bot):
        self.bot = bot
        print('Loading fc.sqlite')
        self.conn = sqlite3.connect('data/fc.sqlite')
        print('Addon "{}" loaded'.format(self.__class__.__name__))

    def __unload(self):
        print('Committing to fc.sqlite')
        self.conn.commit()
        print('Unloading fc.sqlite')
        self.conn.close()

    # based on https://github.com/megumisonoda/SaberBot/blob/master/lib/saberbot/valid_fc.rb
    def verify_fc(self, fc):
        fc = int(fc.replace('-', ''))
        if fc > 0x7FFFFFFFFF or fc < 0x0100000000:
            return None
        principal_id = fc & 0xFFFFFFFF
        checksum = (fc & 0xFF00000000) >> 32
        return (fc if hashlib.sha1(struct.pack('<L', principal_id)).digest()[0] >> 1 == checksum else None)

    def fc_to_string(self, fc):
        fc = str(fc).rjust(12, '0')
        return "{} - {} - {}".format(fc[0:4], fc[4:8], fc[8:12])

    @commands.command(pass_context=True)
    async def fcregister(self, ctx, fc):
        """Add your FC to the database."""
        fc = self.verify_fc(fc)
        if not fc:
            await self.bot.say("The code is invalid")
            return
        c = self.conn.cursor()
        rows = c.execute('SELECT * FROM friend_codes WHERE userid = ?', (int(ctx.message.author.id),))
        for row in rows:
            # if the user already has one, this prevents adding another
            await self.bot.say("Delete the old code using !fcdelete before adding a new one")
            return
        c.execute('INSERT INTO friend_codes VALUES (?,?)', (int(ctx.message.author.id), fc))
        await self.bot.say("{} FC added: {}".format(ctx.message.author.mention, self.fc_to_string(fc)))

    @commands.command(pass_context=True)
    async def fcfind(self, ctx, user):
        """Find another user's FC."""
        c = self.conn.cursor()
        member = ctx.message.mentions[0]
        rows = c.execute('SELECT * FROM friend_codes WHERE userid = ?', (int(ctx.message.author.id),))
        for row in rows:
            # assuming there is only one, which there should be
            rows_m = c.execute('SELECT * FROM friend_codes WHERE userid = ?', (int(member.id),))
            for row_m in rows_m:
                await self.bot.say("FC {} to {}".format(member.mention, self.fc_to_string(row_m[1])))
                try:
                    await self.bot.send_message(member, "{} asked you for your FC, their FC is {}.".format((ctx.message.author), self.fc_to_string(row[1])))
                except discord.errors.Forbidden:
                    pass  # don't fail in case user has DMs disabled for this server, or blocked the bot
                return
            await self.bot.say("This user has no FC registered")
            return
        await self.bot.say("You need to register your FC using !fcregister before searching for others")

    @commands.command(pass_context=True)
    async def fcdelete(self, ctx):
        """Delete your FC"""
        c = self.conn.cursor()
        c.execute('DELETE FROM friend_codes WHERE userid = ?', (int(ctx.message.author.id),))
        await self.bot.say("FC deleted")

    @commands.command()
    async def fctest(self, fc):
        fc = self.verify_fc(fc)
        if fc:
            await self.bot.say(self.fc_to_string(fc))
        else:
            await self.bot.say("Code is invalid, try again")

def setup(bot):
    bot.add_cog(FriendCode(bot))
