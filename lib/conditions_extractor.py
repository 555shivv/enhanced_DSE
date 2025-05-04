import ast
import inspect

def extract_conditions_from_function(func):
    """
    Extracts all conditional expressions (from if, elif, and while) 
    in a given function, including nested ones.
    Returns a list of strings representing those conditions.
    """
    source = inspect.getsource(func)
    tree = ast.parse(source)

    class ConditionExtractor(ast.NodeVisitor):
        def __init__(self):
            self.conditions = []

        def visit_If(self, node):
            self.conditions.append(ast.unparse(node.test))  # if/elif condition
            self.generic_visit(node)  # go inside body and orelse

        def visit_While(self, node):
            self.conditions.append(ast.unparse(node.test))  # while loop condition
            self.generic_visit(node)

        def visit_For(self, node):  # Optional: to include loop bounds or iterations
            self.generic_visit(node)

    extractor = ConditionExtractor()
    extractor.visit(tree)
    return extractor.conditions
