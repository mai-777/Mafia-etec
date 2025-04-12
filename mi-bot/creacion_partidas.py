import asyncio
import discord
import random
from collections import defaultdict

Partida = dict
puntuaciones = defaultdict(int) 

async def crear_partida(ctx, partidas, max_jugadores, modo_rapido=False, tiempo_dia=60, tiempo_noche=30):
    if ctx.guild.id in partidas:
        await ctx.send("Ya hay una partida en curso en este servidor.")
        return

    partidas[ctx.guild.id] = {
        "jugadores": [],
        "max_jugadores": max_jugadores,
        "roles": {},
        "canal_mafiosos": None,
        "canal_dia": ctx.channel.id,
        "fase": "esperando",
        "modo_rapido": modo_rapido,
        "tiempo_dia": tiempo_dia,
        "tiempo_noche": tiempo_noche,
        "protegido_noche": None,
        "investigaciones": {},  # Espía investiga a quién
        "habilidades_usadas": defaultdict(set), # Jugadores que usaron su habilidad
    }

    await ctx.send(f"🎮 Se ha creado una partida para {max_jugadores} jugadores (Modo Rápido: {'Sí' if modo_rapido else 'No'}). Usa `!unirme` para participar.")

async def unirme_partida(ctx, partidas, bot):
    partida = partidas.get(ctx.guild.id)
    if not partida:
        await ctx.send("No hay una partida activa en este servidor.")
        return

    if ctx.author in partida["jugadores"]:
        await ctx.send("Ya estás en la partida.")
        return

    if len(partida["jugadores"]) >= partida["max_jugadores"]:
        await ctx.send("La partida ya está llena.")
        return

    partida["jugadores"].append(ctx.author)
    await ctx.send(f"{ctx.author.mention} se ha unido a la partida.")

    if len(partida["jugadores"]) == partida["max_jugadores"]:
        await iniciar_partida(ctx, partida, partidas)

async def iniciar_partida(ctx, partida, partidas):
    jugadores = partida["jugadores"]
    random.shuffle(jugadores)
    num_jugadores = len(jugadores)
    num_mafiosos = max(1, num_jugadores // 3)
    num_jueces = 1 if num_jugadores >= 7 else 0
    num_espias = 1 if num_jugadores >= 5 else 0

    roles_disponibles = ["Mafioso"] * num_mafiosos + ["Juez"] * num_jueces + ["Espía"] * num_espias
    num_ciudadanos = num_jugadores - len(roles_disponibles)
    roles_disponibles.extend(["Ciudadano"] * num_ciudadanos)
    random.shuffle(roles_disponibles)

    partida["roles"] = {jugadores[i]: roles_disponibles[i] for i in range(num_jugadores)}
    partida["protegido_noche"] = None
    partida["investigaciones"] = {}
    partida["habilidades_usadas"].clear()

    mafiosos = [j for j in jugadores if partida["roles"][j] == "Mafioso"]
    canal_mafia = await crear_canal_mafia(ctx.guild, [j.id for j in mafiosos])
    partida["canal_mafiosos"] = canal_mafia.id
    partida["fase"] = "noche"

    for j in jugadores:
        try:
            await j.send(f"🎭 Tu rol es: **{partida['roles'][j]}**")
        except:
            pass

    await canal_mafia.send(f"🌙 Noche: Mafiosos, elijan a su víctima usando `!matar @usuario` (tienen {partida['tiempo_noche']} segundos si el modo rápido está activo).")
    await ctx.send(f"🌙 La noche ha comenzado. Los roles han sido asignados por privado (Modo Rápido: {'Sí' if partida['modo_rapido'] else 'No'}).")

async def crear_canal_mafia(guild, mafiosos_ids):
    overwrites = {
        guild.default_role: discord.PermissionOverwrite(read_messages=False),
    }
    for id in mafiosos_ids:
        member = guild.get_member(id)
        if member:
            overwrites[member] = discord.PermissionOverwrite(read_messages=True, send_messages=True)
    return await guild.create_text_channel("mafia-privado", overwrites=overwrites)

async def ranking(interaction, puntuaciones):
    if not puntuaciones:
        await interaction.response.send_message("🏆 No hay puntuaciones todavía.", ephemeral=True)
        return
    sorted_puntuaciones = sorted(puntuaciones.items(), key=lambda item: item[1], reverse=True)
    texto = "\n".join([f"{user.name}: {pts} puntos" for user, pts in sorted_puntuaciones])
    await interaction.response.send_message(f"🏆 **Ranking:**\n{texto}", ephemeral=True)

async def fase_juego(interaction, duracion):
    await interaction.channel.send(f"⏳ La fase comienza. Tienen {duracion} segundos.")
    await asyncio.sleep(duracion)
    await interaction.channel.send("⏰ La fase ha terminado.")