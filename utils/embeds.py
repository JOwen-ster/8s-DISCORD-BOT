from discord import Embed, Color


class BotMessageEmbed(Embed):
    def __init__(self, *args, **kwargs):
        super().__init__(color=Color.from_rgb(255,255,255), *args, **kwargs)


class BotConfirmationEmbed(Embed):
    def __init__(self, *args, **kwargs):
        super().__init__(color=Color.green(), *args, **kwargs)


class BotErrorEmbed(Embed):
    def __init__(self, *args, **kwargs):
        super().__init__(color=Color.red(), *args, **kwargs)


class FullTeamsEmbed(Embed):
    def __init__(self, alpha_team: dict[str, str] = None, bravo_team: dict[str, str] = None, *args, **kwargs):
        super().__init__(color=Color.random(), title="Teams", *args, **kwargs)

        if alpha_team is None:
            alpha_team = {"backline": "-", "support": "-", "slayers": ["-", "-"]}
        if bravo_team is None:
            bravo_team = {"backline": "-", "support": "-", "slayers": ["-", "-"]}

        self.alpha_text = (
            f"Backline: <@{alpha_team['backline']}>\n"
            f"Support: <@{alpha_team['support']}>\n"
            f"Slayers: {', '.join(f'<@{s}>' for s in alpha_team['slayers'])}"
        )
        self.bravo_text = (
            f"Backline: <@{bravo_team['backline']}>\n"
            f"Support: <@{bravo_team['support']}>\n"
            f"Slayers: {', '.join(f'<@{s}>' for s in bravo_team['slayers'])}"
        )

        # Add fields to embed
        self.add_field(name="Alpha Team", value=self.alpha_text, inline=False)
        self.add_field(name="Bravo Team", value=self.bravo_text, inline=False)

    # WONT NEED SINCE EMBEDS GET DELETED NOT EDITED
    def update_team(self, alpha_team=None, bravo_team=None):
        if alpha_team:
            self.alpha_text = (
                f"Backline: <@{alpha_team['backline']}>\n"
                f"Support: <@{alpha_team['support']}>\n"
                f"Slayers: {', '.join(f'<@{s}>' for s in alpha_team['slayers'])}"
            )
            self.set_field_at(0, name="Alpha Team", value=self.alpha_text, inline=False)

        if bravo_team:
            self.bravo_text = (
                f"Backline: <@{bravo_team['backline']}>\n"
                f"Support: <@{bravo_team['support']}>\n"
                f"Slayers: {', '.join(f'<@{s}>' for s in bravo_team['slayers'])}"
            )
            self.set_field_at(1, name="Bravo Team", value=self.bravo_text, inline=False)


def createEmbedFields(embed_title: str, **fields):
    embed = Embed(
        title=embed_title,
        color=Color.red(),
    )
    for key, value in fields.items():
        embed.add_field(name=f'{key}', value=f'{value}', inline=False)
    return embed
