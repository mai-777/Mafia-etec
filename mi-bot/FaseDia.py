import time
import discord
import os
from dotenv import load_dotenv
from discord import app_commands
from discord.ext import commands
import asyncio
import random
from creacion_partidas import partidas
from FaseNoche import eliminar_canal_mafia

# Cargar variables de entorno
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

# Crear cliente
intents = discord.Intents.default()
intents.message_content = True
client = commands.Bot(command_prefix="!", intents=intents)

GUILD_ID = discord.Object(id=1354935237976789164)


votos_dia = {}

@client.event
async def on_ready():
    print(f'✅ Bot conectado como {client.user}')
    
    try:
        guild = discord.Object(id=1354935237976789164) 
        synced = await client.tree.sync(guild=guild)
        print(f"Comandos sincronizados en el servidor {guild.id}: {len(synced)} comandos")
    except Exception as e:
        print(f"Error sincronizando comandos: {e}")


@client.tree.command(name="dia", description="Inicia la fase de día y permite votar", guild=GUILD_ID)
async def dia_cmd(interaction: discord.Interaction):
    canal = interaction.channel
    #guild = interaction.guild
    partida = partidas.get(canal.id)

    if not partida:
        await interaction.response.send_message("No hay partida en este canal.")
        return

    jugadores = partida["jugadores"]
    mafiosos = partida["mafiosos"]
    ciudadanos = [jugador_id for jugador_id in jugadores if jugador_id not in mafiosos]
    eliminados = partida.get("eliminados", [])
    if eliminados:
        eliminado = eliminados[-1]
        await canal.send(f"🌅 ¡Amanece y se descubre que {eliminado} ha sido eliminado! Discútanlo antes de votar.")
    else:
        await canal.send("🌅 ¡Amanece! ¡Es hora de la fase de día!")
    
    await canal.send("🗳️ **¡Votación!** Solo los ciudadanos pueden votar. Voten a quién creen que es un mafioso usando `!votar <jugador>`.")
    votos_dia.clear()

    timeout = 45
    start_time = time.time()

    while len(votos_dia) < len(ciudadanos) and time.time()- start_time < timeout:
        await asyncio.sleep(1)

    votos_contados = {}
    for voto in votos_dia.values():
        votos_contados[voto] = votos_contados.get(voto,0)+1
    
    if votos_contados:
        jugador_votado = max(votos_contados, key=votos_contados.get)
        if jugador_votado in mafiosos:
            resultado = "Era un **Mafioso**!!!"
        else:
            resultado = "Era un **Ciudadano** :c"
        await canal.send(f"{jugador_votado} ha sido eliminado. {resultado}")

    partida["jugadores"].remove(jugador_votado)
    if jugador_votado in mafiosos:
        partida["mafiosos"].remove(jugador_votado)
    partida["eliminados"].append(jugador_votado)

    if len(partida["mafiosos"]) == 0:
        await canal.send("🎉 Los **Ciudadanos han ganado**. ¡Felicidades!")
    elif len(partida["jugadores"])<= len(partida["mafiosos"]):
        await canal.send("🎉 Los **Mafiosos han ganado**. ¡Felicidades!")
        await eliminar_canal_mafia(canal)

@client.tree.command(name="votar", description="Vota a quien eliminar durante la fase de día", guild=GUILD_ID)
async def votar_cmd(interaction: discord.Interaction, jugador: discord.Member):
    canal = interaction.channel
    partida = partidas.get(canal.id)

    if not partida:
        await interaction.response.send_message("No hay partida en este canal.")
        return
    
    if interaction.user.id not in [jugador_id for jugador_id in partida["jugadores"] if jugador_id not in partida["mafiosos"]]:
        await interaction.response.send_message("Solo los ciudadanos pueden votar.")
        return

    if interaction.user.id in votos_dia:
        await interaction.response.send_message("Ya has votado. No puedes votar de nuevo.")
        return

    if jugador.id not in partida["jugadores"]:
        await interaction.response.send_message("Ese jugador no está en la partida.")
        return

    votos_dia[interaction.user.id] = jugador.id
    await interaction.response.send_message(f"Voto registrado para eliminar a {jugador.name}.")

client.run(TOKEN)