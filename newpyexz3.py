
import sys
import os
sys.path.insert(0, os.path.abspath("./pyexz3clone"))

import logging
from optparse import OptionParser
from symbolic.loader import loaderFactory
from symbolic.explore import ExplorationEngine

print("PyExZ3 (Python Exploration with Z3)")

sys.path = [os.path.abspath(os.path.join(os.path.dirname(__file__)))] + sys.path

# Set up command-line options
usage = "usage: %prog [options] <path to a *.py file>"
parser = OptionParser(usage=usage)

parser.add_option("-l", "--log", dest="logfile", action="store", help="Save log output to a file", default="")
parser.add_option("-s", "--start", dest="entry", action="store", help="Specify entry point", default="")
parser.add_option("-g", "--graph", dest="dot_graph", action="store_true", help="Generate a DOT graph of execution tree")
parser.add_option("-m", "--max-iters", dest="max_iters", type="int", help="Run specified number of iterations", default=5)
parser.add_option("--cvc", dest="solver", action="store_const", const="cvc", help="Use the CVC SMT solver")
parser.add_option("--z3", dest="solver", action="store_const", const="z3", help="Use the Z3 SMT solver", default="z3")
parser.add_option("-f", "--folder", dest="logfolder", action="store", help="Specify folder to save log files", default="logs")

(options, args) = parser.parse_args()

# Validate input file
if len(args) == 0 or not args[0].endswith(".py") or not os.path.exists(args[0]):
    parser.error("Missing or invalid Python file to execute")
    sys.exit(1)

filename = os.path.abspath(args[0])

# Load the application
app = loaderFactory(filename, options.entry)
if app is None:
    sys.exit(1)

entry_point = app.getEntry()
if entry_point:
    print(f"Exploring {app.getFile()}.{entry_point}")
else:
    print(f"Exploring {app.getFile()} (No specific entry point found)")

# Create the log folder if it doesn't exist
log_folder = os.path.abspath(options.logfolder)
os.makedirs(log_folder, exist_ok=True)

# Initialize variables
solver = options.solver
result = None
total_assertion_errors = 0

try:
    for iteration in range(options.max_iters):
        # Set up logging for this iteration
        log_filename = os.path.join(log_folder, f"iteration_{iteration + 1}.log")
        logger = logging.getLogger(f"Iteration_{iteration + 1}")
        logger.setLevel(logging.DEBUG)

        # Ensure no duplicate handlers
        if not logger.handlers:
            file_handler = logging.FileHandler(log_filename)
            file_handler.setLevel(logging.DEBUG)
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)

        try:
            # Set up the exploration engine
            invocation = app.createInvocation() if entry_point else [filename]
            engine = ExplorationEngine(invocation, solver=solver)
            generatedInputs, returnVals, path = engine.explore(options.max_iters)

            # Check the result
            result = app.executionComplete(returnVals)

            # Generate DOT graph if required
            if options.dot_graph:
                dot_filename = os.path.join(log_folder, f"{os.path.basename(filename)}_{iteration + 1}.dot")
                with open(dot_filename, "w") as file:
                    file.write(path.toDot())

            # Log results of the exploration
            if result is not None and result is not True:
                total_assertion_errors += 1
                logger.error("AssertionError occurred: %s", result)
            else:
                logger.info("Generated Test Cases:")
                for i, test_case in enumerate(generatedInputs):
                    if i < 10:  # Log only the first 10 test cases
                        logger.info(f"Test Case {i + 1}: {test_case}")

        except ImportError as e:
            logger.error("ImportError: %s", e)
            sys.exit(1)

        except AssertionError as e:
            total_assertion_errors += 1
            logger.error("AssertionError occurred: %s", e)
            continue

        except Exception as e:
            logger.error("An unexpected error occurred: %s", e, exc_info=True)
            continue

except Exception as e:
    logging.error("A critical error occurred: %s", e, exc_info=True)

# Calculate and print coverage
if options.max_iters > 0:
    percentage = (total_assertion_errors / options.max_iters) * 100
else:
    percentage = 0

#print(f"Condition Coverage using DSE: {percentage}%")

sys.exit(0)