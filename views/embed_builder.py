# views/embed_builder.py
from __future__ import annotations
import discord
from utils.helpers import hex_to_color


class EmbedBuilderModal(discord.ui.Modal, title="Конструктор embed"):
    em_title = discord.ui.TextInput(label="Заголовок", required=False, max_length=256)
    em_desc = discord.ui.TextInput(label="Описание", style=discord.TextStyle.paragraph, required=False, max_length=4000)
    em_color = discord.ui.TextInput(label="Цвет (HEX)", required=False, max_length=7, placeholder="#5865F2")
    em_image = discord.ui.TextInput(label="URL изображения", required=False, max_length=300)
    em_footer = discord.ui.TextInput(label="Footer", required=False, max_length=2048)

    def __init__(self, channel: discord.TextChannel | None = None):
        super().__init__()
        self.channel = channel

    async def on_submit(self, interaction: discord.Interaction) -> None:
        emb = discord.Embed(
            title=str(self.em_title) or None,
            description=str(self.em_desc) or None,
            color=hex_to_color(str(self.em_color) or None),
        )
        if str(self.em_image):
            emb.set_image(url=str(self.em_image))
        if str(self.em_footer):
            emb.set_footer(text=str(self.em_footer))

        target = self.channel or interaction.channel
        await target.send(embed=emb)
        await interaction.response.send_message("📨 Отправлено.", ephemeral=True)
