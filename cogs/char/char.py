import discord
from discord.ext import commands
from .utils import checks
import aiohttp
import asyncio
import requests
import json
import re

LINK = "http://optc-db.github.io/common/data/"

def virgule(number : int):
    #Convert an int into a proper str (3000000 --> '3,000,000')

    resultat = str(number)
    compteur=0
    i=0
    while i != len(resultat):
        if compteur==3:
            resultat=resultat[:len(resultat)-i]+","+resultat[len(resultat)-i:]
            compteur=0
        else:
            compteur+=1
        i+=1
    return resultat



class Char:

    def __init__(self, bot):

        self.bot = bot




    async def choose_char(self, listNum : list, data : list, channel : discord.Channel, author : discord.Member):
        #Get the ID of a character basing on the a list of IDs

        msg = "```Markdown\n" + str(len(listNum)) + " results found!\n======================\n\n"

        nb = 0

        text = []


        for i in range(0, len(listNum)):
            text.append(json.loads(data[listNum[i]][:-1]))
            msg += "[" + str(i + 1) + "][" + text[i][0] + "][" + text[i][1] + "]\n"
            nb += 1

        msg += "#Please type the number of the character you want to get infos from!\n```"

        await self.bot.send_message(channel, msg)
        answer = await self.bot.wait_for_message(author = author, channel = channel, timeout = 60)
        if answer == None:
            return 0
        else:
            try:
                number = int(answer.content)
                if number > 0 and number < len(text) + 1:
                    return listNum[number - 1]
                else:
                    return -1
            except ValueError:
                return -2



    def embed_char(self, charNum : int, data : list):
        #Create an embed object using the ID of a character
        
        text = json.loads(data[charNum][:-1])

        
        colours = {"PSY" : "FFD700", "INT" : "DA70D6", "STR" : "FA8072", "QCK" : "87CEFA", "DEX" : "90EE90"}
        
        #Title (Name of the character)
        title = text[0]
        

        #Type
        
        color = discord.Colour(value = int(colours[text[1]], 16))
        
        embed = discord.Embed(title = title, colour = color)
        
        embed.set_author(name = "Beafantles", icon_url = "https://discordapp.com/api/users/151661401411289088/avatars/885f299c00c8765aad38b3ba50d6695d.jpg")
        #embed.set_footer(text = "Creator", icon_url = "https://discordapp.com/api/users/151661401411289088/avatars/885f299c00c8765aad38b3ba50d6695d.jpg")
        embed.set_thumbnail(url = "http://onepiece-treasurecruise.com/wp-content/uploads/f" + "0" * (4 - len(str(charNum))) + str(charNum) + ".png")
        embed.add_field(name = "Type", value = text[1], inline = True)

        #Classes
        if type(text[2]) == str:
            classes = text[2].replace('"', '')
        else:
            classes = ", ".join(text[2])
        embed.add_field(name = "Classes", value = classes, inline = True)

        #Stars
        embed.add_field(name = "Stars", value = text[3], inline = True)

        #Cost
        embed.add_field(name = "Cost", value = text[4], inline = True)

        #CMB
        embed.add_field(name = "CMB", value = text[5], inline = True)

        #Slots
        embed.add_field(name = "Slots", value = text[6], inline = True)

        #Max Level
        embed.add_field(name = "Max level", value = text[7], inline = True)

        #EXP to level Max
        embed.add_field(name = "EXP to Max", value = virgule(text[8]), inline = True)

        #LEVEL 1
        embed.add_field(name = "Level 1", value = virgule(text[9]) + " HP / " + virgule(text[10]) + " ATK / " + virgule(text[11]) + " RCV", inline = False)

        #LEVEL MAX
        embed.add_field(name = "Level " + str(text[7]), value = virgule(text[12]) + " HP / " + virgule(text[13]) + " ATK / " + virgule(text[14]) + " RCV", inline = False)

        infos = requests.get(LINK + "details.js")
        text = infos.text
        number = text.find('{')

        #We must convert some parts of the text to convert it into a dict object
        text = text[number+1:-3]
        text = text.replace('special:','"special":')
        text = text.replace('captain:','"captain":')
        text = text.replace('captainNotes:','"captainNotes":')
        text = text.replace('specialName:','"specialName":')
        text = text.replace('specialNotes:','"specialNotes":')
        text = text.replace('specialNote:','"specialNote":')
        text = text.replace('description:','"description":')
        text = text.replace('sailor:','"sailor":')
        text = text.replace('sailorNotes:','"sailorNotes":')

        #The following lines are here because there are some mistakes in the database
        text = text.replace(',\n    },\n','\n    },\n')
        text = text.replace(',\n        ]','\n        ]')
        text = text.replace('],\n            }',']\n            }')
        text = text.replace('], \n            }',']\n            }') #HEHEHE IS THAT A TROLL?! (LINE 6247)
        text = text.replace('},\n        ]','}\n        ]')
        text = text.replace('\\"', "'")

        while re.search("//", text) != None:
            number = re.search("//", text).span()
            maxD = text[number[1]:].find('\n')
            text = text[:number[0]] + text[number[1] + maxD:]


        temp = text.split("},\n")
        temp[0] = '"1": ' + temp[0][temp[0].count('"'):]
        for i in range(1, len(temp)):
            number = temp[i].find(":")
            found = False
            for el in ["description", "specialName", "specialNotes", "sailor"]:
                if el in temp[i][:number]:
                    found = True
                    break
            if found == False:
                nb = temp[i][:number].count(" ")
                temp[i] = '"' + temp[i][nb:number] + '":' + temp[i][number + 1:]

        temp = "{" + "},\n".join(temp)
        temp = temp[:len(temp) - 6] + "}"
        jsonText = json.loads(temp)

        #Captain ability
        embed.add_field(name = "Captain ability", value = jsonText[str(charNum)]["captain"], inline = False)

        #Special
        if type(jsonText[str(charNum)]["special"]) != list:
            embed.add_field(name = jsonText[str(charNum)]["specialName"], value = jsonText[str(charNum)]["special"], inline = False)
            cd = requests.get(LINK + "cooldowns.js")
            cdInfos = cd.text
            cdData = cdInfos.split("\n")
            if "null" not in cdData[charNum]:
                cdJson = json.loads(cdData[charNum][:-1])
                if type(cdJson) == list:
                    if cdJson[0] != cdJson[1]:
                        embed.add_field(name = "Cooldown", value = str(cdJson[0]) + " --> " + str(cdJson[1]) + " turns", inline = False)
                    else:
                        embed.add_field(name = "Cooldown", value = str(cdJson[0]) + " turns", inline = False)
                else:
                    embed.add_field(name = "Cooldown", value = str(cdJson) + " turns", inline = False)
        else:
            cpt = 1
            for spe in jsonText[str(charNum)]["special"]:
                if type(spe["cooldown"]) != int:
                    embed.add_field(name = jsonText[str(charNum)]["specialName"] + ": Step " + str(cpt), value = spe["description"] + "\nCooldown: " + str(spe["cooldown"][0]) + " --> " + str(spe["cooldown"][1]) + " turns", inline = False)
                else:
                    embed.add_field(name = jsonText[str(charNum)]["specialName"] + ": Step " + str(cpt), value = spe["description"] + "\nCooldown: " + str(spe["cooldown"]) + " turns", inline = False)
                cpt += 1
        return embed



    @commands.command(pass_context=True)
    async def char(self, ctx, *char):
        """Cherche un personnage tel un bg"""

        list_chars = []

        #That's how we deal with bad typers
        list_chars.append("".join(char).lower())
        list_chars.append("".join(char).upper())
        if "".join(char) not in list_chars:
            list_chars.append("".join(char))
        if " ".join(char) not in list_chars:
            list_chars.append(" ".join(char))
        if " ".join(char).upper() not in list_chars:
            list_chars.append(" ".join(char).upper())
        if " ".join(char).lower() not in list_chars:
            list_chars.append(" ".join(char).lower())

        char_with_spaces = " ".join(char).split(" ")

        txt1 = ""
        txt2 = ""
        for el in char_with_spaces:
            txt1 += el[0].upper() + el[1:] + " "
            txt2 += el[0].lower() + el[1:] + " "

        txt1 = txt1[:-1]
        txt2 = txt2[:-1]

        if txt1 not in list_chars:
            list_chars.append(txt1)
        if txt2 not in list_chars:
            list_chars.append(txt2)



        #Let's get the results now \o/

        request = requests.get(LINK + "aliases.js")

        text = request.text

        count = 0

        list_results = []

        lignes = text.split("\n")

        for ligne in lignes:
            cpt = 0
            found = False
            while found == False and cpt < len(list_chars):
                if list_chars[cpt] in ligne:
                    maxD = ligne.find(": [")
                    list_results.append(int(ligne[:maxD]))
                    found = True
                cpt += 1

        request2 = requests.get(LINK + "units.js")

        text2 = request2.text

        lignes = text2.split("\n")

        for i in range(0, len(lignes)):
            cpt = 0
            found = False
            while found == False and cpt < len(list_chars):
                if list_chars[cpt] in lignes[i] and i not in list_results:
                    list_results.append(i)
                    found = True
                cpt += 1






        data = request2.text.split("\n")

        if len(list_results) == 0:
            await self.bot.say("No result found :grimacing:")

        elif len(list_results) == 1:
            embed = self.embed_char(list_results[0], data)
            await self.bot.send_message(ctx.message.channel, embed = embed)
        else:
            num = await self.choose_char(list_results, data, ctx.message.channel, ctx.message.author)
            if num > 0:
                embed = self.embed_char(num, data)
                await self.bot.send_message(ctx.message.channel, embed = embed)
            elif num == 0:
                await self.bot.say("I waited for too long, I cancel the research!")
            elif num == -1:
                await self.bot.say("Please type a **correct** number!")
            else:
                await self.bot.say("Please type a **number**!")

def setup(bot):
    n = Char(bot)
    bot.add_cog(n)
