import discord

async def iniciar_fase_dia(ctx, partidas, votos_dia, votantes_dia, victima, rol_victima):
    partida = partidas.get(ctx.guild.id)
    if not partida:
        return

    canal_dia = ctx.guild.get_channel(partida["canal_dia"])
    if not canal_dia:
        return

    votos_dia.clear()
    votantes_dia.clear()
    partida["fase"] = "día"

    await canal_dia.send(f"☀️ Al amanecer, se descubre que {victima.mention} fue asesinado durante la noche.\n🔍 Era un **{rol_victima}**.")
    await canal_dia.send("💬 Comienza la fase de día. Usen `!votar @usuario` para votar a un sospechoso.")

async def comando_votar(ctx, partidas, votos_dia, votantes_dia, acusado):
    partida = partidas.get(ctx.guild.id)
    if not partida or partida["fase"] != "día":
        await ctx.send("❌ No estamos en fase de votación.")
        return

    if ctx.author not in partida["jugadores"]:
        await ctx.send("❌ No puedes votar, estás eliminado.")
        return

    if ctx.author in votantes_dia:
        await ctx.send("❌ Ya votaste.")
        return

    if acusado not in partida["jugadores"]:
        await ctx.send("❌ Ese jugador ya fue eliminado.")
        return

    if acusado not in votos_dia:
        votos_dia[acusado] = 0
    votos_dia[acusado] += 1
    votantes_dia.add(ctx.author)

    await ctx.send(f"🗳️ {ctx.author.display_name} ha votado por {acusado.display_name}.")

    if len(votantes_dia) == len(partida["jugadores"]):
        mas_votado = max(votos_dia.items(), key=lambda x: (x[1], -x[0].id))[0]
        rol_eliminado = partida["roles"].pop(mas_votado)
        partida["jugadores"].remove(mas_votado)

        await ctx.send(f"🔪 {mas_votado.display_name} fue eliminado. Era **{rol_eliminado}**.")

        roles_vivos = [partida["roles"][jugador] for jugador in partida["jugadores"]]
        if "Mafioso" not in roles_vivos:
            await ctx.send("🎉 ¡Los Ciudadanos han ganado!")
            partidas.pop(ctx.guild.id)
            return
        elif all(r == "Mafioso" for r in roles_vivos):
            await ctx.send("💀 ¡La Mafia ha ganado!")
            partidas.pop(ctx.guild.id)
            return

        votos_dia.clear()
        votantes_dia.clear()
        partida["fase"] = "noche"
        await ctx.send("🌙 La noche vuelve a caer. Esperen instrucciones...")
