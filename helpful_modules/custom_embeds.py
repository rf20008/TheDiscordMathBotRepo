from random import randint

from disnake import Color, Embed


def generate_random_color():
    return Color.from_rgb(r=randint(0, 255), g=randint(0, 255), b=randint(0, 255))


class SimpleEmbed(Embed):
    def __init__(
        self,
        title="",
        description="",
        color: Color | None = None,
        footer=None,
    ):
        if color is None:
            color = generate_random_color()
        super().__init__(title=title, description=description, color=color)
        self.set_footer(text=footer)


class ErrorEmbed(SimpleEmbed):
    def __init__(
        self,
        description="",
        color=Color.red(),
        custom_title=None,
        title=None,
        footer=None,
    ):
        if title is None and custom_title is None:
            custom_title="Error!"
        if title != custom_title and (title is not None and custom_title is not None):
            raise ValueError("Titles don't match")
        if custom_title is None:
            custom_title=title
        elif title is None:
            pass
        super().__init__(title=custom_title, description=description, color=color)
        self.set_footer(text=footer)


class SuccessEmbed(SimpleEmbed):
    def __init__(
        self,
        description="",
        color=Color.green(),
        successTitle=None,
        title=None,
        footer=None,
    ):
        if title is None and successTitle is None:
            successTitle = "Success!"
        if title != successTitle and (title is not None and successTitle is not None):
            raise ValueError("Titles don't match")
        if successTitle is None:
            successTitle=title
        elif title is None:
            pass
        super().__init__(title=successTitle, description=description, color=color)
        self.set_footer(text=footer)
