import discord
from collections import defaultdict
import asyncio


async def comando_matar(ctx, partidas, votos_mafia, bot, fase_dia, votos_dia, votantes_dia, victima):
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

    if victima not in partida["jugadores"]:
        await ctx.send("❌ Ese jugador ya está muerto.")
        return

    if victima not in votos_mafia:
        votos_mafia[victima] = 0
    votos_mafia[victima] += 1

    await ctx.send(f"🗳️ Voto registrado para matar a {victima.mention}")

    total_mafiosos = sum(1 for r in partida["roles"].values() if r == "Mafioso")
    if votos_mafia[victima] >= total_mafiosos:
        victima_asesinada = victima
        canal_dia = ctx.guild.get_channel(partida["canal_dia"])

        if partida["protegido_noche"] == victima_asesinada:
            await canal_mafiosos.send(f"🛡️ ¡{victima_asesinada.mention} estaba protegido esta noche!")
            partida["protegido_noche"] = None
        else:
            await canal_mafiosos.send(f"🩸 {victima_asesinada.mention} ha sido asesinado.")
            partida["jugadores"].remove(victima_asesinada)
            rol_victima = partida["roles"].pop(victima_asesinada)
            votos_mafia.clear()

            if not any(r in ["Ciudadano", "Juez", "Espía"] for r in partida["roles"].values()):
                await canal_dia.send("🧛‍♂️ ¡Los mafiosos ganaron!")
                partidas.pop(ctx.guild.id)
                await eliminar_canal_mafia(canal_mafiosos)
                return

            await fase_dia(ctx, partidas, votos_dia, votantes_dia, victima_asesinada, rol_victima)

        if canal_mafiosos:
            await eliminar_canal_mafia(canal_mafiosos)
            partida["canal_mafiosos"] = None


    if partida["modo_rapido"]:
        await asyncio.sleep(partida["tiempo_noche"])
        if partida["fase"] == "noche" and partida["canal_mafiosos"]:
            canal_mafiosos = ctx.guild.get_channel(partida["canal_mafiosos"])
            if canal_mafiosos:
                await canal_mafiosos.send("⏰ ¡El tiempo de la noche ha terminado!")

async def comando_proteger(ctx, partidas, protegido):
    partida = partidas.get(ctx.guild.id)
    if not partida or partida["fase"] != "noche":
        await ctx.send("❌ No estamos en fase de noche.")
        return

    if partida["roles"].get(ctx.author) != "Juez":
        await ctx.send("❌ Solo el Juez puede usar este comando.")
        return

    if ctx.author in partida["habilidades_usadas"]["proteger"]:
        await ctx.send("❌ Ya usaste tu habilidad para proteger.")
        return

    if protegido not in partida["jugadores"]:
        await ctx.send("❌ Ese jugador no está en la partida.")
        return

    partida["protegido_noche"] = protegido
    partida["habilidades_usadas"]["proteger"].add(ctx.author)
    await ctx.send(f"🛡️ Has protegido a {protegido.mention} esta noche.")

async def comando_investigar(ctx, partidas, investigado):
    partida = partidas.get(ctx.guild.id)
    if not partida or partida["fase"] != "noche":
        await ctx.send("❌ No estamos en fase de noche.")
        return

    if partida["roles"].get(ctx.author) != "Espía":
        await ctx.send("❌ Solo el Espía puede usar este comando.")
        return

    if ctx.author in partida["habilidades_usadas"]["investigar"]:
        await ctx.send("❌ Ya usaste tu habilidad para investigar.")
        return

    if investigado not in partida["jugadores"]:
        await ctx.send("❌ Ese jugador no está en la partida.")
        return

    rol_investigado = partida["roles"].get(investigado)
    partida["investigaciones"][ctx.author] = investigado
    partida["habilidades_usadas"]["investigar"].add(ctx.author)

    await ctx.author.send(f"🕵️ Has investigado a {investigado.mention}. Su rol es: **{rol_investigado}**")
    await ctx.send(f"🕵️ Has investigado a {investigado.mention}. Revisa tus mensajes privados.")

async def crear_canal_mafia(ctx, partida):
    guild = ctx.guild
    overwrites = {
        guild.default_role: discord.PermissionOverwrite(read_messages=False),
    }

    for jugador in partida["jugadores"]:
        if partida["roles"].get(jugador) == "Mafioso":
            overwrites[jugador] = discord.PermissionOverwrite(read_messages=True, send_messages=True)

    canal_mafia = await guild.create_text_channel("mafia-secreta", overwrites=overwrites, reason="Canal para los mafiosos")
   
    #guarda el nuevo canal (por si acaso)
    partida["canal_mafiosos"] = canal_mafia.id

    await canal_mafia.send("🌙 La noche ha comenzado. Mafiosos, elijan a su víctima usando `!matar @usuario`.")


async def eliminar_canal_mafia(canal):
    try:
        await canal.delete(reason="Fin de la fase de noche")
    except Exception as e:
        print(f"Error al eliminar canal de mafiosos: {e}")
