import discord
import os
from dotenv import load_dotenv
from discord.ext import commands
from collections import defaultdict

from creacion_partidas import crear_partida, unirme_partida
from FaseNoche import comando_matar
from FaseDia import iniciar_fase_dia

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

intents = discord.Intents.all()
client = commands.Bot(command_prefix="!", intents=intents)

partidas = {}
votos_mafia = defaultdict(int)
votos_dia = defaultdict(int)

@client.event
async def on_ready():
    print("✅ Bot conectado.")

@client.command(name="crear")
async def crear(ctx, max_jugadores: int):
    await crear_partida(ctx, partidas, max_jugadores)

@client.command(name="unirme")
async def unirme(ctx):
    await unirme_partida(ctx, partidas, client)

@client.command(name="matar")
async def matar(ctx, victima: discord.Member):
    await comando_matar(ctx, partidas, votos_mafia, client, iniciar_fase_dia, votos_dia)

@client.command(name="votar")
async def votar(ctx, acusado: discord.Member):
    await iniciar_fase_dia(ctx, partidas, votos_dia, acusado)

client.run(TOKEN)
