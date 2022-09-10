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
    def __init__(self, ctx: Context):
        self.ctx = ctx
        self.processed_commands: set[AstCommand] = set()

        super().__init__()

    def process_arguments(self, arguments: AstChildren[AstNode]):
        for argument in arguments:
            if isinstance(argument, AstJson):
                yield AstJson.from_value(minify(argument.evaluate()))
            else:
                yield argument

    @rule(AstCommand)
    def minify_components(self, node: AstCommand):
        if node not in self.processed_commands:
            self.processed_commands.add(node)
            return AstCommand(
                identifier=node.identifier,
                arguments=AstChildren(self.process_arguments(node.arguments)),
            )
        return node


def beet_default(ctx: Context):
    mc = ctx.inject(Mecha)
    transformer = ctx.inject(MinifyJsonTransformer)

    mc.optimize.extend(transformer)
