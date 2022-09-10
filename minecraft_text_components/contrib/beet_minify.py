from beet import Context
from mecha import (
    AstChildren,
    AstCommand,
    AstJson,
    AstNode,
    Mecha,
    MutatingReducer,
    rule,
)

from minecraft_text_components import minify


class MinifyJsonTransformer(MutatingReducer):
    """A Mecha dispatcher which minifies the `AstJson`s nodes inside a command."""

    def __init__(self, ctx: Context):
        self.ctx = ctx
        self.processed_commands: set[AstCommand] = set()

        super().__init__()

    def process_arguments(self, arguments: AstChildren[AstNode]):
        """Yields minified `AstJson` nodes and other nodes are kept the same."""

        for argument in arguments:
            if isinstance(argument, AstJson):
                yield AstJson.from_value(minify(argument.evaluate()))
            else:
                yield argument

    @rule(AstCommand)
    def minify_components(self, node: AstCommand):
        """Rebuilds a new `AstCommand` from processed arguments.

        If a command has been processed, saves it to an internal set.
        """

        if node not in self.processed_commands:
            self.processed_commands.add(node)
            return AstCommand(
                identifier=node.identifier,
                arguments=AstChildren(self.process_arguments(node.arguments)),
            )

        return node


def minify_commands(ctx: Context):
    """Beet plugin to minify all TextComponents found in commands"""

    mc = ctx.inject(Mecha)
    transformer = ctx.inject(MinifyJsonTransformer)

    mc.optimize.extend(transformer)


def beet_default(ctx: Context):
    ctx.require(minify_commands)
