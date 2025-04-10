import discord
from collections import defaultdict

async def comando_matar(ctx, partidas, votos_mafia, client, fase_dia, votos_dia):
    partida = partidas.get(ctx.guild.id)
    if not partida:
        await ctx.send("No hay partida activa.")
        return

    canal_mafiosos = ctx.guild.get_channel(partida["canal_mafiosos"])
    if not canal_mafiosos or ctx.channel.id != canal_mafiosos.id:
        await ctx.send("Este comando solo puede usarse en el canal de los mafiosos.")
        return

    if partida["roles"].get(ctx.author) != "Mafioso":
        await ctx.send("Solo los mafiosos pueden usar este comando.")
        return

    victima = ctx.message.mentions[0]
    votos_mafia[victima] += 1
    await ctx.send(f"🗳️ Voto registrado para matar a {victima.mention}")

    total_mafiosos = sum(1 for r in partida["roles"].values() if r == "Mafioso")
    if votos_mafia[victima] >= total_mafiosos:
        await canal_mafiosos.send(f"🩸 {victima.mention} ha sido asesinado.")
        partida["jugadores"].remove(victima)
        del partida["roles"][victima]
        votos_mafia.clear()

        canal_dia = ctx.guild.get_channel(partida["canal_dia"])
        await canal_mafiosos.delete()
        partida["canal_mafiosos"] = None

        if not any(r == "Ciudadano" for r in partida["roles"].values()):
            await canal_dia.send("🧛‍♂️ ¡Los mafiosos ganaron!")
            partidas.pop(ctx.guild.id)
            return

        await fase_dia(ctx, partidas, votos_dia, victima)

async def crear_canal_mafia(guild, mafiosos_ids):
    overwrites = {
        guild.default_role: discord.PermissionOverwrite(read_messages=False),
    }
    for id in mafiosos_ids:
        member = guild.get_member(id)
        if member:
            overwrites[member] = discord.PermissionOverwrite(read_messages=True, send_messages=True)
    return await guild.create_text_channel("mafia-privado", overwrites=overwrites)

async def eliminar_canal_mafia(canal):
    await canal.delete()
