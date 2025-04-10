import asyncio
import discord
import random

Partida = dict

async def crear_partida(ctx, partidas, max_jugadores):
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
    }

    await ctx.send(f"🎮 Se ha creado una partida para {max_jugadores} jugadores. Usa `!unirme` para participar.")

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

    mafiosos = random.sample(jugadores, k=max(1, len(jugadores) // 3))
    for j in jugadores:
        partida["roles"][j] = "Mafioso" if j in mafiosos else "Ciudadano"

    canal_mafia = await crear_canal_mafia(ctx.guild, [j.id for j in mafiosos])
    partida["canal_mafiosos"] = canal_mafia.id
    partida["fase"] = "noche"

    for j in jugadores:
        try:
            await j.send(f"🎭 Tu rol es: **{partida['roles'][j]}**")
        except:
            pass

    await canal_mafia.send("🌙 Noche: Mafiosos, elijan a su víctima usando `!matar @usuario`.")
    await ctx.send("🌙 La noche ha comenzado. Los mafiosos han recibido instrucciones por privado.")

async def crear_canal_mafia(guild, mafiosos_ids):
    overwrites = {
        guild.default_role: discord.PermissionOverwrite(read_messages=False),
    }
    for id in mafiosos_ids:
        member = guild.get_member(id)
        if member:
            overwrites[member] = discord.PermissionOverwrite(read_messages=True, send_messages=True)
    return await guild.create_text_channel("mafia-privado", overwrites=overwrites)


async def asignar_roles_y_empezar(ctx, partida, client):
    from random import shuffle
    jugadores = partida["jugadores"]
    shuffle(jugadores)
    mitad = len(jugadores) // 2
    partida["roles"] = {j: ("Mafioso" if i < mitad else "Ciudadano") for i, j in enumerate(jugadores)}

    mafiosos = [j for j in jugadores if partida["roles"][j] == "Mafioso"]
    canal_mafia = await crear_canal_mafia(ctx.guild, [m.id for m in mafiosos])
    partida["canal_mafiosos"] = canal_mafia.id

    for j in jugadores:
        try:
            await j.send(f"Tu rol es: **{partida['roles'][j]}**")
        except:
            pass

    await canal_mafia.send("🌙 Es de noche. Mafiosos, usen `!matar @usuario` para asesinar.")

async def ranking(interaction, puntuaciones):
    if not puntuaciones:
        await interaction.response.send_message("🏆 No hay puntuaciones todavía.", ephemeral=True)
        return
    texto = "\n".join([f"{user}: {pts} puntos" for user, pts in puntuaciones.items()])
    await interaction.response.send_message(f"🏆 **Ranking:**\n{texto}", ephemeral=True)

async def fase_juego(interaction, duracion):
   await interaction.channel.send(f"🌙 La fase comienza. Tienen {duracion} segundos.")
   await asyncio.sleep(duracion)
   await interaction.channel.send("🌞 La fase ha terminado.")