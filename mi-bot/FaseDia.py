import discord
import asyncio
from collections import defaultdict

from creacion_partidas import puntuaciones
from FaseNoche import crear_canal_mafia, eliminar_canal_mafia

async def eliminar_canal_mafia_si_existe(ctx, partida):
    canal_mafia_id = partida.get("canal_mafia")
    if canal_mafia_id:
        canal_mafia = ctx.guild.get_channel(canal_mafia_id)
        if canal_mafia:
            await eliminar_canal_mafia(canal_mafia)

async def iniciar_fase_dia(ctx, partidas, votos_dia, votantes_dia, victima, rol_victima):
    partida = partidas.get(ctx.guild.id)
    if not partida:
        return

    canal_dia = ctx.guild.get_channel(partida.get("canal_dia"))
    if not canal_dia:
        return

    votos_dia.clear()
    votantes_dia.clear()
    partida["fase"] = "día"

    await canal_dia.send(f"☀️ Al amanecer, se descubre que {victima.mention} fue asesinado durante la noche.\n🔍 Era un **{rol_victima}**.")
    await canal_dia.send(f"💬 Comienza la fase de día. Usen `!votar @usuario` para votar a un sospechoso (tienen {partida['tiempo_dia']} segundos si el modo rápido está activo).")

    if partida.get("modo_rapido"):
        await asyncio.sleep(partida["tiempo_dia"])
        if partida.get("fase") == "día" and partida.get("jugadores"):
            await canal_dia.send("⏰ ¡El tiempo del día ha terminado!")
            await determinar_eliminacion_dia(ctx, partidas, votos_dia, votantes_dia)

async def comando_votar(ctx, partidas, votos_dia, votantes_dia, acusado):
    partida = partidas.get(ctx.guild.id)
    if not partida or partida.get("fase") != "día":
        await ctx.send("❌ No estamos en fase de votación.")
        return

    if ctx.author not in partida.get("jugadores", []):
        await ctx.send("❌ No puedes votar, estás eliminado.")
        return

    if ctx.author in votantes_dia:
        await ctx.send("❌ Ya votaste.")
        return

    if acusado not in partida.get("jugadores", []):
        await ctx.send("❌ Ese jugador ya fue eliminado.")
        return

    votos_dia[acusado] = votos_dia.get(acusado, 0) + 1
    votantes_dia.add(ctx.author)

    await ctx.send(f"🗳️ {ctx.author.display_name} ha votado por {acusado.display_name}.")

    if len(votantes_dia) == len(partida.get("jugadores", [])):
        await determinar_eliminacion_dia(ctx, partidas, votos_dia, votantes_dia)

async def determinar_eliminacion_dia(ctx, partidas, votos_dia, votantes_dia):
    partida = partidas.get(ctx.guild.id)
    canal_dia = ctx.guild.get_channel(partida.get("canal_dia"))
    if not partida or not partida.get("jugadores"):
        return

    if not votos_dia:
        await canal_dia.send("No hubo votos durante el día.")
        votos_dia.clear()
        votantes_dia.clear()
        partida["fase"] = "noche"
        await canal_dia.send("🌙 La noche vuelve a caer. Esperen instrucciones...")
        await eliminar_canal_mafia_si_existe(ctx, partida)
        await crear_canal_mafia(ctx, partida)
        return

    mas_votado = max(votos_dia.items(), key=lambda x: (x[1], -x[0].id))[0]
    rol_eliminado = partida["roles"].pop(mas_votado, "Desconocido")
    partida["jugadores"].remove(mas_votado)

    if rol_eliminado == "Mafioso":
        for jugador in partida["jugadores"]:
            if partida["roles"].get(jugador) == "Ciudadano":
                puntuaciones[jugador] += 1
    elif rol_eliminado in ["Ciudadano", "Juez", "Espía"]:
        for jugador in partida["jugadores"]:
            if partida["roles"].get(jugador) == "Mafioso":
                puntuaciones[jugador] += 1

    await canal_dia.send(f"🔪 {mas_votado.display_name} fue eliminado. Era **{rol_eliminado}**.")

    roles_vivos = [partida["roles"].get(jugador) for jugador in partida["jugadores"]]
    if "Mafioso" not in roles_vivos:
        await canal_dia.send("🎉 ¡Los Ciudadanos han ganado!")
        for jugador in partida["jugadores"]:
            if partida["roles"].get(jugador) in ["Ciudadano", "Juez", "Espía"]:
                puntuaciones[jugador] += 3
        await eliminar_canal_mafia_si_existe(ctx, partida)
        partidas.pop(ctx.guild.id)
        return

    if all(rol == "Mafioso" for rol in roles_vivos if rol):
        await canal_dia.send("💀 ¡La Mafia ha ganado!")
        for jugador in partida["jugadores"]:
            if partida["roles"].get(jugador) == "Mafioso":
                puntuaciones[jugador] += 3
        await eliminar_canal_mafia_si_existe(ctx, partida)
        partidas.pop(ctx.guild.id)
        return

    votos_dia.clear()
    votantes_dia.clear()
    partida["fase"] = "noche"
    await canal_dia.send(f"🌙 La noche vuelve a caer. Mafiosos, elijan a su víctima usando `!matar @usuario` (tienen {partida['tiempo_noche']} segundos si el modo rápido está activo). Jueces pueden usar `!proteger @usuario` y Espías `!investigar @usuario` (una vez por partida).")

    await eliminar_canal_mafia_si_existe(ctx, partida)
    await crear_canal_mafia(ctx, partida)
