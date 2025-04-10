import asyncio
import discord
from FaseNoche import crear_canal_mafia

async def crear_partida(ctx, partidas, max_jugadores):
    if ctx.guild.id in partidas:
        await ctx.send("Ya hay una partida en curso.")
        return

    partidas[ctx.guild.id] = {
        "jugadores": [ctx.author],
        "max_jugadores": max_jugadores,
        "roles": {},
        "canal_mafiosos": None,
        "canal_dia": ctx.channel.id
    }
    await ctx.send(f"Partida creada con máximo de {max_jugadores} jugadores. Usa `!unirme` para entrar.")

async def unirme_partida(ctx, partidas, client):
    partida = partidas.get(ctx.guild.id)
    if not partida:
        await ctx.send("No hay partida activa. Usa `!crear` para empezar una.")
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
        await asignar_roles_y_empezar(ctx, partida, client)

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
