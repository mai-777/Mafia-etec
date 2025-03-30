import discord
import os
from dotenv import load_dotenv
from discord import app_commands
from discord.ext import commands
import random
import asyncio

# Cargar variables de entorno
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

# Crear cliente
intents = discord.Intents.default()
intents.message_content = True
client = commands.Bot(command_prefix="!", intents=intents)

GUILD_ID = discord.Object(id=1354935237976789164)

partidas = {}  # Diccionario para guardar partidas
puntuaciones = {}  # Diccionario para guardar puntuaciones

@client.event
async def on_ready():
    print(f'✅ Bot conectado como {client.user}')

    try:
        guild = discord.Object(id=1354935237976789164)
        synced = await client.tree.sync(guild=guild)
        print(f"Synced {len(synced)} commands to guild {guild.id}")

    except Exception as e:
        print(f"Error syncing commands: {e}")

@client.tree.command(name="crear", description="Crea una partida de Mafia", guild=GUILD_ID)
async def crear_partida(interaction: discord.Interaction, numero_jugadores: int, partida_rapida: int = 0):
    if numero_jugadores < 1 or numero_jugadores > 20:
        await interaction.response.send_message("Jugadores: 4-20.")
        return

    partidas[interaction.channel.id] = {
        "jugadores": [interaction.user.id],
        "max_jugadores": numero_jugadores,
        "activa": True,
        "roles_asignados": False,
        "partida_rapida": partida_rapida
    }

    if partida_rapida > 0:
        await interaction.response.send_message(f"Partida rápida creada para {numero_jugadores} con duración de {partida_rapida} segundos. Usa /unirme.")
    else:
        await interaction.response.send_message(f"Partida normal creada para {numero_jugadores}. Usa /unirme.")

@client.tree.command(name="unirme", description="Únete a una partida de Mafia", guild=GUILD_ID)
async def unirme_partida(interaction: discord.Interaction):
    if interaction.channel.id not in partidas or not partidas[interaction.channel.id]["activa"]:
        await interaction.response.send_message("No hay partida aquí.")
        return

    partida = partidas[interaction.channel.id]

    if interaction.user.id in partida["jugadores"]:
        await interaction.response.send_message("Ya estás en la partida.")
        return

    if len(partida["jugadores"]) >= partida["max_jugadores"]:
        await interaction.response.send_message("Partida llena.")
        return

    partida["jugadores"].append(interaction.user.id)
    await interaction.response.send_message(f"{interaction.user.name} se unió. {len(partida['jugadores'])}/{partida['max_jugadores']}")

    # Si la partida está llena, asignamos roles
    if len(partida["jugadores"]) == partida["max_jugadores"] and not partida["roles_asignados"]:
        await asignar_roles(interaction, partida)

async def asignar_roles(interaction, partida):
    roles = ["Mafioso", "Ciudadano", "Doctor", "Detective", "Juez", "Espía"] # Nuevos roles
    jugadores = partida["jugadores"]
    random.shuffle(roles)

    for i, jugador_id in enumerate(jugadores):
        jugador = await client.fetch_user(jugador_id)
        rol = roles[i % len(roles)]  # Asignamos roles cíclicamente si hay más jugadores que roles
        await jugador.send(f"Tu rol es: {rol}")

    partida["roles_asignados"] = True
    await interaction.channel.send("Roles asignados por mensaje privado.")

    # Iniciar la primera fase del juego (ejemplo: noche)
    if partida["partida_rapida"] > 0:
        await fase_juego(interaction, partida["partida_rapida"])
    else:
        await fase_juego(interaction, 60)  # Duración predeterminada para partidas normales

@client.tree.command(name="ranking", description="Muestra la clasificación de jugadores", guild=GUILD_ID)
async def ranking(interaction: discord.Interaction):
    jugadores_ordenados = sorted(puntuaciones.items(), key=lambda x: x[1], reverse=True)

    embed = discord.Embed(title="Clasificación de Mafia", color=discord.Color.blue())
    for jugador_id, puntuacion in jugadores_ordenados:
        jugador = await client.fetch_user(jugador_id)
        embed.add_field(name=jugador.name, value=str(puntuacion), inline=False)

    await interaction.response.send_message(embed=embed)

# Ejemplo de función para simular una fase del juego con temporizador
async def fase_juego(interaction, duracion):
    await interaction.channel.send(f"La fase comienza. Tienen {duracion} segundos.")
    await asyncio.sleep(duracion)
    await interaction.channel.send("La fase ha terminado.")

client.run(TOKEN)