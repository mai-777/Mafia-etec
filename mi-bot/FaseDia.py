import discord

async def iniciar_fase_dia(ctx, partidas, votos_dia, victima):
    partida = partidas.get(ctx.guild.id)
    if not partida:
        await ctx.send("No hay partida activa.")
        return

    canal_dia = ctx.guild.get_channel(partida["canal_dia"])
    if not canal_dia:
        await ctx.send("Error: No se encontró el canal del día.")
        return

    await canal_dia.send(f"☀️ Al amanecer, se descubre que {victima.mention} fue asesinado durante la noche.")
    await canal_dia.send("💬 Comienza la fase de día. Usen `!votar @usuario` para votar a un sospechoso.")

async def comando_votar(ctx, partidas, votos_dia, acusado: discord.Member):
    partida = partidas.get(ctx.guild.id)
    if not partida:
        await ctx.send("No hay partida activa.")
        return

    if partida["roles"].get(ctx.author) != "Ciudadano":
        await ctx.send("Solo los ciudadanos pueden votar de día.")
        return

    votos_dia[acusado] += 1
    await ctx.send(f"🗳️ Voto registrado contra {acusado.mention}")

    total_ciudadanos = sum(1 for r in partida["roles"].values() if r == "Ciudadano")
    if votos_dia[acusado] >= total_ciudadanos:
        await ctx.send(f"☠️ {acusado.mention} ha sido eliminado por votación.")
        partida["jugadores"].remove(acusado)
        del partida["roles"][acusado]
        votos_dia.clear()

        if not any(r == "Ciudadano" for r in partida["roles"].values()):
            await ctx.send("🧛‍♂️ ¡Los mafiosos ganaron!")
            partidas.pop(ctx.guild.id, None)
        elif not any(r == "Mafioso" for r in partida["roles"].values()):
            await ctx.send("🕊️ ¡Los ciudadanos ganaron!")
            partidas.pop(ctx.guild.id, None)
