import os
import discord
from discord.ext import commands
from dotenv import load_dotenv

from creacion_partidas import crear_partida, unirme_partida, Partida
from FaseNoche import comando_matar
from FaseDia import comando_votar, iniciar_fase_dia

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

intents = discord.Intents.all()
client = commands.Bot(command_prefix='!', intents=intents)


partidas = {}
votos_mafia = {}
votos_dia = {}
votantes_dia = set()

@client.event
async def on_ready():
    print("✅ Bot conectado.")

@client.command()
async def crear(ctx, max_jugadores: int):
    await crear_partida(ctx, partidas, max_jugadores)

@client.command()
async def unirme(ctx):
    await unirme_partida(ctx, partidas, client)

@client.command()
async def matar(ctx, victima: discord.Member):
    await comando_matar(ctx, partidas, votos_mafia, client, fase_dia=iniciar_fase_dia, votos_dia=votos_dia, votantes_dia=votantes_dia, victima=victima)

@client.command()
async def votar(ctx, acusado: discord.Member):
    await comando_votar(ctx, partidas, votos_dia, votantes_dia, acusado)

client.run(TOKEN)


