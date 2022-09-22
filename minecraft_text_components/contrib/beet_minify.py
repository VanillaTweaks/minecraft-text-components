import dataclasses

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


class MinifyTextComponentTransformer(MutatingReducer):
    """A Mecha dispatcher which minifies `AstJson` nodes that represent text components
    in commands.

    Assumes all root `AstJson` nodes represent text components.
    """

    def __init__(self, ctx: Context):
        self.ctx = ctx
        self.mecha = ctx.inject(Mecha)
        self.processed_commands: set[AstCommand] = set()

        super().__init__()

    def process_argument(self, argument: AstNode, scope: tuple[str, ...]):
        """Returns a minified copy of the `AstJson` node if it was parsed as a text
        component.

        Otherwise returns the original node.
        """

        if not isinstance(argument, AstJson):
            return argument

        command_tree = self.mecha.spec.tree.get(scope)
        if command_tree is None:
            return argument

        if command_tree.parser != "minecraft:component":
            return argument

        initial_text_component = argument.evaluate()
        minified_text_component = minify(initial_text_component)

        if minified_text_component == initial_text_component:
            return argument

        return AstJson.from_value(minified_text_component)

    @rule(AstCommand)
    def minify_components(self, node: AstCommand):
        """Rebuilds a new `AstCommand` from processed arguments.

        If a command has been processed, saves it to an internal set.
        """

        if node in self.processed_commands:
            return node

        prototype = self.mecha.spec.prototypes[node.identifier]
        arguments: list[AstNode] = []
        changed = False

        for i, argument in enumerate(node.arguments):
            scope = prototype.get_argument(i).scope

            processed_argument = self.process_argument(argument, scope)
            if argument is not processed_argument:
                changed = True

            arguments.append(processed_argument)

        if changed:
            node = dataclasses.replace(node, arguments=AstChildren(arguments))

            self.processed_commands.add(node)

        return node


def minify_commands(ctx: Context):
    """Beet plugin to minify all text components found in commands."""

    mecha = ctx.inject(Mecha)
    transformer = ctx.inject(MinifyTextComponentTransformer)

    mecha.optimize.extend(transformer)


def beet_default(ctx: Context):
    ctx.require(minify_commands)
