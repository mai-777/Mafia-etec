import discord
import os
from dotenv import load_dotenv
from discord import app_commands
from discord.ext import commands
import asyncio
import random
from creacion_partidas import partidas


# Cargar variables de entorno
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

# Crear cliente
intents = discord.Intents.default()
intents.message_content = True
client = commands.Bot(command_prefix="!", intents=intents)

GUILD_ID = discord.Object(id=1354935237976789164)


votos_mafia = {}

@client.event
async def on_ready():
    print(f'✅ Bot conectado como {client.user}')
    
    try:
        guild = discord.Object(id=1354935237976789164) 
        synced = await client.tree.sync(guild=guild)
        print(f"Comandos sincronizados en el servidor {guild.id}: {len(synced)} comandos")
    except Exception as e:
        print(f"Error sincronizando comandos: {e}")

TIMEOUT = 30

async def esperar_votos_mafiosos(votos_mafia, mafiosos):
    start_time = asyncio.get_event_loop().time()
    while len(votos_mafia) < len(mafiosos):
        if asyncio.get_event_loop().time() - start_time > TIMEOUT:
            break
        await asyncio.sleep(1)


@client.tree.command(name="noche", description="Inicia la fase de noche", guild=GUILD_ID)
async def noche_cmd(interaction: discord.Interaction):
    canal = interaction.channel
    guild = interaction.guild
    partida = partidas.get(canal.id)

    if not partida:
        await interaction.response.send_message("No hay partida en este canal.")
        return

    jugadores = partida["jugadores"]
    mafiosos = partida.get("mafiosos", [])

    if not mafiosos:
        await interaction.response.send_message("No hay mafiosos en la partida. La fase de noche no puede comenzar.")
        return

    canal_mafia = await crear_canal_mafia(guild, mafiosos)

    await crear_roles(guild,mafiosos,jugadores)

    partida["estado_noche"] = "en_proceso"

    await interaction.response.send_message("🌙 **Fase de Noche**: Mafiosos, elijan a su víctima en su chat privado.")
    await canal_mafia.send("Bienvenidos mafiosos. Usen `!matar <jugador>` para elegir su víctima.")

    votos_mafia.clear()

    await esperar_votos_mafiosos(votos_mafia,mafiosos)
    partida["estado_noche"] = "completado"

    if len(votos_mafia) == 0:
        await canal.send("La fase de noche terminó sin votos. La partida continúa.")
    else:
        victima = max(votos_mafia,key=votos_mafia.get)
        jugador_votado = guild.get_member(victima)
        await canal.send(f"🌙 Los mafiosos han decidido eliminar a {jugador_votado.name}. ¡Se procesará al amanecer!")

    await eliminar_canal_mafia(canal_mafia)

    if len(partida["mafiosos"] ) == 0:
        await canal.send("🎉 Los **ciudadanos han ganado**. No quedan mafiosos en el juego.")
        await eliminar_canal_mafia(canal_mafia)
    


async def crear_roles(guild, mafiosos,jugadores):
    mafia_rol = discord.utils.get(guild.roles, name="Mafioso")
    if not mafia_rol:
        mafia_rol = await guild.create_role(name="Mafioso", color=discord.Color.red(), reason="Rol para los mafiosos")
    
    ciudadano_rol = discord.utils.get(guild.roles, name="Ciudadano")
    if not ciudadano_rol:
        ciudadano_rol = await guild.create_role(name="Ciudadano", color=discord.Color.blue(), reason="Rol para los ciudadanos")
    for jugador_id in jugadores:
         member = guild.get_member(jugador_id)
         if member:
             if jugador_id in mafiosos:
                await member.add_roles(mafia_rol)
             else:
                await member.add_roles(ciudadano_rol)
                
async def crear_canal_mafia(guild, mafiosos):
    overwrites = {
        guild.default_role: discord.PermissionOverwrite(read_messages=False),
    }

    for mafioso_id in mafiosos:
        member = guild.get_member(mafioso_id)
        if member:
            overwrites[member] = discord.PermissionOverwrite(read_messages=True, send_messages=True)

    canal_mafia = await guild.create_text_channel("Mafia_Chat", overwrites=overwrites)
    return canal_mafia

@client.tree.command(name="matar", description="Vota a quien matar durante la fase de noche", guild=GUILD_ID)
async def matar_cmd(interaction: discord.Interaction, victima: discord.Member):
    if interaction.user.id not in partidas.get(interaction.channel.id, {}).get("mafiosos", []):
        await interaction.response.send_message("No eres mafioso, no puedes votar.")
        return

    votos_mafia[interaction.user.id] = victima.id
    await interaction.response.send_message(f"Voto registrado. Mafioso {interaction.user.name} votó por {victima.name}.")

async def eliminar_canal_mafia(canal_mafia):
    try:
        await canal_mafia.delete()
        print("El Canal de mafia fue eliminado")
    except Exception as e:
        print(f"Error en eliminar el canal de mafiosos: {e}")
client.run(TOKEN)