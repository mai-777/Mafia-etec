import discord
import os
from dotenv import load_dotenv
from discord.ext import commands
from discord import app_commands
# Cargar variables de entorno
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
# Crear cliente
intents = discord.Intents.default()
intents.message_content = True
client = commands.Bot(command_prefix="!", intents=intents)

GUILD_ID = discord.Object(id=1354935237976789164)

@client.event
async def on_ready():
    print(f'✅ Bot conectado como {client.user}')

    try:
        guild = discord.Object(id=1354935237976789164)
        synced = await client.tree.sync(guild=guild)
        print(f"Synced {len(synced)} commands to guild {guild.id}")

    except Exception as e:
        print(f"Error syncing commands: {e}")

@client.event
async def on_message(message):
    if message.author == client.user:
        return    
    if message.content.lower() == 'hola':
        await message.channel.send('¡Hola! Soy un bot hecho en Python. 🤖')

@client.tree.command(name="holaa", description="Saludar", guild=GUILD_ID)
async def Saludar(interaction: discord.Interaction):
    await interaction.response.send_message("Hola a todos!")

@client.tree.command(name="embed", description="prueba de embed", guild=GUILD_ID)
async def embed(interaction: discord.Interaction):
    embed = discord.Embed(title= "Titilazo", description= "Dame a malala", color=discord.Color.red())
    embed.add_field(name="Titulo casilla1", value="Info casilla 1", inline=False)
    embed.add_field(name="Titulo casilla2", value="Info casilla 2", inline=True)
    embed.add_field(name="Titulo casilla3", value="Info casilla 3", inline=True)
    embed.set_footer(text="Este es el footer")
    embed.set_author(name=interaction.user.name)
    await interaction.response.send_message(embed=embed)

class View(discord.ui.View):
    @discord.ui.button(label="Presioname!", style=discord.ButtonStyle.red)
    async def button_callback(self,button,interaction):
        await button.response.send_message("Presionaste el boton!!!")

@client.tree.command(name="boton", description="Mostrar boton", guild=GUILD_ID)
async def myButton(interaction: discord.Interaction):
    await interaction.response.send_message(view=View())


client.run(TOKEN)